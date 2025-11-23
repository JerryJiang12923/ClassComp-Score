#!/usr/bin/env python3
"""
健康监控模块
监控应用运行状态、数据库连接、HTTP端点等
"""
import sys
import os
import time
import requests
import subprocess
from datetime import datetime
from pathlib import Path


class HealthMonitor:
    """健康监控器"""
    
    def __init__(self, verbose=False):
        self.verbose = verbose
        self.checks_passed = 0
        self.checks_failed = 0
        
    def log(self, message, level="INFO"):
        """记录日志"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        if level == "ERROR":
            print(f"❌ [{timestamp}] {message}")
        elif level == "WARNING":
            print(f"⚠️  [{timestamp}] {message}")
        elif level == "INFO":
            if self.verbose:
                print(f"ℹ️  [{timestamp}] {message}")
        else:
            print(f"✅ [{timestamp}] {message}")
    
    def check_http_endpoint(self, url, timeout=10, retries=3):
        """检查 HTTP 端点"""
        self.log(f"检查 HTTP 端点: {url}", "INFO")
        
        for attempt in range(1, retries + 1):
            try:
                response = requests.get(url, timeout=timeout)
                if response.status_code == 200:
                    self.log(f"HTTP 端点响应正常 (状态码: {response.status_code})", "SUCCESS")
                    self.checks_passed += 1
                    return True
                else:
                    self.log(f"HTTP 端点返回异常状态码: {response.status_code}", "WARNING")
            except requests.exceptions.ConnectionError:
                if attempt < retries:
                    self.log(f"连接失败，{timeout}秒后重试 (尝试 {attempt}/{retries})...", "WARNING")
                    time.sleep(timeout)
                else:
                    self.log(f"无法连接到 {url}", "ERROR")
            except requests.exceptions.Timeout:
                self.log(f"请求超时 (> {timeout}秒)", "ERROR")
            except Exception as e:
                self.log(f"HTTP 检查失败: {e}", "ERROR")
        
        self.checks_failed += 1
        return False
    
    def check_database_connection(self):
        """检查数据库连接"""
        self.log("检查数据库连接...", "INFO")
        
        try:
            # 添加项目路径
            sys.path.insert(0, os.getcwd())
            from dotenv import load_dotenv
            load_dotenv()
            
            from classcomp.database import get_conn, put_conn
            
            conn = get_conn()
            cur = conn.cursor()
            cur.execute("SELECT 1")
            result = cur.fetchone()
            put_conn(conn)
            
            if result:
                self.log("数据库连接正常", "SUCCESS")
                self.checks_passed += 1
                return True
            else:
                self.log("数据库查询返回空结果", "ERROR")
                self.checks_failed += 1
                return False
        except ImportError as e:
            self.log(f"无法导入数据库模块: {e}", "ERROR")
            self.checks_failed += 1
            return False
        except Exception as e:
            self.log(f"数据库连接失败: {e}", "ERROR")
            self.checks_failed += 1
            return False
    
    def check_process_running(self, process_name="python"):
        """检查进程是否运行"""
        self.log(f"检查进程: {process_name}", "INFO")
        
        try:
            if sys.platform == "win32":
                # Windows
                cmd = ["tasklist", "/FI", f"IMAGENAME eq {process_name}.exe"]
            else:
                # Linux/Mac
                cmd = ["pgrep", "-f", process_name]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0 and result.stdout.strip():
                self.log(f"进程 {process_name} 正在运行", "SUCCESS")
                self.checks_passed += 1
                return True
            else:
                self.log(f"进程 {process_name} 未运行", "WARNING")
                self.checks_failed += 1
                return False
        except Exception as e:
            self.log(f"进程检查失败: {e}", "ERROR")
            self.checks_failed += 1
            return False
    
    def check_log_files(self, log_dir="logs", max_size_mb=100):
        """检查日志文件"""
        self.log(f"检查日志目录: {log_dir}", "INFO")
        
        if not os.path.exists(log_dir):
            self.log(f"日志目录不存在: {log_dir}", "WARNING")
            return True
        
        log_files = list(Path(log_dir).glob("*.log"))
        
        if not log_files:
            self.log("未找到日志文件", "INFO")
            return True
        
        total_size = 0
        large_files = []
        
        for log_file in log_files:
            size_mb = log_file.stat().st_size / (1024 ** 2)
            total_size += size_mb
            
            if size_mb > max_size_mb:
                large_files.append((log_file.name, size_mb))
        
        if large_files:
            self.log(f"发现超大日志文件:", "WARNING")
            for filename, size in large_files:
                self.log(f"  - {filename}: {size:.1f}MB", "WARNING")
            self.log("建议: 清理或归档旧日志文件", "INFO")
        else:
            self.log(f"日志文件正常 (共 {len(log_files)} 个文件, {total_size:.1f}MB)", "SUCCESS")
            self.checks_passed += 1
        
        return True
    
    def check_error_logs(self, log_dir="logs", error_keywords=None):
        """检查错误日志"""
        if error_keywords is None:
            error_keywords = ["ERROR", "CRITICAL", "Exception", "Traceback"]
        
        self.log("检查错误日志...", "INFO")
        
        log_files = [
            os.path.join(log_dir, "application.log"),
            os.path.join(log_dir, "error.log"),
            os.path.join(log_dir, "service_error.log")
        ]
        
        recent_errors = []
        
        for log_file in log_files:
            if not os.path.exists(log_file):
                continue
            
            try:
                with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
                    # 只读取最后1000行
                    lines = f.readlines()[-1000:]
                    
                    for line in lines:
                        if any(keyword in line for keyword in error_keywords):
                            recent_errors.append((os.path.basename(log_file), line.strip()))
            except Exception as e:
                self.log(f"无法读取日志文件 {log_file}: {e}", "WARNING")
        
        if recent_errors:
            self.log(f"发现 {len(recent_errors)} 个最近的错误", "WARNING")
            if self.verbose:
                for log_name, error_line in recent_errors[:10]:  # 只显示前10个
                    self.log(f"  [{log_name}] {error_line[:100]}", "INFO")
            return False
        else:
            self.log("未发现最近的错误", "SUCCESS")
            self.checks_passed += 1
            return True
    
    def run_health_check(self, host="localhost", port=5000):
        """运行完整健康检查"""
        print("\n🏥 ClassComp Score 健康检查")
        print("=" * 50)
        print(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        
        # 1. 检查 HTTP 端点
        url = f"http://{host}:{port}/health"
        http_ok = self.check_http_endpoint(url)
        
        # 2. 检查数据库连接
        db_ok = self.check_database_connection()
        
        # 3. 检查进程
        process_ok = self.check_process_running()
        
        # 4. 检查日志文件
        logs_ok = self.check_log_files()
        
        # 5. 检查错误日志
        errors_ok = self.check_error_logs()
        
        # 总结
        print("\n" + "=" * 50)
        print("📊 检查结果汇总:")
        print("=" * 50)
        
        total_checks = self.checks_passed + self.checks_failed
        print(f"  通过: {self.checks_passed}/{total_checks}")
        print(f"  失败: {self.checks_failed}/{total_checks}")
        
        if self.checks_failed == 0:
            print("\n✨ 所有检查通过，应用运行正常！")
            return True
        else:
            print(f"\n⚠️  {self.checks_failed} 项检查失败，请检查日志")
            return False
    
    def watch_health(self, host="localhost", port=5000, interval=30):
        """持续监控健康状态"""
        print(f"\n👀 开始持续监控 (每 {interval} 秒检查一次)")
        print("按 Ctrl+C 停止监控\n")
        
        try:
            while True:
                self.checks_passed = 0
                self.checks_failed = 0
                
                self.run_health_check(host, port)
                
                print(f"\n下次检查时间: {interval} 秒后...")
                time.sleep(interval)
                print("\n" + "=" * 50)
        except KeyboardInterrupt:
            print("\n\n监控已停止")


def main():
    """命令行入口"""
    import argparse
    
    parser = argparse.ArgumentParser(description='ClassComp Score 健康检查工具')
    parser.add_argument('--host', type=str, default='localhost', help='服务器地址')
    parser.add_argument('--port', type=int, default=5000, help='服务端口')
    parser.add_argument('--watch', action='store_true', help='持续监控模式')
    parser.add_argument('--interval', type=int, default=30, help='监控间隔(秒)')
    parser.add_argument('--verbose', '-v', action='store_true', help='显示详细信息')
    
    args = parser.parse_args()
    
    monitor = HealthMonitor(verbose=args.verbose)
    
    if args.watch:
        monitor.watch_health(args.host, args.port, args.interval)
    else:
        success = monitor.run_health_check(args.host, args.port)
        sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()