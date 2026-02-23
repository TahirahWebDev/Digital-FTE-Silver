@echo off
REM Install Silver Tier Monitor as Windows Task
REM This makes the monitor start automatically when Windows boots

echo ========================================
echo Silver Tier Monitor - Windows Task Installer
echo ========================================
echo.
echo This will set up the Silver Tier Monitor to:
echo - Start automatically when Windows boots
echo - Run hidden in the background
echo - Monitor Silver Tier 24/7
echo.
echo NOTE: Right-click this file and select 'Run as Administrator'
echo.
pause

REM Create the task (runs under current user)
schtasks /Create /TN "SilverTierMonitor" /TR "python.exe -u F:\Tahirah\Hackathon-0\AI_Employee_Vault\silver_tier_monitor.py" /SC ONLOGON /RL HIGHEST /F

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ========================================
    echo SUCCESS! Silver Tier Monitor installed.
    echo ========================================
    echo.
    echo The monitor will now start automatically:
    echo - When Windows boots
    echo - Runs with highest privileges
    echo - Runs hidden in background
    echo.
    echo To check status:
    echo   schtasks /Query /TN SilverTierMonitor
    echo.
    echo To start manually:
    echo   schtasks /Run /TN SilverTierMonitor
    echo.
    echo To uninstall:
    echo   schtasks /Delete /TN SilverTierMonitor /F
    echo.
    echo Logs: F:\Tahirah\Hackathon-0\AI_Employee_Vault\logs\silver_tier_monitor.log
    echo.
) else (
    echo.
    echo ERROR: Failed to create Windows task.
    echo Please right-click this file and select 'Run as Administrator'
    echo.
)

pause
