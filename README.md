# ClassComp Score

![Version](https://img.shields.io/badge/version-1.1.0-blue.svg)
![Python](https://img.shields.io/badge/Python-3.9%2B-blue)
![Flask](https://img.shields.io/badge/Flask-2.x-orange)
![License](https://img.shields.io/badge/License-MIT-green.svg)

**信息委员电脑评分系统**

一个现代化、响应式的学校机房管理评分系统。信息委员学生可以方便地在桌面或移动设备上，定期检查各班级电脑使用情况，对电脑整洁度、物品摆放、使用规范等方面进行评分。系统支持周期性评分、教师监控和数据统计分析。

---

## ✨ V1.1.0 版本亮点

**V1.1.0 是一次重大的界面和体验升级，核心更新包括：**

- **全面的移动端适配**：所有页面，包括评分、管理面板、教师监控和历史记录，现在都完全支持在手机浏览器上流畅使用。
- **统一的UI/UX设计**：重构了所有核心组件（卡片、按钮、导航栏、角标），实现了现代化、一致的视觉风格。
- **增强的管理面板**：为管理员和教师提供了更清晰、更美观的数据图表和统计卡片。
- **优化的工作流程**：改善了表格的排序、搜索和分页功能，提升了数据管理效率。

---

## 核心功能

- **多角色权限系统**:
    - **学生 (信息委员)**: 登录、评分、查看个人历史。
    - **教师**: 查看所管理年级的评分进度和统计数据。
    - **管理员**: 拥有最高权限，管理用户、配置学期、备份数据。
- **周期性评分**:
    - 学生在设定的评分周期内对指定年级的班级进行评分。
    - 同一周期内的重复评分会智能覆盖，并保留历史记录。
- **数据可视化面板**:
    - 为教师和管理员提供直观的图表，展示评分总览、今日趋势、年级分布等。
- **强大的数据管理**:
    - **用户管理**: 管理员可以轻松创建、删除用户。
    - **学期配置**: 可视化配置学期、周期和参与班级。
    - **数据导出**: 一键导出包含详细评分、历史记录和汇总矩阵的 Excel 报告。
    - **数据备份**: 支持一键备份全站数据为 `.db` (SQLite) 或 `.sql` (PostgreSQL) 文件。

---

## 🛠️ 技术栈

- **后端**: Flask
- **数据库**: SQLite (开发) / PostgreSQL (生产)
- **前端**: Bootstrap 5, jQuery, Font Awesome
- **数据处理与导出**: Pandas, XlsxWriter
- **图表**: Chart.js (通过静态资源引入)
- **表格**: DataTables.js
- **WSGI 服务器**: Gunicorn (Linux/macOS) / Waitress (Windows)

---

## 🚀 快速开始

### 1. 环境准备
- Python 3.9+
- Git

### 2. 克隆与安装
```bash
# 克隆仓库
git clone https://github.com/your-username/ClassComp-Score.git
cd ClassComp-Score

# (推荐) 创建并激活虚拟环境
python -m venv venv
# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt
```

### 3. 配置
```bash
# 从模板创建 .env 文件
# Windows
copy .env.example .env
# macOS/Linux
cp .env.example .env
```
打开 `.env` 文件，根据需要修改 `SECRET_KEY`。默认使用 `sqlite:///classcomp.db` 数据库，无需额外配置。

### 4. 初始化数据库
这将创建所有必要的表和默认的管理员/测试账户。
```bash
python init_db.py
```

### 5. 启动应用
```bash
# 启动开发服务器
python app.py
```
服务将运行在 `http://127.0.0.1:5000`。

---

## 默认账户

- **管理员**: `admin` / `admin123`
- **教师**: `t6` / `123456`
- **学生**: `g6c1` / `123456`

---

## 部署

本项目已为生产环境优化，可使用任何兼容的 WSGI 服务器。

**Windows (使用 Waitress):**
```bash
waitress-serve --host=0.0.0.0 --port=5000 app:app
```

**macOS/Linux (使用 Gunicorn):**
```bash
gunicorn --workers 4 --bind 0.0.0.0:5000 app:app
```
建议将 `render.yaml` 作为在 Render.com 等平台上一键部署的参考。
