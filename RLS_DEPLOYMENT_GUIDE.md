# 🔒 Supabase RLS 部署指南

## 为什么需要RLS？

### 🚨 风险场景
如果不启用RLS，任何获得你API密钥的人都可以：

```javascript
// 恶意代码示例 - 没有RLS时可以成功执行
const supabase = createClient(YOUR_URL, YOUR_ANON_KEY)

// 获取所有用户信息（包括密码哈希）
const { data: users } = await supabase.from('users').select('*')

// 获取所有班级评分数据
const { data: scores } = await supabase.from('scores').select('*')

// 删除所有评分记录
await supabase.from('scores').delete().neq('id', 0)
```

### ✅ 启用RLS后的保护
```javascript
// 相同的恶意代码 - 启用RLS后会被阻止
const { data, error } = await supabase.from('users').select('*')
// 返回: error = "insufficient_privilege" 或空数据
```

## 🚀 部署步骤

### 步骤1：备份现有数据
```sql
-- 在部署RLS前，先备份重要数据
SELECT * FROM users;
SELECT * FROM scores;
SELECT * FROM scores_history;
```

### 步骤2：在Supabase控制台执行RLS设置
1. 登录 [Supabase Dashboard](https://app.supabase.com)
2. 选择你的项目
3. 进入 `SQL Editor`
4. 复制 `supabase_rls_setup.sql` 文件内容并执行

### 步骤3：验证RLS策略
```sql
-- 测试管理员权限
SELECT * FROM users; -- 应该能看到所有用户

-- 测试普通用户权限（模拟）
SET LOCAL "request.jwt.claims" TO '{"sub": "user123", "app_metadata": {"role": "student"}}';
SELECT * FROM users; -- 应该只能看到自己的记录
```

### 步骤4：更新应用代码（如果需要）

#### 选项A：继续使用Flask认证（推荐）
保持当前的Flask session认证，RLS作为额外安全层：

```python
# 在 models.py 中添加用户ID映射
class User:
    def get_supabase_user_id(self):
        """获取对应的Supabase用户ID"""
        # 这需要在迁移时建立映射关系
        return str(self.id)
```

#### 选项B：迁移到Supabase Auth
完全使用Supabase认证系统：

```python
# 新的认证流程
from supabase import create_client

supabase = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)

@app.route('/auth/login', methods=['POST'])
def supabase_login():
    email = request.json.get('email')
    password = request.json.get('password')
    
    result = supabase.auth.sign_in_with_password({
        "email": email,
        "password": password
    })
    
    if result.user:
        # 设置用户角色到 app_metadata
        supabase.auth.admin.update_user_by_id(
            result.user.id,
            {"app_metadata": {"role": "student", "class_name": "高一1班"}}
        )
    
    return jsonify(result)
```

## 🧪 测试RLS策略

### 测试脚本
创建测试文件来验证RLS是否正常工作：

```python
# test_rls.py
import os
from supabase import create_client

# 使用不同的密钥测试
SUPABASE_URL = os.getenv("SUPABASE_URL")
ANON_KEY = os.getenv("SUPABASE_ANON_KEY")  # 公开密钥
SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")  # 服务密钥

def test_anon_access():
    """测试匿名用户访问（应该被阻止）"""
    supabase = create_client(SUPABASE_URL, ANON_KEY)
    
    try:
        result = supabase.table('users').select('*').execute()
        print(f"❌ 匿名用户不应该能访问用户数据: {len(result.data)} 条记录")
    except Exception as e:
        print(f"✅ 匿名用户被正确阻止: {e}")

def test_admin_access():
    """测试管理员访问（应该成功）"""
    supabase = create_client(SUPABASE_URL, SERVICE_KEY)
    
    try:
        result = supabase.table('users').select('*').execute()
        print(f"✅ 管理员可以访问用户数据: {len(result.data)} 条记录")
    except Exception as e:
        print(f"❌ 管理员访问失败: {e}")

if __name__ == "__main__":
    test_anon_access()
    test_admin_access()
```

## 📊 监控和维护

### 1. 性能监控
RLS策略可能影响查询性能，定期检查：

```sql
-- 检查慢查询
SELECT query, mean_time, calls 
FROM pg_stat_statements 
WHERE mean_time > 100 -- 超过100ms的查询
ORDER BY mean_time DESC;

-- 检查RLS策略使用情况
SELECT schemaname, tablename, policyname, cmd, qual 
FROM pg_policies 
WHERE schemaname = 'public';
```

### 2. 安全审计
定期审查和更新RLS策略：

```sql
-- 检查哪些表启用了RLS
SELECT schemaname, tablename, rowsecurity 
FROM pg_tables 
WHERE schemaname = 'public';

-- 检查策略覆盖情况
SELECT tablename, COUNT(*) as policy_count
FROM pg_policies 
WHERE schemaname = 'public'
GROUP BY tablename;
```

## 🚨 常见问题和解决方案

### 问题1：应用无法访问数据
**症状**：Flask应用返回空数据或权限错误
**解决**：
1. 检查是否使用了正确的服务密钥
2. 确认RLS策略的条件是否正确
3. 验证JWT token中包含正确的用户信息

### 问题2：性能下降
**症状**：查询变慢
**解决**：
1. 为RLS策略中使用的列添加索引
2. 使用 `security definer` 函数优化复杂策略
3. 避免在策略中使用复杂的JOIN操作

### 问题3：策略冲突
**症状**：某些操作被意外阻止
**解决**：
1. 使用 `RESTRICTIVE` 策略类型更精确控制
2. 测试策略的组合效果
3. 使用 `EXPLAIN` 分析策略执行

## 📋 部署检查清单

- [ ] 备份现有数据
- [ ] 在测试环境验证RLS策略
- [ ] 更新应用代码（如果需要）
- [ ] 在生产环境部署RLS
- [ ] 测试所有用户角色的访问权限
- [ ] 监控性能影响
- [ ] 更新文档和运维手册

## 🔧 应急回滚方案

如果RLS导致问题，可以临时禁用：

```sql
-- 紧急禁用RLS（不推荐长期使用）
ALTER TABLE users DISABLE ROW LEVEL SECURITY;
ALTER TABLE scores DISABLE ROW LEVEL SECURITY;
ALTER TABLE scores_history DISABLE ROW LEVEL SECURITY;

-- 或者删除特定策略
DROP POLICY "policy_name" ON table_name;
```

## 📚 相关资源

- [Supabase RLS 官方文档](https://supabase.com/docs/guides/auth/row-level-security)
- [PostgreSQL RLS 文档](https://www.postgresql.org/docs/current/ddl-rowsecurity.html)
- [RLS 性能优化指南](https://supabase.com/docs/guides/database/postgres/row-level-security#rls-performance-recommendations)
