# custom_drone_env/server.py
import json
import asyncio
import threading
import websockets
from http.server import BaseHTTPRequestHandler, HTTPServer


class HotReloadHTTPServer:
    """Handles HTTP requests for hot-reloading the simulation world."""
    def __init__(self, reload_callback, host='localhost', port=5000):
        self.reload_callback = reload_callback
        self.http_host = host
        self.http_port = port

    def _start_http(self):
        # We define the handler dynamically to pass the callback
        class ReloadHandler(BaseHTTPRequestHandler):
            def do_GET(req_self):
                if req_self.path == '/reload':
                    print("[DEBUG Server] HTTP GET /reload received. Triggering reload_callback.")
                    self.reload_callback() # Tell the Environment to reload!
                    req_self.send_response(200)
                    req_self.end_headers()
                    req_self.wfile.write(b"Reloading world")
                
            def log_message(self, format, *args):
                pass # Suppress spammy HTTP logs

        server = HTTPServer((self.http_host, self.http_port), ReloadHandler)
        server.serve_forever()


class TelemetryWSServer:
    """Handles WebSocket connections for real-time telemetry streaming and broadcasting."""
    def __init__(self, host='localhost', port=8765):
        self.drone_state = {}
        self.clients = set()
        self.ws_loop = None
        self.ws_host = host
        self.ws_port = port

    def update_state(self, new_state: dict):
        """The environment calls this every step to update the telemetry."""
        # print(f"[DEBUG Server] update_state called: {new_state}") # Can be uncommented, but very spammy
        # Format the data cleanly for Blender's coordinate system
        self.drone_state = {
            "type": "telemetry",
            "location": [new_state.get("x", 0.0), new_state.get("y", 0.0), new_state.get("z", 0.0)],
            "rotation": [new_state.get("r", 0.0), new_state.get("p", 0.0), new_state.get("y_rot", 0.0)],
            "scale": [1.0, 1.0, 1.0]
        }

    def broadcast_data(self, data: dict):
        """Immediately broadcast custom data to all connected clients."""
        print(f"[DEBUG Server] broadcast_data called with: {data}")
        if not self.ws_loop or not self.clients:
            return
            
        message = json.dumps(data)
        
        # Safely execute the broadcast coroutine in the background asyncio loop
        async def _broadcast():
            websockets.broadcast(self.clients, message)
            
        asyncio.run_coroutine_threadsafe(_broadcast(), self.ws_loop)

    def _start_ws(self):
        async def telemetry_handler(websocket):
            print(f"[DEBUG Server] New WebSocket client connected: {websocket.remote_address}")
            self.clients.add(websocket)
            try:
                while True:
                    await websocket.send(json.dumps(self.drone_state))
                    await asyncio.sleep(1/60) # Broadcast at 60 FPS
            finally:
                print(f"[DEBUG Server] WebSocket client disconnected: {websocket.remote_address}")
                self.clients.remove(websocket)

        async def _main():
            self.ws_loop = asyncio.get_running_loop()
            async with websockets.serve(telemetry_handler, self.ws_host, self.ws_port):
                await asyncio.Future() # Run forever

        asyncio.run(_main())


class SimulationIPC(HotReloadHTTPServer, TelemetryWSServer):
    """
    Combined IPC interface used by the PyBullet Environment.
    Inherits from both HTTP (hot-reload) and WebSocket (telemetry) servers.
    """
    def __init__(self, reload_callback, http_port=5000, ws_port=8765):
        print(f"[DEBUG Server] Initializing SimulationIPC on HTTP port {http_port} and WS port {ws_port}")
        # Initialize both parent classes explicitly
        HotReloadHTTPServer.__init__(self, reload_callback=reload_callback, port=http_port)
        TelemetryWSServer.__init__(self, port=ws_port)
        
        # Start background threads immediately upon initialization
        threading.Thread(target=self._start_http, daemon=True).start()
        threading.Thread(target=self._start_ws, daemon=True).start()