# 生产环境部署指南

本指南介绍如何将 ClassComp Score 部署到生产环境，特别是 Render + Supabase 的推荐配置。

---

## 📋 部署前检查清单

### 1. Supabase 数据库设置

- [ ] 在 [Supabase](https://supabase.com) 创建新项目
- [ ] 记录 PostgreSQL 连接字符串
- [ ] 格式：`postgresql://postgres:[密码]@[主机]:5432/postgres`
- [ ] 测试数据库连接
- [ ] **🔒 配置 RLS (Row Level Security)**（强烈推荐）

### 2. Render 部署设置

- [ ] 在 [Render](https://render.com) 创建账号
- [ ] 连接 GitHub 仓库
- [ ] 选择 "New Web Service"

### 3. 环境变量配置

在 Render 的环境变量中设置：

| 变量名 | 值 | 必需 | 说明 |
|--------|----|----|-----|
| `DATABASE_URL` | `postgresql://...` | ✅ | Supabase 连接字符串 |
| `SECRET_KEY` | 自动生成 | ✅ | Flask 会话密钥 |
| `FLASK_ENV` | `production` | ✅ | 生产环境标识 |
| `EXPORT_FOLDER` | `/app/exports` | ✅ | 文件导出目录 |

---

## 🚀 部署步骤

### 步骤1：推送代码

```bash
git add .
git commit -m "Production ready - Render + Supabase deployment"
git push origin main
```

### 步骤2：Render 配置

**方式一：使用 render.yaml 自动配置**

项目已包含 `config/render.yaml` 配置文件，Render 会自动识别并配置。

**方式二：手动配置**

- Build Command: `pip install -r requirements.txt`
- Start Command: `python scripts/pre_start.py && python serve.py`
- Health Check Path: `/health`

### 步骤3：首次部署验证

1. ✅ 检查部署日志是否成功
2. ✅ 访问健康检查端点: `https://your-app.onrender.com/health`
3. ✅ 测试登录功能
4. ✅ 验证数据库连接正常

### 步骤4：初始化系统

1. 使用默认管理员账户登录：`admin` / `admin123`
2. 访问 `/admin/semester` 配置学期和班级
3. 创建必要的用户账户
4. 测试评分功能

---

## ⚙️ 生产环境特性

### 自动检测和优化

- ✅ 自动检测生产环境并禁用调试模式
- ✅ 使用 Gunicorn WSGI 服务器
- ✅ PostgreSQL 数据库支持
- ✅ 启动前环境检查
- ✅ 健康检查监控

### 安全配置

- ✅ 密码哈希存储
- ✅ 角色权限控制
- ✅ SQL 注入防护
- ✅ 输入验证和清理
- ✅ 速率限制

### 性能优化

- ✅ 数据库连接池
- ✅ 适合免费版的资源配置
- ✅ Excel 导出和备份功能
- ✅ 持久化文件存储

---

## 🔒 安全配置

### 1. 更改默认密码

**强烈建议在生产环境中更改所有默认密码！**

```bash
# 使用密码重置脚本
python scripts/reset_password.py
```

### 2. 配置 SECRET_KEY

编辑环境变量，设置强密钥：

```bash
SECRET_KEY=your-long-random-secret-key-here
```

生成安全密钥：
```python
import secrets
print(secrets.token_hex(32))
```

### 3. 数据库安全

如果使用 PostgreSQL：
- 使用强密码
- 限制数据库访问 IP
- 启用 SSL 连接
- 定期备份数据

### 4. 配置 Row Level Security (RLS)

**为什么需要 RLS？**

没有 RLS，任何获得 API 密钥的人都可以：
- 获取所有用户信息（包括密码哈希）
- 获取所有班级评分数据
- 删除所有评分记录

**RLS 部署步骤：**

1. **备份现有数据**
   ```sql
   SELECT * FROM users;
   SELECT * FROM scores;
   SELECT * FROM scores_history;
   ```

2. **在 Supabase 控制台执行 RLS 设置**
   - 登录 [Supabase Dashboard](https://app.supabase.com)
   - 选择你的项目
   - 进入 `SQL Editor`
   - 执行 `config/supabase_rls_setup.sql` 文件内容

3. **验证 RLS 策略**
   ```sql
   -- 检查哪些表启用了 RLS
   SELECT schemaname, tablename, rowsecurity 
   FROM pg_tables 
   WHERE schemaname = 'public';
   ```

详细 RLS 配置请参考原 `docs/deployment/RLS_DEPLOYMENT_GUIDE.md`

---

## 📊 监控和维护

### 日志监控

在 Render Dashboard 中：
- 查看实时日志
- 监控错误率
- 追踪性能指标

### 健康检查

访问 `/health` 端点检查系统状态：
```json
{
  "status": "healthy",
  "database": "connected",
  "timestamp": "2024-01-01T00:00:00Z"
}
```

### 数据备份

1. **自动备份（推荐）**
   - Supabase 自动备份数据库
   - Render 自动备份文件系统

2. **手动备份**
   - 在管理面板中使用"数据备份"功能
   - 定期下载数据库备份文件

---

## 🔧 高级配置

### 推荐配置

1. **使用 PostgreSQL** 而不是 SQLite
2. **配置反向代理** (Nginx/Apache)
3. **启用 HTTPS** (Let's Encrypt)
4. **设置自动备份**
5. **配置监控告警**

### Nginx 配置示例

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### 环境变量

生产环境配置：

```bash
# 数据库 (PostgreSQL)
DATABASE_URL=postgresql://user:password@localhost:5432/classcomp

# Flask 配置
SECRET_KEY=your-production-secret-key
FLASK_ENV=production

# 服务器配置
PORT=5000

# 导出目录
EXPORT_FOLDER=exports
```

---

## 🔄 更新和升级

### 更新应用

```bash
# 1. 备份数据
python scripts/backup_data.py

# 2. 拉取最新代码
git pull origin main

# 3. 更新依赖
pip install -r requirements.txt --upgrade

# 4. 运行迁移脚本 (如果有)
python scripts/migrate_database.py

# 5. 重启服务
# Render 会自动检测代码变更并重新部署
```

---

## 🚨 常见问题解决

### 部署失败

1. 检查 `requirements.txt` 中的依赖
2. 验证 Python 版本兼容性
3. 查看 Render 构建日志

### 数据库连接失败

1. 检查 Supabase 项目状态
2. 验证 `DATABASE_URL` 格式
3. 确认数据库访问权限

### 健康检查失败

1. 检查应用启动是否成功
2. 验证端口配置 (5000)
3. 查看应用错误日志

### 性能问题

1. **响应缓慢**
   - 检查数据库查询性能
   - 优化数据库索引
   - 增加服务器资源

2. **内存不足**
   - 升级 Render 计划
   - 优化数据处理逻辑
   - 减少并发连接数

---

## ✅ 部署检查清单

### 部署前

- [ ] Python 3.9+ 已安装
- [ ] 所有依赖已安装
- [ ] 数据库已配置
- [ ] 环境变量已设置
- [ ] 代码已推送到 GitHub

### 部署后

- [ ] 应用可以访问
- [ ] 健康检查通过
- [ ] 默认密码已更改
- [ ] SECRET_KEY 已设置
- [ ] 数据库连接正常
- [ ] 日志正常记录
- [ ] 备份计划已设置
- [ ] RLS 已配置（如果使用 Supabase）

---

## 📞 获取帮助

- 📖 [本地部署指南](local-deployment.md)
- 🔒 [RLS 部署指南](RLS_DEPLOYMENT_GUIDE.md)（原文档位于 docs/deployment/）
- 🐛 [GitHub Issues](https://github.com/your-repo/ClassComp-Score/issues)
- 📧 技术支持: support@example.com

---

## 📝 部署状态

**当前状态：** ✅ 已准备好生产部署

所有必要的修复已完成，系统已针对 Render + Supabase 环境进行了优化。详见原 `docs/deployment/DEPLOYMENT_STATUS.md` 和 `docs/deployment/PRODUCTION_CHECKLIST.md`。

---

**部署完成后，记得：**
1. ⚠️ 更改所有默认密码
2. 🔒 配置 RLS 安全策略
3. 📊 设置监控和告警
4. 💾 配置定期备份
5. 📖 阅读用户手册培训团队