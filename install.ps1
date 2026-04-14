$ErrorActionPreference = "Stop"

$repoRoot = $PSScriptRoot
Set-Location $repoRoot

$venvPython = Join-Path $repoRoot ".venv\Scripts\python.exe"

if (-not (Test-Path $venvPython)) {
    Write-Host "Creating virtual environment in .venv ..."
    python -m venv .venv
}

$venvPython = Join-Path $repoRoot ".venv\Scripts\python.exe"

Write-Host "Installing/Updating dependencies ..."
& $venvPython -m pip install --upgrade pip
& $venvPython -m pip install -r requirements.txt
& $venvPython -m pip install -r requirements-dev.txt

Write-Host "Installing Playwright Chromium ..."
& $venvPython -m playwright install chromium

Write-Host ""
Write-Host "Setup complete."
Write-Host "Run the report with: .\\run_report.ps1"