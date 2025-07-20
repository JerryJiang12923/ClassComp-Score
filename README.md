# ClassComp Score

**v0.9.9 开发测试中** - 信息委员电脑评分系统

一个用于学校机房管理的评分系统。信息委员学生定期检查各班级电脑使用情况，对电脑整洁度、物品摆放、使用规范等方面进行评分。系统支持周期性评分、教师监控和数据统计分析。

## 系统介绍

**评分流程**：信息委员按年级检查 → 对各班级电脑情况评分 → 生成统计报告

**适用场景**：中小学机房管理、学生自主管理、班级评比

**核心特点**：
- 重复评分覆盖机制
- 多角色权限管理  
- 实时数据统计
- Excel报告导出

## 快速开始

```bash
# 安装依赖
pip install -r requirements.txt

# 初始化数据库
python init_db.py

# 启动服务
python app.py
```

访问 http://localhost:5000

默认账户：
- 管理员：`admin` / `admin123`
- 学生：`g6c1` / `123456`
- 教师：`t6` / `123456`

## 功能

### 学生
- 登录后对指定年级班级评分
- 查看个人评分历史

### 教师  
- 查看本年级班级评分完成情况
- 数据统计和图表

### 管理员
- 用户管理
- 学期配置（班级设置、评分周期）
- 数据导出和备份

## 技术栈

- Flask + SQLite/PostgreSQL
- Bootstrap + jQuery
- Chart.js
- Pandas (Excel导出)

## 部署

### 开发环境
```bash
python app.py
```

### 生产环境
```bash
gunicorn app:app -b 0.0.0.0:5000
```


## 配置

### 环境变量
```bash
DATABASE_URL=sqlite:///classcomp.db
SECRET_KEY=your-secret-key
```

### 学期设置
访问 `/admin/semester` 配置：
- 学期开始日期
- 评分周期
- 班级列表
