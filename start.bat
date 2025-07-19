@echo off
echo ?? ClassComp Score �걸ϵͳ������
echo ====================================
echo.

REM ���Python����
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ? Pythonδ�ҵ���
    echo ��ȷ��Python�Ѱ�װ����ӵ�ϵͳPATH
    echo ���ص�ַ��https://www.python.org/downloads/
    pause
    exit /b 1
)

echo ? Python��������
echo.

REM �������
python -c "import flask; print('? Flask�Ѱ�װ')" >nul 2>&1
if %errorlevel% neq 0 (
    echo ?? ���ڰ�װ����...
    pip install -r requirements.txt
    if %errorlevel% neq 0 (
        echo ? ������װʧ�ܣ����ֶ�����: pip install -r requirements.txt
        pause
        exit /b 1
    )
)

echo ? ����������
echo.

REM ������ݿ�
python -c "
import os
from dotenv import load_dotenv
from db import get_conn, put_conn
try:
    load_dotenv()
    conn = get_conn()
    cur = conn.cursor()
    cur.execute('SELECT 1')
    print('? ���ݿ���������')
    put_conn(conn)
except Exception as e:
    print('??  �״����У����ڳ�ʼ�����ݿ�...')
    exec(open('init_db.py').read())
    print('? ���ݿ��ʼ�����')
" >nul 2>&1

echo.
echo ?? ����Ӧ��...
echo ���ʵ�ַ: http://localhost:5000
echo.
echo Ĭ���˻�:
echo - ����Ա: admin / admin123
echo - ����ѧ��: student1 / student123
echo.

python app.py

pause