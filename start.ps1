# =================================================================
# ContentGuard AI - Windows Startup Script
# =================================================================
# Launches backend FastAPI and frontend Next.js development servers
# in separate designated PowerShell windows.
#
# Usage:
#   .\start.ps1
#
# If execution policy blocks this script, execute with bypass:
#   powershell -ExecutionPolicy Bypass -File .\start.ps1
# =================================================================

$ErrorActionPreference = "Continue"
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

function Write-WarningMsg {
    param([string]$Message)
    Write-Host "  [WARNING] $Message" -ForegroundColor Yellow
}

function Write-ErrorMsg {
    param([string]$Message)
    Write-Host "  [ERROR] $Message" -ForegroundColor Red
}

Write-Section "ContentGuard AI - Starting Development Servers"

# -----------------------------------------------------------------
# 1. Dependency Pre-Flight Checks
# -----------------------------------------------------------------
$VenvPython = Join-Path $ScriptDir "backend\venv\Scripts\python.exe"
if (-not (Test-Path $VenvPython)) {
    Write-ErrorMsg "Backend virtual environment not found at 'backend\venv'."
    Write-Host "  Please run the setup script first: .\setup.ps1" -ForegroundColor Yellow
    exit 1
}

$NodeModulesDir = Join-Path $ScriptDir "frontend\node_modules"
if (-not (Test-Path $NodeModulesDir)) {
    Write-ErrorMsg "Frontend node_modules not found at 'frontend\node_modules'."
    Write-Host "  Please run the setup script first: .\setup.ps1" -ForegroundColor Yellow
    exit 1
}

# -----------------------------------------------------------------
# 2. Port Conflict Checks (Port 8000 and Port 3000)
# -----------------------------------------------------------------
$port8000Occupied = $false
$port3000Occupied = $false

try {
    $conn8000 = Get-NetTCPConnection -LocalPort 8000 -State Listen -ErrorAction SilentlyContinue
    if ($conn8000) { $port8000Occupied = $true }
} catch {}

try {
    $conn3000 = Get-NetTCPConnection -LocalPort 3000 -State Listen -ErrorAction SilentlyContinue
    if ($conn3000) { $port3000Occupied = $true }
} catch {}

if ($port8000Occupied) {
    Write-WarningMsg "Port 8000 (Backend) is currently in use."
    Write-Host "  If ContentGuard AI is already running, run '.\stop.ps1' to stop previous instances." -ForegroundColor Gray
}

if ($port3000Occupied) {
    Write-WarningMsg "Port 3000 (Frontend) is currently in use."
    Write-Host "  If ContentGuard AI is already running, run '.\stop.ps1' to stop previous instances." -ForegroundColor Gray
}

# -----------------------------------------------------------------
# 3. Launch Backend (FastAPI on Port 8000)
# -----------------------------------------------------------------
Write-Host "`nStarting Backend FastAPI Server (Port 8000)..." -ForegroundColor White
$BackendDir = Join-Path $ScriptDir "backend"
$BackendCmd = "Set-Location '$BackendDir'; `$host.UI.RawUI.WindowTitle = 'ContentGuard AI - Backend (Port 8000)'; Write-Host 'Starting ContentGuard AI Backend...' -ForegroundColor Cyan; .\venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload"

$backendProcess = Start-Process powershell -ArgumentList "-NoExit", "-ExecutionPolicy", "Bypass", "-Command", $BackendCmd -PassThru
Write-Success "Backend server launched (Process ID: $($backendProcess.Id))"

# -----------------------------------------------------------------
# 4. Launch Frontend (Next.js on Port 3000)
# -----------------------------------------------------------------
Write-Host "Starting Frontend Next.js Server (Port 3000)..." -ForegroundColor White
$FrontendDir = Join-Path $ScriptDir "frontend"

# Clean any conflicting build cache to prevent Windows EPERM / locked layout.js errors
$NextDir = Join-Path $FrontendDir ".next"
if (Test-Path $NextDir) {
    try {
        Remove-Item -Path $NextDir -Recurse -Force -ErrorAction SilentlyContinue
    } catch {}
}

$FrontendCmd = "Set-Location '$FrontendDir'; `$host.UI.RawUI.WindowTitle = 'ContentGuard AI - Frontend (Port 3000)'; Write-Host 'Starting ContentGuard AI Frontend...' -ForegroundColor Cyan; npm run dev"

$frontendProcess = Start-Process powershell -ArgumentList "-NoExit", "-ExecutionPolicy", "Bypass", "-Command", $FrontendCmd -PassThru
Write-Success "Frontend server launched (Process ID: $($frontendProcess.Id))"

# -----------------------------------------------------------------
# 5. Persist Process IDs for Safe Termination
# -----------------------------------------------------------------
$pidsData = @{
    BackendPid = $backendProcess.Id
    FrontendPid = $frontendProcess.Id
    Timestamp = (Get-Date).ToString("o")
}
$PidsFile = Join-Path $ScriptDir ".running_pids.json"
$pidsData | ConvertTo-Json | Set-Content -Path $PidsFile -Force

# -----------------------------------------------------------------
# 6. Status and Endpoint URLs
# -----------------------------------------------------------------
Write-Section "ContentGuard AI is Live!"
Write-Host ""
Write-Host "  Web Application:   http://localhost:3000" -ForegroundColor Cyan
Write-Host "  Backend API:       http://127.0.0.1:8000" -ForegroundColor Cyan
Write-Host "  API Documentation: http://127.0.0.1:8000/api/v1/docs" -ForegroundColor Cyan
Write-Host ""
Write-Host "  Pre-Configured Demo Accounts:" -ForegroundColor White
Write-Host "    - Admin:    admin@contentguard.demo    / Demo@123" -ForegroundColor Yellow
Write-Host "    - Reviewer: reviewer@contentguard.demo / Demo@123" -ForegroundColor Yellow
Write-Host "    - Creator:  creator@contentguard.demo  / Demo@123" -ForegroundColor Yellow
Write-Host ""
Write-Host "  To stop all servers cleanly:" -ForegroundColor White
Write-Host "    .\stop.ps1" -ForegroundColor Green
Write-Host ""
