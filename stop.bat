@echo off
REM Stop Message_Info (the start.bat window, or the backend/frontend windows of dev.bat)
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\stop-old.ps1" -Port 8010 >nul 2>&1
echo [OK] Message_Info stopped.
timeout /t 2 >nul
