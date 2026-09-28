@echo off
setlocal enabledelayedexpansion
title SZU Board Monitor v2.0

echo ========================================
echo   Shenzhen University Board Monitor
echo   v2.0
echo ========================================
echo.

cd /d "%~dp0"

rem Find Python
if exist "python\python.exe" (
    echo [INFO] Using embedded Python
    set "PYTHON=%~dp0python\python.exe"
    set "PIP_TARGET=%~dp0python\Lib\site-packages"
) else (
    where python >nul 2>nul
    if not errorlevel 1 (
        echo [INFO] Using system Python
        set "PYTHON=python"
        set "PIP_TARGET="
    ) else if exist "C:\DEMO\python.exe" (
        echo [INFO] Using C:\DEMO\Python
        set "PYTHON=C:\DEMO\python.exe"
        set "PIP_TARGET="
    ) else if exist "C:\Python311\python.exe" (
        echo [INFO] Using C:\Python311
        set "PYTHON=C:\Python311\python.exe"
        set "PIP_TARGET="
    ) else (
        echo [ERROR] Python not found!
        echo Please install Python 3.9+ or put python folder next to this bat.
        pause
        exit /b 1
    )
)

rem Check dependencies
"%PYTHON%" -c "import flask" 2>nul
if errorlevel 1 (
    echo [INFO] Installing dependencies...
    if defined PIP_TARGET (
        "%PYTHON%" -m pip install -r requirements.txt --target "%PIP_TARGET%" -i https://pypi.tuna.tsinghua.edu.cn/simple
    ) else (
        "%PYTHON%" -m pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
    )
    if errorlevel 1 (
        echo.
        echo [ERROR] Failed to install dependencies
        pause
        exit /b 1
    )
    echo [INFO] Dependencies installed
)

echo.
echo [INFO] Starting server...
echo [INFO] Browser will open at http://127.0.0.1:5000
echo [INFO] Close this window to stop the server
echo.

rem Start Python in background
start "SZU Board Monitor" "%PYTHON%" main.py

rem Wait for server to be ready (max 15 seconds)
set "ready=0"
for /L %%i in (1,1,30) do (
    if !ready! equ 0 (
        timeout /t 1 /nobreak >nul
        "%PYTHON%" -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:5000/api/config', timeout=1)" 2>nul
        if not errorlevel 1 (
            set "ready=1"
            echo [INFO] Server started, opening browser...
            start http://127.0.0.1:5000
        )
    )
)

if %ready% equ 0 (
    echo [WARN] Server startup timeout, please open http://127.0.0.1:5000 manually
)

echo.
echo [INFO] Server is running. Close this window to stop.
pause
