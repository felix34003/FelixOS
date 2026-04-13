import http.server
import socketserver
import json
import zenoh
import sys
import os
import threading

# Add root to path for utils
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from utils import load_config, get_zenoh_config

# Global state for heartbeats
node_stats = {}
last_counter = "0"

def start_zenoh_sub(config):
    global last_counter
    z_config = get_zenoh_config("connect")
    session = zenoh.open(z_config)


    def hb_handler(sample):
        try:
            hb = json.loads(bytes(sample.payload).decode('utf-8'))
            node_stats[hb['node']] = hb
        except: pass

    def counter_handler(sample):
        global last_counter
        last_counter = bytes(sample.payload).decode('utf-8')

    session.declare_subscriber(f"{config['topics']['heartbeat']}/*", hb_handler)
    session.declare_subscriber(config['topics']['counter'], counter_handler)
    
    while True:
        pass

class StatusHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/plain")
        self.end_headers()
        
        response = "=== FelixOS Network Status ===\n\n"
        response += f"Live Counter: {last_counter}\n\n"
        response += "Active Nodes:\n"
        for node, stats in node_stats.items():
            response += f"- {node}: {stats['status']} (CPU: {stats['cpu_percent']}%, MEM: {stats['memory_percent']}%)\n"
        
        self.wfile.write(response.encode())

def main():
    config = load_config()
    
    # Start Zenoh in a background thread to update stats
    threading.Thread(target=start_zenoh_sub, args=(config,), daemon=True).start()
    
    PORT = 8000
    with socketserver.TCPServer(("", PORT), StatusHandler) as httpd:
        print(f"Status Server running at http://localhost:{PORT}", flush=True)
        httpd.serve_forever()

if __name__ == "__main__":
    main()
