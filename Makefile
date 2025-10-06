# Network Monitor Makefile
# Enhanced Ubuntu Python 3.13 Support

.PHONY: help setup setup-ubuntu run stop clean check

# Default target - complete setup and run
all: run

help:
	@echo "Network Monitor Makefile"
	@echo "========================"
	@echo "Smart OS detection and setup:"
	@echo ""
	@echo "  make setup         - Basic setup (all OS)"
	@echo "  make setup-ubuntu  - Enhanced Ubuntu Python 3.13 setup"
	@echo "  make run           - Setup and run the application"
	@echo "  make check         - Check installation status"
	@echo "  make stop          - Stop the application" 
	@echo "  make clean         - Clean up files"
	@echo ""
	@echo "🐧 Ubuntu: Python 3.13 + all network tools + systemd service"
	@echo "🐧 Linux: Basic setup with system package manager"
	@echo "🪟 Windows: Native Windows commands + Python packages" 
	@echo "🍎 macOS: BSD tools + Homebrew suggestions"

# Enhanced Ubuntu setup with Python 3.13
setup-ubuntu:
	@echo "🐧 Ubuntu Python 3.13 Enhanced Setup"
	@echo "===================================="
	@python3 ubuntu_python313_setup.py

# Test Ubuntu setup script
test-ubuntu:
	@echo "🧪 Testing Ubuntu setup script..."
	@python3 test_ubuntu_setup.py

# Basic setup for all systems
setup:
	@python3 setup_and_run_fixed.py --setup-only

# Setup and run the application
run:
	@python3 setup_and_run_fixed.py --run

# Check installation status
check:
	@python3 setup_and_run_fixed.py --check

# Stop the application (try multiple methods)
stop:
	@echo "🛑 Stopping Network Monitor..."
	@pkill -f "web_network_monitor.py" || echo "No running Python instances found"
	@sudo systemctl stop network-monitor 2>/dev/null || echo "Systemd service not running"

# Clean up files and virtual environments
clean:
	@echo "🧹 Cleaning up..."
	@rm -rf venv venv_network_monitor __pycache__ *.pyc 2>/dev/null || true
	@rm -rf logs/*.log traces/*.log tmp/* 2>/dev/null || true
	@rm -f *.html get-pip.py 2>/dev/null || true
	@echo "✅ Cleanup completed"

# Ubuntu service management
service-install:
	@echo "⚙️ Installing systemd service..."
	@sudo cp network-monitor.service /etc/systemd/system/ 2>/dev/null || echo "Service file not found"
	@sudo systemctl daemon-reload
	@sudo systemctl enable network-monitor.service
	@echo "✅ Service installed and enabled"

service-start:
	@sudo systemctl start network-monitor.service

service-status:
	@sudo systemctl status network-monitor.service

service-logs:
	@sudo journalctl -u network-monitor.service -f

# Development shortcuts
dev-ubuntu:
	@echo "🚀 Ubuntu Development Setup"
	@make setup-ubuntu
	@echo "📝 Creating development environment..."
	@echo "#!/bin/bash" > dev_start.sh
	@echo "source venv_network_monitor/bin/activate" >> dev_start.sh
	@echo "python web_network_monitor.py --port 5000" >> dev_start.sh
	@chmod +x dev_start.sh
	@echo "✅ Use ./dev_start.sh to run in development mode"

# Quick status check
status:
	@echo "🔍 Network Monitor Status"
	@echo "========================"
	@python3 --version 2>/dev/null || echo "❌ Python not found"
	@python3.13 --version 2>/dev/null || echo "⚠️ Python 3.13 not installed"
	@which nmap >/dev/null && echo "✅ nmap available" || echo "❌ nmap not found"
	@which traceroute >/dev/null && echo "✅ traceroute available" || echo "❌ traceroute not found"
	@ps aux | grep -q "[w]eb_network_monitor.py" && echo "✅ Application running" || echo "❌ Application not running"
	@systemctl is-active network-monitor.service 2>/dev/null || echo "⚠️ Service not active"
	@echo "✅ Cleanup complete"
