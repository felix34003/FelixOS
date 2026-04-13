import socket
import serial
import serial.tools.list_ports
import time
import sys
import os

# Add root to path for utils
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from utils import load_config

# Configuration
TCP_PORT = 5006
BIND_IP = '0.0.0.0'

def find_arduino_port():
    ports = list(serial.tools.list_ports.comports())
    for p in ports:
        if 'Arduino' in p.description or 'USB' in p.description:
            return p.device
    common_names = ['/dev/ttyUSB0', '/dev/ttyUSB1', '/dev/ttyACM0', '/dev/ttyACM1']
    for name in common_names:
        try:
            temp_ser = serial.Serial(name)
            temp_ser.close()
            return name
        except: continue
    return None

def main():
    config = load_config()
    arduino_port = find_arduino_port()
    if not arduino_port:
        print("Error: Could not find Arduino. Check USB connection.", flush=True)
        return

    try:
        ser = serial.Serial(arduino_port, 9600, timeout=1)
        print(f"Connected to Arduino on: {arduino_port}", flush=True)
    except Exception as e:
        print(f"Error connecting to serial: {e}", flush=True)
        return

    # Setup Socket Server (Native Implementation Clone)
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # Allow address reuse for quick restarts
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind((BIND_IP, TCP_PORT))
    server_socket.listen(1)
    
    print(f"Native Robot Node active on port {TCP_PORT}. Ready for commands...", flush=True)
    
    try:
        while True:
            conn, addr = server_socket.accept()
            print(f"Accepted Native Connection from {addr}", flush=True)

            while True:
                data = conn.recv(1024).decode('utf-8')
                if not data:
                    break
                
                # Relay to Arduino
                ser.write(data.encode('utf-8'))
                
                # Save last counter to file for telemetry OSD
                if "speed" not in data and "stop" not in data:
                    try:
                        with open(os.path.join(os.path.dirname(__file__), "..", "felix_counter.txt"), "w") as f:
                            f.write(data.strip())
                    except: pass

            conn.close()
            print("Controller Disconnected.", flush=True)
    except KeyboardInterrupt:
        print("\nShutting down...", flush=True)
    finally:
        server_socket.close()
        ser.close()

if __name__ == "__main__":
    main()
