# Minimal Makefile for Network Monitor
# All the heavy lifting is done by Python

.PHONY: help setup run stop clean

# Default target - complete setup and run
all: run

help:
	@echo "Network Monitor (Minimal Makefile)"
	@echo "================================="
	@echo "All setup is handled intelligently by Python:"
	@echo ""
	@echo "  make setup    - Setup everything (OS detection, tools, environment)"
	@echo "  make run      - Setup and run the application"
	@echo "  make stop     - Stop the application" 
	@echo "  make clean    - Clean up files"
	@echo ""
	@echo "🐧 Linux: Installs nmap, arp-scan, advanced tools"
	@echo "🪟 Windows: Uses native Windows commands" 
	@echo "🍎 macOS: Uses BSD tools, suggests Homebrew"

# Setup everything using Python
setup:
	@python3 setup_and_run.py --setup-only

# Setup and run the application
run:
	@python3 setup_and_run.py --run

# Stop the application (basic process kill)
stop:
	@echo "🛑 Stopping Network Monitor..."
	@pkill -f "web_network_monitor.py" || echo "No running instances found"

# Clean up files
clean:
	@echo "🧹 Cleaning up..."
	@rm -rf venv __pycache__ *.log traces/*.log logs/* tmp/* 2>/dev/null || true
	@echo "✅ Cleanup complete"
