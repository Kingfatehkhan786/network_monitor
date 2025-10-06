#!/usr/bin/env python3
"""
Add monitoring status API to check if threads are running
"""

def add_status_api():
    """Add API endpoints to check monitoring status"""
    
    print("🔧 Adding monitoring status API...")
    
    try:
        with open('web_network_monitor.py', 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        
        # Add status API endpoint
        status_api = '''
@app.route('/api/monitoring-status')
def api_monitoring_status():
    """Check status of monitoring threads"""
    try:
        import threading
        
        # Get all active threads
        active_threads = [t.name for t in threading.enumerate() if t.is_alive()]
        
        # Check for monitoring threads
        ping_threads = [t for t in active_threads if 'ping' in t.name.lower()]
        traceroute_threads = [t for t in active_threads if 'traceroute' in t.name.lower()]
        
        status = {
            'total_threads': len(active_threads),
            'ping_monitors_running': len(ping_threads),
            'traceroute_monitors_running': len(traceroute_threads),
            'active_threads': active_threads,
            'ping_threads': ping_threads,
            'traceroute_threads': traceroute_threads,
            'os_detected': CURRENT_OS if 'CURRENT_OS' in globals() else platform.system().lower(),
            'timestamp': datetime.now().isoformat()
        }
        
        return jsonify(status)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/test-ping/<host>')
def api_test_ping(host):
    """Test a single ping to verify connectivity"""
    try:
        # Use OS-appropriate ping command for single test
        if 'get_os_ping_cmd' in globals():
            ping_cmd = get_os_ping_cmd(host, count=1)  # Single ping
        else:
            # Fallback
            if platform.system().lower() == 'windows':
                ping_cmd = ['ping', '-n', '1', host]
            else:
                ping_cmd = ['ping', '-c', '1', host]
        
        import subprocess
        result = subprocess.run(
            ping_cmd,
            capture_output=True,
            text=True,
            timeout=10
        )
        
        return jsonify({
            'host': host,
            'command': ' '.join(ping_cmd),
            'success': result.returncode == 0,
            'output': result.stdout[:500],  # Limit output
            'error': result.stderr[:200] if result.stderr else None,
            'return_code': result.returncode,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

'''
        
        # Add before the main block
        main_pos = content.find("if __name__ == '__main__':")
        if main_pos != -1:
            content = content[:main_pos] + status_api + "\n" + content[main_pos:]
        
        with open('web_network_monitor.py', 'w', encoding='utf-8') as f:
            f.write(content)
        
        print("✅ Added monitoring status API")
        return True
        
    except Exception as e:
        print(f"❌ Error adding status API: {e}")
        return False

def add_force_start_monitoring():
    """Add a route to manually restart monitoring"""
    
    try:
        with open('web_network_monitor.py', 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        
        restart_api = '''
@app.route('/api/restart-monitoring')
def api_restart_monitoring():
    """Manually restart monitoring threads"""
    try:
        print("🔄 Manual restart of monitoring threads requested")
        
        # Start monitoring threads again
        if 'start_monitoring_threads' in globals():
            start_monitoring_threads()
            return jsonify({
                'message': 'Monitoring threads restarted',
                'timestamp': datetime.now().isoformat()
            })
        else:
            return jsonify({
                'error': 'start_monitoring_threads function not found',
                'timestamp': datetime.now().isoformat()
            }), 500
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

'''
        
        # Add before the main block
        main_pos = content.find("if __name__ == '__main__':")
        if main_pos != -1:
            content = content[:main_pos] + restart_api + "\n" + content[main_pos:]
        
        with open('web_network_monitor.py', 'w', encoding='utf-8') as f:
            f.write(content)
        
        print("✅ Added restart monitoring API")
        return True
        
    except Exception as e:
        print(f"❌ Error adding restart API: {e}")
        return False

if __name__ == "__main__":
    print("🔧 Adding Monitoring Status and Control APIs")
    print("==========================================")
    
    success1 = add_status_api()
    success2 = add_force_start_monitoring()
    
    if success1 and success2:
        print("\n✅ All monitoring APIs added!")
        print("\n🌐 New API Endpoints:")
        print("  GET /api/monitoring-status     - Check thread status")
        print("  GET /api/test-ping/<host>      - Test single ping") 
        print("  GET /api/restart-monitoring    - Restart all monitors")
        print("\n🚀 Restart the application to use these APIs")
    else:
        print("\n❌ Some APIs failed to add.")
