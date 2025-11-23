# ClassComp Score 故障排除指南

## 📋 常见问题和解决方案

本指南包含部署和运行 ClassComp Score 时可能遇到的常见问题及其解决方法。

---

## 🔍 部署问题

### 1. Python 未找到或版本过低

**问题:**
```
❌ Python 版本过低: 3.7, 需要 3.9+
或
'python' 不是内部或外部命令
```

**解决方案:**

1. **安装 Python 3.9+**
   - 访问 https://www.python.org/downloads/
   - 下载并安装 Python 3.9 或更高版本
   - **重要:** 安装时勾选 "Add Python to PATH"

2. **验证安装**
   ```cmd
   python --version
   ```

3. **如果仍然无法识别:**
   - 手动添加 Python 到系统 PATH
   - Windows: 系统属性 -> 环境变量 -> Path
   - 添加: `C:\Python39` 和 `C:\Python39\Scripts`

### 2. pip 安装失败

**问题:**
```
❌ 依赖安装失败
ERROR: Could not find a version that satisfies the requirement...
```

**解决方案:**

1. **升级 pip**
   ```cmd
   python -m pip install --upgrade pip
   ```

2. **使用国内镜像源**
   ```cmd
   pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
   ```

3. **清理缓存重试**
   ```cmd
   pip cache purge
   pip install -r requirements.txt
   ```

4. **使用虚拟环境**
   ```cmd
   python -m venv venv
   venv\Scripts\activate
   pip install -r requirements.txt
   ```

### 3. 端口被占用

**问题:**
```
⚠️ 端口 5000 被占用或无法访问
```

**解决方案:**

1. **查找占用端口的进程 (Windows)**
   ```cmd
   netstat -ano | findstr :5000
   ```
   记下最后的 PID，然后：
   ```cmd
   taskkill /PID <PID> /F
   ```

2. **使用不同端口部署**
   ```cmd
   deploy.bat --port 8080
   ```

3. **修改 .env 文件**
   ```
   PORT=8080
   ```

### 4. 权限不足

**问题:**
```
❌ 目录不可写: logs/
需要管理员权限才能安装 Windows 服务
```

**解决方案:**

1. **以管理员身份运行**
   - 右键点击 `deploy.bat`
   - 选择 "以管理员身份运行"

2. **修改文件夹权限**
   - 右键项目文件夹 -> 属性 -> 安全
   - 确保当前用户有 "完全控制" 权限

3. **跳过服务安装**
   ```cmd
   deploy.bat --no-service
   ```

### 5. 数据库初始化失败

**问题:**
```
❌ 数据库初始化失败
```

**解决方案:**

1. **检查数据库文件路径**
   - 确保 `src/classcomp/database/` 目录存在且可写

2. **手动初始化**
   ```cmd
   python scripts/init_db.py
   ```

3. **删除旧数据库重新初始化**
   ```cmd
   del src\classcomp\database\classcomp.db
   python scripts/init_db.py
   ```

4. **检查 .env 配置**
   ```
   DATABASE_URL=sqlite:///classcomp.db
   ```

---

## 🌐 运行时问题

### 6. 应用无法访问

**问题:**
浏览器显示"无法访问此网站"或连接超时

**解决方案:**

1. **检查应用是否运行**
   ```cmd
   tasklist | findstr python
   ```

2. **检查端口监听**
   ```cmd
   netstat -ano | findstr :5000
   ```

3. **检查防火墙设置**
   ```cmd
   netsh advfirewall firewall show rule name=all | findstr 5000
   ```
   
   如果没有规则，添加：
   ```cmd
   netsh advfirewall firewall add rule name="ClassComp Score" dir=in action=allow protocol=TCP localport=5000
   ```

4. **检查日志**
   ```cmd
   type logs\application.log
   type logs\error.log
   ```

5. **尝试本地地址**
   - 使用 `http://127.0.0.1:5000` 而不是 `http://localhost:5000`

### 7. 应用启动后立即关闭

**问题:**
应用窗口一闪而过或命令行立即关闭

**解决方案:**

1. **查看启动日志**
   ```cmd
   python serve.py
   ```
   不要关闭窗口，查看错误消息

2. **常见原因:**
   - 端口被占用 → 使用不同端口
   - 依赖缺失 → 重新安装依赖
   - 数据库损坏 → 重新初始化
   - 配置错误 → 检查 .env 文件

3. **调试模式运行**
   ```cmd
   python app.py
   ```

### 8. 页面显示 500 错误

**问题:**
浏览器显示 "Internal Server Error" 或 500 错误

**解决方案:**

1. **检查错误日志**
   ```cmd
   type logs\error.log
   ```

2. **常见原因:**
   - 数据库连接失败
   - 缺少必要的表或数据
   - Python 代码错误

3. **重新初始化数据库**
   ```cmd
   python scripts/init_db.py
   ```

4. **清理缓存**
   ```cmd
   rd /s /q __pycache__
   rd /s /q src\classcomp\__pycache__
   ```

### 9. 登录失败

**问题:**
使用默认账户无法登录

**解决方案:**

1. **重置管理员密码**
   ```cmd
   python scripts/reset_password.py
   ```

2. **重新初始化用户**
   ```cmd
   python scripts/init_db.py
   ```

3. **检查数据库用户表**
   ```cmd
   python
   >>> from classcomp.database import get_conn
   >>> conn = get_conn()
   >>> cur = conn.cursor()
   >>> cur.execute("SELECT username, role FROM users")
   >>> print(cur.fetchall())
   ```

### 10. 评分提交失败

**问题:**
提交评分时显示错误或评分未保存

**解决方案:**

1. **检查学期配置**
   - 登录管理员账户
   - 进入"学期设置"页面
   - 确保学期配置正确

2. **检查数据库**
   ```cmd
   python
   >>> from classcomp.database import get_conn
   >>> conn = get_conn()
   >>> cur = conn.cursor()
   >>> cur.execute("SELECT * FROM semester_config WHERE is_active = 1")
   >>> print(cur.fetchone())
   ```

3. **查看浏览器控制台**
   - 按 F12 打开开发者工具
   - 查看 Console 和 Network 标签
   - 查找错误信息

---

## 🔧 Windows 服务问题

### 11. 服务安装失败

**问题:**
```
❌ 服务安装失败
```

**解决方案:**

1. **检查 NSSM**
   ```cmd
   nssm --version
   ```
   
   如果未安装：
   - 下载: https://nssm.cc/download
   - 解压到 `C:\nssm`
   - 添加到系统 PATH

2. **手动安装服务**
   ```cmd
   nssm install classcomp-score "C:\Python39\python.exe" "D:\ClassComp-Score\serve.py"
   nssm set classcomp-score AppDirectory "D:\ClassComp-Score"
   nssm set classcomp-score Start SERVICE_AUTO_START
   nssm start classcomp-score
   ```

3. **使用计划任务替代**
   ```cmd
   python scripts/deployment/setup_service.py --no-service
   ```
   然后手动创建计划任务

### 12. 服务无法启动

**问题:**
服务状态显示"已停止"或启动失败

**解决方案:**

1. **查看服务日志**
   ```cmd
   type logs\service_error.log
   ```

2. **检查服务配置**
   ```cmd
   nssm edit classcomp-score
   ```

3. **重新安装服务**
   ```cmd
   nssm stop classcomp-score
   nssm remove classcomp-score confirm
   python scripts/deployment/setup_service.py
   ```

4. **手动启动测试**
   ```cmd
   python serve.py
   ```
   如果手动启动成功但服务失败，检查服务的路径配置

---

## 📊 性能问题

### 13. 应用响应缓慢

**解决方案:**

1. **检查系统资源**
   - 打开任务管理器
   - 查看 CPU 和内存使用情况

2. **优化数据库**
   ```cmd
   python
   >>> from classcomp.database import get_conn
   >>> conn = get_conn()
   >>> cur = conn.cursor()
   >>> cur.execute("VACUUM")
   >>> conn.commit()
   ```

3. **清理日志文件**
   ```cmd
   del logs\*.log
   ```

4. **增加 Waitress 线程数**
   编辑 [`serve.py`](../serve.py:1)，修改：
   ```python
   serve(application, threads=8)  # 增加到 8 个线程
   ```

### 14. 数据库锁定

**问题:**
```
database is locked
```

**解决方案:**

1. **关闭所有访问数据库的程序**
   ```cmd
   taskkill /F /IM python.exe
   ```

2. **重启应用**
   ```cmd
   python serve.py
   ```

3. **如果问题持续，考虑使用 PostgreSQL**

---

## 🔍 诊断工具

### 环境检查工具

```cmd
python scripts/deployment/check_environment.py --verbose
```

### 健康监控工具

```cmd
# 单次检查
python scripts/deployment/health_monitor.py

# 持续监控
python scripts/deployment/health_monitor.py --watch --interval 30
```

### 依赖检查工具

```cmd
python scripts/deployment/install_dependencies.py --verbose
```

---

## 📞 获取更多帮助

### 1. 查看日志

最重要的故障排除方法是查看日志文件：

```cmd
# 应用日志
type logs\application.log

# 错误日志
type logs\error.log

# 部署日志
dir logs\deployment_*.log
type logs\deployment_<timestamp>.log
```

### 2. 详细模式运行

```cmd
deploy.bat --verbose
```

### 3. 调试模式

编辑 [`.env`](../.env:1):
```
FLASK_ENV=development
```

然后运行:
```cmd
python app.py
```

### 4. 联系支持

如果上述方法都无法解决问题:

1. **收集信息:**
   - Python 版本: `python --version`
   - 操作系统版本
   - 错误日志内容
   - 问题重现步骤

2. **提交 Issue:**
   - GitHub Issues: https://github.com/your-repo/ClassComp-Score/issues
   - 包含完整的错误信息和日志

3. **技术支持:**
   - 邮箱: support@example.com
   - 附上诊断报告

---

## ✅ 预防性维护

### 定期任务

1. **每周:**
   - 检查日志文件大小
   - 清理旧日志 (保留最近 30 天)
   - 验证备份完整性

2. **每月:**
   - 更新依赖包
   - 检查系统更新
   - 测试恢复流程

3. **数据库维护:**
   ```cmd
   # SQLite 优化
   python -c "from classcomp.database import get_conn; c = get_conn(); c.cursor().execute('VACUUM'); c.commit()"
   ```

### 监控建议

1. **设置健康检查定时任务**
2. **配置日志轮转**
3. **启用自动备份**
4. **监控磁盘空间**

---

## 📖 相关文档

- [部署指南](DEPLOYMENT_GUIDE.md)
- [API 文档](api/)
- [用户指南](DYNAMIC_PERIOD_USER_GUIDE.md)

---

*最后更新: 2025-11-22*