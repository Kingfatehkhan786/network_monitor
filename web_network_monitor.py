#!/usr/bin/env python3
import subprocess
import time
import platform
import threading
import re
import os
import gc
import json
from datetime import datetime
from flask import Flask, render_template, jsonify, request, Response
from flask_socketio import SocketIO, emit
import queue

# --- Configuration ---
ROUTER_IP = "10.99.0.1"
INTERNET_HOST = "1.1.1.1"
DEVICE_SCAN_INTERVAL = 15  # seconds
GC_INTERVAL = 300  # seconds (5 minutes) - garbage collection interval

# --- Global Variables for Log Rotation ---
LOG_FOLDER = "traces"
current_date = datetime.now().strftime('%Y-%m-%d')
LOG_PING_INTERNAL = os.path.join(LOG_FOLDER, f"internal_ping_{current_date}.log")
LOG_PING_EXTERNAL = os.path.join(LOG_FOLDER, f"external_ping_{current_date}.log")
LOG_TRACERT_INTERNAL = os.path.join(LOG_FOLDER, f"internal_traceroute_{current_date}.log")
LOG_TRACERT_EXTERNAL = os.path.join(LOG_FOLDER, f"external_traceroute_{current_date}.log")
LOG_DEVICES = os.path.join(LOG_FOLDER, f"device_monitor_{current_date}.log")
LOG_TIMEOUTS = os.path.join(LOG_FOLDER, f"timeout_errors_{current_date}.log")

# --- Flask Application Setup ---
app = Flask(__name__)
app.config['SECRET_KEY'] = 'network_monitor_secret_key_2025'
socketio = SocketIO(app, cors_allowed_origins="*")

# --- Locks for thread safety ---
log_rotation_lock = threading.Lock()

# --- Garbage Collection Variables ---
last_gc_time = time.time()
gc_counter = 0

# --- Data queues for real-time updates ---
ping_internal_queue = queue.Queue(maxsize=100)
ping_external_queue = queue.Queue(maxsize=100)
tracert_internal_queue = queue.Queue(maxsize=50)
tracert_external_queue = queue.Queue(maxsize=50)
devices_queue = queue.Queue(maxsize=50)

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
    
    # Get the current filename (might have changed due to date rotation)
    if 'internal_ping' in filename:
        filename = LOG_PING_INTERNAL
    elif 'external_ping' in filename:
        filename = LOG_PING_EXTERNAL
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
            f_timeout.write(f"[{timestamp}] {data}")

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
    is_windows = platform.system().lower() == "windows"
    ping_cmd = "ping"
    ping_params = ["-t", host] if is_windows else [host]

    while True:
        try:
            process = subprocess.Popen([ping_cmd] + ping_params, 
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
                socketio.emit(f'ping_update_{label.lower()}', log_entry)
                
                if not is_windows:
                    time.sleep(1)

            process.stdout.close()
            process.wait()
        except Exception as e:
            print(f"Ping monitor error for {label}: {e}")
            time.sleep(5)

def traceroute_monitor(host, label, log_file, data_queue):
    """Monitor traceroute in background thread"""
    is_windows = platform.system().lower() == "windows"
    tracert_cmd = "tracert" if is_windows else "traceroute"
    tracert_param = "-d" if is_windows else "-n"
    
    while True:
        try:
            start_time = datetime.now()
            log_header = f"\n--- Traceroute started at {start_time.strftime('%Y-%m-%d %H:%M:%S')} ---\n"
            append_to_log(log_file, log_header)
            
            process = subprocess.Popen([tracert_cmd, tracert_param, host], 
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
                    socketio.emit(f'tracert_update_{label.lower()}', log_entry)
            
            process.stdout.close()
            process.wait()
        except Exception as e:
            error_msg = f"Traceroute command failed: {e}\n"
            append_to_log(log_file, error_msg)
            print(f"Traceroute monitor error for {label}: {e}")
        
        time.sleep(1)

def device_monitor():
    """Monitor devices in background thread"""
    known_devices = set()
    
    while True:
        try:
            result = subprocess.run(["arp", "-a"], capture_output=True, text=True, timeout=10)
            current_devices = set(re.findall(r"(\d+\.\d+\.\d+\.\d+)\s+([0-9a-fA-F-]+)", result.stdout))
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
    return render_template('ping.html', 
                         title='External Ping Monitor', 
                         host=INTERNET_HOST, 
                         type='external')

@app.route('/traceroute-internal')
def traceroute_internal():
    return render_template('traceroute.html', 
                         title='Internal Traceroute', 
                         host=ROUTER_IP, 
                         type='internal')

@app.route('/traceroute-external')
def traceroute_external():
    return render_template('traceroute.html', 
                         title='External Traceroute', 
                         host=INTERNET_HOST, 
                         type='external')

@app.route('/devices')
def devices():
    return render_template('devices.html')

@app.route('/timeouts')
def timeouts():
    return render_template('timeouts.html')

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

@socketio.on('disconnect')
def handle_disconnect():
    print('Client disconnected')

def start_monitoring_threads():
    """Start all monitoring threads"""
    print("Starting monitoring threads...")
    
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
        threading.Thread(target=ping_monitor, 
                        args=(INTERNET_HOST, "EXTERNAL", LOG_PING_EXTERNAL, ping_external_queue), 
                        daemon=True),
        threading.Thread(target=traceroute_monitor, 
                        args=(ROUTER_IP, "INTERNAL", LOG_TRACERT_INTERNAL, tracert_internal_queue), 
                        daemon=True),
        threading.Thread(target=traceroute_monitor, 
                        args=(INTERNET_HOST, "EXTERNAL", LOG_TRACERT_EXTERNAL, tracert_external_queue), 
                        daemon=True),
        threading.Thread(target=device_monitor, daemon=True)
    ]
    
    for t in threads:
        t.start()
    
    print("All monitoring threads started successfully!")

if __name__ == '__main__':
    print("Initializing Network Monitor Web Application...")
    print(f"Memory Management: Garbage collection runs every {GC_INTERVAL//60} minutes.")
    
    start_monitoring_threads()
    
    # Run the Flask-SocketIO application
    socketio.run(app, host='0.0.0.0', port=5000, debug=False)
