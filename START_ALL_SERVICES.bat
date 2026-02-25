@echo off
REM Start All AI Employee Services
REM Runs both Gmail and Discord watchers in background

echo ========================================
echo Starting AI Employee Services...
echo ========================================
echo.

REM Start Gmail Integration
echo [1/2] Starting Gmail Integration...
start /B wscript.exe //B "%~dp0gmail-integration\start_gmail_monitor_hidden.vbs"

REM Start Discord/Silver Tier
echo [2/2] Starting Discord Watcher...
start /B wscript.exe //B "%~dp0start_silver_tier_hidden.vbs"

echo.
echo ========================================
echo All services started!
echo ========================================
echo.
echo Running in background:
echo   - Gmail Watcher (polls every 2 min)
echo   - Gmail Orchestrator (approval workflow)
echo   - Discord Watcher (auto-posts to Discord)
echo.
echo Check Logs folder for activity.
echo ========================================
echo.
timeout /t 3
