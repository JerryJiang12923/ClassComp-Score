# ClassComp Score

![Version](https://img.shields.io/badge/version-1.1.0-blue.svg)
![Python](https://img.shields.io/badge/Python-3.9%2B-blue)
![Flask](https://img.shields.io/badge/Flask-2.x-orange)
![License](https://img.shields.io/badge/License-MIT-green.svg)

**信息委员电脑评分系统**

一个现代化、响应式的学校机房管理评分系统。信息委员学生可以方便地在桌面或移动设备上，定期检查各班级电脑使用情况，对电脑整洁度、物品摆放、使用规范等方面进行评分。

---

## ✨ 核心特性

- **多角色权限系统**：干事（信息委员）、教师、管理员三级权限
- **灵活的周期性评分**：支持单周/双周动态切换，智能覆盖重复评分
- **实时数据可视化**：直观的图表展示评分总览、趋势和年级分布
- **完整的数据管理**：用户管理、学期配置、数据导出、一键备份
- **全面移动端适配**：所有功能完美支持手机浏览器操作

---

## 🚀 快速开始

详细步骤请查看 [快速开始指南](docs/quick-start.md)

```bash
# 克隆项目
git clone https://github.com/your-username/ClassComp-Score.git
cd ClassComp-Score

# 安装依赖
pip install -r requirements.txt

# 初始化数据库
python scripts/init_db.py

# 启动应用
python app.py
```

访问 `http://127.0.0.1:5000`，使用默认管理员账户登录：`admin` / `admin123`

---

## 📚 文档导航

| 文档类型 | 链接 | 说明 |
|---------|------|------|
| 📖 快速开始 | [docs/quick-start.md](docs/quick-start.md) | 详细的安装和配置步骤 |
| ✨ 功能特性 | [docs/features.md](docs/features.md) | 完整的功能介绍和截图 |
| 🚀 部署指南 | [docs/deployment/](docs/deployment/) | 本地和生产环境部署 |
| 👥 用户手册 | [docs/user-guide/](docs/user-guide/) | 各角色使用指南 |
| 🔧 开发文档 | [docs/development/](docs/development/) | 架构设计和 API 文档 |
| 🔍 故障排除 | [docs/troubleshooting.md](docs/troubleshooting.md) | 常见问题解决方案 |

---

## 🛠️ 技术栈

- **后端**：Flask 2.x
- **数据库**：SQLite（开发）/ PostgreSQL（生产）
- **前端**：Bootstrap 5, jQuery, Chart.js
- **数据处理**：Pandas, XlsxWriter
- **WSGI 服务器**：Gunicorn（Linux/macOS）/ Waitress（Windows）

---

## 📄 许可证

本项目采用 [MIT License](LICENSE) 开源协议。

---

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📞 支持

- 📖 [完整文档](docs/)
- 🐛 [问题反馈](https://github.com/your-username/ClassComp-Score/issues)
- 💬 [讨论区](https://github.com/your-username/ClassComp-Score/discussions)
