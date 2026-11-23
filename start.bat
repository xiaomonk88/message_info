@echo off
setlocal
title Message_Info
REM ============================================================
REM  Message_Info - one window launcher
REM  - Backend (FastAPI) serves the API AND the built frontend
REM    on ONE port. Everything runs in THIS window.
REM  - Frontend is rebuilt automatically when its source changed.
REM  - Stop: close this window or press Ctrl+C.
REM  - For frontend hot-reload development use dev.bat instead.
REM ============================================================

set "ROOT=%~dp0"
set "PORT=8010"
REM 127.0.0.1 = this computer only; 0.0.0.0 = allow other machines
set "HOST=127.0.0.1"

cd /d "%ROOT%"
if not exist "%ROOT%backend\tmp" mkdir "%ROOT%backend\tmp"
set "TEMP=%ROOT%backend\tmp"
set "TMP=%ROOT%backend\tmp"

echo.
echo  Message_Info is starting ...
echo.

REM ---------- 1. .env ----------
if exist ".env" goto env_ok
if not exist ".env.example" (
    echo [ERROR] .env.example missing.
    goto fail
)
copy ".env.example" ".env" >nul
echo [setup] Created .env from .env.example
:env_ok

REM ---------- 2. Backend venv ----------
set "VENV_PY=%ROOT%backend\.venv\Scripts\python.exe"
if not exist "%VENV_PY%" goto make_venv
REM venv copied from another machine/folder: python may run but packages fail to load
"%VENV_PY%" -c "import sys; assert (3,10) <= sys.version_info < (3,15); import uvicorn, fastapi, sqlalchemy, pydantic_settings, jose, cryptography, paramiko" >nul 2>&1
if not errorlevel 1 goto venv_ok
echo [setup] Existing venv is broken, copied from elsewhere, or missing packages. Recreating ...
rmdir /s /q "%ROOT%backend\.venv"

:make_venv
set "PY_CMD="
for %%V in (3.14 3.13 3.12 3.11 3.10) do (
    if not defined PY_CMD (
        py -%%V --version >nul 2>&1 && set "PY_CMD=py -%%V"
    )
)
if defined PY_CMD goto have_py
python -c "import sys; sys.exit(0 if (3,10) <= sys.version_info < (3,15) else 1)" >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python 3.10 - 3.14 not found. Please install Python first.
    goto fail
)
set "PY_CMD=python"
:have_py
echo [setup] First run: creating Python venv with %PY_CMD% ...
pushd "%ROOT%backend"
%PY_CMD% -m venv .venv
if errorlevel 1 (
    popd
    echo [ERROR] Failed to create venv.
    goto fail
)
echo [setup] Installing backend dependencies, please wait ...
.venv\Scripts\python.exe -m pip install --upgrade pip >nul
.venv\Scripts\python.exe -m pip install -r requirements.txt
if errorlevel 1 (
    popd
    echo [ERROR] Failed to install backend dependencies.
    goto fail
)
popd
:venv_ok

REM ---------- 3. Frontend build (only when missing or outdated) ----------
if not exist "%ROOT%frontend\dist\index.html" goto do_build
powershell -NoProfile -ExecutionPolicy Bypass -File "%ROOT%scripts\frontend-stale.ps1" "%ROOT%frontend" >nul 2>&1
if errorlevel 1 goto do_build
goto build_ok

:do_build
where npm >nul 2>&1
if not errorlevel 1 goto npm_ok
if exist "%ROOT%frontend\dist\index.html" (
    echo [warn] Frontend source changed but Node.js is not installed - using the old build.
    goto build_ok
)
echo [ERROR] Frontend is not built and Node.js / npm is not installed.
echo         Install Node.js 18+ from https://nodejs.org/
goto fail

:npm_ok
echo [build] Frontend changed, building ... (about 10-30 s)
pushd "%ROOT%frontend"
if not exist "node_modules" (
    echo [build] Installing frontend dependencies ...
    call npm install
)
call npm run build
set "BUILD_ERR=%errorlevel%"
popd
if not "%BUILD_ERR%"=="0" (
    echo [ERROR] Frontend build failed, see messages above.
    goto fail
)
:build_ok

REM ---------- 4. Stop old instances (old 2-window launcher, previous runs) ----------
powershell -NoProfile -ExecutionPolicy Bypass -File "%ROOT%scripts\stop-old.ps1" -Port %PORT% >nul 2>&1

REM ---------- 5. Run ----------
set "STATIC_DIR=%ROOT%frontend\dist"

echo.
echo  ====================================================
echo   Message_Info is running
echo   Open : http://localhost:%PORT%
echo   Stop : close this window, or press Ctrl+C
echo  ====================================================
echo.

REM open the browser once the server answers (background, no extra window)
start "" /b powershell -NoProfile -ExecutionPolicy Bypass -File "%ROOT%scripts\open-when-ready.ps1" -Port %PORT%

cd /d "%ROOT%backend"
"%VENV_PY%" -m uvicorn app.main:app --host %HOST% --port %PORT%

echo.
echo  Message_Info stopped.
pause
exit /b 0

:fail
echo.
pause
exit /b 1
