# =================================================================
# ContentGuard AI - Windows Stop Script
# =================================================================
# Safely terminates running FastAPI (port 8000) and Next.js (port 3000)
# development processes without impacting unrelated user applications.
#
# Usage:
#   .\stop.ps1
#
# If execution policy blocks this script, execute with bypass:
#   powershell -ExecutionPolicy Bypass -File .\stop.ps1
# =================================================================

$ErrorActionPreference = "SilentlyContinue"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path

function Write-Section {
    param([string]$Title)
    Write-Host ""
    Write-Host "==================================================================" -ForegroundColor Cyan
    Write-Host "  $Title" -ForegroundColor Cyan
    Write-Host "==================================================================" -ForegroundColor Cyan
}

function Write-Success {
    param([string]$Message)
    Write-Host "  [OK] $Message" -ForegroundColor Green
}

function Write-Notice {
    param([string]$Message)
    Write-Host "  [INFO] $Message" -ForegroundColor Gray
}

Write-Section "ContentGuard AI - Stopping Development Servers"

$stoppedCount = 0

# -----------------------------------------------------------------
# 1. Stop Processes by Recorded Process IDs
# -----------------------------------------------------------------
$PidsFile = Join-Path $ScriptDir ".running_pids.json"
if (Test-Path $PidsFile) {
    try {
        $pidsContent = Get-Content -Path $PidsFile -Raw | ConvertFrom-Json
        if ($pidsContent.BackendPid) {
            $p = Get-Process -Id $pidsContent.BackendPid -ErrorAction SilentlyContinue
            if ($p) {
                # Stop child processes spawned by backend window (e.g., uvicorn, python)
                Get-CimInstance Win32_Process | Where-Object { $_.ParentProcessId -eq $pidsContent.BackendPid } | ForEach-Object {
                    Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue
                }
                Stop-Process -Id $pidsContent.BackendPid -Force -ErrorAction SilentlyContinue
                Write-Success "Stopped Backend host process (PID: $($pidsContent.BackendPid))"
                $stoppedCount++
            }
        }
        if ($pidsContent.FrontendPid) {
            $p = Get-Process -Id $pidsContent.FrontendPid -ErrorAction SilentlyContinue
            if ($p) {
                # Stop child processes spawned by frontend window (e.g., node)
                Get-CimInstance Win32_Process | Where-Object { $_.ParentProcessId -eq $pidsContent.FrontendPid } | ForEach-Object {
                    Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue
                }
                Stop-Process -Id $pidsContent.FrontendPid -Force -ErrorAction SilentlyContinue
                Write-Success "Stopped Frontend host process (PID: $($pidsContent.FrontendPid))"
                $stoppedCount++
            }
        }
    } catch {}
    Remove-Item -Path $PidsFile -Force -ErrorAction SilentlyContinue
}

# -----------------------------------------------------------------
# 2. Port Cleanup: Stop any process still listening on Port 8000
# -----------------------------------------------------------------
try {
    $connections8000 = Get-NetTCPConnection -LocalPort 8000 -State Listen -ErrorAction SilentlyContinue
    if ($connections8000) {
        foreach ($conn in $connections8000) {
            $procId = $conn.OwningProcess
            if ($procId -gt 0) {
                $proc = Get-Process -Id $procId -ErrorAction SilentlyContinue
                if ($proc -and ($proc.ProcessName -match "python|uvicorn|node")) {
                    Stop-Process -Id $procId -Force -ErrorAction SilentlyContinue
                    Write-Success "Released Port 8000 (stopped process '$($proc.ProcessName)' PID: $procId)"
                    $stoppedCount++
                }
            }
        }
    }
} catch {}

# -----------------------------------------------------------------
# 3. Port Cleanup: Stop any process still listening on Port 3000
# -----------------------------------------------------------------
try {
    $connections3000 = Get-NetTCPConnection -LocalPort 3000 -State Listen -ErrorAction SilentlyContinue
    if ($connections3000) {
        foreach ($conn in $connections3000) {
            $procId = $conn.OwningProcess
            if ($procId -gt 0) {
                $proc = Get-Process -Id $procId -ErrorAction SilentlyContinue
                if ($proc -and ($proc.ProcessName -match "node|next")) {
                    Stop-Process -Id $procId -Force -ErrorAction SilentlyContinue
                    Write-Success "Released Port 3000 (stopped process '$($proc.ProcessName)' PID: $procId)"
                    $stoppedCount++
                }
            }
        }
    }
} catch {}

Write-Host ""
if ($stoppedCount -gt 0) {
    Write-Success "ContentGuard AI development servers stopped successfully."
} else {
    Write-Notice "No active ContentGuard AI servers were detected on ports 8000 or 3000."
}
Write-Host ""
