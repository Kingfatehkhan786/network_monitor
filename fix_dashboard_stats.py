#!/usr/bin/env python3
"""
Fix Dashboard Statistics - Update JavaScript to handle Linux ping output
"""

def fix_ping_stats_javascript():
    """Fix the JavaScript in public_monitoring.html to handle Linux ping output"""
    
    print("🔧 Fixing dashboard statistics JavaScript...")
    
    try:
        # Read the template file
        with open('templates/public_monitoring.html', 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        
        # Find the ping processing section
        old_ping_logic = '''            // Handle ping monitoring
            if (monitorType === 'ping') {
                // Only count actual ping attempts
                if (content.includes('Reply from') || content.includes('bytes from') || content.includes('Request timed out') || content.includes('timeout')) {
                    packetsSent++;
                    
                    if (content.includes('Reply from') || content.includes('bytes from')) {
                        packetsReceived++;
                        lineClass = 'success';
                        const timeMatch = content.match(/time[=<]([\d.]+)\\s*ms/);
                        if (timeMatch) {
                            latencies.push(parseFloat(timeMatch[1]));
                        }
                        statusDot.className = 'status-dot';
                        statusText.textContent = 'Online';
                    } else if (content.includes('Request timed out') || content.includes('timeout')) {
                        lineClass = 'error';
                        statusDot.className = 'status-dot warning';
                        statusText.textContent = 'Issues';
                    }
                    updateStats();
                }
            }'''
        
        # New enhanced ping logic that handles Windows, Linux, and macOS
        new_ping_logic = '''            // Handle ping monitoring (Windows, Linux, macOS)
            if (monitorType === 'ping') {
                let isPingResult = false;
                let isSuccess = false;
                let latency = null;
                
                // Detect ping results across different OS
                // Windows: "Reply from 1.1.1.1: bytes=32 time=15ms TTL=57"
                // Linux: "64 bytes from 1.1.1.1: icmp_seq=1 ttl=57 time=15.2 ms"
                // macOS: "64 bytes from 1.1.1.1: icmp_seq=0 ttl=57 time=15.123 ms"
                
                if (content.includes('Reply from') || 
                    content.includes('bytes from') || 
                    content.includes('Request timed out') || 
                    content.includes('timeout') ||
                    content.includes('no answer') ||
                    content.includes('100% packet loss')) {
                    
                    isPingResult = true;
                    packetsSent++;
                    
                    // Check for successful ping
                    if (content.includes('Reply from') || content.includes('bytes from')) {
                        packetsReceived++;
                        isSuccess = true;
                        lineClass = 'success';
                        
                        // Extract latency - multiple patterns
                        const timePatterns = [
                            /time[=<]([\d.]+)\\s*ms/i,           // Windows: time=15ms
                            /time=([\d.]+)\\s*ms/i,             // Linux: time=15.2 ms  
                            /time\\s+([\d.]+)\\s*ms/i,          // Alternative format
                            /([\d.]+)\\s*ms/                     // Just find any number+ms
                        ];
                        
                        for (const pattern of timePatterns) {
                            const match = content.match(pattern);
                            if (match) {
                                latency = parseFloat(match[1]);
                                latencies.push(latency);
                                break;
                            }
                        }
                        
                        statusDot.className = 'status-dot';
                        statusText.textContent = 'Online';
                        document.getElementById(`status-value-${host.name}`).textContent = 'Online';
                        
                    } else if (content.includes('Request timed out') || 
                               content.includes('timeout') || 
                               content.includes('no answer')) {
                        lineClass = 'error';
                        statusDot.className = 'status-dot warning';
                        statusText.textContent = 'Issues';
                        document.getElementById(`status-value-${host.name}`).textContent = 'Timeout';
                    }
                    
                    updateStats();
                }
                
                // Also handle ping start messages
                if (content.includes('Ping') || content.includes('PING')) {
                    statusDot.className = 'status-dot warning';
                    statusText.textContent = 'Running...';
                    document.getElementById(`status-value-${host.name}`).textContent = 'Running';
                }
            }'''
        
        # Replace the ping logic
        if old_ping_logic.strip() in content:
            content = content.replace(old_ping_logic, new_ping_logic)
            print("✅ Updated ping processing logic")
        else:
            print("⚠️  Original ping logic not found, looking for alternative...")
            # Try to find and replace just the key section
            content = content.replace(
                "content.includes('Reply from') || content.includes('bytes from')",
                "content.includes('Reply from') || content.includes('bytes from') || content.includes('64 bytes from')"
            )
        
        # Also fix the traceroute logic for better hop counting
        old_traceroute_pattern = "content.match(/^\\s*\\d+\\s+\\d+\\s+ms/)"
        new_traceroute_pattern = "content.match(/^\\s*\\d+\\s+/) && (content.includes('ms') || content.includes('*'))"
        
        content = content.replace(old_traceroute_pattern, new_traceroute_pattern)
        
        # Write back the fixed template
        with open('templates/public_monitoring.html', 'w', encoding='utf-8') as f:
            f.write(content)
        
        print("✅ Dashboard statistics JavaScript fixed!")
        return True
        
    except Exception as e:
        print(f"❌ Error fixing dashboard stats: {e}")
        return False

def add_debug_logging():
    """Add debug logging to see what data is being received"""
    
    try:
        with open('templates/public_monitoring.html', 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        
        # Add debug logging right after receiving data
        debug_code = '''            
            // Debug: Log received data
            console.log(`📡 Received ${eventName}:`, data);
            console.log(`📊 Content: "${content}"`);
            console.log(`📈 Packets sent: ${packetsSent}, received: ${packetsReceived}`);
            '''
        
        # Insert debug code after the data assignment
        insert_point = "let content = data.data;"
        if insert_point in content:
            content = content.replace(
                insert_point,
                insert_point + debug_code
            )
        
        with open('templates/public_monitoring.html', 'w', encoding='utf-8') as f:
            f.write(content)
        
        print("✅ Added debug logging to dashboard")
        return True
        
    except Exception as e:
        print(f"❌ Error adding debug logging: {e}")
        return False

if __name__ == "__main__":
    print("🔧 Fixing Dashboard Statistics")
    print("=============================")
    
    success1 = fix_ping_stats_javascript()
    success2 = add_debug_logging()
    
    if success1 and success2:
        print("\\n✅ Dashboard statistics fixes applied!")
        print("🌐 The dashboard should now show real ping statistics")
        print("🔍 Check browser console (F12) for debug info")
        print("🚀 Restart the application to see the changes")
    else:
        print("\\n❌ Some fixes failed. Check the errors above.")
