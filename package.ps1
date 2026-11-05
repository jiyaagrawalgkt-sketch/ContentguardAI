# =================================================================
# ContentGuard AI - Clean Portable ZIP Creation Script
# =================================================================
# Packages the ContentGuard AI project into a clean, lightweight,
# portable ZIP archive ready to share with friends or teammates.
#
# Automatically excludes:
#   - Virtual environments (venv/)
#   - Node.js dependencies (node_modules/)
#   - Next.js build artifacts (.next/)
#   - SQLite database files (*.db)
#   - Personal .env secret files
#   - Python bytecode and pytest cache (__pycache__, .pytest_cache)
#   - User uploaded files
#
# Usage:
#   .\package.ps1
# =================================================================

[CmdletBinding()]
param(
    [string]$OutputFile = "ContentGuardAI-Portable.zip"
)

$ErrorActionPreference = "Stop"
$ProgressPreference = "SilentlyContinue"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ZipPath = Join-Path $ScriptDir $OutputFile
$StageRoot = Join-Path $ScriptDir "tmp_package"
$StageDir = Join-Path $StageRoot "ContentGuardAI"

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

Write-Section "Packaging ContentGuard AI for Clean Portable Distribution"

# Clean previous staging directory if exists
if (Test-Path $StageRoot) {
    Remove-Item -Path $StageRoot -Recurse -Force
}
New-Item -ItemType Directory -Path $StageDir -Force | Out-Null

Write-Host "  Collecting portable project files (excluding builds, venvs, and databases)..." -ForegroundColor White

# Define inclusion and exclusion patterns
$excludePatterns = @(
    "\\venv(\\|$)",
    "\\node_modules(\\|$)",
    "\\\.next(\\|$)",
    "\\__pycache__(\\|$)",
    "\\\.pytest_cache(\\|$)",
    "\\tmp_package(\\|$)",
    "\\uploads\\.+",
    "\.db$",
    "\.sqlite$",
    "\.env$",
    "\.env\.local$",
    "\.running_pids\.json$",
    "\.zip$"
)

$files = Get-ChildItem -Path $ScriptDir -Recurse -File | Where-Object {
    $relPath = $_.FullName.Substring($ScriptDir.Length)
    $shouldExclude = $false
    foreach ($pat in $excludePatterns) {
        if ($relPath -match $pat) {
            $shouldExclude = $true
            break
        }
    }
    -not $shouldExclude
}

$copiedCount = 0
foreach ($file in $files) {
    $relPath = $file.FullName.Substring($ScriptDir.Length).TrimStart("\")
    $targetFile = Join-Path $StageDir $relPath
    $targetParent = Split-Path -Parent $targetFile

    if (-not (Test-Path $targetParent)) {
        New-Item -ItemType Directory -Path $targetParent -Force | Out-Null
    }

    Copy-Item -Path $file.FullName -Destination $targetFile -Force
    $copiedCount++
}

Write-Success "Collected $copiedCount clean source and configuration files"

# Create uploads/.gitkeep in staging if not already present
$stageUploads = Join-Path $StageDir "uploads"
if (-not (Test-Path $stageUploads)) {
    New-Item -ItemType Directory -Path $stageUploads -Force | Out-Null
    Set-Content -Path (Join-Path $stageUploads ".gitkeep") -Value "# Keep directory"
}

# Remove existing zip if present
if (Test-Path $ZipPath) {
    Remove-Item -Path $ZipPath -Force
}

Write-Host "  Compressing into '$OutputFile'..." -ForegroundColor White
Compress-Archive -Path "$StageDir\*" -DestinationPath $ZipPath -CompressionLevel Optimal

# Clean up staging folder
Remove-Item -Path $StageRoot -Recurse -Force

$zipItem = Get-Item $ZipPath
$zipSizeMB = [math]::Round($zipItem.Length / 1MB, 2)

Write-Section "Portable Package Created Successfully!"
Write-Host ""
Write-Host "  Output ZIP:  $ZipPath" -ForegroundColor Green
Write-Host "  File Size:   $zipSizeMB MB" -ForegroundColor Yellow
Write-Host ""
Write-Host "  Ready to share! Your friend simply needs to:" -ForegroundColor White
Write-Host "  1. Extract the ZIP to any folder (e.g., C:\Projects\ContentGuardAI)" -ForegroundColor Cyan
Write-Host "  2. Right-click PowerShell -> 'Run as administrator' (or open regular PowerShell)" -ForegroundColor Cyan
Write-Host "  3. Run: .\setup.ps1" -ForegroundColor Cyan
Write-Host "  4. Run: .\start.ps1" -ForegroundColor Cyan
Write-Host ""
