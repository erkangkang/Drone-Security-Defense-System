@echo off
REM 无人机安全防御系统 - 一键启动脚本 (Windows)

set SCRIPT_DIR=%~dp0
set PROJECT_ROOT=%SCRIPT_DIR%..
set FRONTEND_DIR=%PROJECT_ROOT%\src\frontend

echo ========================================
echo   无人机安全防御系统 启动脚本
echo ========================================
echo.

REM 检查 Python
where python >nul 2>nul
if %errorlevel% neq 0 (
    echo [错误] 未找到 Python，请先安装 Python 3.8+
    pause
    exit /b 1
)
echo [OK] Python 已安装

REM 检查并构建前端
if not exist "%FRONTEND_DIR%\dist" (
    echo.
    echo [INFO] 前端未构建，开始构建...

    REM 检查 Node.js
    where node >nul 2>nul
    if %errorlevel% neq 0 (
        echo [警告] 未找到 Node.js，跳过前端构建
        echo [INFO] 将仅启动后端 API 服务
        echo.
        goto :start_backend
    )

    echo [OK] Node.js 已安装

    REM 安装依赖
    echo [1/2] 安装前端依赖...
    cd /d "%FRONTEND_DIR%"
    call npm install
    if %errorlevel% neq 0 (
        echo [错误] 前端依赖安装失败
        pause
        exit /b 1
    )

    REM 构建
    echo [2/2] 构建前端...
    call npm run build
    if %errorlevel% neq 0 (
        echo [错误] 前端构建失败
        pause
        exit /b 1
    )

    echo [OK] 前端构建完成
    echo.
) else (
    echo [OK] 前端已构建
)

:start_backend

REM 设置环境
set PYTHONPATH=%PROJECT_ROOT%\src;%PYTHONPATH%
set CONFIG_FILE=%PROJECT_ROOT%\config\default_config.yaml

if not exist "%CONFIG_FILE%" (
    echo [错误] 配置文件不存在: %CONFIG_FILE%
    pause
    exit /b 1
)

echo.
echo 启动后端服务...
echo 配置: %CONFIG_FILE%
echo 访问: http://localhost:8080
echo.

cd /d "%PROJECT_ROOT%"
python -m src.main --config "%CONFIG_FILE%"
