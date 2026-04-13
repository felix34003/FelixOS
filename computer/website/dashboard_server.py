import zenoh
import json
import sys
import os
import time
import threading
import webbrowser
from flask import Flask, render_template, Response, jsonify, request
from queue import Queue, Empty

sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
from utils import load_config, get_zenoh_config, register_signals

app = Flask(__name__)

frame_queue = Queue(maxsize=1)
node_stats  = {}
odom_data   = {}
pub_cmd_vel = None          # set once zenoh_worker initialises
config      = load_config()
stop_event  = threading.Event()


def video_handler(sample):
    try:
        data = bytes(sample.payload)
        if frame_queue.full():
            try:
                frame_queue.get_nowait()
            except Empty:
                pass
        frame_queue.put_nowait(data)
    except Exception:
        pass


def heartbeat_handler(sample):
    try:
        hb = json.loads(bytes(sample.payload).decode('utf-8'))
        node_stats[hb['node']] = hb
    except Exception:
        pass


def odom_handler(sample):
    global odom_data
    try:
        odom_data = json.loads(bytes(sample.payload).decode('utf-8'))
    except Exception:
        pass


def zenoh_worker():
    global pub_cmd_vel
    print("Connecting to Zenoh...")
    z_config = get_zenoh_config("listen")
    session  = zenoh.open(z_config)

    pub_cmd_vel = session.declare_publisher(config['topics']['cmd_vel'])

    subs = [
        session.declare_subscriber(config['topics']['video'],               video_handler),
        session.declare_subscriber(f"{config['topics']['heartbeat']}/*",    heartbeat_handler),
        session.declare_subscriber(config['topics']['odom'],                odom_handler),
        session.declare_subscriber(config['topics']['shutdown'], lambda _s: stop_event.set()),
    ]

    print("Zenoh Bridge active.")
    stop_event.wait()
    del subs
    session.close()


def gen_frames():
    while not stop_event.is_set():
        try:
            frame = frame_queue.get(timeout=2.0)
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
        except Empty:
            continue


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/video_feed')
def video_feed():
    return Response(gen_frames(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')


@app.route('/stats')
def stats():
    return jsonify(node_stats)


@app.route('/odom')
def odom():
    return jsonify(odom_data)


@app.route('/cmd', methods=['POST'])
def cmd():
    """
    Receive a drive command from the browser and publish it to felix/cmd_vel.
    Body: {"cmd": "w", "speed": 150}
    """
    data = request.get_json(silent=True)
    if pub_cmd_vel is not None and data:
        pub_cmd_vel.put(json.dumps(data))
    return jsonify({'ok': True})


def main():
    register_signals(stop_event)
    threading.Thread(target=zenoh_worker, daemon=True).start()

    def open_browser():
        time.sleep(2)
        print("Launching Dashboard...")
        webbrowser.open("http://localhost:5000")

    threading.Thread(target=open_browser, daemon=True).start()

    import logging
    log = logging.getLogger('werkzeug')
    log.setLevel(logging.ERROR)

    print("Starting FelixOS Mission Control on http://localhost:5000")
    app.run(host='0.0.0.0', port=5000, threaded=True)


if __name__ == "__main__":
    main()
