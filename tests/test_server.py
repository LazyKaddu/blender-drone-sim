import time
import pytest
import urllib.request
from CDE.custom_drone_env.server import SimulationIPC

def test_http_hot_reload_callback():
    """Test that the HTTP server correctly receives /reload requests and triggers the callback."""
    called = False
    
    def mock_callback():
        nonlocal called
        called = True
        
    # Initialize the server (this spins up daemon threads for HTTP and WS)
    ipc = SimulationIPC(reload_callback=mock_callback, http_port=5001, ws_port=8766)
    
    # Give the background threads a tiny bit of time to bind to ports
    time.sleep(0.5)
    
    try:
        # Send a GET request to the hot-reload endpoint
        response = urllib.request.urlopen("http://localhost:5001/reload")
        
        assert response.status == 200
        assert response.read().decode('utf-8') == "Reloading world"
        assert called is True
    except Exception as e:
        pytest.fail(f"HTTP Hot-Reload Server failed: {e}")
