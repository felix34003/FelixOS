import os
import sys
import psutil
import subprocess
import time
from fabric import Connection
from utils import load_config

def identify_running_processes():
    """Identify FelixOS-related python processes on the local PC."""
    current_pid = os.getpid()
    target_scripts = ['video_receiver.py', 'counter_publisher.py', 'start_all.py']
    
    print("Checking for existing FelixOS processes...")
    found_any = False
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            # Check if it's a python process
            name = proc.info['name']
            if name and 'python' in name.lower():
                cmdline = proc.info['cmdline']
                if cmdline:
                    cmd_str = " ".join(cmdline)
                    # Identify if it matches our scripts
                    if any(script in cmd_str for script in target_scripts):
                        if proc.info['pid'] != current_pid:
                            print(f"  [Active] {cmd_str} (PID: {proc.info['pid']})")
                            found_any = True
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    
    if not found_any:
        print("  No other FelixOS processes found.")


def main():
    config = load_config()
    pi_cfg = config['nodes']['pi']
    
    print("=== FelixOS One-Click Startup ===")
    
    # 1. Local PC Identification
    identify_running_processes()

    # 2. Ping Check
    print(f"Pinging Pi at {pi_cfg['ip']}...")
    ping_cmd = ["ping", "-n", "1", pi_cfg['ip']]
    if subprocess.call(ping_cmd, stdout=subprocess.DEVNULL) != 0:
        print("Error: Pi is unreachable. Verify Tailscale is active.")
        return
    print("Pi is online!")

    # 3. Remote Startup
    print(f"Starting remote nodes on Pi ({pi_cfg['ip']})...")
    conn = Connection(
        host=pi_cfg['ip'], 
        user=pi_cfg['user'], 
        connect_kwargs={"password": pi_cfg['ssh_pass']}
    )
    
    # Check for existing FelixOS related scripts on the Pi
    # Using specific patterns for safety
    pi_scripts = "video_publisher|counter_subscriber|status_server"
    print(f"Checking for existing processes on Pi...")
    conn.run(f"pgrep -l -u {pi_cfg['user']} -f '{pi_scripts}' || echo '  No existing Pi processes found.'", warn=True)
    
    # NEW: Forcefully clear the Zenoh port over SSH using sudo
    print("Forcefully clearing Zenoh port (7447) on Pi...")
    conn.run(f"echo '{pi_cfg['ssh_pass']}' | sudo -S fuser -k 7447/tcp || true", warn=True)
    
    # Start Pi nodes in background

    # We use nohup to keep them running after terminal exit
    pi_proj_dir = f"/home/{pi_cfg['user']}/FelixOS"
    conn.run(f"mkdir -p {pi_proj_dir}/pi")
    
    print("Cleaning up old processes on Pi...")
    conn.run("pkill -u ece_441 python3 || true")
    
    print("Uploading latest code to Pi...")
    
    commands = [
        f"nohup {pi_cfg['venv']} {pi_proj_dir}/pi/video_publisher.py >> {pi_proj_dir}/pi_nodes.log 2>&1 &",
        f"nohup {pi_cfg['venv']} {pi_proj_dir}/pi/counter_subscriber.py >> {pi_proj_dir}/pi_nodes.log 2>&1 &",
        f"nohup {pi_cfg['venv']} {pi_proj_dir}/pi/status_server.py >> {pi_proj_dir}/pi_nodes.log 2>&1 &"
    ]

    
    for cmd in commands:
        conn.run(cmd, disown=True)
    
    print("Remote nodes launched.")

    # 3. Local Startup
    print("Launching local PC nodes...")
    
    pc_nodes = []
    
    # 1. Counter Publisher
    print("Launching Local PC Nodes...", flush=True)
    # 1. Counter Publisher
    pc_nodes.append(subprocess.Popen([sys.executable, f"{os.path.dirname(__file__)}/computer/topics/counter_publisher.py"]))
    
    # 2. Native OSD Video Receiver (Fastest Performance)
    pc_nodes.append(subprocess.Popen([sys.executable, f"{os.path.dirname(__file__)}/computer/video_receiver_osd.py"]))
    
    print("System active. Press Ctrl+C to stop all.", flush=True)
    try:
        for node in pc_nodes:
            node.wait()
    except KeyboardInterrupt:
        print("\nShutting down FelixOS...")
    finally:
        for node in pc_nodes:
            node.terminate()
        print("FelixOS session ended.")

if __name__ == "__main__":
    main()
