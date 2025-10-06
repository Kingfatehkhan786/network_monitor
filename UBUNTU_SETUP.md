# 🐧 Ubuntu Python 3.13 Network Monitor Setup

Complete installation guide for Ubuntu systems with Python 3.13 and all dependencies.

## 🚀 Quick Start (Recommended)

```bash
# Clone and enter directory
git clone https://github.com/Kingfatehkhan786/network_monitor.git
cd network_monitor

# Enhanced Ubuntu setup with Python 3.13
make setup-ubuntu

# Start the application
make run
```

## 📋 What Gets Installed

### 🐍 Python 3.13
- **Python 3.13** (latest version from deadsnakes PPA or built from source)
- **pip** for Python 3.13
- **Virtual environment** (`venv_network_monitor`)
- **Development tools** (build-essential, git, curl, wget)

### 📦 System Packages
```bash
# Network Tools
nmap                 # Advanced port scanning
traceroute          # Route tracing
iputils-ping        # Ping command
net-tools           # Network utilities (ifconfig, netstat)
dnsutils            # DNS utilities (nslookup, dig)
arp-scan            # Layer 2 network discovery
iperf3              # Network performance testing
tcpdump             # Packet capture
netcat-openbsd      # Network connectivity testing
mtr-tiny            # Network diagnostics
whois               # WHOIS lookup

# System Tools
curl                # HTTP requests
wget                # Downloads
bridge-utils        # Bridge utilities
vlan                # VLAN utilities
ethtool             # Ethernet tools
telnet              # Telnet client
openssh-client      # SSH client
rsync               # File synchronization
```

### 🐍 Python Packages
```python
# Core Web Framework
Flask==3.0.0
flask-socketio==5.3.6
python-socketio==5.10.0
gunicorn==21.2.0

# Network & System
psutil==5.9.8           # System information
requests==2.31.0        # HTTP requests
speedtest-cli==2.1.3    # Speed testing
python-nmap==0.7.1      # Nmap integration
netaddr==1.0.0          # Network addressing
netifaces>=0.11.0       # Network interfaces
dnspython>=2.4.0        # DNS toolkit
scapy>=2.5.0           # Packet manipulation

# Data & Visualization
matplotlib>=3.7.0       # Plotting
numpy>=1.24.0          # Numerical computing
pandas>=2.0.0          # Data analysis
plotly>=5.15.0         # Interactive plots

# Async & Performance
eventlet>=0.33.0       # Concurrent networking
gevent>=23.7.0         # Asynchronous framework
celery>=5.3.0          # Distributed tasks
redis>=4.6.0           # In-memory store

# Utilities
rich>=13.5.0           # Rich terminal output
click>=8.1.0           # CLI framework
schedule>=1.2.0        # Job scheduling
pyyaml>=6.0.1          # YAML parsing
```

## 🛠️ Installation Methods

### Method 1: Enhanced Ubuntu Setup (Recommended)
```bash
make setup-ubuntu
```

This will:
- ✅ Install Python 3.13 from deadsnakes PPA (or build from source)
- ✅ Install all system packages with apt
- ✅ Create optimized virtual environment
- ✅ Install all Python dependencies with correct versions
- ✅ Create systemd service file
- ✅ Create startup scripts

### Method 2: Manual Step-by-Step
```bash
# 1. Run the Ubuntu Python 3.13 setup directly
python3 ubuntu_python313_setup.py

# 2. Check installation
make check

# 3. Run the application
make run
```

### Method 3: Basic Setup (Fallback)
```bash
# Basic setup for any Linux system
make setup

# Run application
make run
```

## ⚙️ Systemd Service Setup

The enhanced setup creates a systemd service:

```bash
# Install service (done automatically by setup-ubuntu)
make service-install

# Start service
make service-start

# Check status  
make service-status

# View logs
make service-logs

# Stop service
sudo systemctl stop network-monitor
```

Service file location: `/etc/systemd/system/network-monitor.service`

## 🔧 Development Mode

```bash
# Create development environment
make dev-ubuntu

# Start in development mode
./dev_start.sh

# Or manually activate virtual environment
source venv_network_monitor/bin/activate
python web_network_monitor.py --port 5000
```

## 📊 Verification & Status

```bash
# Quick status check
make status

# Detailed installation check
make check

# Manual verification
python3.13 --version
source venv_network_monitor/bin/activate
python -c "import flask, psutil, requests; print('All packages OK')"
nmap --version
traceroute --version
```

## 🌐 Accessing the Application

After setup:
- **Main Dashboard**: http://localhost:5000
- **External Ping Monitor**: http://localhost:5000/external  
- **Internal Ping Monitor**: http://localhost:5000/internal
- **Network Discovery**: http://localhost:5000/network-discovery
- **Port Scanner**: http://localhost:5000/port-scanner

## 🔍 Features Available

### 📡 Live Network Monitoring
- **AJAX-based live updates** (no SocketIO dependency)
- **Real-time ping logs** with TTL values
- **Live packet counters** that increment
- **Latency measurements** in real-time
- **Auto-refresh every 2 seconds**

### 🛠️ Network Tools
- **Nmap port scanning** (all scan types)
- **Network discovery** with ARP scanning
- **Traceroute analysis**
- **Speed testing** with multiple providers
- **DNS lookups** and analysis

### 📊 Advanced Features  
- **Multi-provider monitoring** (Cloudflare, Google, Quad9)
- **Network statistics** and graphs
- **Historical data** storage
- **Export capabilities** (CSV, JSON)
- **REST API** for automation

## 🚨 Troubleshooting

### Python 3.13 Installation Issues
```bash
# If deadsnakes PPA fails, the script will build from source
# This takes 10-15 minutes but ensures Python 3.13 is available

# Manual build (if needed)
wget https://www.python.org/ftp/python/3.13.0/Python-3.13.0.tgz
tar -xzf Python-3.13.0.tgz
cd Python-3.13.0
./configure --enable-optimizations
make -j$(nproc)
sudo make altinstall
```

### Package Installation Issues
```bash
# Update package lists
sudo apt update

# Fix broken packages
sudo apt --fix-broken install

# Install specific package manually
sudo apt install nmap traceroute

# Check package availability
apt-cache search python3.13
```

### Virtual Environment Issues
```bash
# Recreate virtual environment
rm -rf venv_network_monitor
python3.13 -m venv venv_network_monitor
source venv_network_monitor/bin/activate
pip install --upgrade pip
pip install -r requirements_ubuntu.txt
```

### Permission Issues
```bash
# Add user to necessary groups
sudo usermod -a -G sudo $USER

# Fix network tool permissions
sudo chmod u+s /usr/bin/nmap
sudo chmod u+s /usr/bin/traceroute
```

## 📁 File Structure After Setup

```
network_monitor/
├── venv_network_monitor/          # Python 3.13 virtual environment
├── web_network_monitor.py         # Main application
├── ubuntu_python313_setup.py      # Enhanced Ubuntu setup
├── setup_and_run_fixed.py         # Cross-platform setup
├── network-monitor.service        # Systemd service file
├── start_ubuntu.sh                # Ubuntu startup script
├── dev_start.sh                   # Development startup script
├── requirements_ubuntu.txt        # Ubuntu-specific requirements
├── logs/                          # Application logs
├── templates/                     # Web templates
└── static/                        # Static web assets
```

## 🎯 Performance Optimizations

The Ubuntu setup includes:
- **Python 3.13** optimizations (--enable-optimizations)
- **Virtual environment** isolation
- **Systemd service** for production deployment
- **Gunicorn** WSGI server for better performance
- **Redis** for caching (optional)
- **Eventlet/Gevent** for async operations

## 🔐 Security Features

- **Non-root execution** (application runs as regular user)
- **Systemd security** restrictions
- **Network tool** permissions properly configured
- **Virtual environment** isolation
- **CORS** protection in web interface

---

## ✅ Quick Verification Commands

```bash
# Check Python 3.13
python3.13 --version

# Check virtual environment
ls -la venv_network_monitor/

# Check systemd service
systemctl status network-monitor

# Check network tools
which nmap traceroute arp-scan

# Check web application
curl http://localhost:5000/api/monitoring-status

# Check logs
tail -f logs/network_monitor.log
```

**🎉 Your Ubuntu system is now ready for advanced network monitoring with Python 3.13!**
