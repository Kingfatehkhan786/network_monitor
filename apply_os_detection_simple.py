#!/usr/bin/env python3
"""
Simple OS Detection Integration
Adds OS detection and fixes to web_network_monitor.py
"""

def apply_os_detection():
    """Apply OS detection to the main file"""
    
    print("🔧 Applying OS detection to web_network_monitor.py...")
    
    try:
        # Read the file with proper encoding
        with open('web_network_monitor.py', 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        
        # Add OS detection after the imports
        os_detection_code = '''
# OS Detection and Enhanced Commands
CURRENT_OS = platform.system().lower()
IS_LINUX = CURRENT_OS == "linux"
IS_WINDOWS = CURRENT_OS == "windows"  
IS_MACOS = CURRENT_OS == "darwin"
IS_CONTAINER = os.path.exists('/.dockerenv')

print(f"🖥️ Running on: {platform.system()}")
if IS_CONTAINER:
    print("🐳 Container environment detected")

def get_os_ping_cmd(host, count=None):
    """Get OS-appropriate ping command"""
    if IS_WINDOWS:
        return ["ping", "-t", host] if count is None else ["ping", "-n", str(count), host]
    elif IS_LINUX:
        if count is None:
            return ["ping", "-i", "1", "-W", "3", host]  # Continuous  
        else:
            return ["ping", "-c", str(count), "-i", "0.5", "-W", "2", host]  # Finite
    else:  # macOS
        if count is None:
            return ["ping", "-i", "1", host]
        else:
            return ["ping", "-c", str(count), host]

def get_os_traceroute_cmd(host):
    """Get OS-appropriate traceroute command"""
    if IS_WINDOWS:
        return ["tracert", "-d", host]
    else:  # Linux/macOS
        return ["traceroute", "-n", "-w", "2", "-q", "2", "-m", "20", host]

'''
        
        # Find where to insert (after the speedtest import block)
        speedtest_block_end = content.find('SPEEDTEST_AVAILABLE = False')
        if speedtest_block_end != -1:
            # Find the next newline after this
            insert_pos = content.find('\n', speedtest_block_end) + 1
            
            # Insert the OS detection code
            content = content[:insert_pos] + os_detection_code + content[insert_pos:]
        
        # Fix the ping command in ping_monitor function
        content = content.replace(
            'ping_cmd = ["ping", host]',
            'ping_cmd = get_os_ping_cmd(host)'
        )
        
        # Fix the traceroute command 
        content = content.replace(
            'tracert_cmd = ["traceroute", "-n", host]',
            'tracert_cmd = get_os_traceroute_cmd(host)'
        )
        
        # Fix timestamp format for JavaScript compatibility
        content = content.replace(
            "'timestamp': datetime.now().strftime('%H:%M:%S')",
            "'timestamp': datetime.now().isoformat()"
        )
        
        # Write back with proper encoding
        with open('web_network_monitor.py', 'w', encoding='utf-8') as f:
            f.write(content)
        
        print("✅ OS detection applied successfully")
        return True
        
    except Exception as e:
        print(f"❌ Error applying OS detection: {e}")
        return False

if __name__ == "__main__":
    apply_os_detection()
    print("\n🚀 Now try: make run")
