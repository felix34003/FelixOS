import zenoh
import json
import time
import sys
import os
import subprocess

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

    # Publisher for video (H.264 Stream)
    pub_video = session.declare_publisher(
        config['topics']['video'],
        reliability=zenoh.Reliability.BEST_EFFORT,
        congestion_control=zenoh.CongestionControl.DROP
    )
    # Publisher for heartbeat
    pub_hb = session.declare_publisher(f"{config['topics']['heartbeat']}/pi")
    
    # --- GO CRAZY: Hardware H.264 Pipeline ---
    # We use FFmpeg to grab from V4L2 and encode in hardware
    # -f v4l2: Force input format
    # -i /dev/video0: Input device
    # -c:v h264_v4l2m2m: Use Pi hardware H.264 encoder
    # -b:v 2M: Bitrate 2Mbps (Good for 640x480)
    # -g 30: GOP size (Keyframe every 1 second)
    # -f h264 -: Output raw H.264 to stdout
    ffmpeg_cmd = [
        "ffmpeg",
        "-hide_banner", "-loglevel", "error",
        "-f", "v4l2",
        "-video_size", "640x480",
        "-framerate", str(config['config']['video_fps']),
        "-i", "/dev/video0",
        "-c:v", "h264_v4l2m2m",
        "-b:v", "2M",
        "-g", str(config['config']['video_fps']),
        "-f", "h264",
        "-"
    ]

    print("Launching Hardware H.264 Encoder...", flush=True)
    process = subprocess.Popen(ffmpeg_cmd, stdout=subprocess.PIPE, bufsize=0)

    last_hb_time = 0
    status_file = os.path.join(os.path.dirname(__file__), "..", "felix_counter.txt")
    
    print("Go Crazy Vision active. Sending Hardware H.264 to Zenoh...", flush=True)

    try:
        # We read raw H.264 packets (NAL units) from ffmpeg stdout
        # A simple way is to read in chunks and let the decoder handle it
        buffer_size = 4096 
        while True:
            data = process.stdout.read(buffer_size)
            if not data:
                break
            
            # Publish raw H.264 bytes
            pub_video.put(data)
            
            # --- HEARTBEAT & TELEMETRY ---
            now = time.time()
            if now - last_hb_time > 2.0:
                last_counter = 0
                try:
                    if os.path.exists(status_file):
                        with open(status_file, "r") as f:
                            last_counter = int(f.read().strip())
                except: pass

                hb = get_heartbeat("Pi", last_counter=last_counter)
                pub_hb.put(json.dumps(hb))
                last_hb_time = now

    except KeyboardInterrupt:
        print("Stopping Pi Video Publisher...")
    finally:
        process.terminate()
        session.close()

if __name__ == "__main__":
    main()
