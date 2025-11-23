# 快速开始指南

本指南将帮助您在本地环境快速部署和运行 ClassComp Score 系统。

---

## 📋 环境要求

### 必需软件

- **Python 3.9+**：[下载地址](https://www.python.org/downloads/)
  - 安装时务必勾选 "Add Python to PATH"
- **Git**（可选）：用于克隆项目

### 系统支持

- ✅ Windows 10/11
- ✅ macOS 10.14+
- ✅ Linux（Ubuntu, Debian, CentOS 等）

---

## 🚀 安装步骤

### 1. 获取项目

**方式一：使用 Git**
```bash
git clone https://github.com/your-username/ClassComp-Score.git
cd ClassComp-Score
```

**方式二：下载压缩包**
- 访问项目主页下载 ZIP
- 解压到任意目录
- 进入项目文件夹

### 2. 创建虚拟环境（推荐）

**Windows:**
```cmd
python -m venv venv
venv\Scripts\activate
```

**macOS/Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. 安装依赖

```bash
pip install -r requirements.txt
```

如果安装缓慢，可使用国内镜像：
```bash
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

### 4. 配置环境变量

**Windows:**
```cmd
copy .env.example .env
```

**macOS/Linux:**
```bash
cp .env.example .env
```

打开 `.env` 文件，根据需要修改配置：
```bash
# Flask 密钥（建议修改为随机字符串）
SECRET_KEY=your-secret-key-here

# 数据库 URL（默认使用 SQLite）
DATABASE_URL=sqlite:///classcomp.db

# 导出文件目录
EXPORT_FOLDER=exports
```

### 5. 初始化数据库

```bash
python scripts/init_db.py
```

这将创建所有必要的数据库表，并生成默认账户。

### 6. 启动应用

**开发模式（推荐首次使用）：**
```bash
python app.py
```

**生产模式：**

Windows:
```cmd
python serve.py
```

macOS/Linux:
```bash
python serve.py
```

---

## 🎯 首次使用

### 1. 访问系统

打开浏览器，访问：`http://127.0.0.1:5000`

### 2. 使用默认账户登录

系统预置了三类测试账户：

| 角色 | 用户名 | 密码 | 说明 |
|-----|--------|------|------|
| 管理员 | `admin` | `admin123` | 最高权限 |
| 教师 | `t6` | `123456` | 六年级教师 |
| 干事 | `g6c1` | `123456` | 六年级1班信息委员 |

⚠️ **重要**：首次登录后，请立即修改默认密码！

### 3. 配置学期信息（管理员）

1. 使用管理员账户登录
2. 点击顶部导航栏的 **"学期设置"**
3. 配置学期信息：
   - 学期名称（如：2024-2025学年第一学期）
   - 开始日期
   - 第一周期结束日期
   - 周期类型（单周/双周）
4. 添加参与评分的班级
5. 保存配置

### 4. 创建用户账户（管理员）

1. 点击 **"用户管理"**
2. 点击 **"创建新用户"**
3. 填写用户信息：
   - 用户名
   - 密码
   - 角色（admin/teacher/student）
   - 年级（如：6）
   - 班级（如：1）
4. 提交创建

### 5. 开始评分（干事）

1. 使用干事账户登录
2. 在首页看到待评分班级列表
3. 点击班级进入评分页面
4. 填写评分（0-100分）和备注
5. 提交评分

---

## ✅ 验证安装

运行以下命令检查系统状态：

```bash
# 检查 Python 版本
python --version

# 检查依赖安装
pip list | grep Flask

# 测试数据库连接
python -c "from src.classcomp.database import get_conn; print('Database OK' if get_conn() else 'Database Error')"
```

---

## 🔍 常见问题

### 问题 1：pip 安装失败

**错误信息：**
```
ERROR: Could not find a version that satisfies the requirement...
```

**解决方案：**
```bash
# 升级 pip
python -m pip install --upgrade pip

# 使用国内镜像源
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

### 问题 2：端口被占用

**错误信息：**
```
Address already in use
```

**解决方案：**

**Windows:**
```cmd
# 查找占用端口的进程
netstat -ano | findstr :5000

# 结束进程（替换 <PID> 为实际进程 ID）
taskkill /PID <PID> /F
```

**macOS/Linux:**
```bash
# 查找占用端口的进程
lsof -i :5000

# 结束进程
kill -9 <PID>
```

或者修改 `.env` 文件使用不同端口：
```bash
PORT=8080
```

### 问题 3：数据库初始化失败

**解决方案：**
```bash
# 删除旧数据库（会丢失数据）
# Windows
del src\classcomp\database\classcomp.db

# macOS/Linux
rm src/classcomp/database/classcomp.db

# 重新初始化
python scripts/init_db.py
```

### 问题 4：无法访问应用

**检查清单：**
- [ ] 应用是否正在运行？
- [ ] 浏览器地址是否正确？（`http://127.0.0.1:5000`）
- [ ] 防火墙是否阻止了端口？
- [ ] 是否有错误日志？查看 `logs/application.log`

---

## 📚 下一步

- 📖 [功能特性详解](features.md) - 了解系统的所有功能
- 🚀 [生产环境部署](deployment/production-deployment.md) - 部署到服务器
- 👥 [用户使用手册](user-guide/) - 各角色详细操作指南
- 🔍 [故障排除](troubleshooting.md) - 更多问题解决方案

---

## 💡 提示

1. **开发环境**：使用 `python app.py` 启动，支持热重载
2. **生产环境**：使用 `python serve.py` 启动，性能更好
3. **数据备份**：定期在管理面板中导出数据
4. **密码安全**：务必修改所有默认密码
5. **虚拟环境**：建议使用虚拟环境隔离依赖

---

**安装遇到问题？** 查看 [故障排除指南](troubleshooting.md) 或提交 [Issue](https://github.com/your-username/ClassComp-Score/issues)