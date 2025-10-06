#!/usr/bin/env python3
"""
Network Monitor Setup and Run Script
Enhanced Ubuntu Python 3.13 Support
"""

import os
import sys
import subprocess
import platform
import shutil
import argparse
from pathlib import Path

class NetworkMonitorSetup:
    def __init__(self):
        self.os_type = platform.system().lower()
        self.is_windows = self.os_type == 'windows'
        self.is_linux = self.os_type == 'linux'
        self.is_macos = self.os_type == 'darwin'
        self.is_ubuntu = self._detect_ubuntu()
        self.tools_available = {}
        
        # Determine Python command
        self.python_cmd = self._find_python()
        
    def _detect_ubuntu(self):
        """Detect if running on Ubuntu"""
        if not self.is_linux:
            return False
        try:
            with open('/etc/os-release', 'r') as f:
                return 'ubuntu' in f.read().lower()
        except:
            return False
    
    def _find_python(self):
        """Find the best Python executable"""
        candidates = ['python3.13', 'python3', 'python']
        for cmd in candidates:
            if shutil.which(cmd):
                return cmd
        return 'python3'
    
    def _run_command(self, cmd, description="", check=True):
        """Run a command with error handling"""
        if description:
            print(f"🔄 {description}")
        
        try:
            if isinstance(cmd, str):
                result = subprocess.run(cmd, shell=True, check=check, 
                                      capture_output=True, text=True)
            else:
                result = subprocess.run(cmd, check=check, 
                                      capture_output=True, text=True)
            return result.returncode == 0
        except subprocess.CalledProcessError as e:
            print(f"❌ Command failed: {e}")
            return False
    
    def setup_system_requirements(self):
        """Setup system requirements based on OS"""
        print("\n📦 Setting up System Requirements...")
        
        if self.is_ubuntu:
            return self._setup_ubuntu()
        elif self.is_linux:
            return self._setup_linux_generic()
        elif self.is_windows:
            return self._setup_windows()
        elif self.is_macos:
            return self._setup_macos()
        else:
            print("❌ Unsupported operating system")
            return False
    
    def _setup_ubuntu(self):
        """Enhanced Ubuntu setup with Python 3.13"""
        print("🐧 Ubuntu detected - Enhanced setup available!")
        print("=============================================")
        
        # Check if ubuntu_python313_setup.py exists
        if os.path.exists('ubuntu_python313_setup.py'):
            print("🐍 Found ubuntu_python313_setup.py")
            print("This will install Python 3.13 and all dependencies")
            print("Including: nmap, traceroute, all Python packages, systemd service")
            
            response = input("Run enhanced Ubuntu Python 3.13 setup? (Y/n): ").strip().lower()
            if response in ['', 'y', 'yes']:
                print("🚀 Running enhanced Ubuntu setup...")
                result = subprocess.run([sys.executable, 'ubuntu_python313_setup.py'])
                if result.returncode == 0:
                    print("✅ Enhanced Ubuntu setup completed!")
                    return True
                else:
                    print("⚠️ Enhanced setup failed, falling back to basic setup")
        
        # Fallback to basic Ubuntu setup
        return self._setup_ubuntu_basic()
    
    def _setup_ubuntu_basic(self):
        """Basic Ubuntu setup"""
        print("🐧 Basic Ubuntu setup...")
        
        # Update package lists
        if not self._run_command("sudo apt update", "Updating package lists"):
            print("❌ Failed to update packages")
            return False
        
        # Install essential packages
        packages = [
            "python3", "python3-pip", "python3-venv", "python3-dev",
            "nmap", "net-tools", "iputils-ping", "traceroute", 
            "dnsutils", "curl", "wget", "arp-scan", "mtr-tiny",
            "build-essential", "git"
        ]
        
        cmd = f"sudo apt install -y {' '.join(packages)}"
        if not self._run_command(cmd, f"Installing packages: {', '.join(packages)}"):
            print("⚠️ Some packages may have failed to install")
        
        # Install Python packages
        self._install_python_packages()
        
        print("✅ Basic Ubuntu setup completed")
        return True
    
    def _setup_linux_generic(self):
        """Generic Linux setup"""
        print("🐧 Generic Linux setup...")
        
        # Try to detect package manager
        if shutil.which('apt'):
            # Debian/Ubuntu family
            packages = ["python3", "python3-pip", "nmap", "net-tools", "iputils-ping", "traceroute"]
            cmd = f"sudo apt update && sudo apt install -y {' '.join(packages)}"
        elif shutil.which('yum'):
            # RHEL/CentOS family
            packages = ["python3", "python3-pip", "nmap", "net-tools", "iputils", "traceroute"]
            cmd = f"sudo yum install -y {' '.join(packages)}"
        elif shutil.which('dnf'):
            # Fedora
            packages = ["python3", "python3-pip", "nmap", "net-tools", "iputils", "traceroute"]
            cmd = f"sudo dnf install -y {' '.join(packages)}"
        elif shutil.which('pacman'):
            # Arch Linux
            packages = ["python", "python-pip", "nmap", "net-tools", "iputils", "traceroute"]
            cmd = f"sudo pacman -S --noconfirm {' '.join(packages)}"
        else:
            print("❌ Unknown package manager. Please install manually:")
            print("   python3, python3-pip, nmap, net-tools, iputils-ping, traceroute")
            return True
        
        self._run_command(cmd, f"Installing packages: {', '.join(packages)}")
        self._install_python_packages()
        
        print("✅ Generic Linux setup completed")
        return True
    
    def _setup_windows(self):
        """Windows setup"""
        print("🪟 Windows setup...")
        
        # Check Python
        if not shutil.which('python') and not shutil.which('python3'):
            print("❌ Python not found. Please install from python.org")
            return False
        
        # Windows has built-in network tools
        tools = ['ping', 'tracert', 'nslookup', 'netstat']
        for tool in tools:
            self.tools_available[tool] = shutil.which(tool) is not None
        
        self._install_python_packages()
        
        print("✅ Windows setup completed")
        return True
    
    def _setup_macos(self):
        """macOS setup"""
        print("🍎 macOS setup...")
        
        # Check Homebrew
        if shutil.which('brew'):
            print("🍺 Homebrew detected")
            if not shutil.which('nmap'):
                print("💡 For advanced features: brew install nmap")
        
        # macOS has built-in network tools
        tools = ['ping', 'traceroute', 'nslookup', 'netstat', 'dig']
        for tool in tools:
            self.tools_available[tool] = shutil.which(tool) is not None
        
        self._install_python_packages()
        
        print("✅ macOS setup completed")
        return True
    
    def _install_python_packages(self):
        """Install Python packages"""
        print("🐍 Installing Python packages...")
        
        # Core packages
        packages = [
            "flask==3.0.0",
            "flask-socketio==5.3.6",
            "psutil==5.9.8", 
            "requests==2.31.0",
            "speedtest-cli==2.1.3"
        ]
        
        for package in packages:
            cmd = f"{self.python_cmd} -m pip install {package}"
            if not self._run_command(cmd, f"Installing {package}"):
                print(f"⚠️ Failed to install {package}")
        
        # Install from requirements if available
        if os.path.exists('requirements.txt'):
            cmd = f"{self.python_cmd} -m pip install -r requirements.txt"
            self._run_command(cmd, "Installing from requirements.txt")
    
    def check_installation(self):
        """Check if everything is installed correctly"""
        print("\n🔍 Checking Installation...")
        
        # Check Python
        result = subprocess.run([self.python_cmd, '--version'], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ Python: {result.stdout.strip()}")
        else:
            print("❌ Python check failed")
            return False
        
        # Check Python packages
        packages_to_check = ['flask', 'psutil', 'requests']
        for package in packages_to_check:
            try:
                result = subprocess.run([self.python_cmd, '-c', f'import {package}'], 
                                      capture_output=True)
                if result.returncode == 0:
                    print(f"✅ {package} package available")
                else:
                    print(f"❌ {package} package missing")
            except:
                print(f"❌ {package} check failed")
        
        # Check network tools
        print("\n🔧 Available Network Tools:")
        tools = {
            'ping': 'Basic connectivity test',
            'nmap': 'Port scanning',
            'traceroute': 'Route tracing', 
            'tracert': 'Route tracing (Windows)',
            'arp-scan': 'Layer 2 discovery',
            'dig': 'DNS lookup'
        }
        
        for tool, description in tools.items():
            available = shutil.which(tool) is not None
            status = "✅" if available else "❌"
            print(f"  {status} {tool} - {description}")
        
        return True
    
    def run_application(self, port=5000):
        """Run the network monitor application"""
        print(f"\n🚀 Starting Network Monitor on port {port}...")
        
        if not os.path.exists('web_network_monitor.py'):
            print("❌ web_network_monitor.py not found!")
            return False
        
        try:
            # Run the application
            cmd = [self.python_cmd, 'web_network_monitor.py', '--port', str(port)]
            print(f"🔄 Running: {' '.join(cmd)}")
            
            # Start the application (don't capture output for interactive mode)
            subprocess.run(cmd, check=True)
            
        except KeyboardInterrupt:
            print("\n🛑 Application stopped by user")
            return True
        except subprocess.CalledProcessError as e:
            print(f"❌ Application failed: {e}")
            return False
        except Exception as e:
            print(f"❌ Unexpected error: {e}")
            return False
        
        return True

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='Network Monitor Setup and Runner')
    parser.add_argument('--setup-only', action='store_true', 
                       help='Only setup, do not run')
    parser.add_argument('--run', action='store_true',
                       help='Setup and run the application')
    parser.add_argument('--check', action='store_true',
                       help='Only check installation')
    parser.add_argument('--port', type=int, default=5000,
                       help='Port to run the web server on')
    
    args = parser.parse_args()
    
    # Create setup instance
    setup = NetworkMonitorSetup()
    
    print("🌐 Network Monitor Setup")
    print("=======================")
    print(f"🖥️  Operating System: {platform.system()} {platform.release()}")
    print(f"🐍 Python: {setup.python_cmd}")
    if setup.is_ubuntu:
        print("🐧 Ubuntu detected - Enhanced setup available")
    
    success = True
    
    # Check installation
    if args.check:
        return setup.check_installation()
    
    # Setup system requirements
    if args.setup_only or args.run:
        success = setup.setup_system_requirements()
        if not success:
            print("❌ Setup failed")
            return False
        
        # Check installation
        success = setup.check_installation()
        if not success:
            print("❌ Installation check failed")
            return False
    
    # Run application
    if args.run:
        print(f"\n🎯 All setup complete! Starting application on port {args.port}")
        success = setup.run_application(args.port)
    
    if success:
        print("\n✅ Network Monitor setup completed successfully!")
        if not args.run:
            print(f"🚀 To run the application: python3 {__file__} --run --port {args.port}")
    
    return success

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n🛑 Setup interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        sys.exit(1)
