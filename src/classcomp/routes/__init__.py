"""
路由模块包 - Flask 蓝图定义
Route blueprints for ClassComp Score system.
"""

from flask import Blueprint

# 认证路由
auth_bp = Blueprint('auth', __name__, url_prefix='')

# 管理路由  
admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

# 评分路由
scores_bp = Blueprint('scores', __name__, url_prefix='')

# API路由
api_bp = Blueprint('api', __name__, url_prefix='/api')

__all__ = ['auth_bp', 'admin_bp', 'scores_bp', 'api_bp']