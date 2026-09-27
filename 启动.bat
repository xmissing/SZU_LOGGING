@echo off
chcp 65001 >nul
title 深圳大学公告监控系统

echo ========================================
echo   深圳大学公告监控系统 v2.0
echo   SZU Board Monitor
echo ========================================
echo.

cd /d "%~dp0"

rem 检查是否有内嵌 Python 环境
if exist "python\python.exe" (
    echo [信息] 使用内嵌 Python 环境
    set "PYTHON=python\python.exe"
) else (
    echo [信息] 使用系统 Python
    set "PYTHON=python"
)

rem 检查依赖是否安装
%PYTHON% -c "import flask" 2>nul
if errorlevel 1 (
    echo [信息] 正在安装依赖，请稍候...
    %PYTHON% -m pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
    if errorlevel 1 (
        echo.
        echo [错误] 依赖安装失败，请检查网络连接
        pause
        exit /b 1
    )
    echo [信息] 依赖安装完成
)

echo.
echo [信息] 正在启动服务...
echo [信息] 启动后将自动打开浏览器
echo [信息] 如需关闭，请直接关闭此窗口
echo.

start "" http://127.0.0.1:5000

%PYTHON% main.py

pause
