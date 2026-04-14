# NEXT STEPS: Robust Startup and State Management

This document outlines the proposed improvements for the `group4os` startup process to ensure reliability and consistency across the PC and Raspberry Pi.

## 1. Rigorous Process Management (PC)
Current `identify_running_processes()` only lists processes. The next version will:
- **Actively Terminate**: Automatically kill any detected scripts like `dashboard_server.py`, `video_receiver_osd.py`, etc.
- **Port Release**: Wait for a brief timeout to ensure networking ports (like Flask or Zenoh) are fully released before restarting.

## 2. Surgical Process Killing (Pi)
Replace the blanket `pkill python3` with a targeted approach:
- Use `pgrep -f group4os | xargs kill -9` to ensure only this project's nodes are killed.
- This prevents interference with other system processes on the Pi.

## 3. Mandatory State Synchronization & Verification
Ensure the Pi is always in the same state as the PC:
- **Verified Transfers**: Run `test -f` on the Pi after every `conn.put()` to guarantee the file was written successfully.
- **Checksum Verification**: (Optional) Use `md5sum` to ensure file integrity.
- **Halt on Error**: If verification fails, the script will abort immediately instead of starting a broken system.

## 4. Node & Path Validation
Strictly map nodes to the verified directory structure:
- **PC Targets**:
    - `computer/orchestrator.py`
    - `computer/video_receiver_osd.py`
    - `computer/topics/counter_publisher.py`
    - `computer/website/dashboard_server.py`
- **Pi Targets**:
    - `pi/video_publisher.py`
    - `pi/counter_subscriber.py`
    - `pi/status_server.py`
    - `pi/arduino_bridge.py`

## 5. Tailscale Connectivity Check
Enhance the initial ping check to provide clearer instructions if the local Tailscale interface is "Starting" or "NoState".

---
*Drafted by Antigravity on 2026-04-14*
