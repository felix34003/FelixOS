import zenoh
import sys
import os

# Add root to path for utils
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from utils import load_config, get_zenoh_config

def main():
    config = load_config()
    
    print("Connecting to Zenoh as Pi (Counter Sub)...")
    z_config = get_zenoh_config("connect")
    session = zenoh.open(z_config)

    
    # Path to status file for HTTP server
    status_file = "/tmp/felix_counter.txt"

    def counter_handler(sample):
        val = bytes(sample.payload).decode('utf-8')
        print(f"Received counter: {val}", flush=True)
        # Write to file for status_server.py
        with open(status_file, "w") as f:
            f.write(val)

    # Subscribe to counter
    print(f"Subscribing to '{config['topics']['counter']}'...")
    sub_counter = session.declare_subscriber(config['topics']['counter'], counter_handler)
    
    print("Counter Subscriber started. Press Ctrl+C to exit.")
    
    try:
        while True:
            pass
    except KeyboardInterrupt:
        print("Stopping Pi Counter Subscriber...")
    finally:
        session.close()

if __name__ == "__main__":
    main()
