-- ClassComp-Score Supabase RLS 安全配置
-- 部署到Supabase时必须执行的安全策略

-- ====================================
-- 1. 启用所有表的RLS
-- ====================================

-- 启用用户表RLS
ALTER TABLE users ENABLE ROW LEVEL SECURITY;

-- 启用评分表RLS
ALTER TABLE scores ENABLE ROW LEVEL SECURITY;

-- 启用评分历史表RLS
ALTER TABLE scores_history ENABLE ROW LEVEL SECURITY;

-- 启用学期配置表RLS
ALTER TABLE semester_config ENABLE ROW LEVEL SECURITY;
ALTER TABLE semester_classes ENABLE ROW LEVEL SECURITY;

-- ====================================
-- 2. 用户表安全策略
-- ====================================

-- 用户只能查看自己的基本信息（不包括密码哈希）
CREATE POLICY "Users can view their own profile" 
ON users FOR SELECT 
TO authenticated
USING (auth.uid()::text = id::text);

-- 管理员可以查看所有用户（通过app_metadata中的role判断）
CREATE POLICY "Admins can view all users" 
ON users FOR SELECT 
TO authenticated
USING (
  (auth.jwt() ->> 'app_metadata')::json ->> 'role' = 'admin'
);

-- 管理员可以插入新用户
CREATE POLICY "Admins can insert users" 
ON users FOR INSERT 
TO authenticated
WITH CHECK (
  (auth.jwt() ->> 'app_metadata')::json ->> 'role' = 'admin'
);

-- 管理员可以更新用户信息
CREATE POLICY "Admins can update users" 
ON users FOR UPDATE 
TO authenticated
USING (
  (auth.jwt() ->> 'app_metadata')::json ->> 'role' = 'admin'
);

-- 管理员可以删除用户
CREATE POLICY "Admins can delete users" 
ON users FOR DELETE 
TO authenticated
USING (
  (auth.jwt() ->> 'app_metadata')::json ->> 'role' = 'admin'
);

-- ====================================
-- 3. 评分表安全策略
-- ====================================

-- 用户只能查看自己提交的评分
CREATE POLICY "Users can view their own scores" 
ON scores FOR SELECT 
TO authenticated
USING (auth.uid()::text = user_id::text);

-- 教师可以查看本年级的评分数据
CREATE POLICY "Teachers can view grade scores" 
ON scores FOR SELECT 
TO authenticated
USING (
  (auth.jwt() ->> 'app_metadata')::json ->> 'role' IN ('teacher', 'admin')
);

-- 用户只能插入自己的评分
CREATE POLICY "Users can insert their own scores" 
ON scores FOR INSERT 
TO authenticated
WITH CHECK (auth.uid()::text = user_id::text);

-- 用户只能更新自己的评分
CREATE POLICY "Users can update their own scores" 
ON scores FOR UPDATE 
TO authenticated
USING (auth.uid()::text = user_id::text)
WITH CHECK (auth.uid()::text = user_id::text);

-- 管理员可以删除评分
CREATE POLICY "Admins can delete scores" 
ON scores FOR DELETE 
TO authenticated
USING (
  (auth.jwt() ->> 'app_metadata')::json ->> 'role' = 'admin'
);

-- ====================================
-- 4. 评分历史表安全策略
-- ====================================

-- 只有管理员可以查看历史记录
CREATE POLICY "Admins can view score history" 
ON scores_history FOR SELECT 
TO authenticated
USING (
  (auth.jwt() ->> 'app_metadata')::json ->> 'role' = 'admin'
);

-- 系统自动插入历史记录（通过服务密钥）
CREATE POLICY "System can insert score history" 
ON scores_history FOR INSERT 
TO service_role
WITH CHECK (true);

-- ====================================
-- 5. 学期配置表安全策略
-- ====================================

-- 所有认证用户可以读取学期配置
CREATE POLICY "Authenticated users can view semester config" 
ON semester_config FOR SELECT 
TO authenticated
USING (true);

-- 只有管理员可以修改学期配置
CREATE POLICY "Admins can manage semester config" 
ON semester_config FOR ALL 
TO authenticated
USING (
  (auth.jwt() ->> 'app_metadata')::json ->> 'role' = 'admin'
)
WITH CHECK (
  (auth.jwt() ->> 'app_metadata')::json ->> 'role' = 'admin'
);

-- 所有认证用户可以读取班级配置
CREATE POLICY "Authenticated users can view semester classes" 
ON semester_classes FOR SELECT 
TO authenticated
USING (true);

-- 只有管理员可以修改班级配置
CREATE POLICY "Admins can manage semester classes" 
ON semester_classes FOR ALL 
TO authenticated
USING (
  (auth.jwt() ->> 'app_metadata')::json ->> 'role' = 'admin'
)
WITH CHECK (
  (auth.jwt() ->> 'app_metadata')::json ->> 'role' = 'admin'
);

-- ====================================
-- 6. 性能优化索引
-- ====================================

-- 为RLS策略添加索引以提高性能
CREATE INDEX IF NOT EXISTS idx_users_auth_uid ON users(id);
CREATE INDEX IF NOT EXISTS idx_scores_user_id ON scores(user_id);
CREATE INDEX IF NOT EXISTS idx_scores_history_user_id ON scores_history(user_id);

-- ====================================
-- 说明和注意事项
-- ====================================

/*
重要说明：

1. **认证集成**：这些策略假设你使用Supabase Auth进行用户认证
   - 如果使用Flask的session认证，需要调整策略
   - 考虑使用Supabase Auth替代自定义认证系统

2. **角色管理**：策略依赖于JWT中的app_metadata.role字段
   - 在用户注册时设置role到app_metadata
   - 不要将role存储在user_metadata（用户可修改）

3. **服务密钥**：某些操作需要使用服务密钥绕过RLS
   - 历史记录插入
   - 批量数据操作
   - 系统级管理任务

4. **测试**：部署前在Supabase控制台测试所有策略
   - 使用不同角色的测试用户验证访问权限
   - 确认性能影响可接受

5. **应用层配合**：RLS不能完全替代应用层验证
   - 继续在Flask应用中进行业务逻辑验证
   - RLS作为最后一道防线

部署步骤：
1. 在Supabase SQL编辑器中运行此脚本
2. 测试各种场景的数据访问权限
3. 监控查询性能
4. 根据实际使用情况调整策略
*/
