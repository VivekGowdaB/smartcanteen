# PowerShell runner for Smart Canteen Ordering System
$ErrorActionPreference = "Stop"

Set-Location $PSScriptRoot

Write-Host "=======================================================" -ForegroundColor Cyan
Write-Host "  Starting Smart Canteen Ordering System...            " -ForegroundColor Cyan
Write-Host "=======================================================" -ForegroundColor Cyan

if (-not (Test-Path "canteen.db")) {
    Write-Host "[*] Database not found. Seeding initial data..." -ForegroundColor Yellow
    & ".\venv\Scripts\python.exe" seed.py
}

Write-Host "[*] Launching web server..." -ForegroundColor Green
& ".\venv\Scripts\python.exe" wsgi.py
