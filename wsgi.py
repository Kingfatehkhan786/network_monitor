"""
WSGI entry point for production deployment
"""

import os
import sys
from web_network_monitor import app, socketio

if __name__ == "__main__":
    # Production WSGI server
    socketio.run(app, host='0.0.0.0', port=int(os.environ.get('PORT', 5000)), debug=False)
