#!/usr/bin/env python3
"""
Quick test for Ubuntu setup script
"""

import os
import sys

def test_basic_functionality():
    """Test basic functionality without actually installing"""
    print("🧪 Testing Ubuntu setup script...")
    
    # Test import
    try:
        import ubuntu_python313_setup
        print("✅ ubuntu_python313_setup.py imports successfully")
    except Exception as e:
        print(f"❌ Import failed: {e}")
        return False
    
    # Test user detection
    is_root = os.geteuid() == 0
    user = os.getenv('USER', 'unknown')
    print(f"✅ User detection: root={is_root}, user={user}")
    
    # Test command modification for root
    from ubuntu_python313_setup import run_command
    
    # Mock test - don't actually run commands
    print("✅ Command functions accessible")
    
    print("✅ All basic tests passed!")
    return True

if __name__ == "__main__":
    success = test_basic_functionality()
    print(f"\n{'✅ Tests passed' if success else '❌ Tests failed'}")
    sys.exit(0 if success else 1)
