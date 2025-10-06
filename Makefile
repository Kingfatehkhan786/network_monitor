# Makefile for Network Monitor (Ubuntu)

# --- Variables ---
VENV = venv
PYTHON = $(VENV)/bin/python3
PIP = $(VENV)/bin/pip
PORT = 80

.PHONY: help all install env requirements start stop clean

# --- Main Targets ---

all: start

help:
	@echo "Network Monitor Automation"
	@echo "=========================="
	@echo "Usage:"
	@echo "  make install      - Install system dependencies (Python, etc.)"
	@echo "  make env          - Create Python virtual environment"
	@echo "  make requirements - Install Python packages into venv"
	@echo "  make start        - Setup and start the app on port $(PORT) in the background"
	@echo "  make stop         - Stop the background application"
	@echo "  make clean        - Remove venv, logs, and temp files"
	@echo "  make logs         - View application logs"

# Install system dependencies
install:
	@echo "📦 Installing system dependencies (Python, pip, net-tools)..."
	sudo apt-get update
	sudo apt-get install -y python3 python3-pip python3-venv net-tools iputils-ping traceroute
	@echo "✅ System dependencies installed."

# Create virtual environment
env:
	@echo "🐍 Creating Python virtual environment in './$(VENV)'..."
	python3 -m venv $(VENV)
	@echo "✅ Virtual environment created."

# Install Python requirements into the venv
requirements: env
	@echo "📚 Installing Python requirements..."
	$(PIP) install --upgrade pip
	$(PIP) install -r requirements.txt
	@echo "✅ Requirements installed."

# Setup and start the application in the background
start: requirements
	@echo "🚀 Starting Network Monitor in the background on port $(PORT)..."
	@echo "   (Requires sudo for privileged port)"
	@# Use nohup to run in background and detach from terminal. Logs go to network_monitor.log
	sudo nohup $(PYTHON) web_network_monitor.py --port=$(PORT) > network_monitor.log 2>&1 &
	@echo "✅ Application started. PID: $!"
	@echo "   Logs are being written to 'network_monitor.log'"
	@echo "   Access at: http://localhost:$(PORT)"

# Stop the background application
stop:
	@echo "🛑 Stopping Network Monitor..."
	@# Find and kill the process running on the specified port
	PID=$$(sudo lsof -t -i:$(PORT) || echo ""); \
	if [ -n "$$PID" ]; then \
		sudo kill -9 $$PID; \
		echo "✅ Application stopped (PID: $$PID)."; \
	else \
		echo "ℹ️ Application not found running on port $(PORT)."; \
	fi

# View logs
logs:
	@echo "📋 Tailing application logs (Ctrl+C to exit)..."
	@tail -f network_monitor.log

# Clean up generated files
clean:
	@echo "🧹 Cleaning up virtual environment, logs, and temp files..."
	@read -p "This will delete the '$(VENV)' directory and all logs. Are you sure? (y/N): " confirm; \
	if [ "$$confirm" = "y" ] || [ "$$confirm" = "Y" ]; then \
		rm -rf $(VENV) __pycache__ *.log; \
		echo "✅ Cleanup complete."; \
	else \
		echo "❌ Cleanup cancelled."; \
	fi
