# ClassComp Score 部署指南

## 📋 概述

本指南介绍如何使用一键部署脚本在本地环境快速部署 ClassComp Score 系统。

---

## 🎯 快速开始

### Windows 系统

1. **下载项目**
   ```cmd
   git clone https://github.com/your-repo/ClassComp-Score.git
   cd ClassComp-Score
   ```

2. **运行部署脚本**
   ```cmd
   deploy.bat
   ```

3. **访问应用**
   
   打开浏览器访问: http://localhost:5000

### Linux/Mac 系统

1. **下载项目**
   ```bash
   git clone https://github.com/your-repo/ClassComp-Score.git
   cd ClassComp-Score
   ```

2. **添加执行权限**
   ```bash
   chmod +x deploy.sh
   ```

3. **运行部署脚本**
   ```bash
   ./deploy.sh
   ```

4. **访问应用**
   
   打开浏览器访问: http://localhost:5000

---

## 🔧 部署选项

### 命令行参数

**Windows (deploy.bat):**
```cmd
deploy.bat [选项]

选项:
  --port PORT       指定服务端口 (默认: 5000)
  --no-service      不安装 Windows 服务
  --skip-deps       跳过依赖检查
  --verbose         显示详细信息
  --help            显示帮助信息
```

**Linux/Mac (deploy.sh):**
```bash
./deploy.sh [选项]

选项:
  --port PORT              指定服务端口 (默认: 5000)
  --service-type TYPE      服务类型: systemd, supervisord, launchd
  --no-service             不安装后台服务
  --skip-deps              跳过依赖检查
  --verbose                显示详细信息
  --help                   显示帮助信息
```

### 使用示例

```bash
# 部署到不同端口
./deploy.sh --port 8080

# 不安装后台服务
./deploy.sh --no-service

# 显示详细信息
./deploy.sh --verbose

# 组合使用
./deploy.sh --port 8080 --verbose --no-service
```

---

## 📦 部署流程详解

### 1. 环境检查 (check_environment.py)

自动检查：
- ✅ Python 版本 (需要 3.9+)
- ✅ 操作系统兼容性
- ✅ 磁盘空间 (最低 500MB)
- ✅ 端口可用性
- ✅ 文件读写权限
- ✅ 数据库连接

**如果检查失败:**
- 查看错误消息中的具体问题
- 参考 [故障排除指南](TROUBLESHOOTING.md)
- 手动修复问题后重新运行

### 2. 依赖安装 (install_dependencies.py)

自动安装项目依赖：
- 检查现有依赖
- 从 [`requirements.txt`](../requirements.txt:1) 安装缺失包
- 如果失败，自动尝试国内镜像源

**手动安装:**
```bash
# 使用默认源
pip install -r requirements.txt

# 使用清华镜像
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

### 3. 数据库初始化 (init_db.py)

自动执行：
- 创建数据库表结构
- 创建默认管理员账户
- 创建测试用户账户
- 初始化学期配置

**默认账户:**
- 管理员: `admin` / `admin123`
- 教师: `t6` / `123456`
- 学生: `g6c1` / `123456`

### 4. 应用启动 (serve.py)

使用 Waitress (Windows) 或 Gunicorn (Linux/Mac) WSGI 服务器启动应用。

**手动启动:**
```bash
# Windows
python serve.py

# Linux/Mac
python3 serve.py
```

### 5. 服务配置 (setup_service.py)

配置应用作为后台服务：

**Windows:**
- 使用 NSSM 或计划任务
- 配置开机自动启动
- 配置失败自动重启

**Linux (systemd):**
```bash
# 查看服务状态
sudo systemctl status classcomp-score

# 启动服务
sudo systemctl start classcomp-score

# 停止服务
sudo systemctl stop classcomp-score

# 重启服务
sudo systemctl restart classcomp-score

# 查看日志
sudo journalctl -u classcomp-score -f
```

**macOS (launchd):**
```bash
# 启动服务
launchctl start com.classcomp-score

# 停止服务
launchctl stop com.classcomp-score

# 查看状态
launchctl list | grep classcomp
```

### 6. 健康检查 (health_monitor.py)

验证部署成功：
- HTTP 端点响应
- 数据库连接
- 进程运行状态
- 日志文件检查
- 错误日志分析

**手动健康检查:**
```bash
python3 scripts/deployment/health_monitor.py --port 5000
```

---

## 🔐 安全配置

### 1. 更改默认密码

**强烈建议在生产环境中更改所有默认密码！**

```bash
# 使用密码重置脚本
python scripts/reset_password.py
```

### 2. 配置 SECRET_KEY

编辑 [`.env`](.env:1) 文件，设置强密钥：

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

### 4. 防火墙配置

**Windows:**
```cmd
# 允许端口 5000
netsh advfirewall firewall add rule name="ClassComp Score" dir=in action=allow protocol=TCP localport=5000
```

**Linux:**
```bash
# UFW
sudo ufw allow 5000/tcp

# firewalld
sudo firewall-cmd --add-port=5000/tcp --permanent
sudo firewall-cmd --reload
```

---

## 📊 监控和维护

### 日志文件

日志位置: [`logs/`](../logs:1)

- `application.log` - 应用运行日志
- `error.log` - 错误日志
- `service.log` - 服务运行日志
- `deployment_YYYYMMDD_HHMMSS.log` - 部署日志

**查看实时日志:**
```bash
# Windows
type logs\application.log

# Linux/Mac
tail -f logs/application.log
```

### 持续健康监控

```bash
# 每 30 秒检查一次
python3 scripts/deployment/health_monitor.py --watch --interval 30
```

### 数据备份

在管理面板中使用"数据备份"功能，或手动备份：

```bash
# SQLite
cp src/classcomp/database/classcomp.db backups/classcomp_$(date +%Y%m%d).db

# PostgreSQL
pg_dump -h localhost -U postgres classcomp > backups/classcomp_$(date +%Y%m%d).sql
```

---

## 🚀 生产环境部署

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

生产环境 [`.env`](.env:1) 配置：

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
sudo systemctl restart classcomp-score
```

---

## 📞 获取帮助

- 📖 [故障排除指南](TROUBLESHOOTING.md)
- 🐛 [GitHub Issues](https://github.com/your-repo/ClassComp-Score/issues)
- 📧 技术支持: support@example.com

---

## ✅ 部署检查清单

- [ ] Python 3.9+ 已安装
- [ ] 所有依赖已安装
- [ ] 数据库已初始化
- [ ] 应用可以访问 (http://localhost:5000)
- [ ] 健康检查通过
- [ ] 后台服务已配置 (可选)
- [ ] 默认密码已更改
- [ ] SECRET_KEY 已设置
- [ ] 防火墙已配置
- [ ] 日志正常记录
- [ ] 备份计划已设置

---

## 📝 版本历史

- **v1.1.0** (2024-01) - 添加一键部署功能
- **v1.0.0** (2023-12) - 初始版本