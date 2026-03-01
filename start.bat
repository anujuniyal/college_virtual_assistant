@echo off
title EduBot Server Activator
color 0A

echo ========================================
echo     EDUBOT SERVER ACTIVATOR
echo ========================================
echo.
echo Starting EduBot Server and Telegram Bot...
echo.
cd /d "%~dp0"

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found!
    echo Please install Python 3.7 or higher
    pause
    exit /b 1
)

REM Check if required files exist
if not exist "ngrok.exe" (
    echo ERROR: ngrok.exe not found!
    echo Please download ngrok from: https://ngrok.com/download
    pause
    exit /b 1
)

if not exist "wsgi.py" (
    echo ERROR: wsgi.py not found!
    echo Please ensure you're in the correct directory
    pause
    exit /b 1
)

echo.
echo ✅ Requirements checked!
echo 🚀 Starting activation...
echo.

REM Run the activation script
python activate_server.py

echo.
echo ========================================
echo     ACTIVATION COMPLETED
echo ========================================
echo.
echo Thank you for using EduBot!
echo.

pause
