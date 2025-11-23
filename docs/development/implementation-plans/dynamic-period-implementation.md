# 动态评分周期机制实施方案

## 📋 项目概述

实现一个灵活的评分周期系统，支持单周（7天）和双周（14天）两种评分周期模式，并允许在学期中期无缝切换，同时完整保留所有历史数据。

---

## 🎯 核心需求分析

### 当前系统状态

**现有周期计算逻辑** ([`period_utils.py:73-151`](src/classcomp/utils/period_utils.py:73-151))：
- 当前使用固定的14天周期（`DAYS_IN_TWO_WEEKS = 14`）
- 基于学期开始日期和第一周期结束日期计算
- [`calculate_period_info()`](src/classcomp/utils/period_utils.py:73-151) 函数返回周期信息

**数据库结构** ([`create_semester_config.py:33-85`](scripts/create_semester_config.py:33-85))：
- `semester_config` 表：存储学期基本信息
- `semester_classes` 表：存储班级配置

**评分数据表** ([`init_db.py:42-56`](scripts/init_db.py:42-56))：
- `scores` 表：当前评分记录
- `scores_history` 表：历史评分记录

### 核心挑战

1. **周期长度的动态性**：需要支持在学期中期从双周切换到单周，或反之
2. **历史数据完整性**：切换后历史周期的结构不能改变
3. **日期边界计算**：每个周期必须有明确的开始和结束日期
4. **数据查询效率**：需要快速确定任何日期所属的周期
5. **Excel报表生成**：需要正确显示每个周期的实际时长

---

## 🏗️ 架构设计

### 设计原则

1. **周期元数据存储**：每个周期的配置信息独立存储
2. **向后兼容**：不破坏现有数据和查询逻辑
3. **清晰的边界**：周期之间无重叠、无间隙
4. **审计追踪**：记录所有配置变更

### 核心数据结构

```
period_metadata 表
├─ id (主键)
├─ semester_id (外键 -> semester_config)
├─ period_number (周期序号：0, 1, 2, ...)
├─ period_type (周期类型：'weekly' / 'biweekly')
├─ start_date (周期开始日期)
├─ end_date (周期结束日期)
├─ is_active (是否活跃)
├─ created_at (创建时间)
└─ created_by (创建者，用于审计)

period_config_history 表（审计日志）
├─ id (主键)
├─ semester_id (外键)
├─ config_type (配置类型：'weekly' / 'biweekly')
├─ effective_from_period (生效起始周期)
├─ changed_at (变更时间)
└─ changed_by (变更人)
```

---

## 📝 实施计划详细分解

### 阶段一：需求分析与架构设计 ✅

**已完成项**：
- 系统现状分析
- 核心挑战识别
- 架构设计方案
- 数据结构设计

---

### 阶段二：数据库架构升级

#### 任务 2.1：创建周期元数据表

**目标文件**：`scripts/create_period_metadata_tables.py`

**实现要点**：
- 创建 `period_metadata` 表存储每个周期的具体信息
- 创建 `period_config_history` 表记录配置变更历史
- 添加必要的索引优化查询性能
- 同时支持 SQLite 和 PostgreSQL

#### 任务 2.2：扩展学期配置表

**目标文件**：`scripts/alter_semester_config_tables.py`

**SQL变更**：
```sql
ALTER TABLE semester_config ADD COLUMN default_period_type TEXT DEFAULT 'biweekly';
ALTER TABLE semester_config ADD COLUMN current_period_type TEXT DEFAULT 'biweekly';
```

#### 任务 2.3：数据迁移脚本

**目标文件**：`scripts/migrate_existing_periods.py`

**迁移策略**：
1. 扫描现有 `scores` 表的所有评分日期
2. 使用现有逻辑计算每个日期的周期信息
3. 生成 `period_metadata` 记录（标记为 biweekly）
4. 验证数据完整性

---

### 阶段三：后端核心逻辑重构

#### 任务 3.1：重构周期计算工具

**目标文件**：`src/classcomp/utils/period_utils.py`

**关键函数**：

1. **calculate_period_info_v2()** - 新版周期计算
   - 优先从 `period_metadata` 表查询
   - 如果不存在，动态创建新周期
   - 支持周期类型变更逻辑

2. **get_or_create_period()** - 周期获取或创建
   - 处理周期边界计算
   - 自动生成连续周期
   - 事务安全性保证

3. **change_period_type()** - 周期类型变更
   - 验证生效日期
   - 更新配置表
   - 记录变更历史

#### 任务 3.2：更新评分提交逻辑

**目标文件**：`src/classcomp/models/base.py`

**修改点**：
- [`Score.create_score()`](src/classcomp/models/base.py:99-206) 使用新的周期计算函数
- 周期判断从"日期范围推算"改为"精确周期号匹配"
- 添加周期类型信息到评分记录（可选）

#### 任务 3.3：更新查询和统计逻辑

**涉及文件**：
- [`app.py`](app.py) - 多个端点需要更新
  - [`/my_scores`](app.py:971-1137) 教师监控面板
  - [`/api/my_scores`](app.py:1139-1206) 个人评分历史
  - [`/export_excel`](app.py:1253-1786) Excel导出

**关键变更**：
- 所有周期计算统一使用 `calculate_period_info_v2()`
- Excel报表中显示周期类型标签
- 统计查询考虑不同周期长度

---

### 阶段四：前端界面开发

#### 任务 4.1：学期设置页面增强

**目标文件**：[`src/classcomp/templates/admin_semester.html`](src/classcomp/templates/admin_semester.html)

**新增UI组件**：
- 周期类型配置卡片
- 当前周期类型显示
- 周期类型选择器（单周/双周）
- 生效日期选择器
- 变更原因输入框
- 配置历史记录列表

**JavaScript功能**：
- `changePeriodType()` - 周期类型变更
- `loadConfigHistory()` - 加载配置历史
- 表单验证和确认对话框

#### 任务 4.2：首页周期信息显示

**目标文件**：`src/classcomp/templates/index.html`

**显示内容**：
- 当前周期号
- 周期类型徽章（单周/双周）
- 周期日期范围
- 周期天数

#### 任务 4.3：教师监控面板更新

**目标文件**：`src/classcomp/templates/teacher_monitoring.html`

**功能增强**：
- 周期选择下拉框，显示周期类型
- 按周期筛选评分完成情况
- 显示历史周期的实际配置

---

### 阶段五：数据迁移与兼容

#### 任务 5.1：编写数据迁移脚本

**目标**：将现有隐式周期信息转换为显式的 `period_metadata` 记录

**步骤**：
1. 获取活跃学期配置
2. 查询所有唯一评分日期
3. 为每个日期计算周期信息
4. 插入 `period_metadata` 表
5. 验证迁移完整性

#### 任务 5.2：兼容性处理

**策略**：
- 保留旧版函数 `calculate_period_info_legacy()`
- 新版函数支持回退到旧逻辑
- 过渡期双版本并存
- 逐步切换到新版本

---

### 阶段六：测试与验证

#### 任务 6.1：单元测试

**测试文件**：`tests/test_period_utils.py`

**测试用例**：
- 双周到单周的切换
- 单周到双周的切换
- 周期边界无重叠验证
- 历史数据完整性验证
- 评分提交周期检测

#### 任务 6.2：集成测试

**测试场景**：
1. 完整的周期变更流程测试
2. 多次周期变更测试
3. 教师监控面板功能测试
4. Excel导出格式验证

#### 任务 6.3：性能测试

**测试目标**：
- 数据库查询响应时间
- Excel导出速度（1000+ 记录）
- 周期计算缓存命中率

**优化措施**：
- 添加数据库索引
- 实现内存缓存
- 连接池优化

---

### 阶段七：文档与部署

#### 任务 7.1：用户手册

**目标文件**：`docs/USER_GUIDE_DYNAMIC_PERIODS.md`

**内容**：
- 功能概述
- 配置步骤
- 使用指南
- 常见问题

#### 任务 7.2：开发者文档

**目标文件**：`docs/DEVELOPER_GUIDE_DYNAMIC_PERIODS.md`

**内容**：
- 架构说明
- API接口文档
- 关键函数说明
- 测试策略

#### 任务 7.3：部署清单

**检查项**：
- 数据库表结构更新
- 数据迁移执行
- 配置文件更新
- 回滚方案准备

---

## 🔍 关键技术细节

### 周期计算算法

**现有逻辑（固定14天）**：
```python
# 从第一周期结束日期开始，每14天一个周期
days_after_first_period = (target_date - first_period_end).days
period_number = (days_after_first_period - 1) // 14 + 1
```

**新逻辑（动态周期）**：
```python
# 1. 查询 period_metadata 表
SELECT * FROM period_metadata 
WHERE semester_id = ? 
  AND start_date <= ? 
  AND end_date >= ?

# 2. 如果不存在，获取上一周期
SELECT * FROM period_metadata 
WHERE semester_id = ? 
ORDER BY period_number DESC 
LIMIT 1

# 3. 根据 current_period_type 计算新周期
if current_period_type == 'weekly':
    days = 7
else:
    days = 14

new_start = last_period_end + timedelta(days=1)
new_end = new_start + timedelta(days=days-1)
```

### 周期类型变更流程

```
用户操作：变更周期类型
    ↓
验证：生效日期必须在未来
    ↓
更新：semester_config.current_period_type
    ↓
记录：period_config_history
    ↓
触发：下次生成周期时使用新类型
```

### 数据完整性保证

**关键原则**：
- 已生成的 `period_metadata` 记录永不修改
- 周期类型变更只影响未来周期
- 所有查询都基于 `period_metadata` 表

**边界情况处理**：
- 学期开始时自动生成第0周期
- 周期类型变更时不破坏当前周期
- 日期跨周期边界时的查询逻辑

---

## 📊 预期效果

### 功能层面

1. **灵活性**：管理员可以根据实际需求调整周期长度
2. **透明性**：所有历史配置变更都有记录
3. **准确性**：Excel报表正确显示每个周期的类型和时长

### 数据层面

1. **完整性**：历史评分数据的周期归属永久固定
2. **一致性**：所有模块使用统一的周期计算逻辑
3. **可追溯性**：配置变更历史完整记录

### 性能层面

1. **查询效率**：通过索引优化周期查询
2. **计算优化**：减少重复计算，使用缓存
3. **扩展性**：支持未来更多周期类型（如月度）

---

## ⚠️ 风险与应对

### 数据迁移风险

**风险**：历史数据迁移失败或数据丢失
**应对**：
- 迁移前完整备份数据库
- 编写验证脚本对比迁移前后数据
- 提供回滚脚本

### 兼容性风险

**风险**：新旧逻辑切换导致数据不一致
**应对**：
- 过渡期保留双版本逻辑
- 编写对比测试验证一致性
- 灰度发布策略

### 性能风险

**风险**：频繁查询 `period_metadata` 表影响性能
**应对**：
- 添加覆盖索引
- 实现应用层缓存
- 监控慢查询并优化

---

## 📅 实施时间表

| 阶段 | 预估时间 | 关键里程碑 |
|------|---------|-----------|
| 阶段一 | 已完成 | 方案设计完成 ✅ |
| 阶段二 | 2天 | 数据库表结构创建完成 |
| 阶段三 | 3天 | 后端核心逻辑重构完成 |
| 阶段四 | 2天 | 前端界面开发完成 |
| 阶段五 | 1天 | 数据迁移脚本完成 |
| 阶段六 | 2天 | 测试验证完成 |
| 阶段七 | 1天 | 文档和部署完成 |
| **总计** | **11天** | **完整功能上线** |

---

## 📚 相关资源

### 关键文件清单

**现有文件需修改**：
- [`src/classcomp/utils/period_utils.py`](src/classcomp/utils/period_utils.py)
- [`src/classcomp/models/base.py`](src/classcomp/models/base.py)
- [`app.py`](app.py)
- [`src/classcomp/templates/admin_semester.html`](src/classcomp/templates/admin_semester.html)
- [`scripts/create_semester_config.py`](scripts/create_semester_config.py)

**新增文件**：
- `scripts/create_period_metadata_tables.py`
- `scripts/alter_semester_config_tables.py`
- `scripts/migrate_existing_periods.py`
- `tests/test_period_utils.py`
- `docs/USER_GUIDE_DYNAMIC_PERIODS.md`
- `docs/DEVELOPER_GUIDE_DYNAMIC_PERIODS.md`

### 技术参考

**数据库设计**：
- 周期元数据模式
- 历史数据保留策略
- 索引优化方案

**算法设计**：
- 动态周期计算
- 边界条件处理
- 类型变更逻辑

---

## ✅ 验收标准

### 功能验收

- [ ] 支持单周和双周两种周期类型
- [ ] 支持学期中期变更周期类型
- [ ] 历史周期数据保持不变
- [ ] Excel报表正确显示周期类型
- [ ] 配置变更历史完整记录

### 性能验收

- [ ] 周期查询响应时间 < 100ms
- [ ] Excel导出（1000条记录）< 5秒
- [ ] 数据库查询无慢查询（> 1秒）

### 数据验收

- [ ] 迁移后数据完整性100%
- [ ] 周期边界无重叠无间隙
- [ ] 所有评分记录正确归属周期

---

## 🎉 结语

本实施方案提供了完整的动态评分周期机制设计和实施路线图。通过分阶段、模块化的开发方式，确保系统升级的稳定性和可维护性。

关键成功要素：
1. **清晰的数据结构设计**：周期元数据的独立存储
2. **向后兼容的重构策略**：新旧逻辑平滑过渡
3. **完善的测试覆盖**：保证系统可靠性
4. **详细的文档支持**：降低使用和维护成本

建议先完成数据库架构升级和数据迁移，再逐步进行后端和前端的功能开发，最后进行全面测试和文档编写。