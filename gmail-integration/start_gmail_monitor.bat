@echo off
REM Gmail Integration Monitor - Background Runner
REM Starts Gmail Monitor (Watcher + Orchestrator) hidden in background

cd /d "%~dp0"

echo Starting Gmail Integration Monitor...
echo Monitor will run 24/7 in the background.
echo.

REM Start the monitor hidden
start /B wscript.exe //B "%~dp0start_gmail_monitor_hidden.vbs"

echo Gmail Integration Monitor started successfully!
echo Check Logs\gmail_monitor.log for details.
timeout /t 3
