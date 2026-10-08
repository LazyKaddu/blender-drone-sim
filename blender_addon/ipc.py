import threading
import asyncio
import json
import urllib.request
import bpy
from collections import deque

_telemetry_queue = deque()
_ws_thread = None
_loop = None
_running = False

def ping_reload():
    """Sends a GET request to the PyBullet environment to trigger a hot-reload."""
    print("[DEBUG Blender Addon] ping_reload() called. Sending GET request to http://localhost:5000/reload")
    try:
        urllib.request.urlopen("http://localhost:5000/reload", timeout=1.0)
    except Exception as e:
        print(f"[Drone Sim IPC] Failed to ping reload: {e}")

def is_connected():
    return _running

def start_telemetry_listener():
    """Spins up a background thread to listen to WebSocket telemetry."""
    print("[DEBUG Blender Addon] start_telemetry_listener() called.")
    global _ws_thread, _running
    if _running:
        return
    _running = True
    _ws_thread = threading.Thread(target=_run_async_loop, daemon=True)
    _ws_thread.start()

def stop_telemetry_listener():
    """Safely kills the WebSocket thread."""
    print("[DEBUG Blender Addon] stop_telemetry_listener() called.")
    global _running, _loop
    _running = False
    if _loop is not None and _loop.is_running():
        def cancel_all_tasks():
            for task in asyncio.all_tasks(_loop):
                task.cancel()
        try:
            _loop.call_soon_threadsafe(cancel_all_tasks)
        except Exception as e:
            print(f"[Drone Sim IPC] Error while cancelling tasks: {e}")

def _run_async_loop():
    global _loop
    _loop = asyncio.new_event_loop()
    asyncio.set_event_loop(_loop)
    try:
        _loop.run_until_complete(_listen_ws())
    except asyncio.CancelledError:
        pass
    finally:
        try:
            pending = asyncio.all_tasks(_loop)
            for task in pending:
                task.cancel()
            if pending:
                _loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))
        except Exception:
            pass
        _loop.close()

async def _listen_ws():
    import websockets
    uri = "ws://localhost:8765"
    while _running:
        try:
            print(f"[DEBUG Blender Addon] Attempting to connect to {uri}...")
            async with websockets.connect(uri) as ws:
                print("[Drone Sim IPC] Connected to Telemetry Server!")
                while _running:
                    message = await ws.recv()
                    data = json.loads(message)
                    _telemetry_queue.append(data)
        except Exception as e:
            # If PyBullet is down, silently retry every second
            await asyncio.sleep(1.0)

def process_telemetry_queue():
    """
    Called periodically by Blender's app timer (on the main thread).
    We pop off the latest telemetry data and update the 3D objects.
    """
    # Drain the queue so we only process the most recent state
    data = None
    print("processing telemantary queue")
    print("queue items",_telemetry_queue)
    while _telemetry_queue:
        data = _telemetry_queue.popleft()
    print("processing the telmentary")

    print("value of telmary queue ",data)
        
    if data and data.get("type") == "telemetry":
        loc = data.get("location", [0, 0, 0])
        rot = data.get("rotation", [0, 0, 0])
        
        # Find the drone object in Blender (assuming it's named 'Drone')
        drone = bpy.data.objects.get("Drone")
        if drone:
            print("found drone : current location: ",loc)
            drone.location = loc
            # PyBullet rotation is Roll-Pitch-Yaw, which aligns with Blender's XYZ Euler
            drone.rotation_euler = rot
        else:
            print("[Drone Sim IPC] ERROR: Could not find an object named 'Drone' in the Blender scene! Make sure the spelling and capitalization match exactly.")
            
    # Tell Blender to run this timer again in ~16ms (approx 60 FPS)
    return 1.0 / 60.0
