"""
新媒体委员功能数据库迁移脚本
为系统添加新媒体委员角色支持、数据来源标记和权重配置
"""
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'src'))

from classcomp.database import get_conn, put_conn
from werkzeug.security import generate_password_hash

def add_new_media_officer_support():
    """添加新媒体委员功能支持"""
    conn = get_conn()
    cur = conn.cursor()
    
    try:
        # 检测数据库类型
        db_url = os.getenv("DATABASE_URL", "sqlite:///classcomp.db")
        is_sqlite = db_url.startswith("sqlite")
        placeholder = "?" if is_sqlite else "%s"
        
        print("开始新媒体委员功能迁移...")
        
        # 步骤1: 修改 users 表的 role 字段，添加 new_media_officer 角色
        print("步骤1: 更新用户角色约束...")
        if is_sqlite:
            # SQLite 不支持直接 ALTER COLUMN，需要重建表
            # 先检查是否已经支持新角色
            cur.execute("SELECT role FROM users WHERE role = 'new_media_officer' LIMIT 1")
            if cur.fetchone() is None:
                print("  SQLite: 重建 users 表以支持新媒体委员角色...")
                # 创建临时表
                cur.execute("""
                    CREATE TABLE users_new (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        username VARCHAR(50) UNIQUE NOT NULL,
                        password_hash VARCHAR(255) NOT NULL,
                        role VARCHAR(20) DEFAULT 'student' CHECK (role IN ('student', 'teacher', 'admin', 'new_media_officer')),
                        class_name VARCHAR(50),
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        is_active BOOLEAN DEFAULT TRUE
                    )
                """)
                
                # 复制数据
                cur.execute("""
                    INSERT INTO users_new (id, username, password_hash, role, class_name, created_at, is_active)
                    SELECT id, username, password_hash, role, class_name, created_at, is_active
                    FROM users
                """)
                
                # 删除旧表
                cur.execute("DROP TABLE users")
                
                # 重命名新表
                cur.execute("ALTER TABLE users_new RENAME TO users")
                print("  ✓ users 表已重建")
        else:
            # PostgreSQL 可以直接修改约束
            cur.execute("""
                ALTER TABLE users DROP CONSTRAINT IF EXISTS users_role_check
            """)
            cur.execute("""
                ALTER TABLE users ADD CONSTRAINT users_role_check 
                CHECK (role IN ('student', 'teacher', 'admin', 'new_media_officer'))
            """)
            print("  ✓ PostgreSQL 角色约束已更新")
        
        # 步骤2: 在 scores 表中添加数据来源字段
        print("步骤2: 添加数据来源字段...")
        try:
            if is_sqlite:
                cur.execute("""
                    ALTER TABLE scores ADD COLUMN source_type VARCHAR(30) DEFAULT 'info_commissioner' 
                    CHECK (source_type IN ('info_commissioner', 'new_media_officer'))
                """)
            else:
                cur.execute("""
                    ALTER TABLE scores ADD COLUMN IF NOT EXISTS source_type VARCHAR(30) DEFAULT 'info_commissioner' 
                    CHECK (source_type IN ('info_commissioner', 'new_media_officer'))
                """)
            print("  ✓ scores 表已添加 source_type 字段")
        except Exception as e:
            if "duplicate column" in str(e).lower() or "already exists" in str(e).lower():
                print("  ℹ source_type 字段已存在，跳过")
            else:
                raise
        
        # 为 scores_history 表也添加数据来源字段
        try:
            if is_sqlite:
                cur.execute("""
                    ALTER TABLE scores_history ADD COLUMN source_type VARCHAR(30) DEFAULT 'info_commissioner'
                    CHECK (source_type IN ('info_commissioner', 'new_media_officer'))
                """)
            else:
                cur.execute("""
                    ALTER TABLE scores_history ADD COLUMN IF NOT EXISTS source_type VARCHAR(30) DEFAULT 'info_commissioner'
                    CHECK (source_type IN ('info_commissioner', 'new_media_officer'))
                """)
            print("  ✓ scores_history 表已添加 source_type 字段")
        except Exception as e:
            if "duplicate column" in str(e).lower() or "already exists" in str(e).lower():
                print("  ℹ scores_history.source_type 字段已存在，跳过")
            else:
                raise
        
        # 步骤3: 创建权重配置表
        print("步骤3: 创建权重配置表...")
        if is_sqlite:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS score_weight_config (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    config_name VARCHAR(100) NOT NULL,
                    new_media_weight REAL DEFAULT 1.5 CHECK (new_media_weight >= 1.0 AND new_media_weight <= 5.0),
                    info_commissioner_weight REAL DEFAULT 1.0 CHECK (info_commissioner_weight >= 1.0 AND info_commissioner_weight <= 5.0),
                    description TEXT,
                    is_active BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
        else:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS score_weight_config (
                    id SERIAL PRIMARY KEY,
                    config_name VARCHAR(100) NOT NULL,
                    new_media_weight REAL DEFAULT 1.5 CHECK (new_media_weight >= 1.0 AND new_media_weight <= 5.0),
                    info_commissioner_weight REAL DEFAULT 1.0 CHECK (info_commissioner_weight >= 1.0 AND info_commissioner_weight <= 5.0),
                    description TEXT,
                    is_active BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                )
            """)
        print("  ✓ score_weight_config 表已创建")
        
        # 步骤4: 插入默认权重配置
        print("步骤4: 插入默认权重配置...")
        cur.execute(f"SELECT id FROM score_weight_config WHERE config_name = {placeholder}", ('默认权重配置',))
        if not cur.fetchone():
            cur.execute(f"""
                INSERT INTO score_weight_config (config_name, new_media_weight, info_commissioner_weight, description, is_active)
                VALUES ({placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder})
            """, ('默认权重配置', 1.5, 1.0, '新媒体委员评分权重为1.5，信息委员评分权重为1.0', True))
            print("  ✓ 默认权重配置已插入")
        else:
            print("  ℹ 默认权重配置已存在，跳过")
        
        # 步骤5: 创建新媒体委员账户
        print("步骤5: 创建新媒体委员账户...")
        new_media_accounts = [
            ('nmo6', '中预新媒体', '中预新媒体委员'),
            ('nmo7', '初一新媒体', '初一新媒体委员'),
            ('nmo8', '初二新媒体', '初二新媒体委员'),
            ('nmo10', '高一新媒体', '高一新媒体委员'),
            ('nmo11', '高二新媒体', '高二新媒体委员'),
        ]
        
        for username, display_name, class_name in new_media_accounts:
            cur.execute(f"SELECT id FROM users WHERE username = {placeholder}", (username,))
            if not cur.fetchone():
                password_hash = generate_password_hash('123456')  # 默认密码
                cur.execute(f"""
                    INSERT INTO users (username, password_hash, role, class_name)
                    VALUES ({placeholder}, {placeholder}, 'new_media_officer', {placeholder})
                """, (username, password_hash, class_name))
                print(f"  ✓ 新媒体委员账户创建成功: {username} ({display_name})")
            else:
                print(f"  ℹ 账户已存在: {username}")
        
        # 步骤6: 创建索引优化查询
        print("步骤6: 创建索引...")
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_scores_source_type ON scores(source_type)",
            "CREATE INDEX IF NOT EXISTS idx_scores_history_source_type ON scores_history(source_type)",
        ]
        for index_sql in indexes:
            try:
                cur.execute(index_sql)
            except Exception as e:
                print(f"  ⚠ 索引创建警告: {e}")
        print("  ✓ 索引创建完成")
        
        conn.commit()
        print("\n✅ 新媒体委员功能迁移完成！")
        print("\n账户信息:")
        print("=" * 60)
        print("新媒体委员账户（默认密码：123456）:")
        for username, display_name, _ in new_media_accounts:
            print(f"  - {username}: {display_name}")
        print("=" * 60)
        
    except Exception as e:
        conn.rollback()
        print(f"\n❌ 迁移失败: {e}")
        import traceback
        traceback.print_exc()
        raise
    finally:
        put_conn(conn)

if __name__ == "__main__":
    add_new_media_officer_support()