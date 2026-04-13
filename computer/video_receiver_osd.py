import zenoh
import cv2
import numpy as np
import json
import sys
import os
import time
import av

# Add root to path for utils
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from utils import load_config, get_zenoh_config

def main():
    config = load_config()
    
    print("--- NATIVE MISSION CONTROL (H.264 OSD) ---")
    print("Connecting to Zenoh...")
    z_config = get_zenoh_config("listen")
    session = zenoh.open(z_config)

    # Telemetry storage
    node_stats = {}

    # --- H.264 DECODER SETUP ---
    codec = av.CodecContext.create('h264', 'r')
    
    def heartbeat_handler(sample):
        try:
            hb = json.loads(bytes(sample.payload).decode('utf-8'))
            node_stats[hb['node']] = hb
        except: pass

    last_frame = None

    def video_handler(sample):
        nonlocal last_frame
        try:
            # Feed raw H.264 bytes into PyAV
            packets = codec.parse(bytes(sample.payload))
            for packet in packets:
                frames = codec.decode(packet)
                for frame in frames:
                    # Convert PyAV frame to OpenCV BGR format
                    img = frame.to_ndarray(format='bgr24')
                    
                    # --- DRAW OSD (On-Screen Display) ---
                    # Semi-transparent overlay
                    overlay = img.copy()
                    cv2.rectangle(overlay, (5, 5), (315, 80), (0, 0, 0), -1)
                    cv2.addWeighted(overlay, 0.5, img, 0.5, 0, img)

                    # Header
                    cv2.putText(img, "FELIX MISSION CONTROL [H.264]", (10, 20), 
                                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 1)
                    
                    # Stats
                    y = 40
                    for node, stats in node_stats.items():
                        temp = stats.get('temp', '--')
                        cpu = stats.get('cpu_percent', '--')
                        last_c = stats.get('last_counter', '0')
                        
                        color = (0, 255, 0)
                        temp_str = f"| {temp}C" if temp != 0.0 and temp != '--' else ""
                        status_line = f"{node}: {cpu}% CPU {temp_str}"
                        cv2.putText(img, status_line, (10, y), 
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.4, color, 1)
                        
                        count_line = f"STEP: {last_c}"
                        cv2.putText(img, count_line, (10, y + 15), 
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 0), 1)
                        y += 35

                    # Show frame
                    cv2.imshow("FelixOS Live", img)
                    if cv2.waitKey(1) & 0xFF == ord('q'):
                        os._exit(0)

        except Exception as e:
            pass

    # Subscriptions
    sub_video = session.declare_subscriber(config['topics']['video'], video_handler)
    sub_hb = session.declare_subscriber(f"{config['topics']['heartbeat']}/*", heartbeat_handler)
    
    print("Go Crazy OSD Active. Press 'q' in video window to exit.")
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        pass
    finally:
        cv2.destroyAllWindows()
        session.close()

if __name__ == "__main__":
    main()
