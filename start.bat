@echo off
echo ?? ClassComp Score 完备系统启动器
echo ====================================
echo.

REM 检查Python环境
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ? Python未找到！
    echo 请确保Python已安装并添加到系统PATH
    echo 下载地址：https://www.python.org/downloads/
    pause
    exit /b 1
)

echo ? Python环境正常
echo.

REM 检查依赖
python -c "import flask; print('? Flask已安装')" >nul 2>&1
if %errorlevel% neq 0 (
    echo ?? 正在安装依赖...
    pip install -r requirements.txt
    if %errorlevel% neq 0 (
        echo ? 依赖安装失败，请手动运行: pip install -r requirements.txt
        pause
        exit /b 1
    )
)

echo ? 依赖检查完成
echo.

REM 检查数据库
python -c "
import os
from dotenv import load_dotenv
from db import get_conn, put_conn
try:
    load_dotenv()
    conn = get_conn()
    cur = conn.cursor()
    cur.execute('SELECT 1')
    print('? 数据库连接正常')
    put_conn(conn)
except Exception as e:
    print('??  首次运行，正在初始化数据库...')
    exec(open('init_db.py').read())
    print('? 数据库初始化完成')
" >nul 2>&1

echo.
echo ?? 启动应用...
echo 访问地址: http://localhost:5000
echo.
echo 默认账户:
echo - 管理员: admin / admin123
echo - 测试学生: student1 / student123
echo.

python app.py

pause