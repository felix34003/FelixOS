import zenoh
import cv2
import numpy as np
import json
import sys
import os
import time
import threading
import webbrowser
from flask import Flask, render_template, Response, jsonify
from queue import Queue

# Add root to path for utils
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
from utils import load_config, get_zenoh_config

app = Flask(__name__)

# Global state
frame_queue = Queue(maxsize=1)
node_stats = {}
config = load_config()

def video_handler(sample):
    """Directly relay JPEG bytes to the browser without re-encoding."""
    try:
        data = bytes(sample.payload)
        
        # Non-blocking put
        if frame_queue.full():
            try: frame_queue.get_nowait()
            except: pass
        frame_queue.put(data)
    except Exception as e:
        pass

def heartbeat_handler(sample):
    try:
        hb = json.loads(bytes(sample.payload).decode('utf-8'))
        node_stats[hb['node']] = hb
    except: pass

def zenoh_worker():
    print("Connecting to Zenoh...")
    z_config = get_zenoh_config("listen")
    session = zenoh.open(z_config)
    
    # Subscriptions
    sub_video = session.declare_subscriber(config['topics']['video'], video_handler)
    sub_hb = session.declare_subscriber(f"{config['topics']['heartbeat']}/*", heartbeat_handler)
    
    print("Zenoh Bridge active.")
    try:
        while True: time.sleep(1)
    except:
        session.close()

def gen_frames():
    """Generator for MJPEG stream."""
    while True:
        frame = frame_queue.get()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/video_feed')
def video_feed():
    return Response(gen_frames(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/stats')
def stats():
    return jsonify(node_stats)

def main():
    # Start Zenoh in a background thread
    threading.Thread(target=zenoh_worker, daemon=True).start()
    
    # Auto-open browser after a short delay
    def open_browser():
        time.sleep(2)
        print("Launching Dashboard...")
        webbrowser.open("http://localhost:5000")
    
    threading.Thread(target=open_browser, daemon=True).start()
    
    # Disable flask logging for cleaner terminal
    import logging
    log = logging.getLogger('werkzeug')
    log.setLevel(logging.ERROR)
    
    print("Starting FelixOS Mission Control on http://localhost:5000")
    app.run(host='0.0.0.0', port=5000, threaded=True)

if __name__ == "__main__":
    main()
