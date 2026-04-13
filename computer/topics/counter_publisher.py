import zenoh
import json
import time
import sys
import os

# Add root to path for utils
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
from utils import load_config, get_heartbeat, get_zenoh_config

def main():
    config = load_config()
    
    print("Connecting to Zenoh as PC (Counter Pub)...")
    z_config = get_zenoh_config("listen")
    session = zenoh.open(z_config)

    
    # Publisher for counter
    pub_counter = session.declare_publisher(config['topics']['counter'])
    # Publisher for heartbeat
    pub_hb = session.declare_publisher(f"{config['topics']['heartbeat']}/pc")
    
    counter = 0
    rate = config['config']['counter_rate_hz']
    
    print(f"Counter Publisher started. Sending to '{config['topics']['counter']}' at {rate}Hz...")
    
    try:
        while True:
            # Publish counter
            pub_counter.put(str(counter))
            print(f"Sent counter: {counter}")
            counter += 1
            
            # Publish heartbeat every 2 seconds
            if int(time.time()) % 2 == 0:
                hb = get_heartbeat("PC")
                pub_hb.put(json.dumps(hb))
            
            time.sleep(1/rate)
            
    except KeyboardInterrupt:
        print("Stopping PC Counter Publisher...")
    finally:
        session.close()

if __name__ == "__main__":
    main()
