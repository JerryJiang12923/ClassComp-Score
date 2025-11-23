#!/usr/bin/env python3
"""
环境检查模块
检查 Python 版本、系统兼容性、磁盘空间、端口可用性等
"""
import sys
import os
import platform
import shutil
import socket
import subprocess
from pathlib import Path


class EnvironmentChecker:
    """环境检查器"""
    
    def __init__(self, verbose=False):
        self.verbose = verbose
        self.errors = []
        self.warnings = []
        self.info = []
        
    def log(self, message, level="INFO"):
        """记录日志"""
        if level == "ERROR":
            self.errors.append(message)
            print(f"❌ {message}")
        elif level == "WARNING":
            self.warnings.append(message)
            print(f"⚠️  {message}")
        elif level == "INFO":
            self.info.append(message)
            if self.verbose:
                print(f"ℹ️  {message}")
        else:
            print(f"✅ {message}")
    
    def check_python_version(self, min_version=(3, 9)):
        """检查 Python 版本"""
        print("\n[1/6] 检查 Python 版本...")
        current_version = sys.version_info[:2]
        
        if current_version >= min_version:
            version_str = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
            self.log(f"Python {version_str} 已就绪", "SUCCESS")
            return True
        else:
            self.log(
                f"Python 版本过低: {current_version[0]}.{current_version[1]}, "
                f"需要 {min_version[0]}.{min_version[1]}+",
                "ERROR"
            )
            self.log("请访问 https://www.python.org/downloads/ 下载最新版本", "INFO")
            return False
    
    def check_system_compatibility(self):
        """检查系统兼容性"""
        print("\n[2/6] 检查系统兼容性...")
        system = platform.system()
        
        supported_systems = ["Windows", "Linux", "Darwin"]
        if system in supported_systems:
            system_name = "macOS" if system == "Darwin" else system
            self.log(f"系统 {system_name} {platform.release()} 兼容", "SUCCESS")
            return True
        else:
            self.log(f"不支持的操作系统: {system}", "ERROR")
            return False
    
    def check_disk_space(self, min_space_mb=500):
        """检查磁盘空间"""
        print("\n[3/6] 检查磁盘空间...")
        try:
            stat = shutil.disk_usage(os.getcwd())
            free_space_mb = stat.free / (1024 ** 2)
            free_space_gb = stat.free / (1024 ** 3)
            
            if free_space_mb >= min_space_mb:
                self.log(f"磁盘空间充足 ({free_space_gb:.1f}GB 可用)", "SUCCESS")
                return True
            else:
                self.log(
                    f"磁盘空间不足: {free_space_mb:.0f}MB 可用, "
                    f"需要至少 {min_space_mb}MB",
                    "ERROR"
                )
                return False
        except Exception as e:
            self.log(f"无法检查磁盘空间: {e}", "WARNING")
            return True  # 不阻止部署
    
    def check_port_available(self, port=5000, host='0.0.0.0'):
        """检查端口是否可用"""
        print(f"\n[4/6] 检查端口 {port} 可用性...")
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        
        try:
            # 尝试绑定端口
            sock.bind((host, port))
            sock.close()
            self.log(f"端口 {port} 可用", "SUCCESS")
            return True
        except socket.error as e:
            self.log(f"端口 {port} 被占用或无法访问", "WARNING")
            self.log("建议: 使用 --port 参数指定其他端口", "INFO")
            
            # 尝试找到可用端口
            for alternative_port in range(5001, 5010):
                try:
                    test_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    test_sock.bind((host, alternative_port))
                    test_sock.close()
                    self.log(f"建议使用端口: {alternative_port}", "INFO")
                    break
                except socket.error:
                    continue
            
            return False
        finally:
            sock.close()
    
    def check_write_permissions(self):
        """检查文件写入权限"""
        print("\n[5/6] 检查文件权限...")
        test_dirs = [
            os.getcwd(),
            os.path.join(os.getcwd(), 'logs'),
            os.path.join(os.getcwd(), 'exports')
        ]
        
        all_writable = True
        for dir_path in test_dirs:
            try:
                # 确保目录存在
                os.makedirs(dir_path, exist_ok=True)
                
                # 尝试写入测试文件
                test_file = os.path.join(dir_path, '.write_test')
                with open(test_file, 'w') as f:
                    f.write('test')
                os.remove(test_file)
                
                if self.verbose:
                    self.log(f"目录 {dir_path} 可写", "INFO")
            except Exception as e:
                self.log(f"目录 {dir_path} 不可写: {e}", "ERROR")
                all_writable = False
        
        if all_writable:
            self.log("文件权限检查通过", "SUCCESS")
        else:
            self.log("部分目录没有写入权限", "ERROR")
            if platform.system() == "Windows":
                self.log("建议: 以管理员身份运行脚本", "INFO")
            else:
                self.log("建议: 检查文件权限或使用 sudo", "INFO")
        
        return all_writable
    
    def check_database_connection(self):
        """检查数据库连接（可选）"""
        print("\n[6/6] 检查数据库连接...")
        try:
            from dotenv import load_dotenv
            load_dotenv()
            
            db_url = os.getenv("DATABASE_URL", "sqlite:///classcomp.db")
            
            if db_url.startswith("sqlite"):
                db_path = db_url.replace("sqlite:///", "")
                db_dir = os.path.dirname(db_path) if os.path.dirname(db_path) else "."
                
                if os.path.exists(db_path):
                    self.log(f"SQLite 数据库已存在: {db_path}", "SUCCESS")
                elif os.access(db_dir, os.W_OK):
                    self.log(f"SQLite 数据库将创建于: {db_path}", "INFO")
                    self.log("数据库连接检查通过", "SUCCESS")
                else:
                    self.log(f"无法在 {db_dir} 创建数据库文件", "ERROR")
                    return False
            else:
                # PostgreSQL 或其他数据库
                self.log(f"数据库配置: {db_url.split('@')[-1] if '@' in db_url else 'PostgreSQL'}", "INFO")
                self.log("将在启动时测试数据库连接", "INFO")
            
            return True
        except ImportError:
            self.log("python-dotenv 未安装，将在依赖安装步骤中处理", "WARNING")
            return True
        except Exception as e:
            self.log(f"数据库检查失败: {e}", "WARNING")
            return True  # 不阻止部署，稍后再试
    
    def run_all_checks(self, port=5000):
        """运行所有检查"""
        print("🔍 ClassComp Score 环境检查")
        print("=" * 50)
        
        checks = [
            ("Python 版本", self.check_python_version),
            ("系统兼容性", self.check_system_compatibility),
            ("磁盘空间", self.check_disk_space),
            ("端口可用性", lambda: self.check_port_available(port)),
            ("文件权限", self.check_write_permissions),
            ("数据库", self.check_database_connection)
        ]
        
        results = {}
        for check_name, check_func in checks:
            try:
                results[check_name] = check_func()
            except Exception as e:
                self.log(f"{check_name} 检查失败: {e}", "ERROR")
                results[check_name] = False
        
        # 总结
        print("\n" + "=" * 50)
        print("📊 检查结果汇总:")
        print("=" * 50)
        
        passed = sum(1 for v in results.values() if v)
        total = len(results)
        
        for check_name, result in results.items():
            status = "✅ 通过" if result else "❌ 失败"
            print(f"  {status}  {check_name}")
        
        print(f"\n通过: {passed}/{total}")
        
        if self.errors:
            print(f"\n❌ 错误 ({len(self.errors)}):")
            for error in self.errors:
                print(f"  - {error}")
        
        if self.warnings:
            print(f"\n⚠️  警告 ({len(self.warnings)}):")
            for warning in self.warnings:
                print(f"  - {warning}")
        
        # 判断是否可以继续
        critical_checks = ["Python 版本", "系统兼容性", "文件权限"]
        can_proceed = all(results.get(check, False) for check in critical_checks)
        
        if can_proceed:
            print("\n✨ 环境检查完成，可以继续部署！")
        else:
            print("\n❌ 环境检查失败，请修复上述问题后重试")
        
        return can_proceed, results


def main():
    """命令行入口"""
    import argparse
    
    parser = argparse.ArgumentParser(description='ClassComp Score 环境检查工具')
    parser.add_argument('--port', type=int, default=5000, help='要检查的端口号')
    parser.add_argument('--verbose', '-v', action='store_true', help='显示详细信息')
    
    args = parser.parse_args()
    
    checker = EnvironmentChecker(verbose=args.verbose)
    success, results = checker.run_all_checks(port=args.port)
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()