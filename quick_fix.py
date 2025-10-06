#!/usr/bin/env python3
"""
Quick fix for the import error in web_network_monitor.py
"""

def fix_import_error():
    """Fix the missing 'os' import in web_network_monitor.py"""
    
    try:
        # Read the file
        with open('web_network_monitor.py', 'r') as f:
            content = f.read()
        
        # Check if the file has the error
        if 'IS_CONTAINER = os.path.exists' in content and 'import os' not in content:
            print("🔧 Fixing missing 'os' import...")
            
            # Find the first import statement
            lines = content.split('\n')
            for i, line in enumerate(lines):
                if line.strip().startswith('import ') or line.strip().startswith('from '):
                    # Insert 'import os' right after the first import
                    lines.insert(i + 1, 'import os')
                    break
            
            # Write back the fixed content
            with open('web_network_monitor.py', 'w') as f:
                f.write('\n'.join(lines))
            
            print("✅ Fixed missing 'os' import")
            return True
        else:
            print("ℹ️  No import fix needed")
            return True
            
    except Exception as e:
        print(f"❌ Error fixing file: {e}")
        return False

if __name__ == "__main__":
    print("🔧 Quick Fix for Import Error")
    print("============================")
    fix_import_error()
    print("\n🚀 Try running: make run")
