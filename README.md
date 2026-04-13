# 🤖 FelixOS | Advanced Robotics Middleware

FelixOS is a high-performance, cross-platform robotics bridge designed to connect Windows workstations with Raspberry Pi edge nodes using **Zenoh 1.0** and **Tailscale VPN**.

## 🏗️ System Architecture

FelixOS uses a **Hybrid Mesh Topology**:
- **Workstation (PC)**: Acts as the primary Zenoh Listener and orchestration hub.
- **Robot (Pi)**: Acts as a fleet of Zenoh Connectors publishing high-frequency video and telemetry.
- **Network**: All communication happens over a Tailscale private mesh to bypass firewall and NAT issues.

---

## 📁 Directory Structure

The project is organized into two main domains:

### 🖥️ `computer/` (Workstation)
- **`website/`**: Contains the **Mission Control Dashboard**. 
    - `dashboard_server.py`: Flask-based MJPEG bridge and telemetry aggregator.
- **`topics/`**: Data flow agents.
    - `counter_publisher.py`: Generates simulation/command data for the robot.
    - `video_receiver.py`: (Legacy) OpenCV-based video listener.

### 🥧 `pi/` (Raspberry Pi)
- `video_publisher.py`: Captures V4L2 video, resizes for low latency, and sends heartbeats.
- `counter_subscriber.py`: Receives and logs command data from the PC.
- `status_server.py`: Light health-check server for remote monitoring.

### 📝 Core
- `start_all.py`: The **One-Click Orchestrator**. Automates remote SSH deployment and local dashboard launch.
- `config.json`: Master configuration for network endpoints and topics.
- `planning/`: Future feature roadmaps and system design documents.

---

## 🚀 Getting Started

### 1. Requirements
Ensure Python 3.10+ is installed on both systems.
```bash
pip install eclipse-zenoh flask opencv-python psutil fabric
```

### 2. Configuration
Update `config.json` with your Tailscale IP addresses:
- `nodes.pi.ip`: Your Raspberry Pi's Tailscale IP.
- `zenoh.listen`: Local workstation endpoints.

### 3. Launch
Run the master orchestrator from your PC:
```powershell
python start_all.py
```

---

## 📈 Performance & Known Issues

### 🎥 Video Quality vs. CPU Usage
Our current video pipeline is optimized for **Global Zero-Latency** but comes with a hardware trade-off:
- **Resolution**: 320x240 (Standard Low-Def)
- **Framerate**: 30 FPS
- **Pi CPU Load**: ~65% - 70%
- **PC CPU Load**: ~5%

> [!WARNING]
> **Performance Bottleneck:** The Raspberry Pi's CPU is currently performing **Software JPEG Encoding** (`cv2.imencode`). Despite the low resolution, this is mathematically expensive for the Pi. 
> 
> **Future Optimization:** To increase video quality while decreasing CPU load, we must pivot to **Hardware Acceleration** via GStreamer or `libcamera` with H.264/V4L2 encoding. This would theoretically drop Pi CPU usage to <15% even at 720p.

---

## ⚡ Hardware Note: Power Management
FelixOS includes deep telemetry for hardware health. If the dashboard reports **Undervoltage** (throttled code `0x50005`), ensure the Raspberry Pi is powered by a high-quality **5V/3A adapter**. Undervoltage will cause USB resets, leading to camera failure and stuttering.

---

## 🔗 Repository
Maintained at: [felix34003/FelixOS](https://github.com/felix34003/FelixOS)
