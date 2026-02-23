@echo off
REM Install MCP Config for Qwen Code
REM This copies the MCP configuration to Qwen Code's global config location

echo Installing Discord MCP Server for Qwen Code...
echo.

REM Create Qwen config directory if it doesn't exist
mkdir "%APPDATA%\Qwen" 2>nul

REM Copy the mcp.json file
copy /Y "%~dp0discord-mcp-server\mcp.json" "%APPDATA%\Qwen\mcp.json"

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ========================================
    echo SUCCESS! MCP config installed.
    echo ========================================
    echo.
    echo Location: %APPDATA%\Qwen\mcp.json
    echo.
    echo NEXT STEPS:
    echo 1. Close Qwen Code if it's open
    echo 2. Reopen Qwen Code
    echo 3. Tell Qwen: "Send a Discord message saying 'Test!'"
    echo.
) else (
    echo.
    echo ERROR: Failed to copy config file
    echo.
)

pause
