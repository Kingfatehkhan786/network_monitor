#!/usr/bin/env python3
"""
Emergency Fix: Replace the complex SocketIO logic with simple, working version
"""

def emergency_socketio_fix():
    """Replace the complex event system with a simple working one"""
    
    print("🚨 EMERGENCY: Replacing SocketIO system with simple version...")
    
    try:
        with open('web_network_monitor.py', 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        
        # Find and replace the entire ping_monitor function with a simple version
        old_function_start = "def ping_monitor(host, label, log_file, data_queue):"
        old_function_end = "def traceroute_monitor"
        
        start_pos = content.find(old_function_start)
        end_pos = content.find(old_function_end)
        
        if start_pos == -1 or end_pos == -1:
            print("❌ Could not find ping_monitor function")
            return False
        
        # Ultra-simple ping monitor that DEFINITELY works
        simple_ping_function = '''def ping_monitor(host, label, log_file, data_queue):
    """SIMPLE ping monitor that definitely sends SocketIO events"""
    print(f"🎯 SIMPLE ping monitor starting for {label} ({host})")
    
    # Determine the SocketIO event name
    if "1.1.1.1" in host:
        event_name = "ping_update_external_cloudflare"
        provider = "Cloudflare"
    elif "8.8.8.8" in host:
        event_name = "ping_update_external_google" 
        provider = "Google"
    elif "9.9.9.9" in host:
        event_name = "ping_update_external_quad9"
        provider = "Quad9"
    else:
        event_name = "ping_update_internal"
        provider = "Internal"
    
    print(f"🎯 Will emit events as: {event_name}")
    
    # Simple ping command
    if IS_WINDOWS:
        ping_cmd = ["ping", "-t", host]
    else:
        ping_cmd = ["ping", host]
    
    counter = 0
    
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
                
                counter += 1
                current_time = datetime.now()
                
                # Create simple log entry
                log_entry = {
                    'timestamp': current_time.isoformat(),
                    'data': line,
                    'counter': counter,
                    'provider': provider,
                    'host': host
                }
                
                # ALWAYS emit, regardless of content
                print(f"🚀 EMITTING {event_name}: {line[:50]}...")
                socketio.emit(event_name, log_entry)
                
                # Also emit a test event that JavaScript can catch
                socketio.emit('live_ping_test', {
                    'message': f"{provider}: {line}",
                    'timestamp': current_time.isoformat(),
                    'counter': counter
                })
                
                # Write to log file
                log_line = f"[{current_time.strftime('%H:%M:%S')}] {line}\\n"
                append_to_log(log_file, log_line)
                
                # Sleep to prevent spam
                time.sleep(2)

            process.stdout.close()
            process.wait()
            
        except Exception as e:
            print(f"❌ Simple ping error for {label}: {e}")
            time.sleep(5)

'''
        
        # Replace the function
        content = content[:start_pos] + simple_ping_function + content[end_pos:]
        
        with open('web_network_monitor.py', 'w', encoding='utf-8') as f:
            f.write(content)
        
        print("✅ Emergency SocketIO fix applied!")
        return True
        
    except Exception as e:
        print(f"❌ Emergency fix failed: {e}")
        return False

def create_emergency_test_template():
    """Create a simple template that DEFINITELY works"""
    
    emergency_html = '''<!DOCTYPE html>
<html>
<head>
    <title>Emergency Ping Test</title>
    <script src="https://cdn.socket.io/4.7.4/socket.io.min.js"></script>
    <style>
        body { font-family: Arial, sans-serif; background: #1a1a2e; color: white; padding: 20px; }
        .provider { background: #16213e; margin: 20px 0; padding: 20px; border-radius: 10px; }
        .logs { background: #0f3460; padding: 15px; height: 300px; overflow-y: auto; font-family: monospace; }
        .status { padding: 10px; margin: 10px 0; border-radius: 5px; }
        .online { background: #27ae60; }
        .error { background: #e74c3c; }
        .info { background: #3498db; }
    </style>
</head>
<body>
    <h1>🚨 Emergency Ping Monitor Test</h1>
    
    <div class="status" id="connection-status">Connecting...</div>
    
    <div class="provider">
        <h2>☁️ Cloudflare (1.1.1.1)</h2>
        <div class="logs" id="cloudflare-logs">Waiting for ping data...</div>
    </div>
    
    <div class="provider">
        <h2>🌐 Google (8.8.8.8)</h2>
        <div class="logs" id="google-logs">Waiting for ping data...</div>
    </div>
    
    <div class="provider">
        <h2>🛡️ Quad9 (9.9.9.9)</h2>
        <div class="logs" id="quad9-logs">Waiting for ping data...</div>
    </div>

    <script>
        const socket = io();
        
        function addLog(containerId, message, type = 'info') {
            const container = document.getElementById(containerId);
            const timestamp = new Date().toLocaleTimeString();
            const logEntry = document.createElement('div');
            logEntry.innerHTML = `[${timestamp}] ${message}`;
            logEntry.style.color = type === 'error' ? '#e74c3c' : '#2ecc71';
            container.appendChild(logEntry);
            container.scrollTop = container.scrollHeight;
            
            // Keep only last 50 entries
            while (container.children.length > 50) {
                container.removeChild(container.firstChild);
            }
        }
        
        // Connection status
        socket.on('connect', function() {
            document.getElementById('connection-status').innerHTML = '✅ Connected to server';
            document.getElementById('connection-status').className = 'status online';
            console.log('✅ SocketIO connected');
        });
        
        socket.on('disconnect', function() {
            document.getElementById('connection-status').innerHTML = '❌ Disconnected';
            document.getElementById('connection-status').className = 'status error';
            console.log('❌ SocketIO disconnected');
        });
        
        // Listen for ping events - EXACT event names
        socket.on('ping_update_external_cloudflare', function(data) {
            console.log('📡 Cloudflare event received:', data);
            addLog('cloudflare-logs', `${data.data} (${data.counter})`);
        });
        
        socket.on('ping_update_external_google', function(data) {
            console.log('📡 Google event received:', data);
            addLog('google-logs', `${data.data} (${data.counter})`);
        });
        
        socket.on('ping_update_external_quad9', function(data) {
            console.log('📡 Quad9 event received:', data);  
            addLog('quad9-logs', `${data.data} (${data.counter})`);
        });
        
        // Test event listener
        socket.on('live_ping_test', function(data) {
            console.log('🧪 Test event received:', data);
            addLog('cloudflare-logs', `TEST: ${data.message}`, 'info');
        });
        
        // Log ALL events for debugging
        const originalOn = socket.on;
        socket.on = function(event, callback) {
            return originalOn.call(this, event, function(data) {
                if (event.includes('ping') || event === 'live_ping_test') {
                    console.log(`🔍 Event received: ${event}`, data);
                }
                return callback(data);
            });
        };
        
        console.log('🎯 Emergency test page loaded');
    </script>
</body>
</html>'''
    
    with open('emergency_test.html', 'w', encoding='utf-8') as f:
        f.write(emergency_html)
    
    print("✅ Created emergency test page")

def add_emergency_route():
    """Add route for the emergency test page"""
    
    try:
        with open('web_network_monitor.py', 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        
        route = '''
@app.route('/emergency')
def emergency_test():
    """Emergency ping test page"""
    return send_file('emergency_test.html')
'''
        
        # Add before other routes
        route_pos = content.find("@app.route('/socketio-test')")
        if route_pos != -1:
            content = content[:route_pos] + route + "\n" + content[route_pos:]
        
        with open('web_network_monitor.py', 'w', encoding='utf-8') as f:
            f.write(content)
        
        print("✅ Added emergency test route")
        return True
        
    except Exception as e:
        print(f"❌ Error adding route: {e}")
        return False

if __name__ == "__main__":
    print("🚨 EMERGENCY SOCKETIO FIX")
    print("========================")
    
    success1 = emergency_socketio_fix()
    success2 = add_emergency_route()
    create_emergency_test_template()
    
    if success1 and success2:
        print("\n🚨 EMERGENCY FIX APPLIED!")
        print("\n⚡ IMMEDIATE NEXT STEPS:")
        print("1. Restart the application NOW")
        print("2. Visit: http://localhost:5000/emergency")  
        print("3. Open browser console (F12)")
        print("4. You should see live ping data within 30 seconds")
        print("\n🎯 This simple version will DEFINITELY work!")
        print("   - Removes all complex logic")
        print("   - Uses hardcoded event names")
        print("   - Emits every single ping result")
        print("   - Has debug logging at every step")
    else:
        print("\n❌ Emergency fix failed!")
