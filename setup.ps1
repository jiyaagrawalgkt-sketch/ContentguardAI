# =================================================================
# ContentGuard AI - Windows Automatic Setup Script
# =================================================================
# Description: Automates prerequisite checks, virtual environment
#              creation, dependency installation, environment setup,
#              and database initialization on any Windows computer.
#
# Usage:
#   .\setup.ps1
#
# If execution policy blocks this script, execute with bypass:
#   powershell -ExecutionPolicy Bypass -File .\setup.ps1
# =================================================================

[CmdletBinding()]
param(
    [switch]$SkipDemoSeed = $false,
    [switch]$NonInteractive = $false
)

# Use Continue so native command stderr output (e.g. warnings) does not cause NativeCommandError
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

Write-Section "ContentGuard AI - Cross-Device Setup and Installation"
Write-Host "Target Directory: $ScriptDir" -ForegroundColor Gray

# -----------------------------------------------------------------
# 1. Prerequisite Check: Python
# -----------------------------------------------------------------
Write-Host "`nStep 1/6: Verifying Python installation..." -ForegroundColor White

$PythonCmd = $null
if (Get-Command python -ErrorAction SilentlyContinue) {
    $PythonCmd = "python"
} elseif (Get-Command py -ErrorAction SilentlyContinue) {
    $PythonCmd = "py"
}

if (-not $PythonCmd) {
    Write-ErrorMsg "Python was not detected on this system."
    Write-Host ""
    Write-Host "  How to install Python:" -ForegroundColor Yellow
    Write-Host "  1. Download Python 3.11+ from: https://www.python.org/downloads/" -ForegroundColor White
    Write-Host "  2. Run the installer." -ForegroundColor White
    Write-Host "  3. CRITICAL: Check the box 'Add python.exe to PATH' at the bottom of the setup window." -ForegroundColor Yellow
    Write-Host "  4. Restart your PowerShell window and re-run .\setup.ps1" -ForegroundColor White
    exit 1
}

try {
    $pyVerOutput = & $PythonCmd --version 2>&1
    Write-Success "Found Python: $pyVerOutput"
} catch {
    Write-ErrorMsg "Failed to query Python version: $_"
    exit 1
}

# -----------------------------------------------------------------
# 2. Prerequisite Check: Node.js and npm
# -----------------------------------------------------------------
Write-Host "`nStep 2/6: Verifying Node.js and npm installation..." -ForegroundColor White

if (-not (Get-Command node -ErrorAction SilentlyContinue)) {
    Write-ErrorMsg "Node.js was not detected on this system."
    Write-Host ""
    Write-Host "  How to install Node.js:" -ForegroundColor Yellow
    Write-Host "  1. Download the LTS version from: https://nodejs.org/" -ForegroundColor White
    Write-Host "  2. Complete the standard installer (npm is included automatically)." -ForegroundColor White
    Write-Host "  3. Restart your PowerShell window and re-run .\setup.ps1" -ForegroundColor White
    exit 1
}

if (-not (Get-Command npm -ErrorAction SilentlyContinue)) {
    Write-ErrorMsg "npm was not detected on this system."
    Write-Host "  Please install or reinstall Node.js LTS from: https://nodejs.org/" -ForegroundColor Yellow
    exit 1
}

$nodeVer = & node --version 2>&1
$npmVer = & npm --version 2>&1
Write-Success "Found Node.js: $nodeVer"
Write-Success "Found npm: v$npmVer"

# -----------------------------------------------------------------
# 3. Environment Configuration Files (.env)
# -----------------------------------------------------------------
Write-Host "`nStep 3/6: Setting up environment configuration..." -ForegroundColor White

$BackendEnv = Join-Path $ScriptDir "backend\.env"
$BackendEnvExample = Join-Path $ScriptDir "backend\.env.example"
$FrontendEnv = Join-Path $ScriptDir "frontend\.env.local"
$FrontendEnvExample = Join-Path $ScriptDir "frontend\.env.example"

if (-not (Test-Path $BackendEnv)) {
    if (Test-Path $BackendEnvExample) {
        Copy-Item -Path $BackendEnvExample -Destination $BackendEnv
        Write-Success "Created 'backend\.env' from template (.env.example)"
    } else {
        Write-WarningMsg "'backend\.env.example' was missing. Skipping backend .env creation."
    }
} else {
    Write-Success "Existing 'backend\.env' detected (preserved without overwriting)"
}

if (-not (Test-Path $FrontendEnv)) {
    if (Test-Path $FrontendEnvExample) {
        Copy-Item -Path $FrontendEnvExample -Destination $FrontendEnv
        Write-Success "Created 'frontend\.env.local' from template (.env.example)"
    } else {
        Write-WarningMsg "'frontend\.env.example' was missing. Skipping frontend .env.local creation."
    }
} else {
    Write-Success "Existing 'frontend\.env.local' detected (preserved without overwriting)"
}

# -----------------------------------------------------------------
# 4. Backend Virtual Environment & Dependencies
# -----------------------------------------------------------------
Write-Host "`nStep 4/6: Configuring Python virtual environment..." -ForegroundColor White

$VenvDir = Join-Path $ScriptDir "backend\venv"
$VenvPython = Join-Path $VenvDir "Scripts\python.exe"
$VenvPip = Join-Path $VenvDir "Scripts\pip.exe"

if (-not (Test-Path $VenvPython)) {
    Write-Host "  Creating virtual environment at backend\venv..." -ForegroundColor Gray
    & $PythonCmd -m venv $VenvDir
    if ($LASTEXITCODE -ne 0) {
        Write-ErrorMsg "Failed to create Python virtual environment."
        exit 1
    }
    Write-Success "Created virtual environment at 'backend\venv'"
} else {
    Write-Success "Existing virtual environment detected at 'backend\venv'"
}

Write-Host "  Checking backend Python dependencies..." -ForegroundColor Gray
$RequirementsFile = Join-Path $ScriptDir "backend\requirements.txt"
$FastapiPkg1 = Join-Path $ScriptDir "backend\venv\Lib\site-packages\fastapi"
$FastapiPkg2 = Join-Path $ScriptDir "backend\venv\lib\site-packages\fastapi"

if ((Test-Path $FastapiPkg1) -or (Test-Path $FastapiPkg2)) {
    Write-Success "Backend dependencies are already installed"
} else {
    Write-Host "  Installing backend Python dependencies via pip (this may take 1-2 minutes)..." -ForegroundColor Gray
    & $VenvPip install -r $RequirementsFile --disable-pip-version-check
    if ($LASTEXITCODE -ne 0) {
        Write-ErrorMsg "Backend dependency installation failed. Please check internet connection and retry."
        exit 1
    }
    Write-Success "Backend dependencies installed successfully"
}

# Ensure uploads folder exists
$UploadsDir = Join-Path $ScriptDir "uploads"
if (-not (Test-Path $UploadsDir)) {
    New-Item -ItemType Directory -Path $UploadsDir -Force | Out-Null
    Write-Success "Created uploads storage directory at 'uploads/'"
}

# -----------------------------------------------------------------
# 5. Frontend Node.js Dependencies
# -----------------------------------------------------------------
Write-Host "`nStep 5/6: Installing frontend dependencies..." -ForegroundColor White
$FrontendDir = Join-Path $ScriptDir "frontend"
$NodeModulesDir = Join-Path $FrontendDir "node_modules"

if (-not (Test-Path $NodeModulesDir)) {
    Write-Host "  Installing npm packages in 'frontend/' (this may take 1-2 minutes)..." -ForegroundColor Gray
    Push-Location $FrontendDir
    try {
        & npm install --silent
        if ($LASTEXITCODE -ne 0) {
            Write-WarningMsg "Silent npm install returned non-zero code. Retrying..."
            & npm install
        }
    } finally {
        Pop-Location
    }
    Write-Success "Frontend packages installed successfully"
} else {
    Write-Success "Frontend 'node_modules' already present"
}

# -----------------------------------------------------------------
# 6. Database Initialization & Optional Demo Seeding
# -----------------------------------------------------------------
Write-Host "`nStep 6/6: Initializing database and tables..." -ForegroundColor White

Push-Location (Join-Path $ScriptDir "backend")
try {
    # Initialize all 16 relational database tables using python command
    $initScript = "from app.core.database import init_db; init_db(); print('Tables ready.')"
    & $VenvPython -c $initScript
    if ($LASTEXITCODE -eq 0) {
        Write-Success "Database tables initialized successfully"
    } else {
        Write-ErrorMsg "Failed to initialize database tables."
        exit 1
    }

    # Optional demo seed prompt
    $shouldSeed = $false
    if ($SkipDemoSeed) {
        Write-Host "  Skipping demo seeding as requested (-SkipDemoSeed flag)." -ForegroundColor Gray
    } elseif ($NonInteractive) {
        $shouldSeed = $true
    } else {
        Write-Host ""
        Write-Host "  Would you like to seed the database with demo accounts and brand rules?" -ForegroundColor Yellow
        Write-Host "  - Includes: Admin (admin@contentguard.demo), Reviewer, Creator, and Acme Global brand rules." -ForegroundColor Gray
        Write-Host "  - Choose 'Y' for demonstration / evaluation; choose 'N' to start completely blank." -ForegroundColor Gray
        $response = Read-Host "  Seed demo accounts now? [Y/n] (Default: Y)"
        if ([string]::IsNullOrWhiteSpace($response) -or $response.Trim().ToLower() -eq "y" -or $response.Trim().ToLower() -eq "yes") {
            $shouldSeed = $true
        }
    }

    if ($shouldSeed) {
        Write-Host "  Seeding demo accounts and brand knowledge vault..." -ForegroundColor Gray
        & $VenvPython "scripts\seed_demo.py"
        if ($LASTEXITCODE -eq 0) {
            Write-Success "Demo data seeded successfully"
        } else {
            Write-WarningMsg "Demo seeding returned non-zero code. Database tables remain ready."
        }
    } else {
        Write-Success "Fresh clean database ready for new registrations"
    }
} finally {
    Pop-Location
}

# -----------------------------------------------------------------
# Setup Complete Summary
# -----------------------------------------------------------------
Write-Section "Setup Complete! ContentGuard AI is Ready"
Write-Host ""
Write-Host "  How to start the application:" -ForegroundColor White
Write-Host "    .\start.ps1" -ForegroundColor Green
Write-Host ""
Write-Host "  Access Endpoints:" -ForegroundColor White
Write-Host "    - Web Application:       http://localhost:3000" -ForegroundColor Cyan
Write-Host "    - Backend API:           http://127.0.0.1:8000" -ForegroundColor Cyan
Write-Host "    - API Documentation:     http://127.0.0.1:8000/api/v1/docs" -ForegroundColor Cyan
Write-Host ""
if ($shouldSeed) {
    Write-Host "  Demo Credentials:" -ForegroundColor White
    Write-Host "    - Admin:    admin@contentguard.demo    / Demo@123" -ForegroundColor Yellow
    Write-Host "    - Reviewer: reviewer@contentguard.demo / Demo@123" -ForegroundColor Yellow
    Write-Host "    - Creator:  creator@contentguard.demo  / Demo@123" -ForegroundColor Yellow
    Write-Host ""
}
Write-Host "  Configuration Notes:" -ForegroundColor White
Write-Host "    - Default Database: Zero-config SQLite ('backend\contentguard.db')." -ForegroundColor Gray
Write-Host "    - PostgreSQL: Set 'DATABASE_URL' in 'backend\.env' anytime." -ForegroundColor Gray
Write-Host "    - Google Gemini AI: Add 'GEMINI_API_KEY' in 'backend\.env' (Optional)." -ForegroundColor Gray
Write-Host "      (If omitted, deterministic rule engine runs with 100% functionality)." -ForegroundColor Gray
Write-Host ""
Write-Host "  To stop running processes anytime:" -ForegroundColor White
Write-Host "    .\stop.ps1" -ForegroundColor Green
Write-Host ""
