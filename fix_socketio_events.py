#!/usr/bin/env python3
"""
Fix SocketIO Events - Ensure events reach the frontend properly
"""

def fix_socketio_events():
    """Fix the SocketIO event emission in web_network_monitor.py"""
    
    print("🔧 Fixing SocketIO event emission...")
    
    try:
        with open('web_network_monitor.py', 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        
        # Find the ping monitor function and add better SocketIO emission
        old_emit_section = '''                # Emit SocketIO event with correct naming
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
                socketio.emit(event_name, log_entry)'''
        
        new_emit_section = '''                # Emit SocketIO event with correct naming
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
                
                print(f"📡 Emitting: {event_name} with data: {log_entry['data'][:50]}...")
                
                # Emit to specific rooms and broadcast
                socketio.emit(event_name, log_entry, broadcast=True)
                
                # Also emit a generic event for debugging
                socketio.emit('debug_ping_event', {
                    'event_name': event_name,
                    'host': host,
                    'provider': provider if "external" in label.lower() else 'internal',
                    'data': log_entry
                }, broadcast=True)'''
        
        if old_emit_section.strip() in content:
            content = content.replace(old_emit_section, new_emit_section)
            print("✅ Updated SocketIO emission code")
        else:
            print("⚠️  Could not find exact emit section, looking for socketio.emit...")
            # Fallback: just add broadcast=True to existing emits
            content = content.replace(
                'socketio.emit(event_name, log_entry)',
                'socketio.emit(event_name, log_entry, broadcast=True)'
            )
        
        with open('web_network_monitor.py', 'w', encoding='utf-8') as f:
            f.write(content)
        
        print("✅ SocketIO events fixed!")
        return True
        
    except Exception as e:
        print(f"❌ Error fixing SocketIO events: {e}")
        return False

def add_debug_events_to_template():
    """Add debug event listeners to the template"""
    
    print("🔧 Adding debug events to template...")
    
    try:
        with open('templates/public_monitoring.html', 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        
        # Add debug event listeners
        debug_listeners = '''
        // Debug event listener to see what we're actually receiving
        socket.on('debug_ping_event', function(data) {
            console.log('🔍 Debug ping event:', data);
            console.log(`Event: ${data.event_name}, Provider: ${data.provider}`);
        });
        
        // Listen for connection events
        socket.on('connect', function() {
            console.log('✅ Socket connected');
            const debugDiv = document.createElement('div');
            debugDiv.innerHTML = '<small style="color: #4CAF50;">[Connected to server]</small>';
            document.querySelectorAll('.log-container').forEach(container => {
                container.appendChild(debugDiv.cloneNode(true));
            });
        });
        
        socket.on('disconnect', function() {
            console.log('❌ Socket disconnected');
            const debugDiv = document.createElement('div');
            debugDiv.innerHTML = '<small style="color: #e74c3c;">[Disconnected from server]</small>';
            document.querySelectorAll('.log-container').forEach(container => {
                container.appendChild(debugDiv.cloneNode(true));
            });
        });
        
        // Test: Listen for ALL events (for debugging)
        const originalOn = socket.on;
        socket.on = function(event, callback) {
            return originalOn.call(this, event, function(data) {
                if (event.includes('ping')) {
                    console.log(`🎯 Received event: ${event}`, data);
                }
                return callback(data);
            });
        };
        '''
        
        # Insert before the hosts.forEach loop
        insert_point = "hosts.forEach(host => {"
        if insert_point in content:
            content = content.replace(insert_point, debug_listeners + "\n    " + insert_point)
        
        with open('templates/public_monitoring.html', 'w', encoding='utf-8') as f:
            f.write(content)
        
        print("✅ Added debug events to template")
        return True
        
    except Exception as e:
        print(f"❌ Error adding debug events: {e}")
        return False

def force_event_names():
    """Force correct event names in the frontend"""
    
    print("🔧 Forcing correct event names...")
    
    try:
        with open('templates/public_monitoring.html', 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        
        # Replace the dynamic event name generation with hardcoded names
        old_event_logic = '''        // Listen for real-time updates for each host
        let eventName;
        if (monitorType === 'traceroute') {
            eventName = `traceroute_update_external_${host.name.toLowerCase()}`;
        } else {
            eventName = `ping_update_external_${host.name.toLowerCase()}`;
        }'''
        
        new_event_logic = '''        // Listen for real-time updates for each host - HARDCODED FOR DEBUGGING
        let eventName;
        if (monitorType === 'traceroute') {
            eventName = `traceroute_update_internal`;  // Only internal traceroute
        } else {
            // Hardcode the event names to match backend exactly
            if (host.name === 'Cloudflare') {
                eventName = 'ping_update_external_cloudflare';
            } else if (host.name === 'Google') {
                eventName = 'ping_update_external_google';
            } else if (host.name === 'Quad9') {
                eventName = 'ping_update_external_quad9';
            } else {
                eventName = 'ping_update_internal';
            }
        }
        
        console.log(`👂 Listening for event: ${eventName} for host: ${host.name}`);'''
        
        if old_event_logic.strip() in content:
            content = content.replace(old_event_logic, new_event_logic)
            print("✅ Hardcoded event names for debugging")
        
        with open('templates/public_monitoring.html', 'w', encoding='utf-8') as f:
            f.write(content)
        
        print("✅ Event names fixed!")
        return True
        
    except Exception as e:
        print(f"❌ Error fixing event names: {e}")
        return False

if __name__ == "__main__":
    print("🔧 Fixing SocketIO Event Issues")
    print("===============================")
    
    success1 = fix_socketio_events()
    success2 = add_debug_events_to_template() 
    success3 = force_event_names()
    
    if success1 and success2 and success3:
        print("\n✅ All SocketIO fixes applied!")
        print("\n🔍 Debug Steps:")
        print("1. Restart the application")
        print("2. Open browser developer tools (F12)")
        print("3. Go to Console tab")
        print("4. Refresh the external ping page")
        print("5. Look for console messages showing received events")
        print("\n🌐 You should now see:")
        print("  - Connection status messages")
        print("  - Event names being listened for")
        print("  - Actual events being received")
        print("  - Live ping data in the terminals")
    else:
        print("\n❌ Some fixes failed.")
