@echo off
REM Install Gmail Watcher as Windows Task
REM This makes the watcher start automatically when Windows boots

echo ========================================
echo Gmail Watcher - Windows Task Installer
echo ========================================
echo.
echo This will set up Gmail Watcher to:
echo - Start automatically when Windows boots
echo - Run hidden in the background
echo - Monitor Gmail 24/7
echo.
echo NOTE: Right-click this file and select 'Run as Administrator'
echo.
pause

REM Create the task (runs under current user)
schtasks /Create /TN "GmailWatcher" /TR "python.exe -u F:\Tahirah\Hackathon-0\AI_Employee_Vault\gmail-integration\gmail_watcher.py" /SC ONLOGON /RL HIGHEST /F

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ========================================
    echo SUCCESS! Gmail Watcher installed.
    echo ========================================
    echo.
    echo The watcher will now start automatically:
    echo - When Windows boots
    echo - Runs with highest privileges
    echo - Runs hidden in background
    echo.
    echo To check status:
    echo   schtasks /Query /TN GmailWatcher
    echo.
    echo To start manually:
    echo   schtasks /Run /TN GmailWatcher
    echo.
    echo To uninstall:
    echo   schtasks /Delete /TN GmailWatcher /F
    echo.
    echo Logs: F:\Tahirah\Hackathon-0\AI_Employee_Vault\Logs\gmail_watcher.log
    echo.
) else (
    echo.
    echo ERROR: Failed to create Windows task.
    echo Please right-click this file and select 'Run as Administrator'
    echo.
)

pause
