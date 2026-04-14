"""
Health check server for Render.com
Runs alongside the Telegram bot
"""
from flask import Flask
import threading

app = Flask(__name__)

@app.route('/')
def health():
    return 'OK'

def run_server():
    app.run(host='0.0.0.0', port=10000)

def start_health_server():
    """Start health check server in background thread"""
    thread = threading.Thread(target=run_server, daemon=True)
    thread.start()
    return thread
