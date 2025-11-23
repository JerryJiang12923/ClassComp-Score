#!/usr/bin/env python3
"""
依赖安装模块
自动检测和安装项目依赖
"""
import sys
import os
import subprocess
import platform
from pathlib import Path


class DependencyInstaller:
    """依赖安装器"""
    
    def __init__(self, verbose=False):
        self.verbose = verbose
        self.errors = []
        self.installed = []
        
    def log(self, message, level="INFO"):
        """记录日志"""
        if level == "ERROR":
            self.errors.append(message)
            print(f"❌ {message}")
        elif level == "WARNING":
            print(f"⚠️  {message}")
        elif level == "INFO":
            if self.verbose:
                print(f"ℹ️  {message}")
        else:
            print(f"✅ {message}")
    
    def check_pip_installed(self):
        """检查 pip 是否安装"""
        try:
            result = subprocess.run(
                [sys.executable, "-m", "pip", "--version"],
                capture_output=True,
                text=True,
                check=True
            )
            if self.verbose:
                self.log(f"pip 已安装: {result.stdout.strip()}", "INFO")
            return True
        except subprocess.CalledProcessError:
            self.log("pip 未安装或无法访问", "ERROR")
            self.log("请安装 pip: python -m ensurepip --upgrade", "INFO")
            return False
    
    def upgrade_pip(self):
        """升级 pip 到最新版本"""
        if self.verbose:
            print("\n📦 升级 pip...")
        try:
            subprocess.run(
                [sys.executable, "-m", "pip", "install", "--upgrade", "pip"],
                capture_output=not self.verbose,
                check=True
            )
            self.log("pip 已升级到最新版本", "SUCCESS")
            return True
        except subprocess.CalledProcessError as e:
            self.log(f"pip 升级失败: {e}", "WARNING")
            return False
    
    def check_requirements_file(self):
        """检查 requirements.txt 是否存在"""
        req_file = Path("requirements.txt")
        if req_file.exists():
            self.log(f"找到依赖文件: {req_file}", "INFO")
            return True
        else:
            self.log("未找到 requirements.txt 文件", "ERROR")
            return False
    
    def install_from_requirements(self, use_mirror=False):
        """从 requirements.txt 安装依赖"""
        print("\n📦 安装项目依赖...")
        
        if not self.check_requirements_file():
            return False
        
        cmd = [sys.executable, "-m", "pip", "install", "-r", "requirements.txt"]
        
        # 如果使用镜像源
        if use_mirror:
            mirror_url = "https://pypi.tuna.tsinghua.edu.cn/simple"
            cmd.extend(["-i", mirror_url])
            print(f"使用镜像源: {mirror_url}")
        
        try:
            subprocess.run(
                cmd,
                check=True,
                capture_output=not self.verbose
            )
            self.log("依赖安装完成", "SUCCESS")
            return True
        except subprocess.CalledProcessError as e:
            self.log(f"依赖安装失败: {e}", "ERROR")
            
            if not use_mirror:
                print("\n💡 提示: 可以尝试使用国内镜像源重新安装")
                print("   清华镜像: https://pypi.tuna.tsinghua.edu.cn/simple")
                print("   阿里镜像: https://mirrors.aliyun.com/pypi/simple/")
            
            return False
    
    def check_critical_packages(self):
        """检查关键包是否已安装"""
        print("\n🔍 检查关键依赖...")
        
        critical_packages = [
            "flask",
            "flask_cors",
            "flask_login",
            "werkzeug",
            "pandas",
            "waitress" if platform.system() == "Windows" else "gunicorn"
        ]
        
        missing_packages = []
        installed_packages = []
        
        for package in critical_packages:
            try:
                __import__(package.replace("-", "_"))
                installed_packages.append(package)
                if self.verbose:
                    self.log(f"{package} 已安装", "INFO")
            except ImportError:
                missing_packages.append(package)
                self.log(f"{package} 未安装", "WARNING")
        
        if missing_packages:
            print(f"\n⚠️  缺少 {len(missing_packages)} 个关键依赖:")
            for pkg in missing_packages:
                print(f"  - {pkg}")
            return False
        else:
            self.log(f"所有关键依赖已就绪 ({len(installed_packages)} 个)", "SUCCESS")
            return True
    
    def install_package(self, package_name, use_mirror=False):
        """安装单个包"""
        cmd = [sys.executable, "-m", "pip", "install", package_name]
        
        if use_mirror:
            mirror_url = "https://pypi.tuna.tsinghua.edu.cn/simple"
            cmd.extend(["-i", mirror_url])
        
        try:
            subprocess.run(cmd, check=True, capture_output=not self.verbose)
            self.installed.append(package_name)
            self.log(f"{package_name} 安装成功", "SUCCESS")
            return True
        except subprocess.CalledProcessError as e:
            self.log(f"{package_name} 安装失败: {e}", "ERROR")
            return False
    
    def create_virtual_environment(self, venv_path="venv"):
        """创建虚拟环境（可选）"""
        print(f"\n🔧 创建虚拟环境: {venv_path}")
        
        if Path(venv_path).exists():
            self.log(f"虚拟环境已存在: {venv_path}", "INFO")
            return True
        
        try:
            subprocess.run(
                [sys.executable, "-m", "venv", venv_path],
                check=True,
                capture_output=not self.verbose
            )
            self.log(f"虚拟环境创建成功: {venv_path}", "SUCCESS")
            
            # 提供激活指令
            if platform.system() == "Windows":
                activate_cmd = f"{venv_path}\\Scripts\\activate"
            else:
                activate_cmd = f"source {venv_path}/bin/activate"
            
            print(f"\n激活虚拟环境:")
            print(f"  {activate_cmd}")
            
            return True
        except subprocess.CalledProcessError as e:
            self.log(f"虚拟环境创建失败: {e}", "ERROR")
            return False
    
    def run_installation(self, use_mirror=False, skip_upgrade=False):
        """运行完整安装流程"""
        print("📦 ClassComp Score 依赖安装")
        print("=" * 50)
        
        # 1. 检查 pip
        if not self.check_pip_installed():
            return False
        
        # 2. 升级 pip (可选)
        if not skip_upgrade:
            self.upgrade_pip()
        
        # 3. 检查现有依赖
        has_all = self.check_critical_packages()
        
        # 4. 如果缺少依赖，从 requirements.txt 安装
        if not has_all:
            print("\n正在安装缺失的依赖...")
            success = self.install_from_requirements(use_mirror=use_mirror)
            
            if not success and not use_mirror:
                # 安装失败，尝试使用镜像
                print("\n使用国内镜像重试...")
                success = self.install_from_requirements(use_mirror=True)
            
            if not success:
                print("\n❌ 依赖安装失败")
                print("\n💡 建议:")
                print("  1. 检查网络连接")
                print("  2. 尝试手动安装: pip install -r requirements.txt")
                print("  3. 使用虚拟环境: python -m venv venv")
                return False
            
            # 重新检查
            has_all = self.check_critical_packages()
        
        # 5. 总结
        print("\n" + "=" * 50)
        if has_all:
            print("✨ 依赖安装完成，所有必需包已就绪！")
            if self.installed:
                print(f"\n新安装的包 ({len(self.installed)}):")
                for pkg in self.installed:
                    print(f"  - {pkg}")
            return True
        else:
            print("❌ 部分依赖安装失败")
            return False


def main():
    """命令行入口"""
    import argparse
    
    parser = argparse.ArgumentParser(description='ClassComp Score 依赖安装工具')
    parser.add_argument('--mirror', action='store_true', help='使用国内镜像源')
    parser.add_argument('--skip-upgrade', action='store_true', help='跳过 pip 升级')
    parser.add_argument('--verbose', '-v', action='store_true', help='显示详细信息')
    parser.add_argument('--venv', type=str, help='创建虚拟环境')
    
    args = parser.parse_args()
    
    installer = DependencyInstaller(verbose=args.verbose)
    
    # 如果指定了虚拟环境，先创建
    if args.venv:
        installer.create_virtual_environment(args.venv)
        print("\n⚠️  请先激活虚拟环境，然后重新运行此脚本")
        sys.exit(0)
    
    success = installer.run_installation(
        use_mirror=args.mirror,
        skip_upgrade=args.skip_upgrade
    )
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()