#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
周期管理API路由
提供周期配置、查询和变更的API接口
"""

from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from classcomp.database import get_conn, put_conn
from classcomp.utils.period_utils import (
    calculate_period_info_v2,
    change_period_type,
    get_current_semester_config
)
import os

period_api = Blueprint('period_api', __name__, url_prefix='/api/period')

@period_api.route('/info', methods=['GET'])
@login_required
def get_period_info():
    """
    获取指定日期的周期信息
    
    Query参数:
        date: 日期字符串 (YYYY-MM-DD), 可选，默认为当前日期
    
    返回:
        {
            "success": true,
            "period": {
                "period_number": int,
                "period_type": "weekly" | "biweekly",
                "period_start": "YYYY-MM-DD",
                "period_end": "YYYY-MM-DD",
                "display_name": "第X周期 (单周/双周)"
            }
        }
    """
    try:
        target_date = request.args.get('date', None)
        
        conn = get_conn()
        try:
            period_info = calculate_period_info_v2(target_date=target_date, conn=conn)
            
            # 格式化显示名称
            type_label = '单周' if period_info['period_type'] == 'weekly' else '双周'
            display_name = f"第{period_info['period_number'] + 1}周期 ({type_label})"
            
            return jsonify({
                'success': True,
                'period': {
                    'period_number': period_info['period_number'],
                    'period_type': period_info['period_type'],
                    'period_start': period_info['period_start'].strftime('%Y-%m-%d'),
                    'period_end': period_info['period_end'].strftime('%Y-%m-%d'),
                    'display_name': display_name
                }
            })
        finally:
            put_conn(conn)
    
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'获取周期信息失败: {str(e)}'
        }), 500


@period_api.route('/config_history', methods=['GET'])
@login_required
def get_config_history():
    """
    获取周期配置变更历史
    
    返回:
        {
            "success": true,
            "history": [
                {
                    "config_type": "weekly" | "biweekly",
                    "effective_from_period": int,
                    "effective_from_date": "YYYY-MM-DD",
                    "changed_at": "YYYY-MM-DD HH:MM:SS",
                    "changed_by": "username",
                    "reason": "变更原因"
                }
            ]
        }
    """
    try:
        conn = get_conn()
        try:
            # 获取当前学期配置
            config_data = get_current_semester_config(conn)
            if not config_data:
                return jsonify({
                    'success': False,
                    'message': '未找到活跃学期配置'
                }), 404
            
            semester_id = config_data['semester']['id']
            
            cur = conn.cursor()
            db_url = os.getenv("DATABASE_URL", "sqlite:///classcomp.db")
            is_sqlite = db_url.startswith("sqlite")
            placeholder = "?" if is_sqlite else "%s"
            
            # 查询配置历史
            cur.execute(f"""
                SELECT config_type, effective_from_period, effective_from_date,
                       changed_at, changed_by, reason
                FROM period_config_history
                WHERE semester_id = {placeholder}
                ORDER BY changed_at DESC
            """, (semester_id,))
            
            history_records = cur.fetchall()
            
            history = []
            for record in history_records:
                history.append({
                    'config_type': record['config_type'] if hasattr(record, 'keys') else record[0],
                    'effective_from_period': record['effective_from_period'] if hasattr(record, 'keys') else record[1],
                    'effective_from_date': str(record['effective_from_date'] if hasattr(record, 'keys') else record[2]),
                    'changed_at': str(record['changed_at'] if hasattr(record, 'keys') else record[3]),
                    'changed_by': record['changed_by'] if hasattr(record, 'keys') else record[4],
                    'reason': record['reason'] if hasattr(record, 'keys') else record[5]
                })
            
            return jsonify({
                'success': True,
                'history': history
            })
        
        finally:
            put_conn(conn)
    
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'获取配置历史失败: {str(e)}'
        }), 500


@period_api.route('/change_type', methods=['POST'])
@login_required
def change_type():
    """
    变更周期类型（仅管理员）
    
    请求体:
        {
            "new_type": "weekly" | "biweekly",
            "effective_date": "YYYY-MM-DD",
            "reason": "变更原因" (可选)
        }
    
    返回:
        {
            "success": true,
            "message": "变更成功信息",
            "effective_period_number": int
        }
    """
    # 只有管理员可以变更周期类型
    if not current_user.is_admin():
        return jsonify({
            'success': False,
            'message': '权限不足，只有管理员可以变更周期类型'
        }), 403
    
    try:
        data = request.get_json()
        
        new_type = data.get('new_type')
        effective_date = data.get('effective_date')
        reason = data.get('reason', '')
        
        if not new_type or not effective_date:
            return jsonify({
                'success': False,
                'message': '缺少必要参数：new_type 和 effective_date'
            }), 400
        
        # 验证周期类型
        if new_type not in ['weekly', 'biweekly']:
            return jsonify({
                'success': False,
                'message': '无效的周期类型，必须是 weekly 或 biweekly'
            }), 400
        
        conn = get_conn()
        try:
            # 获取当前学期配置
            config_data = get_current_semester_config(conn)
            if not config_data:
                return jsonify({
                    'success': False,
                    'message': '未找到活跃学期配置'
                }), 404
            
            semester_id = config_data['semester']['id']
            
            # 调用变更函数
            success, message, effective_period = change_period_type(
                semester_id=semester_id,
                new_type=new_type,
                effective_from_date=effective_date,
                changed_by=current_user.username,
                reason=reason,
                conn=conn
            )
            
            if success:
                return jsonify({
                    'success': True,
                    'message': message,
                    'effective_period_number': effective_period
                })
            else:
                return jsonify({
                    'success': False,
                    'message': message
                }), 400
        
        finally:
            put_conn(conn)
    
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'变更失败: {str(e)}'
        }), 500


@period_api.route('/list', methods=['GET'])
@login_required
def list_periods():
    """
    列出当前学期的所有周期
    
    返回:
        {
            "success": true,
            "periods": [
                {
                    "period_number": int,
                    "period_type": "weekly" | "biweekly",
                    "start_date": "YYYY-MM-DD",
                    "end_date": "YYYY-MM-DD",
                    "is_current": bool,
                    "display_name": "第X周期 (单周/双周)"
                }
            ]
        }
    """
    try:
        conn = get_conn()
        try:
            # 获取当前学期配置
            config_data = get_current_semester_config(conn)
            if not config_data:
                return jsonify({
                    'success': False,
                    'message': '未找到活跃学期配置'
                }), 404
            
            semester_id = config_data['semester']['id']
            
            # 查询所有周期
            cur = conn.cursor()
            db_url = os.getenv("DATABASE_URL", "sqlite:///classcomp.db")
            is_sqlite = db_url.startswith("sqlite")
            placeholder = "?" if is_sqlite else "%s"
            
            cur.execute(f"""
                SELECT period_number, period_type, start_date, end_date
                FROM period_metadata
                WHERE semester_id = {placeholder} AND is_active = 1
                ORDER BY period_number
            """, (semester_id,))
            
            period_records = cur.fetchall()
            
            # 获取当前日期所属周期
            current_period_info = calculate_period_info_v2(conn=conn)
            current_period_number = current_period_info['period_number']
            
            periods = []
            for record in period_records:
                period_num = record['period_number'] if hasattr(record, 'keys') else record[0]
                period_type = record['period_type'] if hasattr(record, 'keys') else record[1]
                start_date = record['start_date'] if hasattr(record, 'keys') else record[2]
                end_date = record['end_date'] if hasattr(record, 'keys') else record[3]
                
                type_label = '单周' if period_type == 'weekly' else '双周'
                
                periods.append({
                    'period_number': period_num,
                    'period_type': period_type,
                    'start_date': str(start_date),
                    'end_date': str(end_date),
                    'is_current': period_num == current_period_number,
                    'type_label': type_label,
                    'display_name': f"第{period_num + 1}周期 ({type_label})"
                })
            
            return jsonify({
                'success': True,
                'periods': periods,
                'current_period_number': current_period_number
            })
        
        finally:
            put_conn(conn)
    
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'获取周期列表失败: {str(e)}'
        }), 500