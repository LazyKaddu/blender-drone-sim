bl_info = {
    "name": "Drone Sim Link",
    "description": "Bridges Blender to PyBullet for Drone Simulation",
    "author": "Aashish Negi",
    "version": (1, 0),
    "blender": (3, 0, 0),
    "category": "Development",
}

import bpy
import sys
import subprocess

# --- 1. Auto-Install Dependencies ---
def install_dependencies():
    """Ensures websockets is installed in Blender's bundled Python."""
    try:
        import websockets
    except ImportError:
        print("[Drone Sim] Websockets not found. Installing now...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "websockets"])
        print("[Drone Sim] Websockets successfully installed!")

# Install dependencies immediately so we can safely import our modules
install_dependencies()

from . import ipc
from . import operators
from . import ui

# --- 2. Registration ---
classes = (
    operators.DRONE_OT_enable,
    operators.DRONE_OT_compile,
    operators.DRONE_OT_connect,
    operators.DRONE_OT_disconnect,
    operators.DRONE_OT_train,
    ui.DRONE_PT_panel,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
        
    # Register global properties
    bpy.types.Scene.drone_export_path = bpy.props.StringProperty(
        name="URDF Path",
        description="Path to save the compiled URDF",
        default="C:/path/to/export/world.urdf",
        subtype='FILE_PATH'
    )
    
    # This boolean prevents the UI from cluttering up files unrelated to drone sim
    bpy.types.Scene.drone_sim_enabled = bpy.props.BoolProperty(
        name="Drone Sim Enabled",
        description="Is the drone simulation active for this blend file?",
        default=False
    )
    
    # Register the timer that polls the IPC queue
    bpy.app.timers.register(ipc.process_telemetry_queue)

def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)
        
    del bpy.types.Scene.drone_export_path
    del bpy.types.Scene.drone_sim_enabled
    
    ipc.stop_telemetry_listener()
    if bpy.app.timers.is_registered(ipc.process_telemetry_queue):
        bpy.app.timers.unregister(ipc.process_telemetry_queue)
