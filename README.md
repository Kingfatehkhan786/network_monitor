# Network Monitoring Suite

This project is a comprehensive network monitoring suite with both a command-line interface (CLI) and a full-featured web application. It is designed to be lightweight, easy to deploy in an LXC container, and provide real-time insights into your network's health.

## Features

### Core Monitoring
- **Internal & External Ping**: Continuously monitors connectivity to your local gateway and the internet.
- **Traceroute**: Periodically runs traceroutes to analyze the path to both internal and external hosts.
- **Device Discovery**: Scans the local network using ARP to discover and log all connected devices.
- **Timeout Logging**: Automatically isolates and logs `Request timed out` errors from the external ping monitor for quick diagnostics.

### Web Interface (Flask & Socket.IO)
- **Real-time Dashboard**: A modern, responsive web UI to visualize all monitoring data live.
- **Dedicated Pages**: Separate, auto-updating pages for each monitoring function (ping, traceroute, devices, timeouts).
- **Live Statistics**: Displays packet loss, latency, hop counts, and device counts in real-time.
- **API Endpoints**: Provides JSON endpoints to fetch recent log data.

### System & Performance
- **Automatic Log Rotation**: Log files are automatically rotated daily (`*_YYYY-MM-DD.log`) to prevent them from growing indefinitely. Old logs are preserved.
- **Organized Log Storage**: All logs are neatly stored in the `traces/` directory.
- **Automatic Garbage Collection**: A memory management system runs every 5 minutes to prevent memory leaks during long-running sessions. It can also be triggered manually.

## Directory Structure
```
/
├── web_network_monitor.py  # Main Flask web application
├── network_monitor.py      # Original console application
├── requirements.txt        # Python dependencies
├── Makefile                # For easy setup in Ubuntu/LXC
├── README.md               # This file
├── templates/              # HTML files for the web app
│   ├── base.html
│   ├── home.html
│   ├── ping.html
│   ├── traceroute.html
│   ├── devices.html
│   └── timeouts.html
└── traces/                 # Directory for all log files (auto-created)
```

## Quick Start

### For Windows (Local Development)
1.  **Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```
2.  **Run the Web Application**:
    ```bash
    python web_network_monitor.py
    ```
3.  **Access the Dashboard**:
    Open your browser and go to `http://localhost:5000`.

### For Ubuntu / LXC Container (Deployment)
The `Makefile` automates the entire setup process.

1.  **Copy Files**: Transfer the project files to your container.
2.  **Install**:
    ```bash
    make install
    ```
3.  **Run in Production Mode**:
    ```bash
    make run-web-prod
    ```
    This starts the application in the background using Gunicorn.

## Makefile Usage (for Ubuntu/LXC)
- `make install`: Installs Python, all dependencies, and creates directories.
- `make run-web`: Runs the app in a simple development mode.
- `make run-web-prod`: Runs the app in the background using Gunicorn.
- `make status`: Checks if the web application is running.
- `make stop`: Stops the background web application.
- `make logs`: Shows the last 10 lines of key log files.
- `make clean`: Deletes all log files.

## Network Impact

The monitoring processes are designed to be extremely lightweight and have a **negligible impact on your network speed**.

- **Ping**: Sends a tiny data packet (typically 32 bytes) once per second. This is less than 1 kbps of data, which is insignificant on any modern network.
- **Traceroute**: Runs periodically, sending a small number of packets to map a route, and then stops. It is not a continuous process.
- **ARP Scan**: Operates only on your local network and involves very small, infrequent broadcast packets.

You will not notice any slowdown in your regular internet activities like browsing, streaming, or gaming.
