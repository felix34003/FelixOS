import json
import psutil
import time
import os

import zenoh

def load_config():
    config_path = os.path.join(os.path.dirname(__file__), 'config.json')
    if not os.path.exists(config_path):
        # Reach up if called from subdirectory
        config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config.json')
    with open(config_path, 'r') as f:
        return json.load(f)

def get_zenoh_config(mode="connect"):
    """Create a zenoh.Config with endpoints from config.json."""
    config = load_config()
    z_config = zenoh.Config()
    
    if mode == "connect" and "zenoh" in config and "connect" in config["zenoh"]:
        # Set endpoints for connecting
        z_config.insert_json5("connect/endpoints", json.dumps(config["zenoh"]["connect"]))
    elif mode == "listen" and "zenoh" in config and "listen" in config["zenoh"]:
        # Set endpoints for listening
        z_config.insert_json5("listen/endpoints", json.dumps(config["zenoh"]["listen"]))
        
    return z_config

def get_heartbeat(node_name):

    return {
        "node": node_name,
        "status": "Running",
        "cpu_percent": psutil.cpu_percent(),
        "memory_percent": psutil.virtual_memory().percent,
        "timestamp": time.time()
    }
