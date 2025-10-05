#!/usr/bin/env python3
"""
Cross-platform startup script for Network Monitor Web Application
Works on Windows, macOS, and Linux
"""

import sys
import os
import platform
import subprocess
import time

def check_dependencies():
    """Check if all required dependencies are installed"""
    try:
        import flask
        import flask_socketio
        import speedtest
        print("✅ All dependencies are installed")
        return True
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        print("📦 Installing dependencies...")
        
        # Try to install requirements
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
            print("✅ Dependencies installed successfully")
            return True
        except subprocess.CalledProcessError:
            print("❌ Failed to install dependencies")
            return False

def check_system_tools():
    """Check if system tools are available"""
    system_name = platform.system().lower()
    tools_status = {}
    
    # Check ping
    try:
        result = subprocess.run(["ping", "-c", "1" if system_name != "windows" else "-n", "1", "127.0.0.1"], 
                              capture_output=True, timeout=5)
        tools_status['ping'] = result.returncode == 0
    except:
        tools_status['ping'] = False
    
    # Check traceroute/tracert
    tracert_cmd = "tracert" if system_name == "windows" else "traceroute"
    try:
        result = subprocess.run([tracert_cmd, "127.0.0.1"], 
                              capture_output=True, timeout=5)
        tools_status['traceroute'] = True
    except:
        tools_status['traceroute'] = False
    
    # Check ARP
    try:
        result = subprocess.run(["arp", "-a"], capture_output=True, timeout=5)
        tools_status['arp'] = result.returncode == 0
    except:
        tools_status['arp'] = False
    
    print(f"🖥️  System: {platform.system()} {platform.release()}")
    print(f"🐍 Python: {sys.version.split()[0]}")
    print(f"📡 Ping: {'✅' if tools_status['ping'] else '❌'}")
    print(f"🗺️  Traceroute: {'✅' if tools_status['traceroute'] else '❌'}")
    print(f"📱 ARP: {'✅' if tools_status['arp'] else '❌'}")
    
    return all(tools_status.values())

def create_directories():
    """Create necessary directories"""
    dirs = ['traces', 'logs', 'tmp']
    for dir_name in dirs:
        os.makedirs(dir_name, exist_ok=True)
    print("📁 Directories created")

def stop_existing_processes():
    """Stop any existing network monitor processes"""
    system_name = platform.system().lower()
    
    try:
        if system_name == "windows":
            # Windows approach
            subprocess.run(['tasklist', '/FI', 'IMAGENAME eq python.exe'], 
                         capture_output=True, check=False)
        else:
            # Unix approach (Linux/macOS)
            result = subprocess.run(['pgrep', '-f', 'web_network_monitor'], 
                                  capture_output=True, text=True)
            if result.stdout.strip():
                pids = result.stdout.strip().split('\n')
                for pid in pids:
                    try:
                        subprocess.run(['kill', pid], check=False)
                        print(f"🛑 Stopped existing process (PID: {pid})")
                    except:
                        pass
    except:
        pass  # Ignore errors when stopping processes

def main():
    print("🌐 Network Monitor Web Application")
    print("=" * 50)
    
    # Check dependencies
    if not check_dependencies():
        print("❌ Cannot proceed without dependencies")
        sys.exit(1)
    
    # Check system tools
    if not check_system_tools():
        print("⚠️  Some system tools are missing but proceeding anyway...")
    
    # Create directories
    create_directories()
    
    # Stop existing processes
    stop_existing_processes()
    
    print("\n🚀 Starting Network Monitor Web Application...")
    print("📍 Web interface will be available at: http://localhost:5000")
    print("🛑 Press Ctrl+C to stop")
    print("-" * 50)
    
    # Start the application
    try:
        os.chdir(os.path.dirname(os.path.abspath(__file__)))
        subprocess.run([sys.executable, "web_network_monitor.py"])
    except KeyboardInterrupt:
        print("\n🛑 Application stopped by user")
    except Exception as e:
        print(f"❌ Error starting application: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
