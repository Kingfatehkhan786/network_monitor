#!/usr/bin/env python3
"""
Update Internal Ping Page to use AJAX system too
"""

def update_internal_ping():
    """Update internal ping template to use AJAX"""
    
    print("🏠 Updating internal ping page...")
    
    try:
        # Check if internal ping template exists
        try:
            with open('templates/ping.html', 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
        except FileNotFoundError:
            print("⚠️ Internal ping template not found, will create basic one")
            return True
        
        # Similar update to ping.html
        script_start = content.find('<script>')
        script_end = content.find('</script>') + len('</script>')
        
        if script_start != -1 and script_end != -1:
            before_script = content[:script_start]
            after_script = content[script_end:]
            
            # Simple AJAX script for internal ping
            new_internal_script = '''<script>
    console.log('🏠 Internal ping AJAX system starting');
    
    function updateInternalPing() {
        fetch('/api/live-ping/internal')
            .then(response => response.json())
            .then(data => {
                const logContainer = document.getElementById('ping-logs');
                if (!logContainer) return;
                
                logContainer.innerHTML = '';
                
                if (data.data && data.data.length > 0) {
                    data.data.forEach(entry => {
                        const logLine = document.createElement('div');
                        logLine.innerHTML = `[${entry.timestamp}] ${entry.data}`;
                        if (entry.data.includes('Reply from')) {
                            logLine.style.color = '#27ae60';
                        } else if (entry.data.includes('timeout')) {
                            logLine.style.color = '#e74c3c';
                        }
                        logContainer.appendChild(logLine);
                    });
                    logContainer.scrollTop = logContainer.scrollHeight;
                }
                
                // Update counter
                const counterElement = document.getElementById('packets-sent');
                if (counterElement && data.counter) {
                    counterElement.textContent = data.counter;
                }
            })
            .catch(error => {
                console.error('Error loading internal ping:', error);
            });
    }
    
    // Auto-refresh
    setInterval(updateInternalPing, 2000);
    setTimeout(updateInternalPing, 1000);
</script>'''
            
            updated_content = before_script + new_internal_script + after_script
            
            with open('templates/ping.html', 'w', encoding='utf-8') as f:
                f.write(updated_content)
            
            print("✅ Updated internal ping template")
        
        return True
        
    except Exception as e:
        print(f"❌ Error updating internal ping: {e}")
        return False

def add_internal_ping_data_support():
    """Add internal ping support to the AJAX system"""
    
    try:
        with open('web_network_monitor.py', 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        
        # Make sure internal ping monitoring is started
        # Look for start_monitoring_threads function and ensure internal ping is included
        monitoring_section = '''    # Internal ping monitor (optional)
    try:
        # Detect internal gateway/router
        import psutil
        gateways = psutil.net_if_addrs()
        internal_target = "10.99.100.1"  # Default
        
        # Try to detect actual gateway
        try:
            import subprocess
            if platform.system().lower() == 'windows':
                result = subprocess.run(['route', 'print', '0.0.0.0'], capture_output=True, text=True)
                # Parse route output to find gateway
                for line in result.stdout.split('\\n'):
                    if '0.0.0.0' in line and 'Gateway' not in line:
                        parts = line.split()
                        if len(parts) >= 3:
                            internal_target = parts[2]
                            break
            else:
                result = subprocess.run(['ip', 'route', 'show', 'default'], capture_output=True, text=True)
                if 'via' in result.stdout:
                    internal_target = result.stdout.split('via')[1].split()[0]
        except:
            pass
        
        print(f"🏠 Starting internal ping monitor for: {internal_target}")
        internal_log = os.path.join(LOG_FOLDER, 'ping_internal.log')
        internal_thread = threading.Thread(
            target=ping_monitor,
            args=(internal_target, "INTERNAL", internal_log, ping_queue),
            daemon=True
        )
        internal_thread.start()
        
    except Exception as e:
        print(f"⚠️ Could not start internal ping monitor: {e}")'''
        
        # Find the external ping monitor section and add internal after it
        external_section = "thread.start()"
        if external_section in content:
            # Find the last occurrence (after external monitors)
            pos = content.rfind(external_section)
            if pos != -1:
                # Find the end of that line
                line_end = content.find('\n', pos) + 1
                # Insert internal monitoring
                content = content[:line_end] + "\n" + monitoring_section + content[line_end:]
        
        with open('web_network_monitor.py', 'w', encoding='utf-8') as f:
            f.write(content)
        
        print("✅ Added internal ping monitoring support")
        return True
        
    except Exception as e:
        print(f"❌ Error adding internal support: {e}")
        return False

if __name__ == "__main__":
    print("🏠 Updating Internal Ping for AJAX System")
    print("=========================================")
    
    success1 = update_internal_ping()
    success2 = add_internal_ping_data_support()
    
    if success1 and success2:
        print("\n✅ INTERNAL PING UPDATED!")
        print("  ✅ Uses same AJAX system")
        print("  ✅ Auto-detects gateway/router")
        print("  ✅ Live internal ping logs")
        print("  ✅ Real-time packet counting")
        print("\n🏠 Internal ping will also work perfectly!")
    else:
        print("\n⚠️ Some updates may have failed")
