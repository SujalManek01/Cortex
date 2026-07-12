# Cortex Frontend — Start Script
# Run from the project root: .\scripts\start_frontend.ps1

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
$FrontendDir = Join-Path $Root "frontend"

Write-Host ""
Write-Host "  ◈ Cortex Frontend" -ForegroundColor Cyan
Write-Host "  Starting Vite dev server on http://localhost:5173" -ForegroundColor Gray
Write-Host ""

# Check Node
if (-not (Get-Command node -ErrorAction SilentlyContinue)) {
    Write-Error "Node.js 18+ is required. Install it from https://nodejs.org"
    exit 1
}

$NodeVersion = node --version 2>&1
Write-Host "  Node: $NodeVersion" -ForegroundColor DarkGray

# Install npm dependencies if node_modules doesn't exist
$NodeModules = Join-Path $FrontendDir "node_modules"
if (-not (Test-Path $NodeModules)) {
    Write-Host "  Installing npm dependencies..." -ForegroundColor DarkGray
    Set-Location $FrontendDir
    npm install
} else {
    Set-Location $FrontendDir
}

# Start Vite dev server
npm run dev
