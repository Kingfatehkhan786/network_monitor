#!/usr/bin/env python3
"""
Test SocketIO events directly by creating a simple test endpoint
"""

def add_socketio_test_endpoint():
    """Add a test endpoint to manually trigger SocketIO events"""
    
    print("🔧 Adding SocketIO test endpoint...")
    
    try:
        with open('web_network_monitor.py', 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        
        # Add test endpoint before the main block
        test_endpoint = '''
@app.route('/test-socketio')
def test_socketio():
    """Test SocketIO by sending fake ping events"""
    import time
    from datetime import datetime
    
    # Send test events for each provider
    providers = ['cloudflare', 'google', 'quad9']
    
    for provider in providers:
        fake_ping_data = {
            'timestamp': datetime.now().isoformat(),
            'display_time': datetime.now().strftime('%H:%M:%S'),
            'data': f'Reply from {provider} server: bytes=32 time=15ms TTL=57',
            'type': 'ping',
            'host': '1.1.1.1' if provider == 'cloudflare' else ('8.8.8.8' if provider == 'google' else '9.9.9.9'),
            'label': f'EXTERNAL_{provider.upper()}'
        }
        
        event_name = f'ping_update_external_{provider}'
        print(f"🧪 Test emitting: {event_name}")
        socketio.emit(event_name, fake_ping_data)
        
        # Also emit debug event
        socketio.emit('debug_ping_event', {
            'event_name': event_name,
            'host': fake_ping_data['host'],
            'provider': provider,
            'data': fake_ping_data
        })
    
    return jsonify({
        'message': 'Test SocketIO events sent',
        'events_sent': [f'ping_update_external_{p}' for p in providers],
        'timestamp': datetime.now().isoformat()
    })

@socketio.on('connect')
def handle_connect():
    """Handle client connection"""
    print(f"🔗 Client connected: {request.sid}")
    socketio.emit('connection_test', {
        'message': 'You are connected!',
        'timestamp': datetime.now().isoformat()
    })

@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection"""
    print(f"❌ Client disconnected: {request.sid}")

'''
        
        main_pos = content.find("if __name__ == '__main__':")
        if main_pos != -1:
            content = content[:main_pos] + test_endpoint + "\n" + content[main_pos:]
        
        with open('web_network_monitor.py', 'w', encoding='utf-8') as f:
            f.write(content)
        
        print("✅ Added SocketIO test endpoint")
        return True
        
    except Exception as e:
        print(f"❌ Error adding test endpoint: {e}")
        return False

def create_simple_test_page():
    """Create a simple test page to verify SocketIO is working"""
    
    test_html = '''<!DOCTYPE html>
<html>
<head>
    <title>SocketIO Test</title>
    <script src="https://cdn.socket.io/4.7.4/socket.io.min.js"></script>
    <style>
        body { font-family: Arial, sans-serif; background: #2c3e50; color: white; padding: 20px; }
        .log { background: #34495e; padding: 10px; margin: 10px 0; border-radius: 5px; }
        button { padding: 10px 20px; margin: 10px; background: #3498db; color: white; border: none; border-radius: 5px; cursor: pointer; }
    </style>
</head>
<body>
    <h1>🧪 SocketIO Connection Test</h1>
    
    <div>
        <button onclick="testConnection()">Test Connection</button>
        <button onclick="triggerTestEvents()">Trigger Test Ping Events</button>
        <button onclick="clearLogs()">Clear Logs</button>
    </div>
    
    <div id="status">Connecting...</div>
    <div id="logs"></div>

    <script>
        const socket = io();
        const logsDiv = document.getElementById('logs');
        const statusDiv = document.getElementById('status');
        
        function addLog(message, color = '#4CAF50') {
            const log = document.createElement('div');
            log.className = 'log';
            log.style.borderLeft = `4px solid ${color}`;
            log.innerHTML = `[${new Date().toLocaleTimeString()}] ${message}`;
            logsDiv.appendChild(log);
            logsDiv.scrollTop = logsDiv.scrollHeight;
        }
        
        // Connection events
        socket.on('connect', function() {
            statusDiv.innerHTML = '✅ Connected to server';
            statusDiv.style.color = '#4CAF50';
            addLog('Connected to SocketIO server', '#4CAF50');
        });
        
        socket.on('disconnect', function() {
            statusDiv.innerHTML = '❌ Disconnected from server';
            statusDiv.style.color = '#e74c3c';
            addLog('Disconnected from server', '#e74c3c');
        });
        
        // Test events
        socket.on('connection_test', function(data) {
            addLog(`Connection test: ${data.message}`, '#f39c12');
        });
        
        // Listen for all ping events
        socket.on('ping_update_external_cloudflare', function(data) {
            addLog(`🟠 Cloudflare ping: ${data.data}`, '#ff6b35');
        });
        
        socket.on('ping_update_external_google', function(data) {
            addLog(`🔵 Google ping: ${data.data}`, '#4285f4');
        });
        
        socket.on('ping_update_external_quad9', function(data) {
            addLog(`🟣 Quad9 ping: ${data.data}`, '#9b59b6');
        });
        
        socket.on('debug_ping_event', function(data) {
            addLog(`🔍 Debug event: ${data.event_name} - ${data.data.data}`, '#95a5a6');
        });
        
        // Catch all events for debugging
        const originalEmit = socket.emit;
        const originalOn = socket.on;
        
        socket.on = function(event, callback) {
            return originalOn.call(this, event, function(data) {
                if (event.includes('ping') || event.includes('debug')) {
                    addLog(`📡 Received event: ${event}`, '#3498db');
                }
                return callback(data);
            });
        };
        
        function testConnection() {
            socket.emit('test', {message: 'Hello from test page'});
            addLog('Sent test message to server', '#e67e22');
        }
        
        function triggerTestEvents() {
            fetch('/test-socketio')
                .then(response => response.json())
                .then(data => {
                    addLog(`Triggered test events: ${data.events_sent.join(', ')}`, '#2ecc71');
                })
                .catch(error => {
                    addLog(`Error: ${error}`, '#e74c3c');
                });
        }
        
        function clearLogs() {
            logsDiv.innerHTML = '';
        }
    </script>
</body>
</html>'''
    
    with open('socketio_test.html', 'w', encoding='utf-8') as f:
        f.write(test_html)
    
    print("✅ Created SocketIO test page: socketio_test.html")

def add_test_page_route():
    """Add route to serve the test page"""
    
    try:
        with open('web_network_monitor.py', 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        
        test_route = '''
@app.route('/socketio-test')
def socketio_test_page():
    """Serve the SocketIO test page"""
    return send_file('socketio_test.html')
'''
        
        # Add before debug route
        debug_pos = content.find("@app.route('/debug')")
        if debug_pos != -1:
            content = content[:debug_pos] + test_route + "\n" + content[debug_pos:]
        
        with open('web_network_monitor.py', 'w', encoding='utf-8') as f:
            f.write(content)
        
        print("✅ Added test page route")
        return True
        
    except Exception as e:
        print(f"❌ Error adding test route: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Creating SocketIO Test Tools")
    print("==============================")
    
    success1 = add_socketio_test_endpoint()
    success2 = add_test_page_route()
    create_simple_test_page()
    
    if success1 and success2:
        print("\n✅ SocketIO test tools created!")
        print("\n🧪 Testing Steps:")
        print("1. Restart the application")
        print("2. Visit: http://localhost:5000/socketio-test")
        print("3. Click 'Test Connection' - should see connection success")
        print("4. Click 'Trigger Test Ping Events' - should see fake ping data")
        print("5. If this works, the issue is in the real ping monitoring")
        print("6. If this doesn't work, the issue is in SocketIO setup")
        print("\n🌐 Test URLs:")
        print("  http://localhost:5000/socketio-test  - SocketIO connection test")
        print("  http://localhost:5000/test-socketio  - Manual event trigger")
    else:
        print("\n❌ Some test tools failed to create.")
