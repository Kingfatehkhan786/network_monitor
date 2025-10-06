#!/usr/bin/env python3
"""
Ubuntu Python 3.13 Setup for Network Monitor
Complete installation of Python 3.13 and all dependencies
"""

import subprocess
import os
import sys
import platform

def run_command(cmd, description="", check=True, shell=True):
    """Run a shell command with error handling"""
    print(f"🔄 {description}")
    print(f"   Command: {cmd}")
    
    try:
        if shell:
            result = subprocess.run(cmd, shell=True, check=check, 
                                  capture_output=True, text=True)
        else:
            result = subprocess.run(cmd, check=check, 
                                  capture_output=True, text=True)
        
        if result.stdout:
            print(f"   Output: {result.stdout.strip()}")
        
        return result.returncode == 0
    except subprocess.CalledProcessError as e:
        print(f"   ❌ Error: {e}")
        if e.stdout:
            print(f"   stdout: {e.stdout}")
        if e.stderr:
            print(f"   stderr: {e.stderr}")
        return False

def detect_ubuntu_version():
    """Detect Ubuntu version"""
    try:
        with open('/etc/os-release', 'r') as f:
            content = f.read()
            if 'Ubuntu' in content:
                for line in content.split('\n'):
                    if line.startswith('VERSION_ID='):
                        version = line.split('=')[1].strip('"')
                        return version
    except:
        pass
    return None

def setup_python313_ubuntu():
    """Install Python 3.13 on Ubuntu"""
    print("🐍 Setting up Python 3.13 for Ubuntu")
    print("=====================================")
    
    # Check if we're on Ubuntu
    if not os.path.exists('/etc/ubuntu-release') and not os.path.exists('/etc/os-release'):
        print("❌ This script is designed for Ubuntu systems")
        return False
    
    ubuntu_version = detect_ubuntu_version()
    print(f"🔍 Detected Ubuntu version: {ubuntu_version}")
    
    # Update package lists
    if not run_command("sudo apt update", "Updating package lists"):
        print("❌ Failed to update package lists")
        return False
    
    # Install dependencies for building Python
    dependencies = [
        "software-properties-common",
        "build-essential", 
        "zlib1g-dev",
        "libncurses5-dev",
        "libgdbm-dev",
        "libnss3-dev",
        "libssl-dev",
        "libreadline-dev",
        "libffi-dev",
        "libsqlite3-dev",
        "wget",
        "libbz2-dev",
        "liblzma-dev",
        "tk-dev",
        "curl",
        "git"
    ]
    
    deps_cmd = f"sudo apt install -y {' '.join(dependencies)}"
    if not run_command(deps_cmd, "Installing build dependencies"):
        print("❌ Failed to install build dependencies")
        return False
    
    # Add deadsnakes PPA for Python 3.13
    print("🐍 Adding deadsnakes PPA for Python 3.13...")
    if not run_command("sudo add-apt-repository ppa:deadsnakes/ppa -y", 
                      "Adding deadsnakes PPA"):
        print("⚠️ PPA addition failed, trying manual Python 3.13 build...")
        return build_python313_from_source()
    
    # Update after adding PPA
    if not run_command("sudo apt update", "Updating after PPA addition"):
        return False
    
    # Install Python 3.13
    python_packages = [
        "python3.13",
        "python3.13-dev", 
        "python3.13-venv",
        "python3.13-distutils"
    ]
    
    py_cmd = f"sudo apt install -y {' '.join(python_packages)}"
    if not run_command(py_cmd, "Installing Python 3.13"):
        print("⚠️ Package installation failed, trying build from source...")
        return build_python313_from_source()
    
    # Install pip for Python 3.13
    if not run_command("curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py", 
                      "Downloading pip installer"):
        return False
    
    if not run_command("python3.13 get-pip.py", "Installing pip for Python 3.13"):
        print("⚠️ pip installation failed")
    
    # Clean up pip installer
    run_command("rm -f get-pip.py", "Cleaning up pip installer", check=False)
    
    # Verify installation
    if run_command("python3.13 --version", "Verifying Python 3.13 installation"):
        print("✅ Python 3.13 installed successfully!")
        return True
    else:
        return build_python313_from_source()

def build_python313_from_source():
    """Build Python 3.13 from source as fallback"""
    print("🔨 Building Python 3.13 from source...")
    
    # Download Python 3.13 source
    python_version = "3.13.0"
    download_url = f"https://www.python.org/ftp/python/{python_version}/Python-{python_version}.tgz"
    
    if not run_command(f"wget {download_url}", "Downloading Python 3.13 source"):
        return False
    
    if not run_command(f"tar -xzf Python-{python_version}.tgz", 
                      "Extracting Python source"):
        return False
    
    # Build and install
    build_commands = [
        f"cd Python-{python_version}",
        "./configure --enable-optimizations --with-ensurepip=install",
        "make -j$(nproc)",
        "sudo make altinstall"  # altinstall to avoid overwriting system python
    ]
    
    full_cmd = " && ".join(build_commands)
    if not run_command(full_cmd, "Building Python 3.13 (this may take 10-15 minutes)"):
        print("❌ Failed to build Python 3.13 from source")
        return False
    
    # Clean up
    run_command(f"rm -rf Python-{python_version} Python-{python_version}.tgz", 
               "Cleaning up build files", check=False)
    
    # Verify
    if run_command("python3.13 --version", "Verifying Python 3.13 build"):
        print("✅ Python 3.13 built and installed successfully!")
        return True
    
    return False

def install_system_packages():
    """Install required system packages for network monitoring"""
    print("📦 Installing system packages for network monitoring...")
    
    packages = [
        "nmap",           # Network scanning
        "traceroute",     # Traceroute functionality  
        "iputils-ping",   # Ping command
        "net-tools",      # Network utilities (ifconfig, etc.)
        "dnsutils",       # DNS utilities (nslookup, dig)
        "curl",           # HTTP requests
        "wget",           # Downloads
        "arp-scan",       # ARP scanning
        "iperf3",         # Network performance testing
        "tcpdump",        # Packet capture
        "netcat-openbsd", # Network connectivity testing
        "iproute2",       # Modern network utilities
        "bridge-utils",   # Bridge utilities
        "vlan",           # VLAN utilities
        "ethtool",        # Ethernet tools
        "mtr-tiny",       # Network diagnostics
        "whois",          # WHOIS lookup
        "telnet",         # Telnet client
        "openssh-client", # SSH client
        "rsync"           # File synchronization
    ]
    
    cmd = f"sudo apt install -y {' '.join(packages)}"
    return run_command(cmd, "Installing network monitoring tools")

def setup_python_virtual_environment():
    """Set up Python virtual environment"""
    print("🐍 Setting up Python virtual environment...")
    
    # Create virtual environment
    if not run_command("python3.13 -m venv venv_network_monitor", 
                      "Creating virtual environment"):
        return False
    
    # Activate and upgrade pip
    activate_cmd = "source venv_network_monitor/bin/activate && pip install --upgrade pip"
    if not run_command(activate_cmd, "Upgrading pip in virtual environment"):
        return False
    
    return True

def install_python_dependencies():
    """Install all Python dependencies"""
    print("📚 Installing Python dependencies...")
    
    # Enhanced requirements for Ubuntu
    requirements = [
        "Flask==3.0.0",
        "flask-socketio==5.3.6", 
        "python-socketio==5.10.0",
        "speedtest-cli==2.1.3",
        "psutil==5.9.8",
        "requests==2.31.0",
        "beautifulsoup4==4.14.2",
        "python-nmap==0.7.1",
        "netaddr==1.0.0",
        "ipaddress>=1.0.0",
        "iperf3==0.1.11",
        "scapy>=2.5.0",        # Advanced packet manipulation
        "netifaces>=0.11.0",    # Network interface enumeration
        "dnspython>=2.4.0",     # DNS toolkit
        "paramiko>=3.3.0",      # SSH2 protocol library
        "cryptography>=41.0.0", # Cryptographic recipes
        "matplotlib>=3.7.0",    # Plotting for network graphs
        "numpy>=1.24.0",        # Numerical computing
        "pandas>=2.0.0",        # Data analysis
        "plotly>=5.15.0",       # Interactive plots
        "dash>=2.14.0",         # Web dashboards
        "gunicorn>=21.2.0",     # WSGI HTTP Server
        "eventlet>=0.33.0",     # Concurrent networking
        "gevent>=23.7.0",       # Asynchronous framework
        "redis>=4.6.0",         # In-memory data store
        "celery>=5.3.0",        # Distributed task queue
        "schedule>=1.2.0",      # Job scheduling
        "click>=8.1.0",         # Command line interface
        "rich>=13.5.0",         # Rich text and beautiful formatting
        "tabulate>=0.9.0",      # Pretty-print tabular data
        "colorama>=0.4.6",      # Cross-platform colored terminal text
        "tqdm>=4.66.0",         # Progress bars
        "pyyaml>=6.0.1",        # YAML parser
        "toml>=0.10.2",         # TOML parser
        "python-dateutil>=2.8.2", # Date/time utilities
        "pytz>=2023.3",         # Timezone calculations
        "jinja2>=3.1.2",        # Template engine
        "markupsafe>=2.1.3",    # Safe string handling
        "werkzeug>=3.0.0",      # WSGI utility library
        "itsdangerous>=2.1.2",  # Data integrity
    ]
    
    # Install in virtual environment
    for req in requirements:
        activate_and_install = f"source venv_network_monitor/bin/activate && pip install '{req}'"
        if not run_command(activate_and_install, f"Installing {req.split('==')[0]}"):
            print(f"⚠️ Failed to install {req}, continuing...")
    
    # Create requirements.txt with all dependencies
    with open('requirements_ubuntu.txt', 'w') as f:
        f.write("# Ubuntu Network Monitor Requirements - Python 3.13\n")
        f.write("# Generated automatically\n\n")
        for req in requirements:
            f.write(f"{req}\n")
    
    print("✅ Created requirements_ubuntu.txt")
    
    return True

def setup_systemd_service():
    """Create systemd service for network monitor"""
    print("⚙️ Setting up systemd service...")
    
    current_dir = os.getcwd()
    service_content = f"""[Unit]
Description=Network Monitor Web Application  
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory={current_dir}
Environment=PATH={current_dir}/venv_network_monitor/bin
ExecStart={current_dir}/venv_network_monitor/bin/python web_network_monitor.py --port 5000
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
"""
    
    # Write service file
    with open('network-monitor.service', 'w') as f:
        f.write(service_content)
    
    # Install service (requires manual sudo)
    print("📝 Created network-monitor.service file")
    print("To install the service, run:")
    print("  sudo cp network-monitor.service /etc/systemd/system/")
    print("  sudo systemctl daemon-reload")
    print("  sudo systemctl enable network-monitor.service")
    print("  sudo systemctl start network-monitor.service")
    
    return True

def create_ubuntu_startup_script():
    """Create startup script for Ubuntu"""
    startup_script = """#!/bin/bash
# Ubuntu Network Monitor Startup Script

echo "🐧 Ubuntu Network Monitor Startup"
echo "================================="

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
cd "$SCRIPT_DIR"

# Activate virtual environment
if [ -d "venv_network_monitor" ]; then
    echo "🐍 Activating Python virtual environment..."
    source venv_network_monitor/bin/activate
else
    echo "❌ Virtual environment not found! Run ubuntu_python313_setup.py first"
    exit 1
fi

# Set environment variables
export PYTHONPATH="$SCRIPT_DIR:$PYTHONPATH"
export FLASK_ENV=production

# Check Python version
python --version

# Start network monitor
echo "🚀 Starting Network Monitor..."
python web_network_monitor.py --port 5000
"""
    
    with open('start_ubuntu.sh', 'w') as f:
        f.write(startup_script)
    
    # Make executable
    run_command("chmod +x start_ubuntu.sh", "Making startup script executable")
    
    print("✅ Created start_ubuntu.sh startup script")
    return True

def main():
    """Main setup function"""
    print("🐧 Ubuntu Python 3.13 Network Monitor Setup")
    print("============================================")
    
    # Check if running on Ubuntu
    if platform.system() != 'Linux':
        print("❌ This setup is designed for Ubuntu Linux")
        return False
    
    # Check if running as non-root user
    if os.geteuid() == 0:
        print("⚠️  Please run this script as a regular user (not root)")
        print("   sudo commands will be used when needed")
        return False
    
    steps = [
        ("Installing Python 3.13", setup_python313_ubuntu),
        ("Installing system packages", install_system_packages), 
        ("Setting up virtual environment", setup_python_virtual_environment),
        ("Installing Python dependencies", install_python_dependencies),
        ("Creating systemd service", setup_systemd_service),
        ("Creating startup script", create_ubuntu_startup_script)
    ]
    
    for step_name, step_func in steps:
        print(f"\n🔄 {step_name}...")
        if not step_func():
            print(f"❌ Failed: {step_name}")
            return False
        print(f"✅ Completed: {step_name}")
    
    print("\n🎉 UBUNTU SETUP COMPLETED!")
    print("=========================")
    print("✅ Python 3.13 installed")
    print("✅ All system packages installed") 
    print("✅ Virtual environment created")
    print("✅ Python dependencies installed")
    print("✅ Systemd service created")
    print("✅ Startup script created")
    print()
    print("🚀 To start the Network Monitor:")
    print("   ./start_ubuntu.sh")
    print()
    print("🔧 Or use systemd service:")
    print("   sudo systemctl start network-monitor")
    print()
    print("🌐 Access at: http://localhost:5000")
    
    return True

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--help":
        print("Ubuntu Python 3.13 Network Monitor Setup")
        print("========================================")
        print("This script will:")
        print("• Install Python 3.13 from deadsnakes PPA or build from source")
        print("• Install all required system packages (nmap, traceroute, etc.)")
        print("• Create Python virtual environment")
        print("• Install all Python dependencies")
        print("• Create systemd service for auto-start")  
        print("• Create startup script")
        print()
        print("Usage: python3 ubuntu_python313_setup.py")
        sys.exit(0)
    
    success = main()
    sys.exit(0 if success else 1)
