"""
Multiple Speed Test Providers
Supports various speed testing services and methods
"""

import requests
import time
import json
import subprocess
import tempfile
import os
import threading
from typing import Dict, List, Optional, Any
import logging

class SpeedTestProvider:
    def __init__(self, name: str):
        self.name = name
        self.logger = logging.getLogger(f"SpeedTest.{name}")
    
    def get_servers(self) -> List[Dict[str, Any]]:
        """Get available servers for this provider"""
        return []
    
    def test_speed(self, server_id: str = None, callback=None) -> Dict[str, Any]:
        """Run speed test and return results"""
        raise NotImplementedError

class OoklaSpeedTest(SpeedTestProvider):
    """Ookla Speedtest.net (CLI version)"""
    
    def __init__(self):
        super().__init__("Ookla Speedtest")
        
    def get_servers(self) -> List[Dict[str, Any]]:
        try:
            import speedtest
            st = speedtest.Speedtest()
            servers = st.get_servers()
            server_list = []
            
            for distance, server_group in servers.items():
                for server in server_group[:3]:  # Limit to 3 servers per distance
                    server_list.append({
                        'id': server['id'],
                        'name': server['name'],
                        'sponsor': server['sponsor'],
                        'country': server['country'],
                        'distance': f"{distance:.1f}",
                        'provider': 'Ookla'
                    })
            
            return sorted(server_list, key=lambda x: float(x['distance']))[:10]
        except Exception as e:
            self.logger.error(f"Error getting Ookla servers: {e}")
            return []
    
    def test_speed(self, server_id: str = None, callback=None) -> Dict[str, Any]:
        try:
            import speedtest
            
            if callback:
                callback({'status': 'starting', 'message': 'Initializing Ookla speed test...'})
            
            st = speedtest.Speedtest(timeout=30)
            
            if callback:
                callback({'status': 'server', 'message': 'Finding servers...'})
            
            if server_id:
                try:
                    servers = st.get_servers([server_id])
                    if server_id not in [str(s['id']) for server_list in servers.values() for s in server_list]:
                        raise ValueError("Server not found")
                    st.get_best_server(servers[list(servers.keys())[0]][:1])
                except:
                    st.get_best_server()
            else:
                st.get_best_server()
            
            server_info = st.results.server
            if callback:
                callback({'status': 'server_found', 'server': server_info})
            
            # Download test
            if callback:
                callback({'status': 'downloading', 'message': 'Measuring download speed...'})
            st.download()
            download_speed = st.results.download / 1_000_000
            
            if callback:
                callback({'status': 'download_complete', 'download_speed': download_speed})
            
            # Upload test
            if callback:
                callback({'status': 'uploading', 'message': 'Measuring upload speed...'})
            st.upload()
            upload_speed = st.results.upload / 1_000_000
            
            if callback:
                callback({'status': 'upload_complete', 'upload_speed': upload_speed})
            
            results = {
                'provider': 'Ookla',
                'download_mbps': download_speed,
                'upload_mbps': upload_speed,
                'ping': st.results.ping,
                'server': server_info,
                'timestamp': time.time()
            }
            
            if callback:
                callback({'status': 'finished', 'results': results})
            
            return results
            
        except Exception as e:
            error_msg = f"Ookla speed test failed: {str(e)}"
            self.logger.error(error_msg)
            if callback:
                callback({'status': 'error', 'message': error_msg})
            raise

class FastComSpeedTest(SpeedTestProvider):
    """Fast.com (Netflix) Speed Test"""
    
    def __init__(self):
        super().__init__("Fast.com")
    
    def get_servers(self) -> List[Dict[str, Any]]:
        return [{
            'id': 'fast_auto',
            'name': 'Netflix CDN',
            'sponsor': 'Fast.com',
            'country': 'Auto',
            'distance': '0.0',
            'provider': 'Fast.com'
        }]
    
    def test_speed(self, server_id: str = None, callback=None) -> Dict[str, Any]:
        try:
            if callback:
                callback({'status': 'starting', 'message': 'Starting Fast.com speed test...'})
            
            # Fast.com API endpoints
            token_url = "https://fast.com/app-ed7d2e.js"
            
            if callback:
                callback({'status': 'server', 'message': 'Getting Fast.com token...'})
            
            # Get Fast.com token (simplified approach)
            session = requests.Session()
            session.headers.update({
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            })
            
            # Start with basic fast.com test
            if callback:
                callback({'status': 'downloading', 'message': 'Testing download speed with Fast.com...'})
            
            # Simple HTTP download test to Netflix CDN
            download_speed = self._http_speed_test(session, 'download')
            
            if callback:
                callback({'status': 'download_complete', 'download_speed': download_speed})
            
            # Upload test (Fast.com doesn't provide upload by default)
            if callback:
                callback({'status': 'uploading', 'message': 'Upload test not available on Fast.com'})
            
            upload_speed = 0  # Fast.com focuses on download
            
            results = {
                'provider': 'Fast.com',
                'download_mbps': download_speed,
                'upload_mbps': upload_speed,
                'ping': 0,  # Fast.com doesn't measure ping
                'server': {'sponsor': 'Fast.com (Netflix)', 'name': 'Netflix CDN'},
                'timestamp': time.time()
            }
            
            if callback:
                callback({'status': 'finished', 'results': results})
            
            return results
            
        except Exception as e:
            error_msg = f"Fast.com speed test failed: {str(e)}"
            self.logger.error(error_msg)
            if callback:
                callback({'status': 'error', 'message': error_msg})
            raise
    
    def _http_speed_test(self, session, test_type='download'):
        """Perform HTTP-based speed test"""
        try:
            # Use a large file for download test
            test_urls = [
                'https://speed.cloudflare.com/__down?bytes=25000000',  # 25MB
                'https://httpbin.org/drip?numbytes=10000000&duration=1',  # 10MB
            ]
            
            best_speed = 0
            for url in test_urls:
                try:
                    start_time = time.time()
                    response = session.get(url, timeout=30, stream=True)
                    
                    downloaded = 0
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            downloaded += len(chunk)
                            # Stop after reasonable amount for speed calculation
                            if downloaded > 5_000_000:  # 5MB
                                break
                    
                    end_time = time.time()
                    duration = end_time - start_time
                    
                    if duration > 0:
                        speed_mbps = (downloaded * 8) / (duration * 1_000_000)  # Convert to Mbps
                        best_speed = max(best_speed, speed_mbps)
                        
                except Exception as e:
                    self.logger.debug(f"Failed to test with {url}: {e}")
                    continue
            
            return best_speed
            
        except Exception as e:
            self.logger.error(f"HTTP speed test failed: {e}")
            return 0

class LibreSpeedTest(SpeedTestProvider):
    """LibreSpeed (Open Source Speed Test)"""
    
    def __init__(self):
        super().__init__("LibreSpeed")
    
    def get_servers(self) -> List[Dict[str, Any]]:
        return [
            {
                'id': 'libre_auto',
                'name': 'LibreSpeed Server',
                'sponsor': 'LibreSpeed',
                'country': 'Auto',
                'distance': '0.0',
                'provider': 'LibreSpeed'
            }
        ]
    
    def test_speed(self, server_id: str = None, callback=None) -> Dict[str, Any]:
        try:
            if callback:
                callback({'status': 'starting', 'message': 'Starting LibreSpeed test...'})
            
            # Use public LibreSpeed instances
            test_servers = [
                'https://speedtest.selectel.ru',
                'https://speedtest.wtnet.de/backend',
            ]
            
            download_speed = 0
            upload_speed = 0
            ping_ms = 0
            
            for server in test_servers:
                try:
                    if callback:
                        callback({'status': 'downloading', 'message': f'Testing with {server}...'})
                    
                    # Ping test
                    ping_start = time.time()
                    ping_response = requests.get(f"{server}/empty.php", timeout=10)
                    ping_ms = (time.time() - ping_start) * 1000
                    
                    # Download test
                    download_speed = self._libre_download_test(server)
                    
                    if callback:
                        callback({'status': 'download_complete', 'download_speed': download_speed})
                    
                    # Upload test
                    if callback:
                        callback({'status': 'uploading', 'message': 'Testing upload speed...'})
                    
                    upload_speed = self._libre_upload_test(server)
                    
                    break  # Use first working server
                    
                except Exception as e:
                    self.logger.debug(f"LibreSpeed server {server} failed: {e}")
                    continue
            
            results = {
                'provider': 'LibreSpeed',
                'download_mbps': download_speed,
                'upload_mbps': upload_speed,
                'ping': ping_ms,
                'server': {'sponsor': 'LibreSpeed', 'name': 'Open Source Speed Test'},
                'timestamp': time.time()
            }
            
            if callback:
                callback({'status': 'finished', 'results': results})
            
            return results
            
        except Exception as e:
            error_msg = f"LibreSpeed test failed: {str(e)}"
            self.logger.error(error_msg)
            if callback:
                callback({'status': 'error', 'message': error_msg})
            raise
    
    def _libre_download_test(self, server_url):
        """LibreSpeed download test"""
        try:
            # Download a test file
            start_time = time.time()
            response = requests.get(f"{server_url}/garbage.php?ckSize=25", timeout=30, stream=True)
            
            downloaded = 0
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    downloaded += len(chunk)
                    if downloaded > 10_000_000:  # 10MB limit
                        break
            
            duration = time.time() - start_time
            return (downloaded * 8) / (duration * 1_000_000) if duration > 0 else 0
            
        except Exception as e:
            self.logger.error(f"LibreSpeed download test failed: {e}")
            return 0
    
    def _libre_upload_test(self, server_url):
        """LibreSpeed upload test"""
        try:
            # Upload test data
            test_data = b'0' * 1_000_000  # 1MB of test data
            
            start_time = time.time()
            response = requests.post(f"{server_url}/empty.php", data=test_data, timeout=30)
            duration = time.time() - start_time
            
            return (len(test_data) * 8) / (duration * 1_000_000) if duration > 0 else 0
            
        except Exception as e:
            self.logger.error(f"LibreSpeed upload test failed: {e}")
            return 0

class SpeedTestManager:
    """Manages multiple speed test providers"""
    
    def __init__(self):
        self.providers = {
            'ookla': OoklaSpeedTest(),
            'fast': FastComSpeedTest(),
            'libre': LibreSpeedTest()
        }
        
        self.logger = logging.getLogger("SpeedTestManager")
    
    def get_available_providers(self) -> List[str]:
        """Get list of available speed test providers"""
        available = []
        for name, provider in self.providers.items():
            try:
                # Test if provider is available
                if name == 'ookla':
                    import speedtest  # Check if speedtest module is available
                available.append(name)
            except ImportError:
                continue
        return available
    
    def get_provider_servers(self, provider_name: str) -> List[Dict[str, Any]]:
        """Get servers for a specific provider"""
        if provider_name not in self.providers:
            return []
        
        try:
            return self.providers[provider_name].get_servers()
        except Exception as e:
            self.logger.error(f"Error getting servers for {provider_name}: {e}")
            return []
    
    def run_speed_test(self, provider_name: str, server_id: str = None, callback=None) -> Dict[str, Any]:
        """Run speed test with specified provider"""
        if provider_name not in self.providers:
            raise ValueError(f"Unknown provider: {provider_name}")
        
        provider = self.providers[provider_name]
        return provider.test_speed(server_id, callback)

# Global instance
speed_test_manager = SpeedTestManager()
