@echo off
REM Gmail Watcher - Background Runner
REM Starts Gmail Watcher hidden in background

cd /d "%~dp0"

echo Starting Gmail Watcher...
echo Watcher will run 24/7 in the background.
echo.

REM Start the watcher hidden
start /B wscript.exe //B "%~dp0start_gmail_watcher_hidden.vbs"

echo Gmail Watcher started successfully!
echo Check logs\gmail_watcher.log for details.
timeout /t 3
