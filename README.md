# ClassComp Score

![Version](https://img.shields.io/badge/version-1.1.0-blue.svg)
![Python](https://img.shields.io/badge/Python-3.9%2B-blue)
![Flask](https://img.shields.io/badge/Flask-2.x-orange)
![License](https://img.shields.io/badge/License-MIT-green.svg)

**学校机房电脑卫生评分系统**

一个现代化、响应式的学校机房管理评分系统。支持信息委员和新媒体委员对各班级电脑使用情况进行定期评分，并提供完善的数据管理和统计分析功能。

---

## 📋 项目简介

ClassComp Score 是一个专为学校机房管理设计的评分系统，帮助学校建立规范化的电脑卫生管理机制。系统通过周期性评分、智能数据分析和多角色协作，提升机房管理效率。

**核心价值：**
- 🎯 **规范管理**：建立标准化的电脑卫生评分体系
- 📊 **数据驱动**：通过数据分析发现和改进管理问题
- 🤝 **多方协作**：信息委员、新媒体委员、管理员各司其职
- 📱 **随时随地**：完美支持移动端，随时随地完成评分

---

## 👥 用户角色

系统支持三种用户角色，每种角色具有不同的权限和功能：

### 1️⃣ 信息委员（Info Commissioner）
**基础评分人员 | 权重：1.0x**

- 按照评分链条对指定年级班级进行评分
- 评分链条：中预→初一→初二→中预，高一↔高二，高一VCE↔高二VCE
- 查看个人评分历史记录
- 在评分周期内可覆盖之前的评分

**适用场景**：各班级的信息委员负责日常评分工作

### 2️⃣ 新媒体委员（New Media Officer）
**特殊评分人员 | 权重：1.5x**

- 可以对所有年级班级进行评分（不受评分链条限制）
- 评分权重为信息委员的1.5倍
- 评分记录标记为"新媒体委员"来源
- 查看个人评分历史记录

**适用场景**：新媒体部门进行专项检查或毕业班评估

### 3️⃣ 管理员（Administrator）
**系统管理员 | 最高权限**

- 用户管理：创建、删除用户，重置密码
- 学期配置：设置学期、评分周期、参与班级
- 权重配置：调整各类评分人员的权重
- 数据管理：导出Excel报告、备份数据库
- 统计查看：查看所有评分数据和统计分析
- 周期管理：动态切换单周/双周评分周期

**适用场景**：信息技术部门或教务处管理人员

---

## ✨ 核心特性

### 🔐 多角色权限系统
- 三种用户角色，权限清晰
- 灵活的权重配置机制
- 安全的用户认证和会话管理

### 📅 智能周期性评分
- 支持单周（7天）和双周（14天）评分周期
- 可在学期中期动态切换周期类型
- 同周期重复评分自动覆盖，历史记录完整保留
- 智能周期边界处理

### 📊 完善的数据管理
- Excel多表格导出（评分明细、汇总矩阵、统计分析）
- 数据库一键备份和恢复
- 支持SQLite（开发）和PostgreSQL（生产）
- 评分历史完整追溯

### 📈 实时数据可视化
- 评分趋势图表
- 年级班级对比分析
- 评分完成率监控
- 直观的统计卡片展示

### 📱 全面移动端支持
- 响应式界面设计
- 所有功能完美适配手机浏览器
- 触控友好的操作体验
- 随时随地完成评分

---

## 🚀 快速开始

### 环境要求

- Python 3.9+
- pip 包管理器
- SQLite（开发）或 PostgreSQL（生产）

### 安装步骤

```bash
# 1. 克隆项目
git clone https://github.com/your-username/ClassComp-Score.git
cd ClassComp-Score

# 2. 安装依赖
pip install -r requirements.txt

# 3. 初始化数据库
python scripts/init_db.py

# 4. 启动应用
python app.py
```

### 首次登录

访问 `http://127.0.0.1:5000`

**默认管理员账户：**
- 用户名：`admin`
- 密码：`admin123`

⚠️ **重要**：首次登录后请立即修改默认密码！

详细步骤请查看 [快速开始指南](docs/quick-start.md)

---

## 📚 文档导航

### 📖 使用者文档

| 角色 | 文档链接 | 说明 |
|------|---------|------|
| 👨‍🎓 信息委员 | [信息委员使用手册](docs/user-guide/info-commissioner-guide.md) | 评分流程、规则说明、常见问题 |
| 📹 新媒体委员 | [新媒体委员使用手册](docs/user-guide/new-media-officer-guide.md) | 特殊权限、跨年级评分指南 |
| 👨‍💼 管理员 | [管理员使用手册](docs/user-guide/admin-guide.md) | 系统配置、用户管理、数据导出 |

### 🔧 功能文档

| 文档类型 | 链接 | 说明 |
|---------|------|------|
| ✨ 功能特性 | [features.md](docs/features.md) | 完整的功能介绍 |
| 🔄 动态周期 | [动态周期使用指南](docs/user-guide/dynamic-period-usage.md) | 周期切换操作指南 |
| 🔍 故障排除 | [troubleshooting.md](docs/TROUBLESHOOTING.md) | 常见问题解决方案 |

### 🚀 部署文档

| 文档类型 | 链接 | 说明 |
|---------|------|------|
| 💻 本地部署 | [local-deployment.md](docs/deployment/local-deployment.md) | 开发环境部署指南 |
| 🌐 生产部署 | [production-deployment.md](docs/deployment/production-deployment.md) | 生产环境部署指南 |
| 📋 部署检查清单 | [PRODUCTION_CHECKLIST.md](docs/deployment/PRODUCTION_CHECKLIST.md) | 上线前检查事项 |

### 🔨 开发者文档

| 文档类型 | 链接 | 说明 |
|---------|------|------|
| 🏗️ 系统架构 | [development/](docs/development/) | 架构设计和技术选型 |
| 📐 实现计划 | [implementation-plans/](docs/development/implementation-plans/) | 功能实现方案 |

---

## 🛠️ 技术栈

### 后端技术
- **Web框架**：Flask 2.x
- **数据库**：SQLite（开发）/ PostgreSQL（生产）
- **WSGI服务器**：Gunicorn（Linux/macOS）/ Waitress（Windows）
- **数据处理**：Pandas, XlsxWriter

### 前端技术
- **UI框架**：Bootstrap 5
- **JavaScript库**：jQuery, Chart.js
- **图标**：Font Awesome

### 安全特性
- 密码哈希存储（Werkzeug）
- SQL注入防护（参数化查询）
- XSS防护（模板自动转义）
- CSRF防护（表单令牌）
- 登录速率限制

---

## 📁 项目结构

```
ClassComp-Score/
├── app.py                  # 主应用入口
├── requirements.txt        # Python依赖
├── README.md              # 项目说明
│
├── src/classcomp/         # 主应用包
│   ├── models/            # 数据模型
│   ├── routes/            # 路由处理
│   ├── utils/             # 工具函数
│   ├── templates/         # HTML模板
│   ├── static/            # 静态资源
│   └── database/          # 数据库
│
├── scripts/               # 工具脚本
│   ├── init_db.py        # 数据库初始化
│   └── reset_password.py # 密码重置
│
├── docs/                  # 文档
│   ├── user-guide/       # 使用者文档
│   ├── development/      # 开发者文档
│   └── deployment/       # 部署文档
│
├── config/               # 配置文件
└── tests/                # 测试文件
```

---

## 🔄 评分机制

### 评分链条

```
中预班级 → 初一班级 → 初二班级 → 中预班级
     ↑___________________________↓

高一班级 ↔ 高二班级

高一VCE ↔ 高二VCE

        ↓
    新媒体委员
  （可评所有年级）
```

### 评分权重

- **信息委员**：1.0x（基础权重）
- **新媒体委员**：1.5x（专项检查权重）

最终成绩 = 各评分的加权平均值

---

## 📊 数据导出示例

系统支持导出包含以下内容的Excel报告：

1. **评分明细表**：所有评分记录（含历史覆盖记录）
2. **周期汇总表**：每个周期的班级平均分
3. **评分矩阵**：被评班级 × 评分班级的分数矩阵
4. **数据来源标记**：区分信息委员和新媒体委员的评分

---

## 🔒 安全建议

1. **首次部署**
   - 立即修改默认管理员密码
   - 设置强密码策略（8位以上，包含字母数字符号）
   - 启用HTTPS（生产环境必须）

2. **日常运维**
   - 定期备份数据库（建议每周一次）
   - 监控异常登录行为
   - 定期更新系统依赖

3. **用户管理**
   - 及时删除不再使用的账户
   - 定期重置用户密码
   - 为每个用户分配最小必要权限

---

## 📄 许可证

本项目采用 [MIT License](LICENSE) 开源协议。

---

## 🤝 贡献指南

欢迎提交 Issue 和 Pull Request！

### 贡献方式

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 提交 Pull Request

### 开发建议

- 遵循项目现有代码风格
- 为新功能添加文档
- 确保所有测试通过
- 更新CHANGELOG

---

## 📞 支持与反馈

### 获取帮助

- 📖 [查看完整文档](docs/)
- 🐛 [提交Bug报告](https://github.com/your-username/ClassComp-Score/issues)
- 💡 [功能建议](https://github.com/your-username/ClassComp-Score/issues/new?labels=enhancement)
- 💬 [讨论区](https://github.com/your-username/ClassComp-Score/discussions)

### 常见问题

在提交问题前，请先查看：
- [故障排除指南](docs/TROUBLESHOOTING.md)
- [已知问题列表](https://github.com/your-username/ClassComp-Score/issues)

---

## 🙏 致谢

感谢所有为本项目做出贡献的开发者和用户！

---

**⭐ 如果这个项目对你有帮助，请给它一个星标！**
