<#
.SYNOPSIS
  Starts the Flask API (Back End) and Next.js dashboard in separate PowerShell windows.

.EXAMPLE
  .\run-all.ps1
#>

$ErrorActionPreference = "Stop"
$Root = if ($PSScriptRoot) { $PSScriptRoot } else { Split-Path -Parent $MyInvocation.MyCommand.Path }

$BackendDir = Join-Path $Root "Back End"
$FrontendDir = Join-Path $Root "next-shadcn-dashboard-starter"

if (-not (Test-Path $BackendDir)) {
    Write-Error "Back End folder not found: $BackendDir"
}
if (-not (Test-Path $FrontendDir)) {
    Write-Error "next-shadcn-dashboard-starter folder not found: $FrontendDir"
}

$venvPython = Join-Path $BackendDir ".venv\Scripts\python.exe"
if (Test-Path $venvPython) {
    $pythonCmd = "& `"$venvPython`" index.py"
} else {
    $pythonCmd = "python index.py"
}

Write-Host "Starting Flask API in a new window (port 5000)..." -ForegroundColor Cyan
Start-Process powershell -WorkingDirectory $BackendDir -ArgumentList @(
    "-NoExit",
    "-Command",
    "$pythonCmd"
)

Start-Sleep -Seconds 2

Write-Host "Starting Next.js in a new window (see terminal for URL, usually http://localhost:3000)..." -ForegroundColor Cyan
Start-Process powershell -WorkingDirectory $FrontendDir -ArgumentList @(
    "-NoExit",
    "-Command",
    "npm run dev"
)

Write-Host ""
Write-Host "Two windows should open. Close each window to stop that service." -ForegroundColor Green
Write-Host "Ensure Back End/.env and next-shadcn-dashboard-starter/.env.local are configured." -ForegroundColor DarkGray
