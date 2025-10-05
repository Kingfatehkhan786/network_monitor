import subprocess
import time
import platform
import threading
import curses
import re
import os
import gc
from datetime import datetime

# --- Configuration ---
ROUTER_IP = "10.99.0.1"
INTERNET_HOST = "1.1.1.1"
DEVICE_SCAN_INTERVAL = 15 # seconds
GC_INTERVAL = 300 # seconds (5 minutes) - garbage collection interval

# --- Global Variables for Log Rotation ---
LOG_FOLDER = "traces"
current_date = datetime.now().strftime('%Y-%m-%d')
LOG_PING_INTERNAL = os.path.join(LOG_FOLDER, f"internal_ping_{current_date}.log")
LOG_PING_EXTERNAL = os.path.join(LOG_FOLDER, f"external_ping_{current_date}.log")
LOG_TRACERT_INTERNAL = os.path.join(LOG_FOLDER, f"internal_traceroute_{current_date}.log")
LOG_TRACERT_EXTERNAL = os.path.join(LOG_FOLDER, f"external_traceroute_{current_date}.log")
LOG_DEVICES = os.path.join(LOG_FOLDER, f"device_monitor_{current_date}.log")
LOG_TIMEOUTS = os.path.join(LOG_FOLDER, f"timeout_errors_{current_date}.log")

# --- Locks for thread safety ---
ui_lock = threading.Lock()
log_rotation_lock = threading.Lock()

# --- Garbage Collection Variables ---
last_gc_time = time.time()
gc_counter = 0

# --- Core Functions ---
def get_current_log_files():
    """Get current log file names based on today's date"""
    today = datetime.now().strftime('%Y-%m-%d')
    return {
        'internal_ping': os.path.join(LOG_FOLDER, f"internal_ping_{today}.log"),
        'external_ping': os.path.join(LOG_FOLDER, f"external_ping_{today}.log"),
        'internal_tracert': os.path.join(LOG_FOLDER, f"internal_traceroute_{today}.log"),
        'external_tracert': os.path.join(LOG_FOLDER, f"external_traceroute_{today}.log"),
        'devices': os.path.join(LOG_FOLDER, f"device_monitor_{today}.log"),
        'timeouts': os.path.join(LOG_FOLDER, f"timeout_errors_{today}.log")
    }

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
            print(f"\nLog rotation: New log files created for {current_date}")

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

def live_ping_loop(window, host, label, log_file):
    is_windows = platform.system().lower() == "windows"
    ping_cmd = "ping"
    ping_params = ["-t", host] if is_windows else [host] # Linux ping runs forever by default

    process = subprocess.Popen([ping_cmd] + ping_params, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, universal_newlines=True, bufsize=1)

    for line in iter(process.stdout.readline, ''):
        if line.strip() == "" or "Pinging" in line or "64 bytes" in line:
            continue

        log_line = f"{datetime.now().strftime('%H:%M:%S')}: {line}"
        append_to_log(log_file, log_line)

        with ui_lock:
            window.clear()
            window.border(0)
            window.addstr(1, 2, f"--> LIVE PING to {label} ({host}) <--")
            try:
                with open(log_file, 'r') as f:
                    last_lines = f.readlines()[-(window.getmaxyx()[0] - 4):]
                for i, l in enumerate(last_lines):
                    window.addstr(3 + i, 2, l.strip())
                # Clear the last_lines from memory immediately
                del last_lines
            except FileNotFoundError:
                window.addstr(3, 2, "Log file not yet created.")
            window.refresh()
        
        if not is_windows:
            time.sleep(1) # Manually create 1-sec interval for non-Windows

    process.stdout.close()
    process.wait()

def live_traceroute_loop(window, host, label, log_file):
    is_windows = platform.system().lower() == "windows"
    tracert_cmd = "tracert" if is_windows else "traceroute"
    tracert_param = "-d" if is_windows else "-n"
    
    while True:
        start_time = datetime.now()
        log_header = f"\n--- Traceroute started at {start_time.strftime('%Y-%m-%d %H:%M:%S')} ---\n"
        append_to_log(log_file, log_header)
        with ui_lock:
            window.clear()
            window.border(0)
            window.addstr(1, 2, f"--> TRACEROUTE to {label} ({host}) <--")
            window.addstr(2, 2, f"Started: {start_time.strftime('%H:%M:%S')} (Restarts on completion)")
            window.refresh()
        line_num = 4
        try:
            process = subprocess.Popen([tracert_cmd, tracert_param, host], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, universal_newlines=True)
            for line in iter(process.stdout.readline, ''):
                append_to_log(log_file, line)
                with ui_lock:
                    if line_num < window.getmaxyx()[0] - 2:
                        window.addstr(line_num, 2, line.strip())
                        window.refresh()
                        line_num += 1
            process.stdout.close()
            process.wait()
        except Exception as e:
            error_msg = f"Traceroute command failed: {e}\n"
            append_to_log(log_file, error_msg)
            with ui_lock:
                window.addstr(line_num, 2, error_msg)
                window.refresh()
        time.sleep(1)

def live_device_discovery_loop(window, log_file):
    known_devices = set()
    while True:
        with ui_lock:
            window.clear()
            window.border(0)
            window.addstr(1, 2, f"--> LIVE DEVICE DISCOVERY (Last Scan: {datetime.now().strftime('%H:%M:%S')}) <--")
        try:
            result = subprocess.run(["arp", "-a"], capture_output=True, text=True, timeout=10)
            current_devices = set(re.findall(r"(\d+\.\d+\.\d+\.\d+)\s+([0-9a-fA-F-]+)", result.stdout))
            new_devices = current_devices - known_devices
            if new_devices:
                log_entry = f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}: NEW DEVICES DETECTED\n"
                for device in new_devices:
                    log_entry += f"  - IP: {device[0]}, MAC: {device[1]}\n"
                append_to_log(log_file, log_entry)
            known_devices = current_devices
            line_num = 3
            for ip, mac in sorted(list(current_devices)):
                is_new = "*** NEW DEVICE ***" if (ip, mac) in new_devices else ""
                device_str = f"IP: {ip.ljust(15)} MAC: {mac.ljust(17)} {is_new}"
                if line_num < window.getmaxyx()[0] - 1:
                    with ui_lock:
                        window.addstr(line_num, 2, device_str)
                    line_num += 1
            with ui_lock:
                window.refresh()
        except Exception as e:
            append_to_log(log_file, f"Device scan failed: {e}\n")
        time.sleep(DEVICE_SCAN_INTERVAL)

def main(stdscr):
    curses.curs_set(0)
    stdscr.nodelay(1)
    height, width = stdscr.getmaxyx()
    # Layout: 4 small windows on top (60% height), 1 wide on bottom (40% height)
    top_h = int(height * 0.6)
    bot_h = height - top_h
    h_half, w_half = top_h // 2, width // 2

    win_ping_int = curses.newwin(h_half, w_half, 0, 0)
    win_ping_ext = curses.newwin(h_half, w_half, 0, w_half)
    win_tracert_int = curses.newwin(h_half, w_half, h_half, 0)
    win_tracert_ext = curses.newwin(h_half, w_half, h_half, w_half)
    win_devices = curses.newwin(bot_h, width, top_h, 0)

    threads = [
        threading.Thread(target=live_ping_loop, args=(win_ping_int, ROUTER_IP, "INTERNAL", LOG_PING_INTERNAL), daemon=True),
        threading.Thread(target=live_ping_loop, args=(win_ping_ext, INTERNET_HOST, "EXTERNAL", LOG_PING_EXTERNAL), daemon=True),
        threading.Thread(target=live_traceroute_loop, args=(win_tracert_int, ROUTER_IP, "INTERNAL", LOG_TRACERT_INTERNAL), daemon=True),
        threading.Thread(target=live_traceroute_loop, args=(win_tracert_ext, INTERNET_HOST, "EXTERNAL", LOG_TRACERT_EXTERNAL), daemon=True),
        threading.Thread(target=live_device_discovery_loop, args=(win_devices, LOG_DEVICES), daemon=True)
    ]

    for t in threads:
        t.start()

    # Manual garbage collection on startup
    gc.collect()
    
    while True:
        key = stdscr.getch()
        if key == ord('q'):
            break
        elif key == ord('g'):  # Manual garbage collection with 'g' key
            collected = gc.collect()
            # Flash a message about garbage collection
            stdscr.addstr(0, 0, f"GC: Collected {collected} objects")
            stdscr.refresh()
            time.sleep(1)
        time.sleep(0.1)

if __name__ == "__main__":
    print("Initializing 5-Panel Network Command Center...")
    if platform.system().lower() == "windows":
        print("IMPORTANT: If this is your first time, run 'pip install windows-curses'.")
    print("Starting in 3 seconds...")
    time.sleep(3)
    try:
        # Create traces folder if it doesn't exist
        if not os.path.exists(LOG_FOLDER):
            os.makedirs(LOG_FOLDER)
            print(f"Created '{LOG_FOLDER}' folder for log files.")
        
        # Create initial log files if they don't exist (don't clear existing data)
        for log in [LOG_PING_INTERNAL, LOG_PING_EXTERNAL, LOG_TRACERT_INTERNAL, LOG_TRACERT_EXTERNAL, LOG_DEVICES, LOG_TIMEOUTS]:
            with open(log, 'a') as f:  # 'a' mode creates file if it doesn't exist without clearing
                pass
        
        print(f"Log files for {current_date} are ready in '{LOG_FOLDER}' folder.")
        print("Note: Log files will automatically rotate when the date changes.")
        print(f"Memory Management: Garbage collection runs every {GC_INTERVAL//60} minutes.")
        print("Controls: Press 'q' to quit, 'g' for manual garbage collection.")
        
        # Enable automatic garbage collection
        gc.enable()
        print(f"Garbage collection enabled. Initial collection freed {gc.collect()} objects.")
        
        curses.wrapper(main)
        print("Dashboard stopped. All data saved to individual .log files.")
    except Exception as e:
        print(f"An error occurred: {e}")
