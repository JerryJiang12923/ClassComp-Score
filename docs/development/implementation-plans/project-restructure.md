# ClassComp-Score 项目重组计划

## 当前问题
- 所有Python文件散落在根目录
- 缺少标准的包结构
- 没有清晰的模块分层
- 配置、工具、核心代码混在一起

## 目标结构

```
ClassComp-Score/
├── src/
│   └── classcomp/              # 主应用包
│       ├── __init__.py
│       ├── app.py              # Flask应用工厂
│       ├── config.py           # 配置管理
│       ├── models/             # 数据模型层
│       │   ├── __init__.py
│       │   ├── user.py
│       │   └── score.py
│       ├── routes/             # 路由层
│       │   ├── __init__.py
│       │   ├── auth.py         # 认证路由
│       │   ├── admin.py        # 管理路由
│       │   ├── scores.py       # 评分路由
│       │   └── api.py          # API路由
│       ├── forms/              # 表单层
│       │   ├── __init__.py
│       │   └── forms.py
│       ├── utils/              # 工具模块
│       │   ├── __init__.py
│       │   ├── time_utils.py
│       │   ├── period_utils.py
│       │   ├── class_sorting_utils.py
│       │   └── validators.py
│       ├── middleware/         # 中间件
│       │   ├── __init__.py
│       │   └── security.py
│       ├── database/           # 数据库层
│       │   ├── __init__.py
│       │   ├── connection.py
│       │   └── manager.py
│       ├── constants/          # 常量定义
│       │   ├── __init__.py
│       │   └── security.py
│       ├── static/             # 静态资源
│       │   ├── css/
│       │   │   ├── bootstrap.min.css
│       │   │   └── custom.css
│       │   └── exports/        # 导出文件目录
│       └── templates/          # 模板文件
│           ├── auth/
│           ├── admin/
│           └── ...
├── scripts/                    # 脚本工具
│   ├── init_db.py
│   ├── reset_password.py
│   ├── create_semester_config.py
│   └── timezone_check.py
├── tests/                      # 测试目录
│   ├── __init__.py
│   ├── test_models.py
│   ├── test_routes.py
│   └── test_utils.py
├── docs/                       # 文档目录
│   ├── deployment/
│   │   ├── DEPLOYMENT_STATUS.md
│   │   ├── PRODUCTION_CHECKLIST.md
│   │   └── RLS_DEPLOYMENT_GUIDE.md
│   └── api/
├── config/                     # 配置文件
│   ├── gunicorn.conf.py
│   ├── render.yaml
│   └── supabase_rls_setup.sql
├── .env.example
├── .gitignore
├── .roomodes
├── LICENSE
├── README.md
├── requirements.txt
├── setup.py
├── wsgi.py                     # WSGI入口
└── manage.py                   # 管理命令入口
```

## 重组步骤

### 1. 创建目录结构
- [x] 创建 `src/classcomp/` 主包目录
- [ ] 创建子包目录：models, routes, forms, utils, middleware, database, constants
- [ ] 创建 scripts, tests, docs, config 目录

### 2. 移动和重构核心代码
- [ ] 拆分 `app.py` 为应用工厂和路由模块
- [ ] 重构 `models.py` 为独立的模型文件
- [ ] 移动表单到 `forms/` 包
- [ ] 整理工具模块到 `utils/` 包
- [ ] 移动数据库代码到 `database/` 包
- [ ] 移动中间件到 `middleware/` 包
- [ ] 移动常量到 `constants/` 包

### 3. 更新导入语句
- [ ] 更新所有文件的 import 路径
- [ ] 确保相对导入正确
- [ ] 处理循环导入问题

### 4. 创建 __init__.py 文件
- [ ] 为每个包创建 `__init__.py`
- [ ] 导出公共接口

### 5. 整理配置和脚本
- [ ] 移动配置文件到 `config/`
- [ ] 移动工具脚本到 `scripts/`
- [ ] 移动文档到 `docs/`

### 6. 创建打包文件
- [ ] 创建 `setup.py` 或 `pyproject.toml`
- [ ] 更新 `requirements.txt`
- [ ] 创建 `MANIFEST.in`

### 7. 测试和验证
- [ ] 验证所有导入路径
- [ ] 测试应用启动
- [ ] 测试关键功能
- [ ] 更新文档

## 注意事项
1. 保持向后兼容：暂时保留旧的导入路径
2. 逐步迁移：先重构结构，再优化代码
3. 保持功能完整：确保所有功能正常工作
4. 更新部署配置：调整 WSGI 和服务器配置