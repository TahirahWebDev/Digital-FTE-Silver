@echo off
REM Silver Tier Autonomous Monitor - Windows Startup Script
REM This script starts the Silver Tier Monitor hidden in the background

cd /d "%~dp0"

echo Starting Silver Tier Autonomous Monitor...
echo Monitor will run 24/7 in the background.
echo.

REM Start the monitor in a hidden window using VBScript
start /B wscript.exe //B "%~dp0start_monitor_hidden.vbs"

echo Monitor started successfully!
echo Check logs\silver_tier_monitor.log for details.
timeout /t 3
