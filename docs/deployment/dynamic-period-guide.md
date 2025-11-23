# 动态周期功能部署指南

本文档提供了部署和启用动态评分周期机制的详细步骤。

---

## 📋 功能概述

动态周期功能允许管理员在学期中灵活切换评分周期类型（单周/双周），所有历史数据完整保留。

### 核心特性

- **灵活切换**：支持双周 ↔ 单周动态切换
- **数据完整**：历史评分数据永久保留原有周期信息
- **无缝过渡**：切换时不影响当前周期
- **审计追踪**：记录所有配置变更历史

---

## 🚀 部署前检查

### 1. 系统要求

- Python 3.7+
- SQLite 3.8+ 或 PostgreSQL 9.5+
- 已部署的 ClassComp-Score 系统

### 2. 备份数据

**重要：在执行任何数据库操作前，请务必备份数据！**

```bash
# SQLite 备份
cp src/classcomp/database/classcomp.db src/classcomp/database/classcomp.db.backup

# PostgreSQL 备份
pg_dump -h your_host -U your_user -d your_database > backup_$(date +%Y%m%d).sql
```

---

## 📝 部署步骤

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

**创建的表结构：**

**period_metadata 表**
| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER | 主键 |
| semester_id | INTEGER | 学期ID |
| period_number | INTEGER | 周期号（从0开始） |
| period_type | TEXT | 周期类型（weekly/biweekly） |
| start_date | TEXT/DATE | 开始日期 |
| end_date | TEXT/DATE | 结束日期 |
| is_active | INTEGER | 是否活跃 |
| created_at | TEXT/TIMESTAMP | 创建时间 |
| created_by | TEXT | 创建者 |

**period_config_history 表**
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
# 使用你的 WSGI 服务器重启应用
sudo systemctl restart classcomp-score  # Linux
# 或
python serve.py  # Windows
```

---

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

---

## 🎯 使用指南

部署完成后，管理员可以在系统中使用动态周期功能：

1. **查看当前周期配置**
   - 登录管理员账户
   - 进入"学期设置"页面
   - 查看"评分周期配置"卡片

2. **变更周期类型**
   - 选择新的周期类型（单周/双周）
   - 选择生效日期（必须是未来日期）
   - 填写变更原因（可选）
   - 点击"变更周期类型"按钮
   - 确认操作

3. **查看配置历史**
   - 点击"查看配置历史"按钮
   - 查看所有周期类型变更记录

详细使用说明请参考 [动态周期使用指南](../user-guide/dynamic-period-usage.md)

---

## 🔍 故障排除

### 问题1：sqlite3.Row 对象错误

**症状：** `'sqlite3.Row' object has no attribute 'get'`

**解决方案：** 确保使用最新版本的 `src/classcomp/utils/period_utils.py`，已将 Row 对象转换为字典。

### 问题2：表不存在

**症状：** `no such table: period_metadata`

**解决方案：** 运行 `python scripts/create_period_metadata_tables.py`

### 问题3：字段不存在

**症状：** `no such column: current_period_type`

**解决方案：** 运行 `python scripts/alter_semester_config_tables.py`

### 问题4：数据迁移失败

**解决方案：**
1. 检查数据库备份是否存在
2. 查看迁移脚本日志
3. 手动检查数据完整性
4. 如有问题，从备份恢复并重试

---

## ✅ 验证清单

部署完成后，请验证以下项目：

- [ ] `period_metadata` 表已创建
- [ ] `period_config_history` 表已创建
- [ ] `semester_config` 表已添加新字段
- [ ] 历史数据迁移成功（如果有）
- [ ] 测试脚本全部通过
- [ ] 应用可以正常启动
- [ ] 管理员可以查看周期配置
- [ ] 管理员可以变更周期类型
- [ ] 配置历史记录正常显示

---

## 📚 相关文档

- [动态周期使用指南](../user-guide/dynamic-period-usage.md) - 用户操作手册
- [动态周期实施方案](../development/implementation-plans/dynamic-period-implementation.md) - 完整的技术设计
- [故障排除指南](../troubleshooting.md) - 常见问题解决

---

## 📞 技术支持

如遇到问题，请检查：
1. 数据库连接是否正常
2. 所有脚本是否按顺序执行
3. 测试脚本是否全部通过

或提交 [Issue](https://github.com/your-repo/ClassComp-Score/issues) 获取帮助。

---

## 📝 版本历史

| 版本 | 日期 | 说明 |
|------|------|------|
| 1.0.0 | 2025-11-22 | 初始版本，实现动态周期机制 |

---

**部署成功后，别忘了阅读 [用户使用指南](../user-guide/dynamic-period-usage.md) 了解如何使用这个强大的功能！**