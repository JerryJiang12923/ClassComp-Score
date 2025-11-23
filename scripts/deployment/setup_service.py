#!/usr/bin/env python3
"""
服务配置模块
配置应用作为后台服务运行（Windows服务/systemd/launchd）
"""
import sys
import os
import platform
import subprocess
import shutil
from pathlib import Path


class ServiceSetup:
    """服务配置器"""
    
    def __init__(self, verbose=False):
        self.verbose = verbose
        self.system = platform.system()
        self.app_name = "ClassComp-Score"
        self.service_name = "classcomp-score"
        
    def log(self, message, level="INFO"):
        """记录日志"""
        if level == "ERROR":
            print(f"❌ {message}")
        elif level == "WARNING":
            print(f"⚠️  {message}")
        elif level == "INFO":
            if self.verbose:
                print(f"ℹ️  {message}")
        else:
            print(f"✅ {message}")
    
    def setup_windows_service(self, port=5000):
        """配置 Windows 服务"""
        print("\n⚙️  配置 Windows 服务...")
        
        # 检查是否以管理员身份运行
        try:
            import ctypes
            is_admin = ctypes.windll.shell32.IsUserAnAdmin()
            if not is_admin:
                self.log("需要管理员权限才能安装 Windows 服务", "WARNING")
                self.log("建议: 右键点击脚本，选择'以管理员身份运行'", "INFO")
                return False
        except Exception:
            pass
        
        # 检查 NSSM 是否可用
        nssm_path = shutil.which("nssm")
        if not nssm_path:
            self.log("NSSM 未安装，将使用计划任务替代", "WARNING")
            return self.setup_windows_scheduled_task(port)
        
        # 使用 NSSM 安装服务
        app_dir = os.getcwd()
        python_exe = sys.executable
        script_path = os.path.join(app_dir, "serve.py")
        
        # 检查服务是否已存在
        check_cmd = ["nssm", "status", self.service_name]
        result = subprocess.run(check_cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            self.log(f"服务 {self.service_name} 已存在，正在移除...", "INFO")
            subprocess.run(["nssm", "stop", self.service_name], capture_output=True)
            subprocess.run(["nssm", "remove", self.service_name, "confirm"], capture_output=True)
        
        # 安装新服务
        install_cmd = [
            "nssm", "install", self.service_name,
            python_exe, script_path
        ]
        
        try:
            subprocess.run(install_cmd, check=True, capture_output=True)
            
            # 配置服务参数
            config_commands = [
                ["nssm", "set", self.service_name, "AppDirectory", app_dir],
                ["nssm", "set", self.service_name, "DisplayName", f"{self.app_name} Service"],
                ["nssm", "set", self.service_name, "Description", "班级评分系统后台服务"],
                ["nssm", "set", self.service_name, "Start", "SERVICE_AUTO_START"],
                ["nssm", "set", self.service_name, "AppStdout", os.path.join(app_dir, "logs", "service.log")],
                ["nssm", "set", self.service_name, "AppStderr", os.path.join(app_dir, "logs", "service_error.log")],
                ["nssm", "set", self.service_name, "AppEnvironmentExtra", f"PORT={port}"],
            ]
            
            for cmd in config_commands:
                subprocess.run(cmd, capture_output=True)
            
            # 启动服务
            subprocess.run(["nssm", "start", self.service_name], check=True, capture_output=True)
            
            self.log(f"Windows 服务 '{self.service_name}' 安装并启动成功", "SUCCESS")
            self.log("服务已配置为开机自动启动", "INFO")
            
            print("\n管理服务:")
            print(f"  启动: nssm start {self.service_name}")
            print(f"  停止: nssm stop {self.service_name}")
            print(f"  重启: nssm restart {self.service_name}")
            print(f"  移除: nssm remove {self.service_name}")
            
            return True
        except subprocess.CalledProcessError as e:
            self.log(f"服务安装失败: {e}", "ERROR")
            return False
    
    def setup_windows_scheduled_task(self, port=5000):
        """配置 Windows 计划任务（NSSM 不可用时的替代方案）"""
        print("\n⚙️  配置 Windows 计划任务...")
        
        app_dir = os.getcwd()
        python_exe = sys.executable
        script_path = os.path.join(app_dir, "serve.py")
        
        # 创建启动脚本
        startup_script = os.path.join(app_dir, "start_service.bat")
        with open(startup_script, 'w', encoding='utf-8') as f:
            f.write(f"""@echo off
cd /d "{app_dir}"
set PORT={port}
"{python_exe}" "{script_path}"
""")
        
        # 创建计划任务 XML
        task_xml = os.path.join(app_dir, "task.xml")
        with open(task_xml, 'w', encoding='utf-8') as f:
            f.write(f"""<?xml version="1.0" encoding="UTF-16"?>
<Task version="1.2" xmlns="http://schemas.microsoft.com/windows/2004/02/mit/task">
  <RegistrationInfo>
    <Description>{self.app_name} 自动启动任务</Description>
  </RegistrationInfo>
  <Triggers>
    <LogonTrigger>
      <Enabled>true</Enabled>
    </LogonTrigger>
  </Triggers>
  <Principals>
    <Principal>
      <LogonType>InteractiveToken</LogonType>
      <RunLevel>HighestAvailable</RunLevel>
    </Principal>
  </Principals>
  <Settings>
    <MultipleInstancesPolicy>IgnoreNew</MultipleInstancesPolicy>
    <DisallowStartIfOnBatteries>false</DisallowStartIfOnBatteries>
    <StopIfGoingOnBatteries>false</StopIfGoingOnBatteries>
    <AllowHardTerminate>true</AllowHardTerminate>
    <StartWhenAvailable>true</StartWhenAvailable>
    <RunOnlyIfNetworkAvailable>false</RunOnlyIfNetworkAvailable>
    <AllowStartOnDemand>true</AllowStartOnDemand>
    <Enabled>true</Enabled>
    <Hidden>false</Hidden>
    <RunOnlyIfIdle>false</RunOnlyIfIdle>
    <WakeToRun>false</WakeToRun>
    <ExecutionTimeLimit>PT0S</ExecutionTimeLimit>
    <Priority>7</Priority>
  </Settings>
  <Actions>
    <Exec>
      <Command>"{startup_script}"</Command>
      <WorkingDirectory>{app_dir}</WorkingDirectory>
    </Exec>
  </Actions>
</Task>
""")
        
        # 注册计划任务
        try:
            # 删除已存在的任务
            subprocess.run(
                ["schtasks", "/Delete", "/TN", self.service_name, "/F"],
                capture_output=True
            )
            
            # 创建新任务
            subprocess.run(
                ["schtasks", "/Create", "/TN", self.service_name, "/XML", task_xml],
                check=True,
                capture_output=True
            )
            
            self.log("计划任务创建成功", "SUCCESS")
            self.log("应用将在用户登录时自动启动", "INFO")
            
            print("\n管理计划任务:")
            print(f"  查看: schtasks /Query /TN {self.service_name}")
            print(f"  运行: schtasks /Run /TN {self.service_name}")
            print(f"  停止: taskkill /F /IM python.exe")
            print(f"  删除: schtasks /Delete /TN {self.service_name} /F")
            
            # 清理临时文件
            os.remove(task_xml)
            
            return True
        except subprocess.CalledProcessError as e:
            self.log(f"计划任务创建失败: {e}", "ERROR")
            return False
    
    def setup_systemd_service(self, port=5000):
        """配置 systemd 服务 (Linux)"""
        print("\n⚙️  配置 systemd 服务...")
        
        app_dir = os.getcwd()
        python_exe = sys.executable
        service_file = f"/etc/systemd/system/{self.service_name}.service"
        
        # 创建服务单元文件内容
        service_content = f"""[Unit]
Description={self.app_name} Service
After=network.target

[Service]
Type=simple
User={os.getenv('USER', 'root')}
WorkingDirectory={app_dir}
Environment="PATH={os.path.dirname(python_exe)}:$PATH"
Environment="PORT={port}"
ExecStart={python_exe} {app_dir}/serve.py
Restart=always
RestartSec=10
StandardOutput=append:{app_dir}/logs/service.log
StandardError=append:{app_dir}/logs/service_error.log

[Install]
WantedBy=multi-user.target
"""
        
        # 写入临时文件
        temp_service_file = f"/tmp/{self.service_name}.service"
        try:
            with open(temp_service_file, 'w') as f:
                f.write(service_content)
            
            # 使用 sudo 复制到系统目录
            subprocess.run(
                ["sudo", "cp", temp_service_file, service_file],
                check=True
            )
            
            # 重新加载 systemd
            subprocess.run(["sudo", "systemctl", "daemon-reload"], check=True)
            
            # 启用并启动服务
            subprocess.run(["sudo", "systemctl", "enable", self.service_name], check=True)
            subprocess.run(["sudo", "systemctl", "start", self.service_name], check=True)
            
            self.log(f"systemd 服务 '{self.service_name}' 配置成功", "SUCCESS")
            
            print("\n管理服务:")
            print(f"  启动: sudo systemctl start {self.service_name}")
            print(f"  停止: sudo systemctl stop {self.service_name}")
            print(f"  重启: sudo systemctl restart {self.service_name}")
            print(f"  状态: sudo systemctl status {self.service_name}")
            print(f"  日志: sudo journalctl -u {self.service_name} -f")
            
            return True
        except subprocess.CalledProcessError as e:
            self.log(f"systemd 服务配置失败: {e}", "ERROR")
            self.log("请确保以 sudo 权限运行此脚本", "INFO")
            return False
        except PermissionError:
            self.log("权限不足，需要 sudo 权限", "ERROR")
            return False
        finally:
            # 清理临时文件
            if os.path.exists(temp_service_file):
                os.remove(temp_service_file)
    
    def setup_launchd_service(self, port=5000):
        """配置 launchd 服务 (macOS)"""
        print("\n⚙️  配置 launchd 服务...")
        
        app_dir = os.getcwd()
        python_exe = sys.executable
        
        # LaunchAgent plist 文件路径
        launch_agents_dir = os.path.expanduser("~/Library/LaunchAgents")
        os.makedirs(launch_agents_dir, exist_ok=True)
        plist_file = os.path.join(launch_agents_dir, f"com.{self.service_name}.plist")
        
        # 创建 plist 内容
        plist_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.{self.service_name}</string>
    <key>ProgramArguments</key>
    <array>
        <string>{python_exe}</string>
        <string>{app_dir}/serve.py</string>
    </array>
    <key>WorkingDirectory</key>
    <string>{app_dir}</string>
    <key>EnvironmentVariables</key>
    <dict>
        <key>PORT</key>
        <string>{port}</string>
    </dict>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>{app_dir}/logs/service.log</string>
    <key>StandardErrorPath</key>
    <string>{app_dir}/logs/service_error.log</string>
</dict>
</plist>
"""
        
        try:
            # 写入 plist 文件
            with open(plist_file, 'w') as f:
                f.write(plist_content)
            
            # 加载服务
            subprocess.run(["launchctl", "unload", plist_file], capture_output=True)
            subprocess.run(["launchctl", "load", plist_file], check=True)
            
            self.log(f"launchd 服务配置成功: {plist_file}", "SUCCESS")
            
            print("\n管理服务:")
            print(f"  启动: launchctl start com.{self.service_name}")
            print(f"  停止: launchctl stop com.{self.service_name}")
            print(f"  卸载: launchctl unload {plist_file}")
            print(f"  重新加载: launchctl load {plist_file}")
            
            return True
        except subprocess.CalledProcessError as e:
            self.log(f"launchd 服务配置失败: {e}", "ERROR")
            return False
    
    def setup_service(self, port=5000, service_type=None, skip_service=False):
        """根据操作系统配置相应的服务"""
        if skip_service:
            self.log("跳过服务配置", "INFO")
            return True
        
        print("\n⚙️  配置后台服务")
        print("=" * 50)
        
        # 确保日志目录存在
        os.makedirs("logs", exist_ok=True)
        
        if self.system == "Windows":
            return self.setup_windows_service(port)
        elif self.system == "Linux":
            if service_type == "supervisord":
                self.log("supervisord 配置尚未实现", "WARNING")
                return False
            else:
                return self.setup_systemd_service(port)
        elif self.system == "Darwin":  # macOS
            return self.setup_launchd_service(port)
        else:
            self.log(f"不支持的操作系统: {self.system}", "ERROR")
            return False


def main():
    """命令行入口"""
    import argparse
    
    parser = argparse.ArgumentParser(description='ClassComp Score 服务配置工具')
    parser.add_argument('--port', type=int, default=5000, help='服务端口号')
    parser.add_argument('--service-type', type=str, choices=['systemd', 'supervisord', 'launchd'], help='服务类型')
    parser.add_argument('--skip-service', action='store_true', help='跳过服务配置')
    parser.add_argument('--verbose', '-v', action='store_true', help='显示详细信息')
    
    args = parser.parse_args()
    
    setup = ServiceSetup(verbose=args.verbose)
    success = setup.setup_service(
        port=args.port,
        service_type=args.service_type,
        skip_service=args.skip_service
    )
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()