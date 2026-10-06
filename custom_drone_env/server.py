# custom_drone_env/server.py
import json
import asyncio
import threading
import websockets
from http.server import BaseHTTPRequestHandler, HTTPServer

class SimulationIPC:
    def __init__(self, reload_callback):
        self.reload_callback = reload_callback
        self.drone_state = {}
        
        # Start background threads immediately upon initialization
        threading.Thread(target=self._start_http, daemon=True).start()
        threading.Thread(target=self._start_ws, daemon=True).start()

    # --- HTTP Hot-Reload Server ---
    def _start_http(self):
        # We define the handler dynamically to pass the callback
        class ReloadHandler(BaseHTTPRequestHandler):
            def do_GET(req_self):
                if req_self.path == '/reload':
                    self.reload_callback() # Tell the Environment to reload!
                    req_self.send_response(200)
                    req_self.end_headers()
                    req_self.wfile.write(b"Reloading world")
                
            def log_message(self, format, *args):
                pass # Suppress spammy HTTP logs

        server = HTTPServer(('localhost', 5000), ReloadHandler)
        server.serve_forever()

    # --- WebSocket Telemetry Server ---
    def update_state(self, new_state: dict):
        """The environment calls this every step to update the telemetry."""
        self.drone_state = new_state

    def _start_ws(self):
        async def telemetry_handler(websocket):
            while True:
                await websocket.send(json.dumps(self.drone_state))
                await asyncio.sleep(1/60) # Broadcast at 60 FPS

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        start_server = websockets.serve(telemetry_handler, "localhost", 8765)
        loop.run_until_complete(start_server)
        loop.run_forever()