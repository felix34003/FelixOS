import zenoh
import cv2
import json
import time
import sys
import os

# Add root to path for utils
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from utils import load_config, get_heartbeat, get_zenoh_config

def main():
    config = load_config()
    pi_ip = config['nodes']['pi']['ip']
    
    # Zenoh session setup
    print(f"Connecting to Zenoh as Pi ({pi_ip})...")
    z_config = get_zenoh_config("connect")
    session = zenoh.open(z_config)

    
    # Publisher for video
    pub_video = session.declare_publisher(config['topics']['video'])
    # Publisher for heartbeat
    pub_hb = session.declare_publisher(f"{config['topics']['heartbeat']}/pi")
    
    import time
    
    # Camera setup: Try indices 0, 2, 4 (Standard Pi indices)
    cap = None
    while not cap or not cap.isOpened():
        for idx in [0, 1, 2, 3, 4]:
            print(f"Attempting to open camera at index {idx}...", flush=True)
            # Use V4L2 backend for Linux stability
            cap = cv2.VideoCapture(idx, cv2.CAP_V4L2)
            if cap.isOpened():
                print(f"Successfully opened camera at index {idx}", flush=True)
                break
            cap.release()
            cap = None
        
        if not cap:
            print("Error: Could not open any USB camera. Waiting 2s before retry...", flush=True)
            time.sleep(2)  # Prevent CPU spike during hardware failure


    print("Video Publisher started. Sending stream to 'felix/video'...", flush=True)
    
    last_hb_time = 0
    status_file = os.path.join(os.path.dirname(__file__), "..", "felix_counter.txt")
    
    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            # --- LAG REDUCTION ---
            # Resize to 640x480 for faster encoding/transmission
            frame = cv2.resize(frame, (640, 480))
            
            # Encode at medium quality (40% is the sweet spot for balance)
            _, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 40])
            
            # Publish frame
            pub_video.put(buffer.tobytes())
            
            # --- HEARTBEAT & TELEMETRY ---
            now = time.time()
            if now - last_hb_time > 2.0:
                # Read last counter received by this Pi
                last_counter = 0
                try:
                    if os.path.exists(status_file):
                        with open(status_file, "r") as f:
                            last_counter = int(f.read().strip())
                except:
                    pass

                hb = get_heartbeat("Pi", last_counter=last_counter)
                pub_hb.put(json.dumps(hb))
                last_hb_time = now
            
            # Control FPS (using small sleep to prevent CPU hogging)
            time.sleep(1/config['config']['video_fps'])
            
    except KeyboardInterrupt:
        print("Stopping Pi Video Publisher...")
    finally:
        cap.release()
        session.close()

if __name__ == "__main__":
    main()
