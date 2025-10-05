#!/bin/bash
# Production deployment script for Network Monitor

set -e

echo "🚀 Starting Network Monitor Production Deployment..."

# Create directories
echo "📁 Creating directories..."
mkdir -p logs traces static/css static/js

# Install dependencies
echo "📦 Installing dependencies..."
pip install -r requirements.txt

# Setup environment
echo "⚙️ Setting up environment..."
if [ ! -f .env ]; then
    echo "⚠️  Creating .env from template..."
    cp .env.example .env
    echo "🔧 Please edit .env file with your settings before running!"
    exit 1
fi

# Create systemd service
echo "🔧 Installing systemd service..."
sudo cp network-monitor.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable network-monitor
echo "✅ Systemd service installed"

# Start the service
echo "🚀 Starting Network Monitor service..."
sudo systemctl start network-monitor
sudo systemctl status network-monitor --no-pager

echo "✅ Network Monitor deployed successfully!"
echo ""
echo "📊 Service Status:"
echo "   Status: sudo systemctl status network-monitor"
echo "   Logs: sudo journalctl -u network-monitor -f"
echo "   Stop: sudo systemctl stop network-monitor" 
echo "   Restart: sudo systemctl restart network-monitor"
echo ""
echo "🌐 Access your monitor at: http://localhost:5000"
