# Tests 目录

此目录包含所有测试、调试、验证和工具文件。

## 文件分类

### 🧪 测试文件
- `test_*.py` - 单元测试和功能测试
- `test_*.xlsx` - 测试相关的Excel文件
- `quick_test.py` - 快速测试脚本

### 🔍 检查和验证工具
- `check_*.py` - 数据库结构和数据检查工具
- `verify_*.py` - 数据验证工具

### 🛠️ 调试工具
- `debug_*.py` - 调试脚本
- `debug_*.xlsx` - 调试生成的文件

### 📦 数据库工具
- `create_*.py` - 数据库创建工具
- `migrate_database.py` - 数据库迁移脚本
- `classcomp_production_backup.db` - 备份数据库

### 🔧 其他工具
- `tools/` - 其他工具脚本

## 使用说明

这些文件主要用于开发和调试过程中，生产环境不需要。如需运行某个测试或工具：

```bash
cd tests
python test_excel_export.py
```

或从项目根目录：

```bash
python tests/check_database_data.py
```
