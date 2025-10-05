# Network Monitor Web Application Makefile
# For Ubuntu LXC Container Setup

.PHONY: help install setup-python install-deps setup-dirs run-web run-console clean status logs

# Default target
help:
	@echo "Network Monitor Web Application Setup"
	@echo "====================================="
	@echo ""
	@echo "Available targets:"
	@echo "  install         - Complete installation (recommended)"
	@echo "  setup-python    - Install Python 3 and pip"
	@echo "  install-deps    - Install Python dependencies"
	@echo "  setup-dirs      - Create necessary directories"
	@echo "  run-web         - Run web application on port 5000"
	@echo "  run-console     - Run console version (original)"
	@echo "  status          - Show application status"
	@echo "  logs            - Show recent logs"
	@echo "  clean           - Clean up logs and temporary files"
	@echo "  stop            - Stop running applications"
	@echo ""
	@echo "Quick start: make install && make run-web"

# Complete installation
install: setup-python install-deps setup-dirs
	@echo "✅ Installation complete!"
	@echo "🚀 Run 'make run-web' to start the web application"
	@echo "🌐 Then visit http://localhost:5000 in your browser"

# Install Python 3 and essential packages
setup-python:
	@echo "📦 Installing Python 3 and essential packages..."
	sudo apt update
	sudo apt install -y python3 python3-pip python3-venv
	sudo apt install -y net-tools iputils-ping traceroute
	sudo apt install -y build-essential python3-dev
	@echo "✅ Python 3 installation complete"

# Install Python dependencies
install-deps:
	@echo "📚 Installing Python dependencies..."
	python3 -m pip install --user --upgrade pip
	python3 -m pip install --user -r requirements.txt
	@echo "✅ Dependencies installed"

# Create necessary directories
setup-dirs:
	@echo "📁 Creating directories..."
	mkdir -p traces
	mkdir -p logs
	mkdir -p tmp
	@echo "✅ Directories created"

# Run web application
run-web:
	@echo "🌐 Starting Network Monitor Web Application..."
	@echo "📍 Access at: http://localhost:5000"
	@echo "🛑 Press Ctrl+C to stop"
	@echo ""
	python3 web_network_monitor.py

# Run web application with gunicorn (production)
run-web-prod:
	@echo "🌐 Starting Network Monitor Web Application (Production)..."
	@echo "📍 Access at: http://localhost:5000"
	@echo "🛑 Use 'make stop' to stop"
	@echo ""
	gunicorn --worker-class eventlet -w 1 --bind 0.0.0.0:5000 web_network_monitor:app --daemon --pid tmp/app.pid
	@echo "✅ Application started in background"

# Run console version
run-console:
	@echo "🖥️  Starting Network Monitor Console Application..."
	@echo "📋 Press 'q' to quit, 'g' for garbage collection"
	@echo ""
	python3 network_monitor.py

# Check application status
status:
	@echo "📊 Network Monitor Status"
	@echo "========================"
	@echo ""
	@if [ -f tmp/app.pid ]; then \
		PID=$$(cat tmp/app.pid); \
		if ps -p $$PID > /dev/null 2>&1; then \
			echo "🟢 Web Application: Running (PID: $$PID)"; \
		else \
			echo "🔴 Web Application: Stopped (stale PID file)"; \
			rm -f tmp/app.pid; \
		fi; \
	else \
		echo "🔴 Web Application: Not running"; \
	fi
	@echo ""
	@echo "📁 Log Files:"
	@ls -la traces/ 2>/dev/null || echo "   No log files found"
	@echo ""
	@echo "💾 Disk Usage:"
	@du -sh traces/ 2>/dev/null || echo "   No traces directory"

# Show recent logs
logs:
	@echo "📋 Recent Network Monitor Logs"
	@echo "==============================="
	@echo ""
	@echo "🌍 External Ping (last 10 lines):"
	@tail -n 10 traces/external_ping_$$(date +%Y-%m-%d).log 2>/dev/null || echo "   No external ping logs today"
	@echo ""
	@echo "🏠 Internal Ping (last 10 lines):"
	@tail -n 10 traces/internal_ping_$$(date +%Y-%m-%d).log 2>/dev/null || echo "   No internal ping logs today"
	@echo ""
	@echo "⚠️  Timeouts (last 10 lines):"
	@tail -n 10 traces/timeout_errors_$$(date +%Y-%m-%d).log 2>/dev/null || echo "   No timeout errors today (good!)"

# Stop applications
stop:
	@echo "🛑 Stopping Network Monitor applications..."
	@if [ -f tmp/app.pid ]; then \
		PID=$$(cat tmp/app.pid); \
		if ps -p $$PID > /dev/null 2>&1; then \
			kill $$PID && echo "✅ Web application stopped"; \
		else \
			echo "ℹ️  Web application was not running"; \
		fi; \
		rm -f tmp/app.pid; \
	else \
		echo "ℹ️  No PID file found"; \
	fi
	@pkill -f "python3.*network_monitor.py" && echo "✅ Console application stopped" || echo "ℹ️  Console application was not running"

# Clean up logs and temporary files
clean:
	@echo "🧹 Cleaning up..."
	@read -p "This will delete all log files. Are you sure? (y/N): " confirm; \
	if [ "$$confirm" = "y" ] || [ "$$confirm" = "Y" ]; then \
		rm -rf traces/*.log; \
		rm -rf logs/*; \
		rm -rf tmp/*; \
		echo "✅ Cleanup complete"; \
	else \
		echo "❌ Cleanup cancelled"; \
	fi

# Archive old logs
archive-logs:
	@echo "📦 Archiving old logs..."
	@ARCHIVE_NAME="network_logs_$$(date +%Y%m%d_%H%M%S).tar.gz"; \
	tar -czf "$$ARCHIVE_NAME" traces/; \
	echo "✅ Logs archived to $$ARCHIVE_NAME"

# Test network connectivity
test-network:
	@echo "🔍 Testing Network Connectivity"
	@echo "==============================="
	@echo ""
	@echo "🏠 Router (10.99.0.1):"
	@ping -c 3 10.99.0.1 || echo "❌ Router unreachable"
	@echo ""
	@echo "🌍 Internet (1.1.1.1):"
	@ping -c 3 1.1.1.1 || echo "❌ Internet unreachable"
	@echo ""
	@echo "📡 DNS Resolution:"
	@nslookup google.com || echo "❌ DNS issues"

# Show system information
sysinfo:
	@echo "💻 System Information"
	@echo "===================="
	@echo ""
	@echo "🐧 OS: $$(lsb_release -d 2>/dev/null | cut -f2 || echo 'Unknown Linux')"
	@echo "🐍 Python: $$(python3 --version)"
	@echo "💾 Memory: $$(free -h | grep '^Mem:' | awk '{print $$3 "/" $$2}')"
	@echo "💿 Disk: $$(df -h . | tail -1 | awk '{print $$3 "/" $$2 " (" $$5 " used)"}')"
	@echo "🌐 Network Interfaces:"
	@ip -brief addr show | grep -v lo

# Run in development mode with auto-reload
dev:
	@echo "🔧 Starting Development Mode..."
	@echo "📍 Access at: http://localhost:5000"
	@echo "🔄 Auto-reload enabled"
	@echo ""
	FLASK_ENV=development python3 web_network_monitor.py

# Install as systemd service
install-service:
	@echo "⚙️  Installing as systemd service..."
	@echo "📝 Creating service file..."
	@sudo tee /etc/systemd/system/network-monitor.service > /dev/null <<EOF
[Unit]
Description=Network Monitor Web Application
After=network.target

[Service]
Type=simple
User=$$(whoami)
WorkingDirectory=$$(pwd)
ExecStart=/usr/bin/python3 $$(pwd)/web_network_monitor.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF
	@sudo systemctl daemon-reload
	@sudo systemctl enable network-monitor
	@echo "✅ Service installed. Use 'sudo systemctl start network-monitor' to start"

# Show version and info
version:
	@echo "Network Monitor Web Application"
	@echo "Version: 1.0.0"
	@echo "Author: Network Monitoring System"
	@echo "License: MIT"
	@echo ""
	@echo "Components:"
	@echo "  - Flask Web Server"
	@echo "  - Real-time Socket.IO"
	@echo "  - Network Monitoring"
	@echo "  - Log Rotation"
	@echo "  - Garbage Collection"
