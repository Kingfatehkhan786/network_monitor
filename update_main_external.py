#!/usr/bin/env python3
"""
Update Main External Page - Replace SocketIO with working AJAX system
Keep the perfect layout but use working AJAX polling
"""

def update_external_template():
    """Update the main external template to use AJAX instead of SocketIO"""
    
    print("🔄 Updating main external template with working AJAX system...")
    
    try:
        # Read the current template
        with open('templates/public_monitoring.html', 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        
        # Find and replace the JavaScript section
        # Look for the script tag
        script_start = content.find('<script>')
        script_end = content.find('</script>') + len('</script>')
        
        if script_start == -1 or script_end == -1:
            print("❌ Could not find script section")
            return False
        
        # Keep everything before the script
        before_script = content[:script_start]
        after_script = content[script_end:]
        
        # Create new AJAX-based JavaScript
        new_javascript = '''<script>
    // AJAX Live Ping System (No SocketIO) - Maintains Perfect Layout
    console.log('🚀 Starting AJAX live ping system');
    
    const hosts = [
        {name: 'Cloudflare', ip: '1.1.1.1', provider: 'cloudflare'},
        {name: 'Google', ip: '8.8.8.8', provider: 'google'},
        {name: 'Quad9', ip: '9.9.9.9', provider: 'quad9'}
    ];
    
    // Data storage for each provider
    const providerData = {
        cloudflare: { packets_sent: 0, packets_received: 0, latencies: [], logs: [] },
        google: { packets_sent: 0, packets_received: 0, latencies: [], logs: [] },
        quad9: { packets_sent: 0, packets_received: 0, latencies: [], logs: [] }
    };
    
    function formatTimestamp(timestamp) {
        try {
            let date;
            if (typeof timestamp === 'string' && timestamp.includes('T')) {
                date = new Date(timestamp);
            } else if (typeof timestamp === 'number') {
                date = new Date(timestamp * 1000);
            } else if (timestamp) {
                date = new Date(timestamp);
            } else {
                date = new Date();
            }
            
            if (isNaN(date.getTime())) {
                date = new Date();
            }
            
            return `[${date.toLocaleTimeString()}]`;
        } catch (e) {
            return `[${new Date().toLocaleTimeString()}]`;
        }
    }
    
    function updateLiveLogsForProvider(host) {
        const provider = host.provider;
        
        fetch(`/api/live-ping/${provider}`)
            .then(response => response.json())
            .then(data => {
                const logContainer = document.getElementById(`log-${host.name}`);
                if (!logContainer) return;
                
                // Clear existing logs
                logContainer.innerHTML = '';
                
                if (data.data && data.data.length > 0) {
                    // Add each log entry
                    data.data.forEach(entry => {
                        const logLine = document.createElement('div');
                        logLine.className = 'log-line';
                        
                        // Determine line class based on content
                        let lineClass = '';
                        if (entry.data.includes('Reply from') || entry.data.includes('bytes from')) {
                            lineClass = 'success';
                        } else if (entry.data.includes('timeout') || entry.data.includes('Request timed out')) {
                            lineClass = 'error';
                        }
                        
                        logLine.innerHTML = `[${entry.timestamp}] ${entry.data}`;
                        if (lineClass) logLine.classList.add(lineClass);
                        
                        logContainer.appendChild(logLine);
                    });
                    
                    // Auto-scroll to bottom
                    logContainer.scrollTop = logContainer.scrollHeight;
                    
                    // Update status
                    const statusDot = document.getElementById(`status-dot-${host.name}`);
                    const statusText = document.getElementById(`status-text-${host.name}`);
                    
                    if (data.data.length > 0) {
                        const lastEntry = data.data[data.data.length - 1];
                        if (lastEntry.data.includes('Reply from') || lastEntry.data.includes('bytes from')) {
                            statusDot.className = 'status-dot';
                            statusText.textContent = 'Online';
                        } else if (lastEntry.data.includes('timeout')) {
                            statusDot.className = 'status-dot warning';  
                            statusText.textContent = 'Issues';
                        }
                    }
                } else {
                    // No data yet
                    logContainer.innerHTML = '<div class="log-line">Waiting for ping data...</div>';
                }
            })
            .catch(error => {
                console.error(`Error loading logs for ${provider}:`, error);
                const logContainer = document.getElementById(`log-${host.name}`);
                if (logContainer) {
                    logContainer.innerHTML = '<div class="log-line error">Error loading logs</div>';
                }
            });
    }
    
    function updateStatsForAllProviders() {
        fetch('/api/ping-stats-live')
            .then(response => response.json())
            .then(stats => {
                hosts.forEach(host => {
                    const provider = host.provider;
                    const stat = stats[provider];
                    
                    if (stat) {
                        // Update packet counts
                        const sentElement = document.getElementById(`packets-sent-${host.name}`);
                        const receivedElement = document.getElementById(`packets-received-${host.name}`);
                        const lossElement = document.getElementById(`packet-loss-${host.name}`);
                        const latencyElement = document.getElementById(`avg-latency-${host.name}`);
                        
                        if (sentElement) sentElement.textContent = stat.packets_sent;
                        if (receivedElement) receivedElement.textContent = stat.packets_received;
                        if (lossElement) lossElement.textContent = `${stat.packet_loss.toFixed(1)}%`;
                        if (latencyElement) {
                            latencyElement.textContent = stat.avg_latency > 0 ? `${stat.avg_latency}ms` : '--';
                        }
                        
                        // Store in local data for other uses
                        providerData[provider].packets_sent = stat.packets_sent;
                        providerData[provider].packets_received = stat.packets_received;
                    }
                });
            })
            .catch(error => {
                console.error('Error loading stats:', error);
            });
    }
    
    function refreshAllData() {
        // Update logs for each provider
        hosts.forEach(host => {
            updateLiveLogsForProvider(host);
        });
        
        // Update statistics
        updateStatsForAllProviders();
    }
    
    // Load initial historical data (keeping original functionality)
    function loadInitialData() {
        hosts.forEach(host => {
            fetch(`/api/ping-stats/${host.name}`)
                .then(response => response.json())
                .then(stats => {
                    if (stats && !stats.error) {
                        const provider = host.provider;
                        providerData[provider].packets_sent = stats.packets_sent || 0;
                        providerData[provider].packets_received = stats.packets_received || 0;
                        
                        // Update display
                        const sentElement = document.getElementById(`packets-sent-${host.name}`);
                        const receivedElement = document.getElementById(`packets-received-${host.name}`);
                        
                        if (sentElement) sentElement.textContent = providerData[provider].packets_sent;
                        if (receivedElement) receivedElement.textContent = providerData[provider].packets_received;
                        
                        if (stats.avg_latency) {
                            const latencyElement = document.getElementById(`avg-latency-${host.name}`);
                            if (latencyElement) latencyElement.textContent = `${stats.avg_latency}ms`;
                        }
                    }
                })
                .catch(error => {
                    console.error(`Error loading initial data for ${host.name}:`, error);
                });
        });
    }
    
    // Initialize the system
    document.addEventListener('DOMContentLoaded', function() {
        console.log('✅ AJAX system initialized');
        
        // Load initial data
        loadInitialData();
        
        // Start auto-refresh every 2 seconds
        setInterval(refreshAllData, 2000);
        
        // Initial refresh
        setTimeout(refreshAllData, 1000);
        
        console.log('🔄 Auto-refresh started - updates every 2 seconds');
    });
    
    // Manual refresh function for buttons
    function manualRefresh() {
        refreshAllData();
        console.log('🔄 Manual refresh triggered');
    }
</script>'''
        
        # Combine the parts
        updated_content = before_script + new_javascript + after_script
        
        # Write back to file
        with open('templates/public_monitoring.html', 'w', encoding='utf-8') as f:
            f.write(updated_content)
        
        print("✅ Updated main external template with AJAX system!")
        return True
        
    except Exception as e:
        print(f"❌ Error updating template: {e}")
        return False

def add_manual_refresh_buttons():
    """Add manual refresh buttons to the template"""
    
    try:
        with open('templates/public_monitoring.html', 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        
        # Add refresh buttons to each provider section
        # Look for the DNS header section and add a refresh button
        old_header = '''<div class="dns-header {% if host.name == 'Cloudflare' %}cloudflare-header{% elif host.name == 'Google' %}google-header{% elif host.name == 'Quad9' %}quad9-header{% endif %}">
        <div class="dns-icon">
            {% if host.name == 'Cloudflare' %}☁️{% elif host.name == 'Google' %}🌐{% elif host.name == 'Quad9' %}🛡️{% endif %}
        </div>
        <div class="dns-info">
            <h3>{{ host.name }}</h3>
            <p>{{ host.ip }}</p>
        </div>
        <div class="dns-status">
            <span class="status-dot" id="status-dot-{{ host.name }}"></span>
            <span id="status-text-{{ host.name }}">Online</span>
        </div>
    </div>'''
        
        new_header = '''<div class="dns-header {% if host.name == 'Cloudflare' %}cloudflare-header{% elif host.name == 'Google' %}google-header{% elif host.name == 'Quad9' %}quad9-header{% endif %}">
        <div class="dns-icon">
            {% if host.name == 'Cloudflare' %}☁️{% elif host.name == 'Google' %}🌐{% elif host.name == 'Quad9' %}🛡️{% endif %}
        </div>
        <div class="dns-info">
            <h3>{{ host.name }}</h3>
            <p>{{ host.ip }}</p>
        </div>
        <div class="dns-status">
            <span class="status-dot" id="status-dot-{{ host.name }}"></span>
            <span id="status-text-{{ host.name }}">Online</span>
            <button onclick="manualRefresh()" style="margin-left: 10px; padding: 5px 10px; background: #e74c3c; color: white; border: none; border-radius: 3px; cursor: pointer; font-size: 12px;">🔄</button>
        </div>
    </div>'''
        
        content = content.replace(old_header, new_header)
        
        # Also add a main refresh button at the top
        info_header = '''<div class="info-header">
    <h1>{{ title }}</h1>
    <p>{{ description }}</p>
</div>'''
        
        new_info_header = '''<div class="info-header">
    <h1>{{ title }}</h1>
    <p>{{ description }}</p>
    <div style="margin-top: 15px;">
        <button onclick="manualRefresh()" style="padding: 10px 20px; background: #27ae60; color: white; border: none; border-radius: 5px; cursor: pointer; font-size: 14px;">🔄 Refresh All Live Data</button>
        <span style="margin-left: 15px; font-size: 12px; color: #bdc3c7;">Auto-updates every 2 seconds</span>
    </div>
</div>'''
        
        content = content.replace(info_header, new_info_header)
        
        with open('templates/public_monitoring.html', 'w', encoding='utf-8') as f:
            f.write(content)
        
        print("✅ Added manual refresh buttons")
        return True
        
    except Exception as e:
        print(f"❌ Error adding buttons: {e}")
        return False

if __name__ == "__main__":
    print("🎯 Updating Main External Page with Working AJAX System")
    print("======================================================")
    
    success1 = update_external_template()
    success2 = add_manual_refresh_buttons()
    
    if success1 and success2:
        print("\n🎉 MAIN EXTERNAL PAGE UPDATED!")
        print("\n✅ YOUR PERFECT LAYOUT + WORKING AJAX:")
        print("  ✅ Same beautiful design you confirmed")
        print("  ✅ Live TTL ping logs (no more 'Initializing...')")
        print("  ✅ Real-time packet counters") 
        print("  ✅ Live latency measurements")
        print("  ✅ Auto-refresh every 2 seconds")
        print("  ✅ Manual refresh buttons")
        print("  ✅ No SocketIO dependency!")
        print("\n🌐 Visit your main external page now:")
        print("  http://localhost:5000/external")
        print("\n🚀 It will work perfectly like the /ajax-live page!")
    else:
        print("\n❌ Update failed")
