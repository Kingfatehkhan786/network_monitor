#!/usr/bin/env python3
"""
Minimal SocketIO test - create the simplest possible working example
"""

def create_minimal_test():
    """Create the most basic SocketIO test possible"""
    
    # Create a super simple HTML page that just tests SocketIO
    minimal_html = '''<!DOCTYPE html>
<html>
<head>
    <title>Minimal SocketIO Test</title>
    <script src="https://cdn.socket.io/4.7.4/socket.io.min.js"></script>
</head>
<body style="background: #000; color: #0f0; font-family: monospace; padding: 20px;">
    <h1>🔬 MINIMAL SOCKETIO TEST</h1>
    <div id="status">CONNECTING...</div>
    <div id="output"></div>
    <button onclick="sendTest()">SEND TEST</button>
    
    <script>
        const socket = io();
        const output = document.getElementById('output');
        const status = document.getElementById('status');
        
        function log(msg) {
            output.innerHTML += '<br>' + new Date().toLocaleTimeString() + ': ' + msg;
            console.log(msg);
        }
        
        socket.on('connect', function() {
            status.innerHTML = '✅ CONNECTED';
            status.style.color = '#0f0';
            log('✅ SocketIO CONNECTED');
        });
        
        socket.on('disconnect', function() {
            status.innerHTML = '❌ DISCONNECTED';  
            status.style.color = '#f00';
            log('❌ SocketIO DISCONNECTED');
        });
        
        // Listen for test events
        socket.on('test_response', function(data) {
            log('📨 RECEIVED TEST_RESPONSE: ' + JSON.stringify(data));
        });
        
        socket.on('simple_ping', function(data) {
            log('📡 RECEIVED SIMPLE_PING: ' + JSON.stringify(data));
        });
        
        function sendTest() {
            socket.emit('test_request', {message: 'Hello from client'});
            log('📤 SENT test_request');
        }
        
        // Listen for ANY event (debugging)
        const originalOn = socket.on;
        socket.on = function(event, callback) {
            return originalOn.call(this, event, function(data) {
                log('🎯 ANY EVENT: ' + event);
                return callback(data);
            });
        };
        
        log('🚀 JavaScript loaded');
    </script>
</body>
</html>'''
    
    with open('minimal_test.html', 'w', encoding='utf-8') as f:
        f.write(minimal_html)
    
    print("✅ Created minimal test HTML")

def add_minimal_routes():
    """Add minimal test routes to web_network_monitor.py"""
    
    try:
        with open('web_network_monitor.py', 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        
        # Add minimal test routes and events
        minimal_code = '''
@app.route('/minimal')
def minimal_test():
    """Minimal SocketIO test page"""
    return send_file('minimal_test.html')

@app.route('/force-emit')
def force_emit():
    """Force emit a test event"""
    print("🔥 FORCE EMITTING TEST EVENT")
    socketio.emit('simple_ping', {
        'message': 'FORCED TEST EVENT',
        'timestamp': datetime.now().isoformat(),
        'test': True
    })
    return jsonify({'message': 'Event emitted'})

@socketio.on('test_request')
def handle_test_request(data):
    """Handle test request from client"""
    print(f"📥 RECEIVED test_request: {data}")
    socketio.emit('test_response', {
        'message': 'Server received your message',
        'original': data,
        'timestamp': datetime.now().isoformat()
    })
    print("📤 SENT test_response")

# Simplified ping emitter for testing
def emit_test_pings():
    """Emit simple test pings every 5 seconds"""
    import threading
    import time
    
    def ping_loop():
        counter = 0
        while True:
            try:
                counter += 1
                test_data = {
                    'message': f'Test ping #{counter}',
                    'timestamp': datetime.now().isoformat(),
                    'counter': counter
                }
                
                print(f"🧪 EMITTING simple_ping #{counter}")
                socketio.emit('simple_ping', test_data)
                
                # Also emit the external ping events
                socketio.emit('ping_update_external_cloudflare', test_data)
                socketio.emit('ping_update_external_google', test_data)
                socketio.emit('ping_update_external_quad9', test_data)
                
                time.sleep(5)
            except Exception as e:
                print(f"❌ Test ping error: {e}")
                time.sleep(5)
    
    thread = threading.Thread(target=ping_loop, daemon=True)
    thread.start()
    print("🧪 Started test ping emitter")

'''
        
        # Add before the main block
        main_pos = content.find("if __name__ == '__main__':")
        if main_pos != -1:
            content = content[:main_pos] + minimal_code + "\n" + content[main_pos:]
        
        # Add the test ping emitter call to the main block
        start_threads_pos = content.find("start_monitoring_threads()")
        if start_threads_pos != -1:
            content = content.replace(
                "start_monitoring_threads()",
                "start_monitoring_threads()\n    emit_test_pings()"
            )
        
        with open('web_network_monitor.py', 'w', encoding='utf-8') as f:
            f.write(content)
        
        print("✅ Added minimal test routes")
        return True
        
    except Exception as e:
        print(f"❌ Error adding minimal routes: {e}")
        return False

if __name__ == "__main__":
    print("🔬 Creating Minimal SocketIO Test")
    print("================================")
    
    create_minimal_test()
    success = add_minimal_routes()
    
    if success:
        print("\n🔬 MINIMAL TEST READY!")
        print("\n🧪 DEBUGGING STEPS:")
        print("1. Restart the application")
        print("2. Visit: http://localhost:5000/minimal")
        print("3. You should see:")
        print("   ✅ 'CONNECTED' status")
        print("   📡 'RECEIVED SIMPLE_PING' every 5 seconds")
        print("4. Click 'SEND TEST' button")
        print("5. You should see 'RECEIVED TEST_RESPONSE'")
        print("\n🔍 If this doesn't work, the problem is:")
        print("   - SocketIO server configuration")
        print("   - CORS issues") 
        print("   - Network/firewall blocking")
        print("\n🌐 Test URLs:")
        print("   http://localhost:5000/minimal      - Minimal test")
        print("   http://localhost:5000/force-emit   - Force emit event")
    else:
        print("\n❌ Failed to create minimal test")
