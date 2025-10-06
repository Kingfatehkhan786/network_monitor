# 🚀 Network Monitor - Simple Start Guide

## One Command Setup & Run

### For Linux/macOS:
```bash
make run
```
or
```bash
python3 setup_and_run.py --run
```

### For Windows:
```cmd
run.bat
```
or
```cmd
python setup_and_run.py --run
```

## What It Does Automatically

### 🖥️ **OS Detection**
- **Linux**: Installs `nmap`, `arp-scan`, `tcpdump`, advanced tools
- **Windows**: Uses `ping`, `tracert`, `netstat`, native commands  
- **macOS**: Uses BSD tools, suggests Homebrew packages

### 📦 **Automatic Setup**
1. Detects your operating system
2. Installs system dependencies (Linux only)
3. Creates Python virtual environment
4. Installs Python packages
5. Integrates OS-appropriate network tools
6. Fixes all timestamp and command issues
7. Starts the application

### 🌐 **Access Your Monitor**
Once started, visit:
- **Main Dashboard**: http://localhost
- **Speed Test**: http://localhost/speed-test
- **Network Discovery**: http://localhost/devices

## Manual Options

```bash
# Setup only (don't start)
python3 setup_and_run.py --setup-only

# Run on different port
python3 setup_and_run.py --run --port 8080

# Just run (skip setup)
python3 setup_and_run.py --run --no-setup
```

## Makefile Commands (Linux/macOS)

```bash
make setup    # Setup everything  
make run      # Setup and run
make stop     # Stop application
make clean    # Clean up files
```

## Features by Operating System

### 🐧 **Linux (Ubuntu/Debian)**
- ✅ Advanced port scanning with `nmap`
- ✅ Layer 2 discovery with `arp-scan`  
- ✅ Network statistics with `ss`
- ✅ DNS analysis with `dig`
- ✅ Packet capture with `tcpdump`
- ✅ Container optimizations

### 🪟 **Windows**
- ✅ Native Windows network commands
- ✅ PowerShell integration ready
- ✅ Windows firewall friendly
- ✅ No additional installations needed

### 🍎 **macOS**
- ✅ Native BSD network tools
- ✅ Homebrew integration
- ✅ macOS-optimized parameters
- ✅ Terminal.app friendly

## That's It! 

**No complex configuration, no multiple scripts, no OS-specific commands to remember.**

Just run and monitor your network! 🌐✨
