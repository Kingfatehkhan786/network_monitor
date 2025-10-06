#!/usr/bin/env python3
"""
Advanced Network Tools with OS Detection
Enhanced networking capabilities for Linux/Mac with Windows fallback
"""

import subprocess
import platform
import json
import re
import time
from datetime import datetime
import socket
import threading

class NetworkToolsManager:
    def __init__(self):
        self.os_type = platform.system().lower()
        self.is_linux = self.os_type == "linux"
        self.is_windows = self.os_type == "windows"
        self.is_macos = self.os_type == "darwin"
        
        print(f"🖥️ Operating System: {platform.system()}")
        print(f"🔧 Advanced tools available: {'Yes' if self.is_linux or self.is_macos else 'No'}")
        
        # Check available tools
        self.available_tools = self._check_available_tools()
        
    def _check_available_tools(self):
        """Check which advanced tools are available"""
        tools = {}
        
        if self.is_linux or self.is_macos:
            # Advanced Linux/Mac tools
            advanced_tools = ['nmap', 'arp-scan', 'ss', 'netstat', 'dig', 'nslookup', 'whois', 'tcpdump']
            for tool in advanced_tools:
                try:
                    subprocess.run([tool, '--version'], capture_output=True, timeout=2)
                    tools[tool] = True
                    print(f"✅ {tool} available")
                except (subprocess.SubprocessError, FileNotFoundError, subprocess.TimeoutExpired):
                    tools[tool] = False
                    print(f"❌ {tool} not available")
        else:
            # Basic Windows tools
            basic_tools = ['ping', 'tracert', 'nslookup', 'netstat']
            for tool in basic_tools:
                tools[tool] = True  # Assume available on Windows
                
        return tools
    
    def get_ping_command(self, host, count=None):
        """Get OS-appropriate ping command"""
        if self.is_windows:
            return ["ping", "-t", host] if count is None else ["ping", "-n", str(count), host]
        elif self.is_linux:
            if count is None:
                return ["ping", "-i", "1", "-W", "3", host]  # Continuous
            else:
                return ["ping", "-c", str(count), "-i", "0.5", "-W", "2", host]  # Finite
        else:  # macOS
            if count is None:
                return ["ping", "-i", "1", host]
            else:
                return ["ping", "-c", str(count), host]
    
    def get_traceroute_command(self, host):
        """Get OS-appropriate traceroute command"""
        if self.is_windows:
            return ["tracert", "-d", host]
        else:  # Linux/macOS
            return ["traceroute", "-n", "-w", "2", "-q", "2", "-m", "20", host]
    
    def advanced_port_scan(self, target, ports="22,80,443,8080"):
        """Advanced port scanning (Linux/Mac only)"""
        if not (self.is_linux or self.is_macos) or not self.available_tools.get('nmap'):
            return self._basic_port_check(target, ports)
        
        try:
            print(f"🔍 Advanced port scan: {target} ports {ports}")
            nmap_cmd = ["nmap", "-p", ports, "-sS", "--open", target]
            
            result = subprocess.run(
                nmap_cmd,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            return self._parse_nmap_ports(result.stdout)
            
        except Exception as e:
            print(f"Port scan error: {e}")
            return self._basic_port_check(target, ports)
    
    def network_discovery_advanced(self, network_range):
        """Advanced network discovery using multiple methods"""
        discovered_devices = []
        
        if self.is_linux and self.available_tools.get('nmap'):
            # Method 1: nmap ping sweep
            discovered_devices.extend(self._nmap_discovery(network_range))
            
        if self.is_linux and self.available_tools.get('arp-scan'):
            # Method 2: ARP scan (local network only)
            discovered_devices.extend(self._arp_discovery(network_range))
        
        # Method 3: Fallback ping sweep (all OS)
        if not discovered_devices:
            discovered_devices.extend(self._ping_sweep_discovery(network_range))
        
        # Method 4: Active connections (Linux/Mac)
        if self.is_linux or self.is_macos:
            discovered_devices.extend(self._active_connections_discovery())
        
        return self._deduplicate_devices(discovered_devices)
    
    def _nmap_discovery(self, network_range):
        """Use nmap for network discovery"""
        devices = []
        try:
            print(f"🔍 nmap discovery on {network_range}")
            nmap_cmd = ["nmap", "-sn", "-T4", network_range]
            
            result = subprocess.run(
                nmap_cmd,
                capture_output=True,
                text=True,
                timeout=45
            )
            
            lines = result.stdout.split('\n')
            current_device = {}
            
            for line in lines:
                line = line.strip()
                
                if 'Nmap scan report for' in line:
                    if current_device:
                        devices.append(current_device)
                    
                    # Extract IP and hostname
                    parts = line.split()
                    if len(parts) >= 5 and '(' in line and ')' in line:
                        hostname = parts[4]
                        ip = line.split('(')[1].split(')')[0]
                    else:
                        ip = parts[-1]
                        hostname = ip
                    
                    current_device = {
                        'ip': ip,
                        'hostname': hostname,
                        'method': 'nmap',
                        'status': 'up',
                        'timestamp': datetime.now().isoformat()
                    }
                
                elif 'Host is up' in line and current_device:
                    # Extract response time
                    time_match = re.search(r'\(([\d.]+)s latency\)', line)
                    if time_match:
                        current_device['latency'] = f"{float(time_match.group(1)) * 1000:.1f}ms"
            
            if current_device:
                devices.append(current_device)
                
        except Exception as e:
            print(f"nmap discovery error: {e}")
        
        return devices
    
    def _arp_discovery(self, network_range):
        """Use arp-scan for local network discovery"""
        devices = []
        try:
            print(f"🔍 ARP scan on {network_range}")
            arp_cmd = ["arp-scan", "--local", "--timeout=2"]
            
            result = subprocess.run(
                arp_cmd,
                capture_output=True,
                text=True,
                timeout=20
            )
            
            lines = result.stdout.split('\n')
            for line in lines:
                # Parse ARP scan output: IP, MAC, Vendor
                parts = line.split('\t')
                if len(parts) >= 2 and re.match(r'^\d+\.\d+\.\d+\.\d+', parts[0]):
                    devices.append({
                        'ip': parts[0].strip(),
                        'mac': parts[1].strip() if len(parts) > 1 else 'Unknown',
                        'vendor': parts[2].strip() if len(parts) > 2 else 'Unknown',
                        'method': 'arp-scan',
                        'status': 'up',
                        'timestamp': datetime.now().isoformat()
                    })
                    
        except Exception as e:
            print(f"ARP scan error: {e}")
        
        return devices
    
    def _active_connections_discovery(self):
        """Find devices from active network connections"""
        devices = []
        try:
            if self.available_tools.get('ss'):
                # Use ss (modern netstat replacement)
                cmd = ["ss", "-tuln"]
            else:
                # Fallback to netstat
                cmd = ["netstat", "-tuln"]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            
            # Extract unique IPs from connections
            ips = set()
            for line in result.stdout.split('\n'):
                # Look for IP addresses in the output
                ip_matches = re.findall(r'(\d+\.\d+\.\d+\.\d+)', line)
                for ip in ip_matches:
                    if not ip.startswith('127.') and not ip.startswith('0.'):
                        ips.add(ip)
            
            for ip in ips:
                devices.append({
                    'ip': ip,
                    'hostname': self._reverse_dns(ip),
                    'method': 'active_connections',
                    'status': 'connected',
                    'timestamp': datetime.now().isoformat()
                })
                
        except Exception as e:
            print(f"Active connections discovery error: {e}")
        
        return devices
    
    def _reverse_dns(self, ip):
        """Attempt reverse DNS lookup"""
        try:
            return socket.gethostbyaddr(ip)[0]
        except:
            return ip
    
    def _ping_sweep_discovery(self, network_range):
        """Fallback ping sweep discovery"""
        devices = []
        try:
            import ipaddress
            network = ipaddress.IPv4Network(network_range, strict=False)
            
            # Limit to prevent overwhelming
            hosts = list(network.hosts())[:50] if len(list(network.hosts())) > 50 else list(network.hosts())
            
            for ip in hosts:
                ip_str = str(ip)
                ping_cmd = self.get_ping_command(ip_str, count=1)
                
                try:
                    result = subprocess.run(
                        ping_cmd,
                        capture_output=True,
                        timeout=3
                    )
                    
                    if result.returncode == 0:
                        devices.append({
                            'ip': ip_str,
                            'hostname': self._reverse_dns(ip_str),
                            'method': 'ping_sweep',
                            'status': 'up',
                            'timestamp': datetime.now().isoformat()
                        })
                        
                except subprocess.TimeoutExpired:
                    continue
                    
        except Exception as e:
            print(f"Ping sweep error: {e}")
        
        return devices
    
    def _basic_port_check(self, target, ports):
        """Basic port connectivity check (fallback)"""
        results = []
        port_list = [int(p.strip()) for p in ports.split(',')]
        
        for port in port_list:
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(2)
                result = sock.connect_ex((target, port))
                sock.close()
                
                results.append({
                    'port': port,
                    'status': 'open' if result == 0 else 'closed',
                    'service': self._get_service_name(port)
                })
            except:
                results.append({
                    'port': port,
                    'status': 'unknown',
                    'service': self._get_service_name(port)
                })
        
        return results
    
    def _parse_nmap_ports(self, nmap_output):
        """Parse nmap port scan output"""
        ports = []
        lines = nmap_output.split('\n')
        
        for line in lines:
            if '/tcp' in line and 'open' in line:
                parts = line.split()
                if len(parts) >= 3:
                    port_info = parts[0].split('/')[0]
                    service = parts[2] if len(parts) > 2 else 'unknown'
                    
                    ports.append({
                        'port': int(port_info),
                        'status': 'open',
                        'service': service
                    })
        
        return ports
    
    def _get_service_name(self, port):
        """Get common service name for port"""
        common_ports = {
            22: 'ssh', 80: 'http', 443: 'https', 21: 'ftp',
            23: 'telnet', 25: 'smtp', 53: 'dns', 110: 'pop3',
            143: 'imap', 993: 'imaps', 995: 'pop3s', 8080: 'http-alt'
        }
        return common_ports.get(port, 'unknown')
    
    def _deduplicate_devices(self, devices):
        """Remove duplicate devices based on IP"""
        seen_ips = set()
        unique_devices = []
        
        for device in devices:
            if device['ip'] not in seen_ips:
                seen_ips.add(device['ip'])
                unique_devices.append(device)
        
        return unique_devices
    
    def get_network_interfaces_advanced(self):
        """Get detailed network interface information"""
        interfaces = []
        
        try:
            if self.is_linux:
                # Use ip command on Linux
                result = subprocess.run(['ip', 'addr', 'show'], capture_output=True, text=True)
                interfaces = self._parse_ip_addr(result.stdout)
            elif self.is_windows:
                # Use ipconfig on Windows  
                result = subprocess.run(['ipconfig', '/all'], capture_output=True, text=True)
                interfaces = self._parse_ipconfig(result.stdout)
            else:  # macOS
                # Use ifconfig on macOS
                result = subprocess.run(['ifconfig'], capture_output=True, text=True)
                interfaces = self._parse_ifconfig(result.stdout)
                
        except Exception as e:
            print(f"Network interface discovery error: {e}")
        
        return interfaces
    
    def _parse_ip_addr(self, output):
        """Parse Linux 'ip addr' output"""
        interfaces = []
        current_interface = {}
        
        for line in output.split('\n'):
            line = line.strip()
            
            # Interface line
            if re.match(r'^\d+:', line):
                if current_interface:
                    interfaces.append(current_interface)
                
                parts = line.split()
                name = parts[1].rstrip(':')
                current_interface = {
                    'name': name,
                    'status': 'UP' if 'UP' in line else 'DOWN',
                    'ips': [],
                    'mac': None
                }
            
            # MAC address
            elif 'link/ether' in line:
                parts = line.split()
                current_interface['mac'] = parts[1]
            
            # IP address
            elif 'inet ' in line:
                parts = line.split()
                ip_with_mask = parts[1]
                ip = ip_with_mask.split('/')[0]
                current_interface['ips'].append(ip)
        
        if current_interface:
            interfaces.append(current_interface)
        
        return interfaces
    
    def _parse_ipconfig(self, output):
        """Parse Windows ipconfig output"""
        # Simplified parser for Windows
        interfaces = []
        # Implementation would parse ipconfig /all output
        return interfaces
    
    def _parse_ifconfig(self, output):
        """Parse macOS ifconfig output"""
        # Simplified parser for macOS
        interfaces = []
        # Implementation would parse ifconfig output
        return interfaces

# Global instance
network_tools = NetworkToolsManager()

def get_ping_command_enhanced(host, count=None):
    """Enhanced ping command with OS detection"""
    return network_tools.get_ping_command(host, count)

def get_traceroute_command_enhanced(host):
    """Enhanced traceroute command with OS detection"""
    return network_tools.get_traceroute_command(host)

def discover_network_devices_enhanced(network_range):
    """Enhanced network discovery using multiple methods"""
    return network_tools.network_discovery_advanced(network_range)

def port_scan_enhanced(target, ports="22,80,443,8080"):
    """Enhanced port scanning"""
    return network_tools.advanced_port_scan(target, ports)
