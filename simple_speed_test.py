"""
Simple HTTP-based Speed Test
Works around firewall restrictions by using common HTTP endpoints
"""

import requests
import time
import threading
from typing import Callable, Dict, Any

class SimpleSpeedTest:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def test_download_speed(self, callback: Callable = None) -> float:
        """Test download speed using HTTP downloads"""
        try:
            # Use multiple test files for better accuracy
            test_urls = [
                'https://speed.cloudflare.com/__down?bytes=10000000',  # 10MB
                'https://httpbin.org/drip?numbytes=5000000&duration=1',  # 5MB
                'https://www.google.com/images/branding/googlelogo/2x/googlelogo_color_272x92dp.png',
            ]
            
            best_speed = 0
            
            for i, url in enumerate(test_urls):
                try:
                    if callback:
                        callback({
                            'status': 'downloading',
                            'message': f'Testing download speed... ({i+1}/{len(test_urls)})'
                        })
                    
                    start_time = time.time()
                    response = self.session.get(url, timeout=30, stream=True)
                    
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
                        
                        if callback:
                            callback({
                                'status': 'download_progress',
                                'message': f'Download test {i+1}: {speed_mbps:.2f} Mbps'
                            })
                        
                except Exception as e:
                    print(f"Download test {i+1} failed: {e}")
                    continue
            
            return best_speed
            
        except Exception as e:
            print(f"Download speed test failed: {e}")
            return 0
    
    def test_upload_speed(self, callback: Callable = None) -> float:
        """Test upload speed using HTTP uploads"""
        try:
            # Generate test data
            test_data = b'0' * 1_000_000  # 1MB of test data
            
            upload_urls = [
                'https://httpbin.org/post',
                'https://httpbin.org/put',
            ]
            
            best_speed = 0
            
            for i, url in enumerate(upload_urls):
                try:
                    if callback:
                        callback({
                            'status': 'uploading',
                            'message': f'Testing upload speed... ({i+1}/{len(upload_urls)})'
                        })
                    
                    start_time = time.time()
                    response = self.session.post(url, data=test_data, timeout=30)
                    end_time = time.time()
                    
                    duration = end_time - start_time
                    
                    if duration > 0 and response.status_code == 200:
                        speed_mbps = (len(test_data) * 8) / (duration * 1_000_000)  # Convert to Mbps
                        best_speed = max(best_speed, speed_mbps)
                        
                        if callback:
                            callback({
                                'status': 'upload_progress',
                                'message': f'Upload test {i+1}: {speed_mbps:.2f} Mbps'
                            })
                        
                except Exception as e:
                    print(f"Upload test {i+1} failed: {e}")
                    continue
            
            return best_speed
            
        except Exception as e:
            print(f"Upload speed test failed: {e}")
            return 0
    
    def test_ping(self, callback: Callable = None) -> float:
        """Test ping using HTTP requests"""
        try:
            ping_urls = [
                'https://www.google.com',
                'https://www.cloudflare.com',
                'https://httpbin.org/get'
            ]
            
            ping_times = []
            
            for url in ping_urls:
                try:
                    start_time = time.time()
                    response = self.session.get(url, timeout=10)
                    end_time = time.time()
                    
                    if response.status_code == 200:
                        ping_ms = (end_time - start_time) * 1000
                        ping_times.append(ping_ms)
                        
                except Exception as e:
                    print(f"Ping test to {url} failed: {e}")
                    continue
            
            if ping_times:
                return sum(ping_times) / len(ping_times)  # Average ping
            else:
                return 0
                
        except Exception as e:
            print(f"Ping test failed: {e}")
            return 0
    
    def run_full_test(self, callback: Callable = None) -> Dict[str, Any]:
        """Run complete speed test"""
        try:
            if callback:
                callback({'status': 'starting', 'message': 'Starting simple HTTP speed test...'})
            
            # Test ping
            if callback:
                callback({'status': 'ping', 'message': 'Testing ping...'})
            
            ping = self.test_ping(callback)
            
            if callback:
                callback({
                    'status': 'ping_complete',
                    'message': f'Ping: {ping:.2f} ms'
                })
            
            # Test download
            download_speed = self.test_download_speed(callback)
            
            if callback:
                callback({
                    'status': 'download_complete',
                    'download_speed': download_speed,
                    'message': f'Download: {download_speed:.2f} Mbps'
                })
            
            # Test upload
            upload_speed = self.test_upload_speed(callback)
            
            if callback:
                callback({
                    'status': 'upload_complete',
                    'upload_speed': upload_speed,
                    'message': f'Upload: {upload_speed:.2f} Mbps'
                })
            
            results = {
                'provider': 'Simple HTTP Test',
                'download_mbps': download_speed,
                'upload_mbps': upload_speed,
                'ping': ping,
                'server': {'sponsor': 'HTTP Test', 'name': 'Multiple Endpoints'},
                'timestamp': time.time()
            }
            
            if callback:
                callback({
                    'status': 'finished',
                    'results': results,
                    'message': f'Test completed! Download: {download_speed:.2f} Mbps, Upload: {upload_speed:.2f} Mbps, Ping: {ping:.2f} ms'
                })
            
            return results
            
        except Exception as e:
            error_msg = f"Simple speed test failed: {str(e)}"
            if callback:
                callback({'status': 'error', 'message': error_msg})
            raise

# Global instance
simple_speed_test = SimpleSpeedTest()
