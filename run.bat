@echo off
TITLE Smart Canteen Ordering System
cd /d "%~dp0"

echo =======================================================
echo   Starting Smart Canteen Ordering System...
echo =======================================================

IF NOT EXIST "canteen.db" (
    echo [*] Database not found. Seeding initial data...
    .\venv\Scripts\python.exe seed.py
)

echo [*] Launching web server...
.\venv\Scripts\python.exe wsgi.py

pause
