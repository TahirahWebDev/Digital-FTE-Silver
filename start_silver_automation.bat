@echo off
REM Silver Tier Auto-Runner
REM Keeps the watcher running in the background

cd /d "%~dp0"

echo ========================================
echo Silver Tier Automation - Starting...
echo ========================================
echo.
echo This will watch the 04_Approved folder
echo and auto-post to Discord when files appear.
echo.
echo Press Ctrl+C to stop.
echo ========================================
echo.

python run_silver_tier.py

pause
