#!/usr/bin/env python3
"""
管理员密码重置脚本
用于解决 Render 部署后管理员密码环境变量不生效的问题
"""

import os
import sys
from werkzeug.security import generate_password_hash

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from db import get_conn, put_conn

def reset_admin_password():
    """重置管理员密码"""
    conn = get_conn()
    try:
        cur = conn.cursor()
        
        # 从环境变量获取管理员信息
        admin_username = os.getenv('ADMIN_USERNAME', 'admin')
        admin_password = os.getenv('ADMIN_PASSWORD', 'admin123')
        
        print(f"正在重置管理员密码...")
        print(f"用户名: {admin_username}")
        print(f"新密码: {'*' * len(admin_password)}")
        
        # 检测数据库类型
        db_url = os.getenv("DATABASE_URL", "sqlite:///classcomp.db")
        is_sqlite = db_url.startswith("sqlite")
        placeholder = "?" if is_sqlite else "%s"
        
        # 检查管理员用户是否存在
        cur.execute(f"SELECT id, username FROM users WHERE username = {placeholder}", (admin_username,))
        user = cur.fetchone()
        
        if user:
            # 更新密码
            password_hash = generate_password_hash(admin_password)
            cur.execute(f"""
                UPDATE users 
                SET password_hash = {placeholder}
                WHERE username = {placeholder}
            """, (password_hash, admin_username))
            
            conn.commit()
            print(f"✅ 管理员密码重置成功！")
            print(f"用户名: {admin_username}")
            print(f"请使用新密码登录")
        else:
            print(f"❌ 用户 {admin_username} 不存在")
            # 创建管理员用户
            password_hash = generate_password_hash(admin_password)
            cur.execute(f"""
                INSERT INTO users (username, password_hash, role, class_name)
                VALUES ({placeholder}, {placeholder}, 'admin', '管理员')
            """, (admin_username, password_hash))
            
            conn.commit()
            print(f"✅ 管理员账户创建成功！")
            print(f"用户名: {admin_username}")
            
        return True
        
    except Exception as e:
        print(f"❌ 密码重置失败: {e}")
        return False
    finally:
        put_conn(conn)

if __name__ == "__main__":
    print("🔐 管理员密码重置工具")
    print("=" * 40)
    
    success = reset_admin_password()
    if success:
        print("\n🎉 密码重置完成！")
        sys.exit(0)
    else:
        print("\n💥 密码重置失败，请检查错误信息")
        sys.exit(1)
