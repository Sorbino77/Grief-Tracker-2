@echo off
REM ===================================================================
REM  ShipTrack — one-click launcher.
REM  Double-click this file to start the dev server and open the browser.
REM  Hand off the real work to scripts\launch.ps1.
REM ===================================================================
setlocal
cd /d "%~dp0"

powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\launch.ps1" %*
set "EXIT_CODE=%ERRORLEVEL%"

if not "%EXIT_CODE%"=="0" (
    echo.
    echo Launcher exited with code %EXIT_CODE%.
    pause
)
exit /b %EXIT_CODE%
