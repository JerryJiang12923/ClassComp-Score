#!/usr/bin/env python3
"""Quick test script to verify the system works"""
import requests
import sys

# Test URLs
BASE_URL = "http://localhost:5000"

def test_login():
    """Test login functionality"""
    session = requests.Session()
    
    # Test admin login
    login_data = {
        'username': 'admin',
        'password': 'admin123'
    }
    
    response = session.post(f"{BASE_URL}/login", data=login_data)
    if response.status_code == 200:
        print("✓ Admin login successful")
        
        # Test accessing admin users page
        response = session.get(f"{BASE_URL}/admin/users")
        if response.status_code == 200 and '用户管理' in response.text:
            print("✓ Admin users page accessible")
            
            # Count users in page
            user_count = response.text.count('中预_') + response.text.count('初一_') + response.text.count('初二_') + response.text.count('高一_') + response.text.count('高二_')
            print(f"✓ Found approximately {user_count} student users in admin interface")
            
        else:
            print("✗ Admin users page failed")
    else:
        print("✗ Admin login failed")

def test_student_login():
    """Test student login"""
    session = requests.Session()
    
    # Test student login
    login_data = {
        'username': '中预_中预1班_学生1',
        'password': 'student123'
    }
    
    response = session.post(f"{BASE_URL}/login", data=login_data)
    if response.status_code == 200:
        print("✓ Student login successful")
    else:
        print("✗ Student login failed")

def main():
    print("=== ClassComp Score 全量测试验证 ===")
    print("服务器地址: http://localhost:5000")
    print()
    
    try:
        # Check if server is running
        response = requests.get(BASE_URL, timeout=5)
        print("✓ 服务器运行正常")
    except:
        print("✗ 服务器未运行，请确保已启动")
        return
    
    test_login()
    test_student_login()
    
    print()
    print("=== 测试账号列表 ===")
    print("管理员: admin / admin123")
    print("学生示例: 中预_中预1班_学生1 / student123")
    print("教师示例: 中预老师 / teacher123")
    print()
    print("访问地址: http://localhost:5000")
    print("管理员用户管理: http://localhost:5000/admin/users")

if __name__ == "__main__":
    main()