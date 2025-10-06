@echo off
REM Network Monitor - Windows Runner
REM Simple batch file that uses the Python setup script

echo Network Monitor - Windows Setup and Runner
echo ============================================

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python not found. Please install Python from python.org
    pause
    exit /b 1
)

REM Run the Python setup and runner
echo Starting Network Monitor with automatic setup...
python setup_and_run.py --run

pause
