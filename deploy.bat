@echo off
REM Production deployment script for Network Monitor (Windows)

echo 🚀 Starting Network Monitor Production Deployment...

REM Create directories
echo 📁 Creating directories...
if not exist "logs" mkdir logs
if not exist "traces" mkdir traces
if not exist "static\css" mkdir static\css
if not exist "static\js" mkdir static\js

REM Install dependencies
echo 📦 Installing dependencies...
pip install -r requirements.txt

REM Setup environment
echo ⚙️ Setting up environment...
if not exist ".env" (
    echo ⚠️  Creating .env from template...
    copy .env.example .env
    echo 🔧 Please edit .env file with your settings before running!
    pause
    exit /b 1
)

REM Start the application
echo 🚀 Starting Network Monitor...
echo 📊 Starting with Gunicorn (Production Server)...
gunicorn --config gunicorn_config.py wsgi:app

echo ✅ Network Monitor started successfully!
echo.
echo 🌐 Access your monitor at: http://localhost:5000
pause
