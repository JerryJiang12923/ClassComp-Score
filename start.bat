@echo off
chcp 65001 >nul
echo 🚀 ClassComp Score 班级评分系统启动器
echo ====================================
echo.

REM 检测Python环境
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Python未找到！
    echo 请确保Python已安装并添加到系统PATH
    echo 下载地址：https://www.python.org/downloads/
    pause
    exit /b 1
)

echo ✅ Python环境正常
echo.

REM 安装依赖
echo 📦 检查并安装依赖...
pip install -r requirements.txt >nul 2>&1

echo ✅ 依赖检查完成
echo.

REM 检查数据库
python -c "import os; from dotenv import load_dotenv; from db import get_conn, put_conn; load_dotenv(); conn = get_conn(); cur = conn.cursor(); cur.execute('SELECT 1'); print('✅ 数据库连接正常'); put_conn(conn)" 2>nul || (
    echo 🔄 首次运行，正在初始化数据库...
    python init_db.py
    echo ✅ 数据库初始化完成
)

echo.
echo 🎯 启动应用...
echo 访问地址: http://localhost:5000
echo.
echo 默认账户:
echo - 管理员: admin / admin123
echo - 测试学生: student1 / student123
echo - 全校数据教师: ts / teacher123
echo - 年级教师: t6, t7, t8, t10, t11 / password123
echo.

python app.py

pause