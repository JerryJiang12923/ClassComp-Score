# 本地部署指南

本指南介绍如何在本地开发环境部署 ClassComp Score 系统。

---

## 快速部署

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

## 部署选项

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

## 部署流程详解

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
- 参考 [故障排除指南](../troubleshooting.md)
- 手动修复问题后重新运行

### 2. 依赖安装 (install_dependencies.py)

自动安装项目依赖：
- 检查现有依赖
- 从 [`requirements.txt`](../../requirements.txt) 安装缺失包
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

配置应用作为后台服务（可选）：

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
python scripts/deployment/health_monitor.py --port 5000
```

---

## 手动部署步骤

如果部署脚本无法使用，可手动进行以下步骤：

### 1. 环境准备

```bash
# 克隆项目
git clone https://github.com/your-repo/ClassComp-Score.git
cd ClassComp-Score

# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate
```

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

### 3. 配置环境

```bash
# 复制配置文件
# Windows
copy .env.example .env
# macOS/Linux
cp .env.example .env

# 编辑 .env 文件，根据需要修改配置
```

### 4. 初始化数据库

```bash
python scripts/init_db.py
```

### 5. 启动应用

```bash
# 开发模式
python app.py

# 生产模式
python serve.py
```

---

## 监控和维护

### 日志文件

日志位置: [`logs/`](../../logs)

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
python scripts/deployment/health_monitor.py --watch --interval 30
```

### 数据备份

在管理面板中使用"数据备份"功能，或手动备份：

```bash
# SQLite
# Windows
copy src\classcomp\database\classcomp.db backups\classcomp_%date%.db

# macOS/Linux
cp src/classcomp/database/classcomp.db backups/classcomp_$(date +%Y%m%d).db

# PostgreSQL
pg_dump -h localhost -U postgres classcomp > backups/classcomp_$(date +%Y%m%d).sql
```

---

## 性能优化

### 开发环境

```python
# app.py 中启用调试模式
app.config['DEBUG'] = True
app.config['PROPAGATE_EXCEPTIONS'] = True
```

### 生产环境

```bash
# 增加 Waitress 线程数
python -c "from waitress import serve; serve(app, threads=8, port=5000)"
```

---

## 常见问题

### 问题: 部署失败

**解决方案:**
1. 检查 Python 版本: `python --version`
2. 查看详细日志: `deploy.bat --verbose`
3. 检查依赖: `pip list`

### 问题: 数据库错误

**解决方案:**
1. 确保 `src/classcomp/database/` 目录存在
2. 删除旧数据库重新初始化
3. 检查文件读写权限

### 问题: 服务无法启动

**解决方案:**
1. 检查端口是否被占用
2. 查看详细日志
3. 尝试不同端口

详见 [故障排除指南](../troubleshooting.md)

---

## 下一步

- ✅ 本地测试应用功能
- 🚀 [生产环境部署](production-deployment.md)
- 👥 [用户手册](../user-guide/)
- 🔍 [故障排除](../troubleshooting.md)

---

**部署遇到问题？** 查看 [故障排除指南](../troubleshooting.md) 或提交 [Issue](https://github.com/your-repo/ClassComp-Score/issues)