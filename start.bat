@echo off
setlocal
title Bolt Tightening Quality System - Launcher

rem Root directory of this script (works no matter where the folder is placed)
set "ROOT=%~dp0"

echo ================================================
echo  Bolt Tightening Quality Intelligent Detection
echo  and Process Traceability System - Launcher
echo ================================================
echo.

rem Install frontend dependencies on first run (skip if already installed)
if not exist "%ROOT%frontend\node_modules" (
    echo [0] Installing frontend dependencies, please wait...
    pushd "%ROOT%frontend"
    call npm install
    popd
    echo.
)

echo [1/3] Starting backend  (FastAPI)  -^> http://localhost:8000
start "Bolt-Backend" /D "%ROOT%backend" cmd /k "python -m uvicorn main:app --host 0.0.0.0 --port 8000"

echo [2/3] Starting frontend (Vite)     -^> http://localhost:5173
start "Bolt-Frontend" /D "%ROOT%frontend" cmd /k "npm run dev"

echo [3/3] Opening browser...
timeout /t 5 /nobreak >nul
start "" http://localhost:5173

echo.
echo All services started. Please keep the two new windows open.
echo To stop the system, close the Backend and Frontend windows.
echo.
pause
endlocal
