@echo off
chcp 65001 >nul
setlocal

cd /d "%~dp0"
title 舆澜网城 - 多智能体舆论传播仿真

echo ========================================
echo   舆澜网城：多智能体舆论传播仿真系统
echo ========================================
echo.

where python >nul 2>&1
if errorlevel 1 (
    echo [错误] 未找到 Python，请先安装 Python 3.10 或更高版本并加入 PATH。
    pause
    exit /b 1
)

for /f "tokens=2 delims= " %%v in ('python -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')" 2^>nul') do set PY_VER=%%v
for /f "tokens=1,2 delims=." %%a in ("%PY_VER%") do (
    if %%a LSS 3 (
        echo [错误] 需要 Python 3.10 或更高版本，当前为 %PY_VER%
        pause
        exit /b 1
    )
    if %%a EQU 3 if %%b LSS 10 (
        echo [错误] 需要 Python 3.10 或更高版本，当前为 %PY_VER%
        echo        旧版 Django 2.2 不支持 Python 3.12+，请升级 Python。
        pause
        exit /b 1
    )
)

if not exist "venv\Scripts\python.exe" (
    echo [0/3] 创建虚拟环境 venv ...
    python -m venv venv
    if errorlevel 1 (
        echo [错误] 无法创建虚拟环境。
        pause
        exit /b 1
    )
)

set "PYTHON=venv\Scripts\python.exe"
set "PIP=venv\Scripts\python.exe -m pip"

if not defined DEEPSEEK_API_KEY (
    echo [提示] 未设置 DEEPSEEK_API_KEY，DeepSeek 对话将不可用。
    echo        可在本窗口执行: set DEEPSEEK_API_KEY=你的key
    echo        或于「系统环境变量」中永久配置。
    echo.
)

echo [1/3] 安装依赖...
%PIP% install -r requirements.txt
if errorlevel 1 (
    echo [错误] 依赖安装失败。
    pause
    exit /b 1
)

echo.
echo [2/3] 执行数据库迁移并启动服务...
echo 访问地址: http://127.0.0.1:8000/
echo 按 Ctrl+C 可停止服务。
echo.

start "" "http://127.0.0.1:8000/"
"%PYTHON%" run_project.py --migrate --port 8000

pause
