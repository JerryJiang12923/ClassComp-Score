# 动态周期机制部署指南

本文档提供了部署和启用动态评分周期机制的详细步骤。

## 📋 部署前检查清单

### 1. 系统要求
- Python 3.7+
- SQLite 3.8+ 或 PostgreSQL 9.5+
- 已部署的ClassComp-Score系统

### 2. 备份数据
**重要：在执行任何数据库操作前，请务必备份数据！**

```bash
# SQLite备份
cp src/classcomp/database/classcomp.db src/classcomp/database/classcomp.db.backup

# PostgreSQL备份
pg_dump -h your_host -U your_user -d your_database > backup_$(date +%Y%m%d).sql
```

## 🚀 部署步骤

### 步骤1：创建周期元数据表

运行以下脚本创建必要的数据库表：

```bash
python scripts/create_period_metadata_tables.py
```

**预期输出：**
```
============================================================
创建周期元数据表和配置历史表
============================================================
✅ 成功创建表: period_metadata
✅ 成功创建表: period_config_history
✅ 所有操作完成
```

### 步骤2：扩展学期配置表

添加周期类型配置字段：

```bash
python scripts/alter_semester_config_tables.py
```

**预期输出：**
```
============================================================
扩展学期配置表
============================================================
✅ 成功添加字段: default_period_type
✅ 成功添加字段: current_period_type
✅ 学期配置表扩展完成
```

### 步骤3：迁移现有评分数据（可选）

如果有历史评分数据，运行迁移脚本：

```bash
python scripts/migrate_existing_periods.py
```

**注意：** 此脚本会将现有评分记录映射到周期元数据表中。

### 步骤4：验证部署

运行综合测试脚本验证所有功能：

```bash
python scripts/test_dynamic_period.py
```

**预期结果：** 6/6 测试通过（100%通过率）

### 步骤5：重启应用

```bash
# 开发环境
python app.py

# 生产环境
# 使用你的WSGI服务器重启应用
```

## 🔧 配置选项

### 环境变量

| 变量名 | 默认值 | 说明 |
|--------|--------|------|
| DATABASE_URL | sqlite:///classcomp.db | 数据库连接URL |
| SECRET_KEY | your-secret-key | Flask密钥 |

### 周期类型

| 类型 | 值 | 说明 |
|------|-----|------|
| 双周 | biweekly | 14天一个周期（默认） |
| 单周 | weekly | 7天一个周期 |

## 📊 数据库表结构

### period_metadata 表

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER | 主键 |
| semester_id | INTEGER | 学期ID |
| period_number | INTEGER | 周期号（从0开始） |
| period_type | TEXT | 周期类型 |
| start_date | TEXT/DATE | 开始日期 |
| end_date | TEXT/DATE | 结束日期 |
| is_active | INTEGER | 是否活跃 |
| created_at | TEXT/TIMESTAMP | 创建时间 |
| created_by | TEXT | 创建者 |

### period_config_history 表

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER | 主键 |
| semester_id | INTEGER | 学期ID |
| config_type | TEXT | 配置类型 |
| effective_from_period | INTEGER | 生效周期号 |
| effective_from_date | TEXT/DATE | 生效日期 |
| changed_at | TEXT/TIMESTAMP | 变更时间 |
| changed_by | TEXT | 变更者 |
| reason | TEXT | 变更原因 |

## 🔍 故障排除

### 问题1：sqlite3.Row 对象错误

**症状：** `'sqlite3.Row' object has no attribute 'get'`

**解决方案：** 确保使用最新版本的 `period_utils.py`，已将Row对象转换为字典。

### 问题2：表不存在

**症状：** `no such table: period_metadata`

**解决方案：** 运行 `python scripts/create_period_metadata_tables.py`

### 问题3：字段不存在

**症状：** `no such column: current_period_type`

**解决方案：** 运行 `python scripts/alter_semester_config_tables.py`

## 📞 技术支持

如遇到问题，请检查：
1. 数据库连接是否正常
2. 所有脚本是否按顺序执行
3. 测试脚本是否全部通过

## 📝 版本历史

| 版本 | 日期 | 说明 |
|------|------|------|
| 1.0.0 | 2025-11-22 | 初始版本，实现动态周期机制 |