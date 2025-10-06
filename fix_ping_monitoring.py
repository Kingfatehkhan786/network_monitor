#!/usr/bin/env python3
"""
Fix Ping Monitoring Issues
Replaces the broken ping_monitor function with a working one
"""

def fix_ping_monitoring():
    """Fix the ping monitoring function in web_network_monitor.py"""
    
    print("🔧 Fixing ping monitoring...")
    
    try:
        # Read the file
        with open('web_network_monitor.py', 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        
        # Find the ping_monitor function
        start_marker = "def ping_monitor(host, label, log_file, data_queue):"
        end_marker = "def traceroute_monitor"
        
        start_pos = content.find(start_marker)
        end_pos = content.find(end_marker)
        
        if start_pos == -1 or end_pos == -1:
            print("❌ Could not find ping_monitor function")
            return False
        
        # New working ping_monitor function
        new_ping_function = '''def ping_monitor(host, label, log_file, data_queue):
    """Fixed ping monitor with proper OS detection"""
    print(f"🔍 Starting ping monitor for {label} ({host})")
    
    # Use OS-appropriate ping command
    ping_cmd = get_os_ping_cmd(host)
    print(f"📡 Ping command: {' '.join(ping_cmd)}")
    
    while True:
        try:
            process = subprocess.Popen(
                ping_cmd, 
                stdout=subprocess.PIPE, 
                stderr=subprocess.STDOUT, 
                text=True, 
                universal_newlines=True, 
                bufsize=1
            )

            for line in iter(process.stdout.readline, ''):
                line = line.strip()
                if not line:
                    continue
                
                # OS-specific filtering
                skip_patterns = []
                if IS_WINDOWS:
                    skip_patterns = ["Pinging", "Ping statistics", "Packets:"]
                elif IS_LINUX:
                    skip_patterns = ["PING ", "ping statistics", "packets transmitted", "---"]
                else:  # macOS
                    skip_patterns = ["PING ", "---"]
                
                # Skip unwanted lines
                if any(pattern in line for pattern in skip_patterns):
                    continue
                
                # Log the ping result
                current_time = datetime.now()
                log_line = f"[{current_time.strftime('%H:%M:%S')}] {line}\\n"
                append_to_log(log_file, log_line)
                
                # Create log entry with proper timestamp
                log_entry = {
                    'timestamp': current_time.isoformat(),  # ISO format for JavaScript
                    'display_time': current_time.strftime('%H:%M:%S'),
                    'data': line,
                    'type': 'ping',
                    'host': host,
                    'label': label
                }
                add_to_queue(data_queue, log_entry)
                
                # Emit SocketIO event with correct naming
                event_name = f'ping_update_{label.lower()}'
                
                if "external" in label.lower():
                    # Map IPs to provider names for external monitoring
                    provider_map = {
                        '1.1.1.1': 'cloudflare',
                        '8.8.8.8': 'google', 
                        '9.9.9.9': 'quad9'
                    }
                    provider = provider_map.get(host, 'unknown')
                    event_name = f'ping_update_external_{provider}'
                elif "internal" in label.lower():
                    event_name = 'ping_update_internal'
                
                print(f"📡 Emitting: {event_name}")
                socketio.emit(event_name, log_entry)
                
                # Sleep between pings (OS appropriate)
                if IS_LINUX:
                    time.sleep(1)  # Linux ping has built-in interval
                else:
                    time.sleep(2)  # Windows/macOS need manual sleep

            process.stdout.close()
            process.wait()
            
        except Exception as e:
            print(f"❌ Ping monitor error for {label}: {e}")
            # Send error to UI
            error_entry = {
                'timestamp': datetime.now().isoformat(),
                'display_time': datetime.now().strftime('%H:%M:%S'),
                'data': f"Ping error: {str(e)}",
                'type': 'error',
                'host': host,
                'label': label
            }
            add_to_queue(data_queue, error_entry)
            time.sleep(5)

'''
        
        # Replace the function
        content = content[:start_pos] + new_ping_function + content[end_pos:]
        
        # Write back the file
        with open('web_network_monitor.py', 'w', encoding='utf-8') as f:
            f.write(content)
        
        print("✅ Ping monitoring fixed!")
        return True
        
    except Exception as e:
        print(f"❌ Error fixing ping monitoring: {e}")
        return False

def fix_monitoring_startup():
    """Fix the monitoring thread startup"""
    
    print("🔧 Fixing monitoring thread startup...")
    
    try:
        with open('web_network_monitor.py', 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        
        # Look for the thread startup section
        if "start_monitoring_threads" in content:
            print("📡 Monitoring threads startup already exists")
        else:
            # Add monitoring thread startup function
            startup_function = '''
def start_monitoring_threads():
    """Start all monitoring threads"""
    print("🚀 Starting monitoring threads...")
    
    # External ping monitors
    external_hosts = [
        {"host": "1.1.1.1", "label": "EXTERNAL_CLOUDFLARE"},
        {"host": "8.8.8.8", "label": "EXTERNAL_GOOGLE"},
        {"host": "9.9.9.9", "label": "EXTERNAL_QUAD9"}
    ]
    
    for host_info in external_hosts:
        log_file = os.path.join(LOG_FOLDER, f'ping_{host_info["label"].lower()}.log')
        thread = threading.Thread(
            target=ping_monitor,
            args=(host_info["host"], host_info["label"], log_file, ping_queue),
            daemon=True
        )
        thread.start()
        print(f"✅ Started ping monitor: {host_info['label']}")
    
    # Internal traceroute monitor
    internal_host = "10.99.100.1"  # Default internal target
    traceroute_log = os.path.join(LOG_FOLDER, 'traceroute_internal.log')
    thread = threading.Thread(
        target=traceroute_monitor,
        args=(internal_host, "INTERNAL_TRACEROUTE", traceroute_log, traceroute_queue),
        daemon=True
    )
    thread.start()
    print("✅ Started internal traceroute monitor")
    
    print("🎯 All monitoring threads started!")

'''
            
            # Add before the main block
            main_pos = content.find("if __name__ == '__main__':")
            if main_pos != -1:
                content = content[:main_pos] + startup_function + "\\n" + content[main_pos:]
        
        # Make sure the startup function is called
        if "start_monitoring_threads()" not in content:
            # Add the call in the main block
            content = content.replace(
                "socketio.run(app, host='0.0.0.0', port=args.port, debug=False, allow_unsafe_werkzeug=True)",
                "start_monitoring_threads()\\n    socketio.run(app, host='0.0.0.0', port=args.port, debug=False, allow_unsafe_werkzeug=True)"
            )
        
        with open('web_network_monitor.py', 'w', encoding='utf-8') as f:
            f.write(content)
        
        print("✅ Monitoring startup fixed!")
        return True
        
    except Exception as e:
        print(f"❌ Error fixing startup: {e}")
        return False

if __name__ == "__main__":
    print("🔧 Fixing Ping and Monitoring Issues")
    print("===================================")
    
    success = fix_ping_monitoring()
    if success:
        success = fix_monitoring_startup()
    
    if success:
        print("\\n✅ All fixes applied successfully!")
        print("🚀 Now try running: python setup_and_run.py --run --port 8080")
    else:
        print("\\n❌ Some fixes failed. Check the errors above.")
