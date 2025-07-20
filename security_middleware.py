#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
安全中间件
实施安全策略，如速率限制、日志记录等
"""

import time
import hashlib
from collections import defaultdict
from functools import wraps
from flask import request, jsonify, g
from security_constants import SESSION_SECURITY

class SecurityMiddleware:
    """安全中间件"""
    
    def __init__(self):
        self.login_attempts = defaultdict(list)
        self.rate_limits = defaultdict(list)
    
    def rate_limit(self, max_requests=60, window=60):
        """速率限制装饰器"""
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                client_ip = request.remote_addr
                now = time.time()
                
                # 清理过期记录
                cutoff = now - window
                self.rate_limits[client_ip] = [
                    timestamp for timestamp in self.rate_limits[client_ip]
                    if timestamp > cutoff
                ]
                
                # 检查速率限制
                if len(self.rate_limits[client_ip]) >= max_requests:
                    return jsonify({
                        'success': False,
                        'message': 'Rate limit exceeded. Please try again later.'
                    }), 429
                
                # 记录请求
                self.rate_limits[client_ip].append(now)
                
                return func(*args, **kwargs)
            return wrapper
        return decorator
    
    def login_protection(self, func):
        """登录保护装饰器 - 只用于登录路由"""
        @wraps(func)
        def wrapper(*args, **kwargs):
            client_ip = request.remote_addr
            now = time.time()
            
            # 清理过期的登录尝试记录
            cutoff = now - SESSION_SECURITY['LOCKOUT_DURATION']
            self.login_attempts[client_ip] = [
                timestamp for timestamp in self.login_attempts[client_ip]
                if timestamp > cutoff
            ]
            
            # 检查是否被锁定
            if len(self.login_attempts[client_ip]) >= SESSION_SECURITY['MAX_LOGIN_ATTEMPTS']:
                return jsonify({
                    'success': False,
                    'message': f'Account locked due to too many failed attempts. Try again in {SESSION_SECURITY["LOCKOUT_DURATION"]/60:.0f} minutes.'
                }), 423
            
            # 执行原函数
            result = func(*args, **kwargs)
            
            # 只有在登录路由且真正失败时才记录失败尝试
            # 判断是否为登录失败：检查是否有 flash 消息包含错误信息
            from flask import get_flashed_messages
            flashed_messages = get_flashed_messages()
            is_login_failed = any('错误' in msg or 'error' in msg.lower() for msg in flashed_messages)
            
            # 或者检查是否是返回登录页面（而不是重定向到其他页面）
            if (hasattr(result, 'status_code') and result.status_code == 200 and 
                hasattr(result, 'data') and b'login' in result.data.lower()) or is_login_failed:
                self.login_attempts[client_ip].append(now)
            
            return result
        return wrapper
    
    def log_security_event(self, event_type, details):
        """记录安全事件"""
        timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
        client_ip = request.remote_addr if request else 'unknown'
        user_agent = request.headers.get('User-Agent', 'unknown') if request else 'unknown'
        
        log_entry = f"[{timestamp}] SECURITY {event_type}: {details} | IP: {client_ip} | UA: {user_agent}"
        
        # 写入安全日志文件
        with open('security.log', 'a', encoding='utf-8') as f:
            f.write(log_entry + '\n')
        
        print(f"🔒 {log_entry}")

# 全局安全中间件实例
security_middleware = SecurityMiddleware()
