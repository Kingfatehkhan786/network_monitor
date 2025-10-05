"""
Production Configuration Management
"""

import os
from datetime import timedelta

class Config:
    """Base configuration"""
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-key-change-in-production')
    DEBUG = False
    TESTING = False
    
    # Network Monitor Settings
    LOG_RETENTION_DAYS = int(os.environ.get('LOG_RETENTION_DAYS', 30))
    MAX_LOG_SIZE_MB = int(os.environ.get('MAX_LOG_SIZE_MB', 100))
    PING_INTERVAL = int(os.environ.get('PING_INTERVAL', 5))
    
    # Security Settings
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    PERMANENT_SESSION_LIFETIME = timedelta(hours=24)
    
    # Performance Settings
    SEND_FILE_MAX_AGE_DEFAULT = timedelta(hours=1)
    
    # SocketIO Settings
    SOCKETIO_ASYNC_MODE = 'threading'
    SOCKETIO_LOGGER = False
    SOCKETIO_ENGINEIO_LOGGER = False

class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    SESSION_COOKIE_SECURE = False

class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    
    # Production-specific settings
    SESSION_COOKIE_SECURE = True
    PREFERRED_URL_SCHEME = 'https'
    
    # Logging
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')

class TestingConfig(Config):
    """Testing configuration"""
    TESTING = True
    DEBUG = True
    SESSION_COOKIE_SECURE = False

# Configuration mapping
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}
