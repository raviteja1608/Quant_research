@echo off
REM ============================================================================
REM Simple Price Alert Service Launcher
REM Just double-click this file to start the service
REM ============================================================================

echo.
echo ============================================================================
echo   Starting Price Alert Service
echo ============================================================================
echo.
echo Make sure IBKR TWS or Gateway is running before starting!
echo.
echo The service will run in this window.
echo Press Ctrl+C to stop the service.
echo.
echo ============================================================================
echo.

REM Change to the script directory
cd /d "%~dp0"

REM Run the Python script with the correct Python executable
"C:\Users\ravit\AppData\Local\Programs\Python\Python314\python.exe" price_alert_service.py

echo.
echo ============================================================================
echo Service stopped.
echo ============================================================================
pause
