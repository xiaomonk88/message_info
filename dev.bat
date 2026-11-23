@echo off
setlocal
title Message_Info dev
REM ============================================================
REM  Development mode (only needed when editing frontend code):
REM  backend with --reload + Vite dev server with hot reload.
REM  Opens 2 extra windows. For normal use run start.bat instead.
REM ============================================================

set "ROOT=%~dp0"
cd /d "%ROOT%"

if not exist "%ROOT%backend\.venv\Scripts\python.exe" (
    echo [ERROR] Backend venv not found. Run start.bat once first.
    pause
    exit /b 1
)
where npm >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Node.js / npm not found. Install Node.js 18+ from https://nodejs.org/
    pause
    exit /b 1
)
if not exist "%ROOT%frontend\node_modules" (
    pushd "%ROOT%frontend"
    call npm install
    popd
)

powershell -NoProfile -ExecutionPolicy Bypass -File "%ROOT%scripts\stop-old.ps1" -Port 8010 >nul 2>&1

start "message_info-backend" cmd /k "cd /d %ROOT%backend && .venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 8010"
start "message_info-frontend" cmd /k "cd /d %ROOT%frontend && npm run dev"

timeout /t 4 >nul
start "" "http://localhost:5173"
exit /b 0
