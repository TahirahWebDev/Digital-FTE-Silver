@echo off
REM Install Gmail Integration Monitor as Windows Task
REM This makes the monitor start automatically when Windows boots

echo ========================================
echo Gmail Integration Monitor - Windows Task Installer
echo ========================================
echo.
echo This will set up Gmail Monitor to:
echo - Start automatically when Windows boots
echo - Run hidden in the background
echo - Monitor Gmail Watcher and Orchestrator 24/7
echo - Auto-recover from failures
echo.
echo NOTE: Right-click this file and select 'Run as Administrator'
echo.
pause

REM Create the task (runs under current user)
schtasks /Create /TN "GmailIntegrationMonitor" /TR "python.exe -u F:\Tahirah\Hackathon-0\AI_Employee_Vault\gmail-integration\gmail_monitor.py" /SC ONLOGON /RL HIGHEST /F

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ========================================
    echo SUCCESS! Gmail Integration Monitor installed.
    echo ========================================
    echo.
    echo The monitor will now start automatically:
    echo - When Windows boots
    echo - Runs with highest privileges
    echo - Runs hidden in background
    echo - Manages Gmail Watcher and Orchestrator
    echo.
    echo To check status:
    echo   schtasks /Query /TN GmailIntegrationMonitor
    echo.
    echo To start manually:
    echo   schtasks /Run /TN GmailIntegrationMonitor
    echo.
    echo To uninstall:
    echo   schtasks /Delete /TN GmailIntegrationMonitor /F
    echo.
    echo Logs: F:\Tahirah\Hackathon-0\AI_Employee_Vault\Logs\gmail_monitor.log
    echo.
) else (
    echo.
    echo ERROR: Failed to create Windows task.
    echo Please right-click this file and select 'Run as Administrator'
    echo.
)

pause
