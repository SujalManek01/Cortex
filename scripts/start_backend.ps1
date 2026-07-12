# Cortex Backend — Start Script
# Run from the project root: .\scripts\start_backend.ps1

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
$BackendDir = Join-Path $Root "backend"

Write-Host ""
Write-Host "  ◈ Cortex Backend" -ForegroundColor Cyan
Write-Host "  Starting FastAPI on http://localhost:8000" -ForegroundColor Gray
Write-Host ""

# Check for Python in virtual environments first
$PythonCmd = "python"
$VenvPaths = @(
    (Join-Path $Root ".venv\Scripts\python.exe"),
    (Join-Path $Root "venv\Scripts\python.exe"),
    (Join-Path $BackendDir ".venv\Scripts\python.exe"),
    (Join-Path $BackendDir "venv\Scripts\python.exe")
)

if ($env:VIRTUAL_ENV) {
    $VenvPython = Join-Path $env:VIRTUAL_ENV "Scripts\python.exe"
    if (Test-Path $VenvPython) {
        $PythonCmd = $VenvPython
    }
} else {
    foreach ($Path in $VenvPaths) {
        if (Test-Path $Path) {
            $PythonCmd = $Path
            break
        }
    }
}

# If no venv python, check if python is in PATH
if ($PythonCmd -eq "python" -and -not (Get-Command python -ErrorAction SilentlyContinue)) {
    Write-Error "Python 3.12+ is required. Install it from https://python.org or configure a virtual environment."
    exit 1
}

# Print resolved Python path/version
if ($PythonCmd -ne "python") {
    Write-Host "  Using Virtual Environment Python: $PythonCmd" -ForegroundColor DarkGray
}
$PythonVersion = & $PythonCmd --version 2>&1
Write-Host "  Python: $PythonVersion" -ForegroundColor DarkGray

# Check if dependencies (fastapi and uvicorn) are installed
Write-Host "  Verifying dependencies..." -ForegroundColor Gray
$CheckDeps = & $PythonCmd -c "import fastapi, uvicorn" 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "" -ForegroundColor Red
    Write-Host "  [ERROR] Missing required dependencies (fastapi, uvicorn)." -ForegroundColor Red
    Write-Host "  Please install them using:" -ForegroundColor Yellow
    Write-Host "  & `"$PythonCmd`" -m pip install -r backend/requirements.txt" -ForegroundColor Yellow
    Write-Host ""
    exit 1
}

# Ensure logs directory exists
$LogsDir = Join-Path $Root "logs"
if (-not (Test-Path $LogsDir)) {
    New-Item -ItemType Directory -Path $LogsDir | Out-Null
}

# Start Uvicorn from project root using python -m uvicorn (so pythonpath includes backend/)
Set-Location $Root
Write-Host "  Starting Uvicorn..." -ForegroundColor Gray
& $PythonCmd -m uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000

