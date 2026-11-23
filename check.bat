@echo off
title message_info diagnostic
echo.
echo ===========================================
echo  message_info Environment Diagnostic
echo ===========================================
echo.
echo [Current directory]
cd
echo.
echo [Python]
where python 2>nul
python --version 2>nul
if errorlevel 1 echo   ^>^> python NOT FOUND ^<^<
echo.
echo [Node.js]
where node 2>nul
node --version 2>nul
if errorlevel 1 echo   ^>^> node NOT FOUND ^<^<
echo.
echo [npm]
where npm 2>nul
call npm --version 2>nul
if errorlevel 1 echo   ^>^> npm NOT FOUND ^<^<
echo.
echo [Project files]
if exist .env                              (echo   .env: OK)                              else echo   .env: MISSING
if exist .env.example                      (echo   .env.example: OK)                      else echo   .env.example: MISSING
if exist backend\app\main.py               (echo   backend\app\main.py: OK)               else echo   backend\app\main.py: MISSING
if exist backend\requirements.txt          (echo   backend\requirements.txt: OK)          else echo   backend\requirements.txt: MISSING
if exist frontend\package.json             (echo   frontend\package.json: OK)             else echo   frontend\package.json: MISSING
if exist backend\.venv\Scripts\python.exe  (echo   backend venv: INSTALLED)               else echo   backend venv: NOT CREATED
if exist frontend\node_modules             (echo   frontend node_modules: INSTALLED)      else echo   frontend node_modules: NOT INSTALLED
echo.
echo [Python in PATH]
echo %PATH% | findstr /i python
echo.
pause
