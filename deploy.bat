@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

REM ====================================================
REM  ClassComp Score 一键部署脚本 (Windows)
REM  功能: 环境检查 -> 依赖安装 -> 数据库初始化 -> 
REM        应用启动 -> 服务配置 -> 健康检查
REM ====================================================

set APP_NAME=ClassComp-Score
set PORT=5000
set VERBOSE=0
set SKIP_SERVICE=0
set SKIP_DEPS=0

REM 解析命令行参数
if not "%1"=="" (
    if "%1"=="--help" goto show_help
    if "%1"=="--port" (
        set PORT=%2
        shift
        shift
        goto parse_args
    )
    if "%1"=="--no-service" (
        set SKIP_SERVICE=1
        shift
        goto parse_args
    )
    if "%1"=="--skip-deps" (
        set SKIP_DEPS=1
        shift
        goto parse_args
    )
    if "%1"=="--verbose" (
        set VERBOSE=1
        shift
        goto parse_args
    )
)

:parse_args_done

echo.
echo 🚀 %APP_NAME% 一键部署向导
echo ================================================
echo.

REM ========== [1/7] 环境检查 ==========
echo [1/7] 环境检查...
python scripts/deployment/check_environment.py --port %PORT% %if %VERBOSE%==1 --verbose%

if !errorlevel! neq 0 (
    echo.
    echo ❌ 环境检查失败！
    echo.
    echo 常见解决方案:
    echo   1. 确保 Python 3.9+ 已安装
    echo   2. 在系统 PATH 中添加 Python 路径
    echo   3. 检查磁盘空间是否充足 (至少 500MB)
    echo   4. 检查端口 %PORT% 是否被占用
    echo.
    pause
    exit /b 1
)

REM ========== [2/7] 依赖安装 ==========
if %SKIP_DEPS%==0 (
    echo.
    echo [2/7] 安装依赖...
    python scripts/deployment/install_dependencies.py %if %VERBOSE%==1 --verbose%
    
    if !errorlevel! neq 0 (
        echo.
        echo ⚠️  依赖安装失败，尝试使用镜像源...
        python scripts/deployment/install_dependencies.py --mirror %if %VERBOSE%==1 --verbose%
        
        if !errorlevel! neq 0 (
            echo.
            echo ❌ 依赖安装失败！
            pause
            exit /b 1
        )
    )
) else (
    echo.
    echo [2/7] 跳过依赖检查
)

REM ========== [3/7] 数据库初始化 ==========
echo.
echo [3/7] 初始化数据库...
python scripts/init_db.py

if !errorlevel! neq 0 (
    echo.
    echo ⚠️  数据库初始化失败，稍后可能重试
)

REM ========== [4/7] 启动应用 ==========
echo.
echo [4/7] 启动应用...
echo.
echo 🌐 应用访问地址: http://localhost:%PORT%
echo.
echo 📚 默认账户:
echo   管理员: admin / admin123
echo   教师: t6 / 123456
echo   学生: g6c1 / 123456
echo.
echo ℹ️  按 Ctrl+C 停止应用
echo.

set PORT=%PORT%
python serve.py

REM ========== [5/7] 配置后台服务 ==========
if %SKIP_SERVICE%==0 (
    cls
    echo.
    echo [5/7] 配置后台服务...
    echo.
    
    REM 检查管理员权限
    net session >nul 2>&1
    if !errorlevel! neq 0 (
        echo.
        echo ⚠️  需要管理员权限来安装 Windows 服务
        echo 💡 请以管理员身份重新运行此脚本
        echo.
        pause
    ) else (
        python scripts/deployment/setup_service.py --port %PORT% %if %VERBOSE%==1 --verbose%
        
        if !errorlevel! neq 0 (
            echo.
            echo ⚠️  服务配置失败
            echo.
        )
    )
) else (
    echo.
    echo [5/7] 跳过服务配置
)

REM ========== [6/7] 健康检查 ==========
echo.
echo [6/7] 运行健康检查...
python scripts/deployment/health_monitor.py --host localhost --port %PORT% %if %VERBOSE%==1 --verbose%

REM ========== [7/7] 完成 ==========
echo.
echo ================================================
echo ✨ 部署完成！
echo ================================================
echo.
echo 📖 文档:
echo   - 完整指南: docs/DEPLOYMENT_GUIDE.md
echo   - 故障排除: docs/TROUBLESHOOTING.md
echo   - API文档: docs/api/
echo.
echo 🔧 管理命令:
echo   - 启动应用: python serve.py
echo   - 启动开发: python app.py
echo   - 查看日志: type logs\application.log
echo.
echo 💬 需要帮助? 查看部署文档或故障排除指南
echo.
pause
exit /b 0

:show_help
echo.
echo 用法: deploy.bat [选项]
echo.
echo 选项:
echo   --port PORT         指定服务端口 (默认: 5000)
echo   --no-service        不安装 Windows 服务
echo   --skip-deps         跳过依赖检查
echo   --verbose           显示详细信息
echo   --help              显示此帮助信息
echo.
echo 示例:
echo   deploy.bat                      使用默认设置部署
echo   deploy.bat --port 8080          使用端口 8080 部署
echo   deploy.bat --no-service         不安装后台服务
echo   deploy.bat --verbose            显示详细信息
echo.
exit /b 0