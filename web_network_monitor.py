#!/usr/bin/env python3
import subprocess
import time
import platform
import threading
import re
import os
import gc
import json
from datetime import datetime, timedelta
from flask import Flask, render_template, jsonify, request, Response, send_file
from flask_socketio import SocketIO, emit
import queue
import zipfile
import io
try:
    import speedtest
    SPEEDTEST_AVAILABLE = True
except ImportError:
    SPEEDTEST_AVAILABLE = False
    print("Speedtest module not available")

# Enhanced speed test providers removed - keeping it simple
ENHANCED_SPEEDTEST_AVAILABLE = False
SIMPLE_SPEEDTEST_AVAILABLE = False
import socket
import ipaddress
import psutil
import requests
from concurrent.futures import ThreadPoolExecutor
# Import notifications with error handling
try:
    from notifications import NotificationManager, check_network_alerts
    NOTIFICATIONS_AVAILABLE = True
except ImportError as e:
    print(f"Notifications module not available: {e}")
    NOTIFICATIONS_AVAILABLE = False

# --- Configuration ---
ROUTER_IP = "10.99.0.1"
INTERNET_HOSTS = [
    {'name': 'Cloudflare', 'ip': '1.1.1.1'},
    {'name': 'Google', 'ip': '8.8.8.8'},
    {'name': 'Quad9', 'ip': '9.9.9.9'}
]
DEVICE_SCAN_INTERVAL = 15  # seconds
GC_INTERVAL = 300  # seconds (5 minutes) - garbage collection interval

# --- Global Variables for Log Rotation ---
LOG_FOLDER = "traces"
current_date = datetime.now().strftime('%Y-%m-%d')
LOG_PING_INTERNAL = os.path.join(LOG_FOLDER, f"internal_ping_{current_date}.log")
LOG_PING_EXTERNAL_TEMPLATE = os.path.join(LOG_FOLDER, "external_ping_{host}_{date}.log")
LOG_TRACERT_INTERNAL = os.path.join(LOG_FOLDER, f"internal_traceroute_{current_date}.log")
LOG_TRACERT_EXTERNAL = os.path.join(LOG_FOLDER, f"external_traceroute_{current_date}.log")
LOG_DEVICES = os.path.join(LOG_FOLDER, f"device_monitor_{current_date}.log")
LOG_TIMEOUTS = os.path.join(LOG_FOLDER, f"timeout_errors_{current_date}.log")

# --- Flask Application Setup ---
app = Flask(__name__)
app.secret_key = 'network_monitor_secret_key_change_in_production'
socketio = SocketIO(app, cors_allowed_origins="*")

# Initialize timing variables
last_gc_time = time.time()
gc_counter = 0

# --- Data queues for real-time updates ---
ping_internal_queue = queue.Queue(maxsize=100)
ping_external_queue = queue.Queue(maxsize=100)
tracert_internal_queue = queue.Queue(maxsize=50)
tracert_external_queue = queue.Queue(maxsize=50)
speed_test_queue = queue.Queue(maxsize=10)
devices_queue = queue.Queue(maxsize=50)

# --- Network Detection Functions ---
def get_network_info():
    """Detect comprehensive network configuration"""
    network_info = {
        'interfaces': [],
        'default_gateway': None,
        'dns_servers': [],
        'public_ip': None,
        'local_ip': None,
        'subnet': None,
        'network_range': None
    }
    
    try:
        # Get network interfaces using psutil
        interfaces = psutil.net_if_addrs()
        for interface_name, addr_list in interfaces.items():
            for addr in addr_list:
                if addr.family == socket.AF_INET and addr.address != '127.0.0.1':
                    network_info['interfaces'].append({
                        'name': interface_name,
                        'ip': addr.address,
                        'netmask': addr.netmask,
                        'broadcast': addr.broadcast,
                        'is_primary': False
                    })

        # Get default gateway using system commands
        system_name = platform.system().lower()
        try:
            if system_name == 'windows':
                # Try ipconfig first (more reliable)
                result = subprocess.run(['ipconfig'], capture_output=True, text=True)
                lines = result.stdout.split('\n')
                for line in lines:
                    if 'Default Gateway' in line and ':' in line:
                        gateway = line.split(':')[1].strip()
                        if gateway and gateway != '':
                            network_info['default_gateway'] = gateway
                            break
                
                # Fallback to route command
                if not network_info['default_gateway']:
                    result = subprocess.run(['route', 'print', '0.0.0.0'], capture_output=True, text=True)
                    lines = result.stdout.split('\n')
                    for line in lines:
                        if '0.0.0.0' in line and 'Gateway' not in line and len(line.split()) >= 3:
                            parts = line.split()
                            gateway = parts[2]
                            if gateway != '0.0.0.0' and '.' in gateway:
                                network_info['default_gateway'] = gateway
                                break
            else:
                result = subprocess.run(['ip', 'route', 'show', 'default'], capture_output=True, text=True)
                if result.returncode == 0:
                    parts = result.stdout.split()
                    if len(parts) >= 3:
                        network_info['default_gateway'] = parts[2]
        except:
            # Fallback method
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                s.connect(("8.8.8.8", 80))
                local_ip = s.getsockname()[0]
                s.close()
                network_info['local_ip'] = local_ip
                
                # Try to determine gateway by common patterns
                ip_parts = local_ip.split('.')
                gateway_ip = f"{ip_parts[0]}.{ip_parts[1]}.{ip_parts[2]}.1"
                network_info['default_gateway'] = gateway_ip
            except:
                pass
            
        # Determine primary interface and local IP
        for interface in network_info['interfaces']:
            if interface['ip'].startswith('192.168.') or interface['ip'].startswith('10.') or interface['ip'].startswith('172.'):
                network_info['local_ip'] = interface['ip']
                network_info['subnet'] = interface['netmask']
                interface['is_primary'] = True
                
                # Calculate network range
                try:
                    network = ipaddress.IPv4Network(f"{interface['ip']}/{interface['netmask']}", strict=False)
                    network_info['network_range'] = str(network)
                except:
                    pass
                break
        
        # Get DNS servers
        try:
            import subprocess
            if platform.system().lower() == 'windows':
                result = subprocess.run(['nslookup', 'google.com'], capture_output=True, text=True)
                lines = result.stdout.split('\n')
                for line in lines:
                    if 'Server:' in line:
                        dns_ip = line.split(':')[-1].strip()
                        if dns_ip and dns_ip != 'Unknown':
                            network_info['dns_servers'].append(dns_ip)
            else:
                with open('/etc/resolv.conf', 'r') as f:
                    for line in f:
                        if line.startswith('nameserver'):
                            dns_ip = line.split()[1]
                            network_info['dns_servers'].append(dns_ip)
        except:
            pass
            
        # Get public IP
        try:
            response = requests.get('https://httpbin.org/ip', timeout=5)
            network_info['public_ip'] = response.json().get('origin')
        except:
            try:
                response = requests.get('https://api.ipify.org?format=json', timeout=5)
                network_info['public_ip'] = response.json().get('ip')
            except:
                pass
                
    except Exception as e:
        print(f"Network detection error: {e}")
    
    return network_info

def advanced_port_scan(target_ip, common_ports=True):
    """Advanced port scanning with basic socket scanning"""
    try:
        scan_result = {
            'host': target_ip,
            'status': 'unknown',
            'open_ports': [],
            'os_info': {},
            'services': []
        }
        
        # Define port lists
        if common_ports:
            ports_to_scan = [21, 22, 23, 25, 53, 80, 110, 135, 139, 143, 443, 993, 995, 3389, 5900, 8080, 8443]
        else:
            ports_to_scan = list(range(1, 1001))  # Top 1000 ports
        
        # Quick ping to check if host is up
        ping_result = ping_single_host(target_ip, timeout=2)
        scan_result['status'] = 'up' if ping_result['alive'] else 'down'
        
        if not ping_result['alive']:
            return scan_result
        
        # Scan ports
        open_ports = []
        with ThreadPoolExecutor(max_workers=50) as executor:
            futures = {executor.submit(scan_single_port, target_ip, port): port for port in ports_to_scan}
            
            for future in futures:
                port = futures[future]
                try:
                    is_open, service_info = future.result()
                    if is_open:
                        open_ports.append(port)
                        scan_result['services'].append({
                            'port': port,
                            'service': service_info.get('service', 'unknown'),
                            'version': service_info.get('version', ''),
                            'product': service_info.get('product', '')
                        })
                except:
                    pass
        
        scan_result['open_ports'] = sorted(open_ports)
        return scan_result
        
    except Exception as e:
        print(f"Port scan error for {target_ip}: {e}")
        return {'host': target_ip, 'status': 'error', 'error': str(e)}

def scan_single_port(ip, port, timeout=1):
    """Scan a single port using socket connection"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        result = sock.connect_ex((ip, port))
        sock.close()
        
        if result == 0:
            # Port is open, try to identify service
            service_info = identify_service(port)
            return True, service_info
        else:
            return False, {}
    except:
        return False, {}

def identify_service(port):
    """Identify common services by port number"""
    services = {
        21: {'service': 'ftp', 'product': 'FTP Server'},
        22: {'service': 'ssh', 'product': 'SSH Server'},
        23: {'service': 'telnet', 'product': 'Telnet Server'},
        25: {'service': 'smtp', 'product': 'SMTP Server'},
        53: {'service': 'dns', 'product': 'DNS Server'},
        80: {'service': 'http', 'product': 'HTTP Server'},
        110: {'service': 'pop3', 'product': 'POP3 Server'},
        135: {'service': 'msrpc', 'product': 'Microsoft RPC'},
        139: {'service': 'netbios-ssn', 'product': 'NetBIOS Session'},
        143: {'service': 'imap', 'product': 'IMAP Server'},
        443: {'service': 'https', 'product': 'HTTPS Server'},
        993: {'service': 'imaps', 'product': 'IMAP over SSL'},
        995: {'service': 'pop3s', 'product': 'POP3 over SSL'},
        3389: {'service': 'rdp', 'product': 'Remote Desktop'},
        5900: {'service': 'vnc', 'product': 'VNC Server'},
        8080: {'service': 'http-alt', 'product': 'HTTP Alternative'},
        8443: {'service': 'https-alt', 'product': 'HTTPS Alternative'}
    }
    
    return services.get(port, {'service': f'port-{port}', 'product': 'Unknown Service'})

def network_discovery_scan():
    """Discover devices on the local network"""
    network_info = get_network_info()
    discovered_devices = []
    
    if not network_info['network_range']:
        # Fallback to common network ranges
        common_ranges = ['192.168.1.0/24', '192.168.0.0/24', '10.0.0.0/24']
        for range_str in common_ranges:
            try:
                network = ipaddress.IPv4Network(range_str)
                print(f"Trying fallback network range: {range_str}")
                break
            except:
                continue
        else:
            print("No network range available for discovery")
            return discovered_devices
    else:
        network = ipaddress.IPv4Network(network_info['network_range'])
    
    try:
        print(f"Starting network discovery scan for {network}")
        # Quick ping sweep with timeout
        with ThreadPoolExecutor(max_workers=20) as executor:  # Reduced workers for stability
            futures = []
            
            host_count = 0
            for ip in network.hosts():
                if str(ip) != network_info.get('local_ip'):  # Skip own IP
                    futures.append(executor.submit(ping_single_host, str(ip), timeout=1))
                    host_count += 1
                    if host_count >= 254:  # Limit scan size
                        break
            
            print(f"Scanning {len(futures)} hosts...")
            for i, future in enumerate(futures):
                try:
                    result = future.result(timeout=5)  # Timeout for individual results
                    if result['alive']:
                        discovered_devices.append(result)
                        print(f"Found device: {result['ip']} ({result['response_time']}ms)")
                except Exception as e:
                    print(f"Error scanning host {i}: {e}")
                    continue
    
    except Exception as e:
        print(f"Network discovery error: {e}")
    
    print(f"Network discovery completed. Found {len(discovered_devices)} devices.")
    return discovered_devices

def ping_single_host(ip, timeout=1):
    """Ping a single host"""
    system_name = platform.system().lower()
    
    try:
        if system_name == "windows":
            cmd = ["ping", "-n", "1", "-w", str(timeout * 1000), ip]
        else:
            cmd = ["ping", "-c", "1", "-W", str(timeout), ip]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout + 1)
        
        return {
            'ip': ip,
            'alive': result.returncode == 0,
            'response_time': extract_ping_time(result.stdout) if result.returncode == 0 else None
        }
    except:
        return {'ip': ip, 'alive': False, 'response_time': None}

def extract_ping_time(ping_output):
    """Extract ping time from ping output"""
    try:
        if 'time=' in ping_output:
            time_str = ping_output.split('time=')[1].split()[0]
            return float(time_str.replace('ms', ''))
        elif 'time<' in ping_output:
            return 1.0
    except:
        pass
    return None

# --- Core Functions ---
def update_log_files():
    """Update global log file variables when date changes"""
    global LOG_PING_INTERNAL, LOG_PING_EXTERNAL, LOG_TRACERT_INTERNAL
    global LOG_TRACERT_EXTERNAL, LOG_DEVICES, LOG_TIMEOUTS, current_date
    
    new_date = datetime.now().strftime('%Y-%m-%d')
    if new_date != current_date:
        with log_rotation_lock:
            current_date = new_date
            LOG_PING_INTERNAL = os.path.join(LOG_FOLDER, f"internal_ping_{current_date}.log")
            LOG_PING_EXTERNAL = os.path.join(LOG_FOLDER, f"external_ping_{current_date}.log")
            LOG_TRACERT_INTERNAL = os.path.join(LOG_FOLDER, f"internal_traceroute_{current_date}.log")
            LOG_TRACERT_EXTERNAL = os.path.join(LOG_FOLDER, f"external_traceroute_{current_date}.log")
            LOG_DEVICES = os.path.join(LOG_FOLDER, f"device_monitor_{current_date}.log")
            LOG_TIMEOUTS = os.path.join(LOG_FOLDER, f"timeout_errors_{current_date}.log")
            print(f"Log rotation: New log files created for {current_date}")

def periodic_garbage_collection():
    """Perform garbage collection if enough time has passed"""
    global last_gc_time, gc_counter
    
    current_time = time.time()
    if current_time - last_gc_time >= GC_INTERVAL:
        gc_counter += 1
        collected = gc.collect()
        last_gc_time = current_time
        
        # Log garbage collection activity
        gc_msg = f"Garbage Collection #{gc_counter}: Collected {collected} objects\n"
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # Write to a system log in traces folder
        gc_log_file = os.path.join(LOG_FOLDER, f"system_gc_{datetime.now().strftime('%Y-%m-%d')}.log")
        with open(gc_log_file, "a", encoding='utf-8') as f:
            f.write(f"[{timestamp}] {gc_msg}")

def append_to_log(filename, data):
    update_log_files()  # Check for date change before logging
    periodic_garbage_collection()  # Perform garbage collection if needed

    # Log rotation check
    try:
        if os.path.exists(filename) and os.path.getsize(filename) > 100 * 1024 * 1024:  # 100 MB
            with log_rotation_lock:
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                os.rename(filename, f"{filename}.{timestamp}")
    except OSError as e:
        print(f"Error rotating log file {filename}: {e}")

    # Get the current filename (might have changed due to date rotation)
    if 'internal_ping' in filename:
        filename = LOG_PING_INTERNAL
    elif 'external_ping' in filename:
        pass  # Filename is now passed in correctly
    elif 'internal_traceroute' in filename:
        filename = LOG_TRACERT_INTERNAL
    elif 'external_traceroute' in filename:
        filename = LOG_TRACERT_EXTERNAL
    elif 'device_monitor' in filename:
        filename = LOG_DEVICES
    elif 'timeout_errors' in filename:
        filename = LOG_TIMEOUTS

    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    with open(filename, "a", encoding='utf-8') as f:
        f.write(f"[{timestamp}] {data}")

    # Log only external ping timeouts to the separate file
    if ("Request timed out" in data or "Request timeout" in data) and 'external_ping' in filename:
        with open(LOG_TIMEOUTS, "a", encoding='utf-8') as f_timeout:
            f_timeout.write(f"[{timestamp}] {os.path.basename(filename)}: {data}")

def add_to_queue(queue_obj, data, max_size=100):
    """Add data to queue with size limit"""
    try:
        if queue_obj.full():
            queue_obj.get_nowait()  # Remove oldest item
        queue_obj.put_nowait(data)
    except:
        pass

# --- Monitoring Functions ---
def ping_monitor(host, label, log_file, data_queue):
    """Monitor ping in background thread"""
    system_name = platform.system().lower()
    
    if system_name == "windows":
        ping_cmd = ["ping", "-t", host]
    elif system_name == "darwin":  # macOS
        ping_cmd = ["ping", host]
    else:  # Linux and others
        ping_cmd = ["ping", host]

    while True:
        try:
            process = subprocess.Popen(ping_cmd, 
                                     stdout=subprocess.PIPE, 
                                     stderr=subprocess.STDOUT, 
                                     text=True, 
                                     universal_newlines=True, 
                                     bufsize=1)

            for line in iter(process.stdout.readline, ''):
                if line.strip() == "" or "Pinging" in line or "64 bytes" in line:
                    continue

                log_line = f"{datetime.now().strftime('%H:%M:%S')}: {line.strip()}\n"
                append_to_log(log_file, log_line)
                
                # Add to queue for real-time display
                log_entry = {
                    'timestamp': datetime.now().strftime('%H:%M:%S'),
                    'data': line.strip(),
                    'type': 'ping',
                    'host': host,
                    'label': label
                }
                add_to_queue(data_queue, log_entry)
                
                # Emit to connected clients
                socketio.emit(f'ping_update_{label.lower().replace("_", "_")}', log_entry)
                
                # Reload settings to get the latest ping interval
                settings_file = os.path.join(LOG_FOLDER, 'app_settings.json')
                ping_interval = 5  # Default
                if os.path.exists(settings_file):
                    with open(settings_file, 'r') as f:
                        try:
                            settings = json.load(f)
                            ping_interval = settings.get('ping_interval', 5)
                        except json.JSONDecodeError:
                            pass
                time.sleep(ping_interval)

            process.stdout.close()
            process.wait()
        except Exception as e:
            print(f"Ping monitor error for {label}: {e}")
            time.sleep(5)

def traceroute_monitor(host, label, log_file, data_queue):
    """Monitor traceroute in background thread"""
    system_name = platform.system().lower()
    
    if system_name == "windows":
        tracert_cmd = ["tracert", "-d", host]
    elif system_name == "darwin":  # macOS
        tracert_cmd = ["traceroute", "-n", host]
    else:  # Linux and others
        tracert_cmd = ["traceroute", "-n", host]
    
    while True:
        # For internal traceroute, check if host is reachable first
        if "INTERNAL" in label:
            # Quick ping test to see if internal host is reachable
            ping_result = ping_single_host(host, timeout=2)
            if not ping_result['alive']:
                error_msg = f"Internal host {host} is not reachable. Traceroute disabled.\n"
                append_to_log(log_file, error_msg)
                
                log_entry = {
                    'timestamp': datetime.now().strftime('%H:%M:%S'),
                    'data': f"Error: Host {host} is not reachable via ping. Traceroute disabled.",
                    'type': 'traceroute',
                    'host': host,
                    'label': label
                }
                add_to_queue(data_queue, log_entry)
                socketio.emit(f'traceroute_update_{label.lower().replace("_", "_")}', log_entry)
                
                # Wait longer before next attempt for internal traceroute
                time.sleep(30)
                continue
        try:
            start_time = datetime.now()
            log_header = f"\n--- Traceroute started at {start_time.strftime('%Y-%m-%d %H:%M:%S')} ---\n"
            append_to_log(log_file, log_header)
            
            # Emit start message
            start_entry = {
                'timestamp': datetime.now().strftime('%H:%M:%S'),
                'data': f"Traceroute started to {host}",
                'type': 'traceroute',
                'host': host,
                'label': label
            }
            add_to_queue(data_queue, start_entry)
            socketio.emit(f'traceroute_update_{label.lower().replace("_", "_")}', start_entry)
            
            process = subprocess.Popen(tracert_cmd, 
                                     stdout=subprocess.PIPE, 
                                     stderr=subprocess.STDOUT, 
                                     text=True, 
                                     universal_newlines=True)
            
            for line in iter(process.stdout.readline, ''):
                if line.strip():
                    append_to_log(log_file, line)
                    
                    log_entry = {
                        'timestamp': datetime.now().strftime('%H:%M:%S'),
                        'data': line.strip(),
                        'type': 'traceroute',
                        'host': host,
                        'label': label
                    }
                    add_to_queue(data_queue, log_entry)
                    socketio.emit(f'traceroute_update_{label.lower().replace("_", "_")}', log_entry)
            
            process.stdout.close()
            process.wait()
        except Exception as e:
            error_msg = f"Traceroute command failed: {e}\n"
            append_to_log(log_file, error_msg)
            print(f"Traceroute monitor error for {label}: {e}")
        
        time.sleep(1)

def run_speed_test(provider='ookla', server_id=None):
    """Run an internet speed test in a background thread."""
    try:
        socketio.emit('speed_test_update', {'status': 'starting', 'message': 'Initializing speed test...'})
        
        # Create speedtest instance with timeout and error handling
        st = speedtest.Speedtest(timeout=30)
        
        socketio.emit('speed_test_update', {'status': 'server', 'message': 'Finding servers...'})
        
        # Check if we should use simple HTTP test
        if provider == 'simple' and SIMPLE_SPEEDTEST_AVAILABLE:
            try:
                def callback(data):
                    socketio.emit('speed_test_update', data)
                
                results = simple_speed_test.run_full_test(callback)
                
                # Log results
                log_file = os.path.join(LOG_FOLDER, f"speed_tests_{current_date}.log")
                append_to_log(log_file, json.dumps(results) + '\n')
                return
            except Exception as simple_error:
                print(f"Simple speed test failed: {simple_error}")
                socketio.emit('speed_test_update', {
                    'status': 'error', 
                    'message': f'Simple HTTP test failed: {str(simple_error)}'
                })
                return
        
        # Check if we should use enhanced speed test
        elif ENHANCED_SPEEDTEST_AVAILABLE and provider != 'ookla':
            try:
                # Use enhanced speed test system
                def callback(data):
                    socketio.emit('speed_test_update', data)
                
                results = speed_test_manager.run_speed_test(provider, server_id, callback)
                
                # Log results
                log_file = os.path.join(LOG_FOLDER, f"speed_tests_{current_date}.log")
                append_to_log(log_file, json.dumps(results) + '\n')
                return
            except Exception as enhanced_error:
                print(f"Enhanced speed test failed for {provider}: {enhanced_error}")
                socketio.emit('speed_test_update', {
                    'status': 'warning', 
                    'message': f'{provider.title()} provider failed, trying Ookla fallback...'
                })
                # Continue to Ookla fallback
            
        # Use Ookla speedtest
        if server_id and server_id.isdigit():
            try:
                # Use specific server with better error handling
                server_id_int = int(server_id)
                servers = st.get_servers([server_id_int])
                if server_id_int in servers and servers[server_id_int]:
                    st.results.server = servers[server_id_int][0]
                else:
                    raise ValueError("Server not found")
            except Exception as server_error:
                print(f"Server selection error: {server_error}, falling back to best server")
                socketio.emit('speed_test_update', {'status': 'server', 'message': 'Selected server unavailable, finding best server...'})
                st.get_best_server()
        else:
            # Use best server
            st.get_best_server()
        
        server_info = st.results.server
        socketio.emit('speed_test_update', {'status': 'server_found', 'server': server_info})

        socketio.emit('speed_test_update', {'status': 'downloading', 'message': 'Measuring download speed...'})
        st.download()
        download_speed = st.results.download / 1_000_000  # Convert to Mbps
        socketio.emit('speed_test_update', {
            'status': 'download_complete', 
            'download_speed': download_speed,
            'message': f'Download speed: {download_speed:.2f} Mbps'
        })

        socketio.emit('speed_test_update', {'status': 'uploading', 'message': 'Measuring upload speed...'})
        st.upload()
        upload_speed = st.results.upload / 1_000_000  # Convert to Mbps
        socketio.emit('speed_test_update', {
            'status': 'upload_complete', 
            'upload_speed': upload_speed,
            'message': f'Upload speed: {upload_speed:.2f} Mbps'
        })

        results = {
            'download': st.results.download,
            'upload': st.results.upload,
            'ping': st.results.ping,
            'download_mbps': download_speed,
            'upload_mbps': upload_speed,
            'server': st.results.server
        }
        
        socketio.emit('speed_test_update', {
            'status': 'finished', 
            'results': results,
            'message': f'Speed test completed! Download: {download_speed:.2f} Mbps, Upload: {upload_speed:.2f} Mbps'
        })
        
        # Log results
        log_file = os.path.join(LOG_FOLDER, f"speed_tests_{current_date}.log")
        append_to_log(log_file, json.dumps(results) + '\n')

    except Exception as e:
        error_str = str(e)
        print(f"Primary speed test failed: {error_str}")
        
        # Try simple HTTP speed test as last resort
        if SIMPLE_SPEEDTEST_AVAILABLE:
            try:
                socketio.emit('speed_test_update', {
                    'status': 'fallback', 
                    'message': 'Primary speed test failed, trying simple HTTP test...'
                })
                
                def callback(data):
                    socketio.emit('speed_test_update', data)
                
                results = simple_speed_test.run_full_test(callback)
                
                # Log results
                log_file = os.path.join(LOG_FOLDER, f"speed_tests_{current_date}.log")
                append_to_log(log_file, json.dumps(results) + '\n')
                return
                
            except Exception as simple_error:
                print(f"Simple speed test also failed: {simple_error}")
        
        # If all methods fail, provide helpful error message
        if "HTTP Error 403" in error_str or "36223" in error_str:
            error_message = "All speed test methods blocked by firewall. Please check network settings or try from a different network."
        elif "timeout" in error_str.lower() or "timed out" in error_str.lower():
            error_message = "Speed test timed out. Please check your internet connection and try again."
        elif "connection" in error_str.lower() or "network" in error_str.lower():
            error_message = "Cannot connect to any speed test servers. Please check your internet connectivity."
        else:
            error_message = f"All speed test methods failed. Error: {error_str}"
        
        print(f"Final speed test error: {error_message}")
        socketio.emit('speed_test_update', {'status': 'error', 'message': error_message})

def device_monitor():
    """Monitor devices in background thread"""
    known_devices = set()
    system_name = platform.system().lower()
    
    while True:
        try:
            if system_name == "windows":
                result = subprocess.run(["arp", "-a"], capture_output=True, text=True, timeout=10)
                # Convert Windows format (XX-XX-XX) to standard format (XX:XX:XX)
                devices_raw = re.findall(r"(\d+\.\d+\.\d+\.\d+)\s+([0-9a-fA-F-]+)", result.stdout)
                current_devices = set((ip, mac.replace('-', ':')) for ip, mac in devices_raw)
            elif system_name == "darwin":  # macOS
                result = subprocess.run(["arp", "-a"], capture_output=True, text=True, timeout=10)
                current_devices = set(re.findall(r"(\d+\.\d+\.\d+\.\d+)\s+at\s+([0-9a-fA-F:]+)", result.stdout))
            else:  # Linux
                result = subprocess.run(["arp", "-a"], capture_output=True, text=True, timeout=10)
                current_devices = set(re.findall(r"(\d+\.\d+\.\d+\.\d+)\s+.*?([0-9a-fA-F:]+)", result.stdout))
            new_devices = current_devices - known_devices
            
            if new_devices:
                log_entry = f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}: NEW DEVICES DETECTED\n"
                for device in new_devices:
                    log_entry += f"  - IP: {device[0]}, MAC: {device[1]}\n"
                append_to_log(LOG_DEVICES, log_entry)
            
            known_devices = current_devices
            
            # Prepare device data for web display
            device_list = []
            for ip, mac in sorted(list(current_devices)):
                is_new = (ip, mac) in new_devices
                device_list.append({
                    'ip': ip,
                    'mac': mac,
                    'is_new': is_new,
                    'timestamp': datetime.now().strftime('%H:%M:%S')
                })
            
            # Add to queue and emit
            device_data = {
                'timestamp': datetime.now().strftime('%H:%M:%S'),
                'devices': device_list,
                'total_count': len(device_list),
                'new_devices': len(new_devices)
            }
            add_to_queue(devices_queue, device_data)
            socketio.emit('devices_update', device_data)
            
        except Exception as e:
            append_to_log(LOG_DEVICES, f"Device scan failed: {e}\n")
            print(f"Device monitor error: {e}")
        
        time.sleep(DEVICE_SCAN_INTERVAL)

# --- Flask Routes ---
@app.route('/')
def home():
    return render_template('home.html')

@app.route('/internal')
def internal_ping():
    return render_template('ping.html', 
                         title='Internal Ping Monitor', 
                         host=ROUTER_IP, 
                         type='internal')

@app.route('/external')
def external_ping():
    return render_template('public_monitoring.html', 
                         title='External Ping Monitor', 
                         hosts=INTERNET_HOSTS, 
                         monitor_type='ping')

@app.route('/traceroute-internal')
def traceroute_internal():
    return render_template('traceroute.html', 
                         title='Internal Traceroute', 
                         host=ROUTER_IP, 
                         type='internal')

@app.route('/traceroute-external')
def traceroute_external():
    return render_template('public_monitoring.html', 
                         title='External Traceroute', 
                         hosts=INTERNET_HOSTS, 
                         monitor_type='traceroute')

@app.route('/devices')
def devices():
    return render_template('devices.html')

@app.route('/speed-test')
def speed_test():
    return render_template('speed_test.html')

@app.route('/downloads')
def downloads():
    return render_template('log_download.html')

@app.route('/timeouts')
def timeouts():
    return render_template('timeouts.html')

@app.route('/network-info')
def network_info():
    return render_template('network_info.html')

@app.route('/port-scanner')
def port_scanner():
    return render_template('port_scanner.html')

@app.route('/network-discovery')
def network_discovery():
    return render_template('network_discovery.html')

@app.route('/advanced-monitoring')
def advanced_monitoring():
    return render_template('advanced_monitoring.html')

@app.route('/api/logs/<log_type>')
def get_logs(log_type):
    """API endpoint to get recent log entries"""
    try:
        log_files = {
            'internal_ping': LOG_PING_INTERNAL,
            'external_ping': LOG_PING_EXTERNAL,
            'internal_tracert': LOG_TRACERT_INTERNAL,
            'external_tracert': LOG_TRACERT_EXTERNAL,
            'devices': LOG_DEVICES,
            'timeouts': LOG_TIMEOUTS
        }
        
                # Handle dynamic external log files
        if log_type.startswith('external_ping_'):
            host_name = log_type.replace('external_ping_', '')
            log_files[log_type] = LOG_PING_EXTERNAL_TEMPLATE.format(host=host_name, date=current_date)

        if log_type not in log_files:
            return jsonify({'error': 'Invalid log type'}), 400
        
        log_file = log_files[log_type]
        lines = []
        
        if os.path.exists(log_file):
            with open(log_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()[-100:]  # Get last 100 lines
        
        return jsonify({
            'log_type': log_type,
            'lines': [line.strip() for line in lines],
            'count': len(lines)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/ping-stats/<log_type>')
def get_ping_stats(log_type):
    """Calculate ping statistics from log files."""
    try:
        log_files = {
            'internal': LOG_PING_INTERNAL,
            'Cloudflare': LOG_PING_EXTERNAL_TEMPLATE.format(host='Cloudflare', date=current_date),
            'Google': LOG_PING_EXTERNAL_TEMPLATE.format(host='Google', date=current_date),
            'Quad9': LOG_PING_EXTERNAL_TEMPLATE.format(host='Quad9', date=current_date),
        }
        log_file = log_files.get(log_type)

        if not log_file or not os.path.exists(log_file):
            return jsonify({
                'packets_sent': 0,
                'packets_received': 0,
                'packet_loss': 0,
                'avg_latency': 0
            })

        packets_sent = 0
        packets_received = 0
        latencies = []

        with open(log_file, 'r', encoding='utf-8') as f:
            for line in f:
                # Only count lines that contain actual ping results
                if 'Reply from' in line or 'bytes from' in line or 'Request timed out' in line or 'timeout' in line:
                    packets_sent += 1
                    
                    if 'Reply from' in line or 'bytes from' in line:
                        packets_received += 1
                        latency = extract_ping_time(line)
                        if latency:
                            latencies.append(latency)
        
        packet_loss = ((packets_sent - packets_received) / packets_sent * 100) if packets_sent > 0 else 0
        avg_latency = sum(latencies) / len(latencies) if latencies else 0

        return jsonify({
            'packets_sent': packets_sent,
            'packets_received': packets_received,
            'packet_loss': round(packet_loss, 2),
            'avg_latency': round(avg_latency, 2)
        })

    except Exception as e:
        print(f"Error in ping stats for {log_type}: {e}")
        return jsonify({
            'packets_sent': 0,
            'packets_received': 0,
            'packet_loss': 0,
            'avg_latency': 0
        })

@app.route('/api/download-logs')
def download_logs():
    start_date_str = request.args.get('start')
    end_date_str = request.args.get('end')

    if not start_date_str or not end_date_str:
        return jsonify({'error': 'Start and end dates are required'}), 400

    try:
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d')
        
        memory_file = io.BytesIO()
        with zipfile.ZipFile(memory_file, 'w', zipfile.ZIP_DEFLATED) as zf:
            for filename in os.listdir(LOG_FOLDER):
                try:
                    # Extract date from filename like 'internal_ping_2025-10-05.log'
                    file_date_str = re.search(r'(\d{4}-\d{2}-\d{2})', filename)
                    if file_date_str:
                        file_date = datetime.strptime(file_date_str.group(1), '%Y-%m-%d')
                        if start_date <= file_date <= end_date:
                            zf.write(os.path.join(LOG_FOLDER, filename), arcname=filename)
                except (ValueError, IndexError):
                    continue # Ignore files that don't match the date format

        memory_file.seek(0)
        return send_file(memory_file, 
                         download_name=f'network_logs_{start_date_str}_to_{end_date_str}.zip', 
                         as_attachment=True)

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/speed-test-servers')
def get_speed_test_servers():
    """Get available speed test servers"""
    try:
        provider = request.args.get('provider', 'ookla')
        
        if ENHANCED_SPEEDTEST_AVAILABLE and provider != 'ookla':
            # Use enhanced speed test system for non-Ookla providers
            servers = speed_test_manager.get_provider_servers(provider)
            return jsonify({'servers': servers})
        
        # Default Ookla behavior
        if not SPEEDTEST_AVAILABLE:
            return jsonify({'error': 'Speedtest not available', 'servers': []}), 500
            
        st = speedtest.Speedtest()
        servers = st.get_servers()
        server_list = []
        
        for server_id, server_data in servers.items():
            for server in server_data[:5]:  # Limit to 5 servers per location
                server_list.append({
                    'id': server['id'],
                    'name': server['name'],
                    'sponsor': server['sponsor'],
                    'country': server['country'],
                    'distance': round(server['d'], 2),
                    'provider': 'ookla'
                })
        
        # Sort by distance and limit to 10
        server_list.sort(key=lambda x: x['distance'])
        return jsonify({'servers': server_list[:10]})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/network-info')
def api_network_info():
    """Get comprehensive network information"""
    try:
        info = get_network_info()
        return jsonify(info)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/port-scan', methods=['POST'])
def api_port_scan():
    """Perform port scan on target"""
    try:
        data = request.get_json()
        target_ip = data.get('target_ip')
        scan_type = data.get('scan_type', 'common')
        
        if not target_ip:
            return jsonify({'error': 'Target IP required'}), 400
            
        result = advanced_port_scan(target_ip, scan_type == 'common')
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/advanced-scan', methods=['POST'])
def advanced_scan():
    """Perform an advanced network scan."""
    try:
        data = request.get_json()
        ip_range = data.get('ip_range')
        ports = [int(p.strip()) for p in data.get('port_range', '').split(',') if p.strip()]
        os_detection = data.get('os_detection')

        if not ip_range or not ports:
            return jsonify({'error': 'IP range and ports are required'}), 400

        def scan_host(ip):
            ping_res = ping_single_host(ip, timeout=1)
            if ping_res['alive']:
                open_ports = []
                for port in ports:
                    is_open, service_info = scan_single_port(ip, port, timeout=0.5)
                    if is_open:
                        open_ports.append({'port': port, 'service': service_info})
                if open_ports:
                    socketio.emit('advanced_scan_update', {'ip': ip, 'status': 'open', 'ports': open_ports})

        network = ipaddress.ip_network(ip_range, strict=False)
        with ThreadPoolExecutor(max_workers=50) as executor:
            for ip in network.hosts():
                executor.submit(scan_host, str(ip))
        
        return jsonify({'message': 'Scan initiated'})

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/network-discovery')
def api_network_discovery():
    """Discover devices on local network"""
    try:
        devices = network_discovery_scan()
        return jsonify({'devices': devices})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/logs/filtered/<log_type>')
def get_filtered_logs(log_type):
    """Get filtered logs by date range"""
    try:
        start_date = request.args.get('start')
        end_date = request.args.get('end')
        start_time = request.args.get('start_time', '00:00')
        end_time = request.args.get('end_time', '23:59')
        
        if not start_date or not end_date:
            return jsonify({'error': 'Start and end dates required'}), 400
        
        # Parse dates
        start_datetime = datetime.strptime(f"{start_date} {start_time}", '%Y-%m-%d %H:%M')
        end_datetime = datetime.strptime(f"{end_date} {end_time}", '%Y-%m-%d %H:%M')
        
        filtered_lines = []
        
        # Search through log files in date range
        current_date = start_datetime.date()
        while current_date <= end_datetime.date():
            date_str = current_date.strftime('%Y-%m-%d')
            
            # Construct possible log file names
            possible_files = []
            if log_type == 'timeouts':
                possible_files.append(os.path.join(LOG_FOLDER, f"timeout_errors_{date_str}.log"))
            elif log_type == 'internal_ping':
                possible_files.append(os.path.join(LOG_FOLDER, f"internal_ping_{date_str}.log"))
            elif log_type == 'external_ping':
                # Multiple external ping files
                for host in ['Cloudflare', 'Google', 'Quad9']:
                    possible_files.append(os.path.join(LOG_FOLDER, f"external_ping_{host}_{date_str}.log"))
            
            for log_file in possible_files:
                if os.path.exists(log_file):
                    try:
                        with open(log_file, 'r', encoding='utf-8') as f:
                            for line in f:
                                # Parse timestamp from line
                                if line.startswith('['):
                                    try:
                                        timestamp_str = line[1:20]  # [YYYY-MM-DD HH:MM:SS]
                                        line_datetime = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')
                                        
                                        if start_datetime <= line_datetime <= end_datetime:
                                            filtered_lines.append(line.strip())
                                    except:
                                        continue
                    except:
                        continue
            
            current_date += timedelta(days=1)
        
        return jsonify({
            'log_type': log_type,
            'lines': filtered_lines[-1000:],  # Limit to last 1000 lines
            'count': len(filtered_lines),
            'date_range': f"{start_date} {start_time} to {end_date} {end_time}"
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/system-stats')
def api_system_stats():
    """Get comprehensive system statistics"""
    try:
        stats = {
            'cpu': {
                'usage_percent': psutil.cpu_percent(interval=1),
                'count': psutil.cpu_count(),
                'frequency': psutil.cpu_freq()._asdict() if psutil.cpu_freq() else {}
            },
            'memory': {
                'total': psutil.virtual_memory().total,
                'available': psutil.virtual_memory().available,
                'percent': psutil.virtual_memory().percent,
                'used': psutil.virtual_memory().used
            },
            'disk': {
                'total': psutil.disk_usage('/').total,
                'used': psutil.disk_usage('/').used,
                'free': psutil.disk_usage('/').free,
                'percent': psutil.disk_usage('/').percent
            },
            'network': {
                'bytes_sent': psutil.net_io_counters().bytes_sent,
                'bytes_recv': psutil.net_io_counters().bytes_recv,
                'packets_sent': psutil.net_io_counters().packets_sent,
                'packets_recv': psutil.net_io_counters().packets_recv
            },
            'processes': len(psutil.pids()),
            'boot_time': psutil.boot_time(),
            'uptime': time.time() - psutil.boot_time()
        }
        return jsonify(stats)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/test-notifications', methods=['POST'])
def test_notifications():
    """Test notification systems"""
    if not NOTIFICATIONS_AVAILABLE:
        return jsonify({'success': False, 'error': 'Notifications module not available'}), 500
    
    try:
        notifier = NotificationManager()
        results = notifier.test_notifications()
        return jsonify({'success': True, 'message': 'Notification test completed', 'results': results})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/send-alert', methods=['POST'])
def send_alert():
    """Send a manual alert notification"""
    if not NOTIFICATIONS_AVAILABLE:
        return jsonify({'success': False, 'error': 'Notifications module not available'}), 500
    
    try:
        data = request.get_json()
        title = data.get('title', 'Manual Alert')
        message = data.get('message', 'Test alert from network monitor')
        severity = data.get('severity', 'INFO')
        
        notifier = NotificationManager()
        results = notifier.send_notification(title, message, severity)
        return jsonify({'success': True, 'results': results})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/settings', methods=['GET', 'POST'])
def settings_api():
    """Get or save application settings"""
    settings_file = os.path.join(LOG_FOLDER, 'app_settings.json')
    
    if request.method == 'POST':
        try:
            settings = request.get_json()
            with open(settings_file, 'w') as f:
                json.dump(settings, f, indent=2)
            return jsonify({'success': True, 'message': 'Settings saved successfully'})
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 500
    
    else:  # GET
        try:
            if os.path.exists(settings_file):
                with open(settings_file, 'r') as f:
                    settings = json.load(f)
            else:
                # Default settings
                settings = {
                    'ping_interval': 5,
                    'device_interval': 15,
                    'auto_restart': True,
                    'auto_alert': True,
                    'auto_optimize': True,
                    'alert_email': '',
                    'max_log_size': 100,
                    'auto_discovery': True,
                    'scan_timeout': 30
                }
            return jsonify(settings)
        except Exception as e:
            return jsonify({'error': str(e)}), 500

@app.route('/api/gc')
def manual_gc():
    """Manual garbage collection endpoint"""
    collected = gc.collect()
    return jsonify({
        'collected': collected,
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    })

# --- SocketIO Events ---
@socketio.on('connect')
def handle_connect():
    print('Client connected')
    emit('status', {'msg': 'Connected to Network Monitor'})

@socketio.on('run_speed_test')
def handle_run_speed_test(data=None):
    if data:
        server_id = data.get('server_id')
        provider = data.get('provider', 'ookla')
    else:
        server_id = None
        provider = 'ookla'
    
    print(f"Received request to run speed test with provider: {provider}, server: {server_id}")
    socketio.start_background_task(run_speed_test, provider, server_id)

@socketio.on('disconnect')
def handle_disconnect():
    print('Client disconnected')

def start_monitoring_threads():
    """Start all monitoring threads"""
    print("Starting monitoring threads...")
    
    # Auto-detect network configuration
    network_info = get_network_info()
    global ROUTER_IP
    print(f"🔍 Network detection result: {network_info}")
    if network_info.get('default_gateway'):
        ROUTER_IP = network_info['default_gateway']
        print(f"🌐 Auto-detected gateway: {ROUTER_IP}")
        
        # Test if gateway is reachable
        ping_result = ping_single_host(ROUTER_IP, timeout=3)
        if ping_result['alive']:
            print(f"✅ Gateway {ROUTER_IP} is reachable ({ping_result['response_time']}ms)")
        else:
            print(f"⚠️  Gateway {ROUTER_IP} is not reachable - internal monitoring may be limited")
    else:
        print(f"⚠️  Could not detect gateway. Using default: {ROUTER_IP}")
    
    # Create traces folder if it doesn't exist
    if not os.path.exists(LOG_FOLDER):
        os.makedirs(LOG_FOLDER)
        print(f"Created '{LOG_FOLDER}' folder for log files.")
    
    # Enable garbage collection
    gc.enable()
    print(f"Garbage collection enabled. Initial collection freed {gc.collect()} objects.")
    
    # Start monitoring threads
    threads = [
        threading.Thread(target=ping_monitor, 
                        args=(ROUTER_IP, "INTERNAL", LOG_PING_INTERNAL, ping_internal_queue), 
                        daemon=True),
        threading.Thread(target=traceroute_monitor, 
                        args=(ROUTER_IP, "INTERNAL", LOG_TRACERT_INTERNAL, tracert_internal_queue), 
                        daemon=True),
        threading.Thread(target=device_monitor, daemon=True)
    ]

    # Dynamically create threads for each public host
    for host_info in INTERNET_HOSTS:
        host_name = host_info['name']
        host_ip = host_info['ip']
        
        # Ping monitor thread
        ping_log_file = LOG_PING_EXTERNAL_TEMPLATE.format(host=host_name, date=current_date)
        threads.append(threading.Thread(
            target=ping_monitor, 
            args=(host_ip, f"EXTERNAL_{host_name.upper()}", ping_log_file, ping_external_queue), 
            daemon=True))
        
        # Traceroute monitor thread
        tracert_log_file = os.path.join(LOG_FOLDER, f"external_traceroute_{host_name}_{current_date}.log")
        threads.append(threading.Thread(
            target=traceroute_monitor, 
            args=(host_ip, f"EXTERNAL_{host_name.upper()}", tracert_log_file, tracert_external_queue), 
            daemon=True))
    
    for t in threads:
        t.start()
    
    print("All monitoring threads started successfully!")

if __name__ == '__main__':
    print("Initializing Network Monitor Web Application...")
    print(f"Memory Management: Garbage collection runs every {GC_INTERVAL//60} minutes.")
    
    start_monitoring_threads()
    
    # Run the Flask-SocketIO application
        # Note: For Windows development, we can't use Gunicorn.
    # The Makefile handles Gunicorn for Linux production.
    socketio.run(app, host='0.0.0.0', port=5000, debug=False, allow_unsafe_werkzeug=True)
