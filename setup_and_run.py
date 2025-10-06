#!/usr/bin/env python3
"""
Network Monitor - Intelligent Setup and Runner
Automatically detects OS and configures everything accordingly
"""

import os
import sys
import platform
import subprocess
import shutil
import json
import argparse
from pathlib import Path

class NetworkMonitorSetup:
    def __init__(self):
        self.os_type = platform.system().lower()
        self.is_linux = self.os_type == "linux"
        self.is_windows = self.os_type == "windows" 
        self.is_macos = self.os_type == "darwin"
        self.is_container = os.path.exists('/.dockerenv')
        
        print(f"🖥️  Operating System: {platform.system()}")
        print(f"🐳 Container Environment: {'Yes' if self.is_container else 'No'}")
        
        self.tools_available = {}
        self.python_cmd = self._get_python_command()
        
    def _get_python_command(self):
        """Get the appropriate Python command"""
        for cmd in ['python3', 'python']:
            try:
                result = subprocess.run([cmd, '--version'], capture_output=True, text=True)
                if result.returncode == 0:
                    return cmd
            except FileNotFoundError:
                continue
        return 'python3'  # Default fallback
    
    def _run_command(self, cmd, shell=False, check=True, capture_output=False):
        """Run a command with error handling"""
        try:
            if isinstance(cmd, str) and not shell:
                cmd = cmd.split()
            
            result = subprocess.run(
                cmd, 
                shell=shell, 
                check=check, 
                capture_output=capture_output,
                text=True
            )
            return result
        except subprocess.CalledProcessError as e:
            print(f"❌ Command failed: {' '.join(cmd) if isinstance(cmd, list) else cmd}")
            return None
        except FileNotFoundError:
            print(f"❌ Command not found: {cmd[0] if isinstance(cmd, list) else cmd}")
            return None
    
    def check_system_requirements(self):
        """Check and install system requirements based on OS"""
        print("\n📦 Checking System Requirements...")
        
        if self.is_linux:
            self._setup_linux()
        elif self.is_windows:
            self._setup_windows()
        elif self.is_macos:
            self._setup_macos()
        else:
            print("❓ Unknown OS - using basic setup")
    
    def _setup_linux(self):
        """Setup for Linux/Ubuntu"""
        print("🐧 Setting up for Linux/Ubuntu...")
        
        # Check if we have sudo access
        if os.geteuid() != 0 and shutil.which('sudo'):
            print("🔒 Installing system packages (requires sudo)...")
            
            packages = [
                # Basic requirements
                'python3', 'python3-pip', 'python3-venv', 'python3-dev',
                # Network tools  
                'net-tools', 'iputils-ping', 'traceroute', 'nmap', 'arp-scan',
                'dnsutils', 'whois', 'netcat-openbsd', 'tcpdump',
                # Editors
                'nano', 'vim', 'curl', 'wget'
            ]
            
            # Update package list
            self._run_command(['sudo', 'apt-get', 'update'], check=False)
            
            # Install packages
            cmd = ['sudo', 'apt-get', 'install', '-y'] + packages
            if self._run_command(cmd, check=False):
                print("✅ Linux packages installed")
            
            # Set network capabilities
            capabilities = [
                ['sudo', 'setcap', 'cap_net_raw+ep', '/bin/ping'],
                ['sudo', 'setcap', 'cap_net_raw+ep', '/usr/bin/traceroute'],
                ['sudo', 'setcap', 'cap_net_raw+ep', '/usr/bin/nmap']
            ]
            
            for cap_cmd in capabilities:
                self._run_command(cap_cmd, check=False)
        
        # Check available tools
        self._check_network_tools_linux()
    
    def _setup_windows(self):
        """Setup for Windows"""
        print("🪟 Setting up for Windows...")
        
        # Check Python
        if not shutil.which('python') and not shutil.which('python3'):
            print("❌ Python not found. Please install Python from python.org")
            return False
        
        # Check basic Windows tools
        tools = ['ping', 'tracert', 'nslookup', 'netstat']
        for tool in tools:
            self.tools_available[tool] = shutil.which(tool) is not None
        
        print("✅ Windows setup complete")
        return True
    
    def _setup_macos(self):
        """Setup for macOS"""
        print("🍎 Setting up for macOS...")
        
        # Check if Homebrew is available
        if shutil.which('brew'):
            print("🍺 Homebrew detected - can install advanced tools")
            
            # Suggest nmap installation
            if not shutil.which('nmap'):
                print("💡 To get advanced features, install: brew install nmap")
        
        # Check available tools
        tools = ['ping', 'traceroute', 'nslookup', 'netstat', 'dig']
        for tool in tools:
            self.tools_available[tool] = shutil.which(tool) is not None
        
        print("✅ macOS setup complete")
        return True
    
    def _check_network_tools_linux(self):
        """Check available network tools on Linux"""
        tools = {
            'nmap': 'Advanced port scanning',
            'arp-scan': 'Layer 2 network discovery', 
            'ss': 'Network statistics',
            'dig': 'DNS lookup',
            'tcpdump': 'Packet analysis',
            'netcat': 'Network connections',
            'whois': 'Domain information'
        }
        
        print("\n🔍 Checking Advanced Network Tools:")
        for tool, description in tools.items():
            available = shutil.which(tool) is not None
            self.tools_available[tool] = available
            status = "✅" if available else "❌"
            print(f"  {status} {tool} - {description}")
    
    def setup_python_environment(self):
        """Setup Python virtual environment and requirements"""
        print("\n🐍 Setting up Python Environment...")
        
        # Create virtual environment
        venv_path = Path('venv')
        if not venv_path.exists():
            print("📦 Creating virtual environment...")
            result = self._run_command([self.python_cmd, '-m', 'venv', 'venv'])
            if not result:
                print("❌ Failed to create virtual environment")
                return False
        
        # Get pip command
        if self.is_windows:
            pip_cmd = str(venv_path / 'Scripts' / 'pip.exe')
            python_cmd = str(venv_path / 'Scripts' / 'python.exe')
        else:
            pip_cmd = str(venv_path / 'bin' / 'pip')
            python_cmd = str(venv_path / 'bin' / 'python')
        
        # Install/upgrade pip
        print("📚 Installing/upgrading pip...")
        self._run_command([python_cmd, '-m', 'pip', 'install', '--upgrade', 'pip'])
        
        # Install requirements
        if Path('requirements.txt').exists():
            print("📦 Installing Python packages...")
            result = self._run_command([pip_cmd, 'install', '-r', 'requirements.txt'])
            if result:
                print("✅ Python packages installed")
            else:
                print("❌ Failed to install some packages")
        
        return True
    
    def integrate_advanced_tools(self):
        """Integrate advanced network tools based on OS"""
        print("\n🔧 Integrating Advanced Network Tools...")
        
        # Create enhanced version of main file
        if not Path('web_network_monitor.py').exists():
            print("❌ web_network_monitor.py not found")
            return False
        
        # Backup original
        if not Path('web_network_monitor.py.backup').exists():
            shutil.copy2('web_network_monitor.py', 'web_network_monitor.py.backup')
            print("💾 Backup created: web_network_monitor.py.backup")
        
        # Apply fixes based on OS
        self._apply_os_fixes()
        
        print("✅ Advanced tools integrated")
        return True
    
    def _apply_os_fixes(self):
        """Apply OS-specific fixes to the main application"""
        
        # Read the current file
        with open('web_network_monitor.py', 'r') as f:
            content = f.read()
        
        # Add OS detection imports at the top
        import_addition = '''
# OS Detection and Advanced Tools
import platform
CURRENT_OS = platform.system().lower()
IS_LINUX = CURRENT_OS == "linux"
IS_WINDOWS = CURRENT_OS == "windows"  
IS_MACOS = CURRENT_OS == "darwin"
IS_CONTAINER = os.path.exists('/.dockerenv')

print(f"🖥️ Running on: {platform.system()}")
if IS_CONTAINER:
    print("🐳 Container environment detected")

def get_os_appropriate_ping_cmd(host, count=None):
    """Get OS-appropriate ping command"""
    if IS_WINDOWS:
        return ["ping", "-t", host] if count is None else ["ping", "-n", str(count), host]
    elif IS_LINUX:
        if count is None:
            return ["ping", "-i", "1", "-W", "3", host]  # Continuous  
        else:
            return ["ping", "-c", str(count), "-i", "0.5", "-W", "2", host]  # Finite
    else:  # macOS
        if count is None:
            return ["ping", "-i", "1", host]
        else:
            return ["ping", "-c", str(count), host]

def get_os_appropriate_traceroute_cmd(host):
    """Get OS-appropriate traceroute command"""
    if IS_WINDOWS:
        return ["tracert", "-d", host]
    else:  # Linux/macOS
        return ["traceroute", "-n", "-w", "2", "-q", "2", "-m", "20", host]

'''
        
        # Insert after the first import block
        import_pos = content.find('\n', content.find('import '))
        if import_pos != -1:
            content = content[:import_pos] + import_addition + content[import_pos:]
        
        # Fix ping command generation
        content = content.replace(
            'ping_cmd = ["ping", host]',
            'ping_cmd = get_os_appropriate_ping_cmd(host)'
        )
        
        # Fix traceroute command generation  
        content = content.replace(
            'tracert_cmd = ["traceroute", "-n", host]',
            'tracert_cmd = get_os_appropriate_traceroute_cmd(host)'
        )
        
        # Fix timestamp format for JavaScript compatibility
        content = content.replace(
            "'timestamp': datetime.now().strftime('%H:%M:%S'),",
            "'timestamp': datetime.now().isoformat(),"
        )
        
        # Write the modified content back
        with open('web_network_monitor.py', 'w') as f:
            f.write(content)
    
    def create_directories(self):
        """Create necessary directories"""
        dirs = ['traces', 'logs', 'tmp', 'static', 'templates']
        for dir_name in dirs:
            Path(dir_name).mkdir(exist_ok=True)
        print(f"📁 Created directories: {', '.join(dirs)}")
    
    def run_application(self, port=80):
        """Run the network monitor application"""
        print(f"\n🚀 Starting Network Monitor on port {port}...")
        
        # Check if port requires privileges
        if port < 1024 and not self.is_windows:
            if os.geteuid() != 0:
                print(f"🔒 Port {port} requires root privileges. Restarting with sudo...")
                # Restart the script with sudo
                args = [sys.executable] + sys.argv + ['--no-setup']
                os.execvp('sudo', ['sudo', '-E'] + args)
                return
        
        # Determine Python command to use
        if Path('venv').exists():
            if self.is_windows:
                python_cmd = str(Path('venv') / 'Scripts' / 'python.exe')
            else:
                python_cmd = str(Path('venv') / 'bin' / 'python')
        else:
            python_cmd = self.python_cmd
        
        # Set environment variables
        env = os.environ.copy()
        env['PYTHONUNBUFFERED'] = '1'
        
        print(f"🌐 Starting server on http://localhost:{port}")
        print("🛑 Press Ctrl+C to stop")
        
        try:
            # Run the application
            subprocess.run([
                python_cmd, 'web_network_monitor.py', '--port', str(port)
            ], env=env)
        except KeyboardInterrupt:
            print("\n🛑 Application stopped by user")
        except Exception as e:
            print(f"❌ Application error: {e}")
    
    def show_summary(self):
        """Show setup summary"""
        print("\n" + "="*50)
        print("📊 NETWORK MONITOR SETUP COMPLETE")
        print("="*50)
        print(f"🖥️  OS: {platform.system()} {platform.release()}")
        print(f"🐍 Python: {platform.python_version()}")
        print(f"🐳 Container: {'Yes' if self.is_container else 'No'}")
        print()
        
        if self.is_linux:
            print("🐧 Linux Features:")
            advanced_tools = ['nmap', 'arp-scan', 'tcpdump', 'dig']
            for tool in advanced_tools:
                status = "✅" if self.tools_available.get(tool) else "❌"
                print(f"  {status} {tool}")
        elif self.is_windows:
            print("🪟 Windows Features:")
            print("  ✅ Windows network commands")
            print("  ✅ PowerShell integration ready")
        elif self.is_macos:
            print("🍎 macOS Features:")
            print("  ✅ Native BSD tools")
            print("  ✅ Homebrew integration")
        
        print()
        print("🌐 Access URLs (after starting):")
        print("  Main Dashboard: http://localhost")
        print("  Speed Test: http://localhost/speed-test")  
        print("  Network Discovery: http://localhost/devices")
        print()
        print("🚀 Start with: python setup_and_run.py --run")
        print("🛑 Stop with: Ctrl+C")

def main():
    parser = argparse.ArgumentParser(description='Network Monitor Setup and Runner')
    parser.add_argument('--setup-only', action='store_true', help='Only run setup, do not start app')
    parser.add_argument('--run', action='store_true', help='Run the application')
    parser.add_argument('--port', type=int, default=80, help='Port to run on (default: 80)')
    parser.add_argument('--no-setup', action='store_true', help='Skip setup, just run')
    
    args = parser.parse_args()
    
    setup = NetworkMonitorSetup()
    
    if not args.no_setup:
        setup.check_system_requirements()
        setup.setup_python_environment() 
        setup.integrate_advanced_tools()
        setup.create_directories()
        setup.show_summary()
    
    if args.run or (not args.setup_only and not args.no_setup):
        setup.run_application(args.port)

if __name__ == "__main__":
    main()
