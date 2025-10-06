#!/bin/bash
# Quick test for Ubuntu setup

echo "🧪 Quick Ubuntu Setup Test"
echo "=========================="

# Check if we're on Ubuntu
if ! grep -q "Ubuntu" /etc/os-release 2>/dev/null; then
    echo "⚠️ Not running on Ubuntu, but test can still proceed"
fi

# Check Python availability
echo "🐍 Checking Python..."
python3 --version || echo "❌ python3 not found"
python3.13 --version 2>/dev/null && echo "✅ python3.13 available" || echo "⚠️ python3.13 not available"

# Check if script exists and can be imported
echo "📝 Testing ubuntu_python313_setup.py..."
if [ -f "ubuntu_python313_setup.py" ]; then
    echo "✅ ubuntu_python313_setup.py exists"
    python3 -c "import ubuntu_python313_setup; print('✅ Script imports successfully')" || echo "❌ Import failed"
else
    echo "❌ ubuntu_python313_setup.py not found"
fi

# Test basic functionality
echo "🔧 Running basic test..."
python3 test_ubuntu_setup.py

echo ""
echo "🚀 To run the full setup:"
echo "   make setup-ubuntu"
echo ""
echo "🧪 To test setup script:"
echo "   make test-ubuntu"
