@echo off
title EduBot 24x7 Monitor
color 0A
echo.
echo ========================================
echo     EduBot 24x7 Auto Monitor
echo ========================================
echo.
echo Starting 24x7 monitoring service...
echo This will keep your bot running continuously
echo.
echo Press Ctrl+C to stop monitoring
echo.
echo ========================================
echo.

REM Change to the correct directory
cd /d "%~dp0"

REM Start the Python monitor
python run_24x7.py

echo.
echo ========================================
echo     Monitoring Stopped
echo ========================================
echo.
pause
