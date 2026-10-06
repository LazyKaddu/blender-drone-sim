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
import os

# --- 1. Auto-Install Dependencies ---
def install_dependencies():
    """Ensures websockets is installed in Blender's bundled Python."""
    try:
        import websockets
    except ImportError:
        print("[Drone Sim] Websockets not found. Installing now...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "websockets"])
        print("[Drone Sim] Websockets successfully installed!")

# We install dependencies immediately when the addon is loaded so we can safely import our IPC module
install_dependencies()

from . import ipc
from . import exporter

# --- 2. UI Panel ---
class DRONE_PT_panel(bpy.types.Panel):
    bl_label = "Drone Simulation Toolkit"
    bl_idname = "DRONE_PT_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Drone Sim"

    def draw(self, context):
        layout = self.layout
        
        # URDF Export Settings
        layout.label(text="Export Settings:")
        layout.prop(context.scene, "drone_export_path")
        
        # Compile Button
        layout.operator("drone.compile_and_reload", text="Compile & Reload", icon='FILE_REFRESH')
        
        layout.separator()
        
        # Telemetry Connection Status
        if ipc.is_connected():
            layout.label(text="Telemetry: Connected", icon='PLAY')
            layout.operator("drone.disconnect_telemetry", text="Disconnect", icon='CANCEL')
        else:
            layout.operator("drone.connect_telemetry", text="Connect Telemetry", icon='LINKED')

# --- 3. Operators ---
class DRONE_OT_compile(bpy.types.Operator):
    bl_idname = "drone.compile_and_reload"
    bl_label = "Compile and Reload"
    
    def execute(self, context):
        export_path = context.scene.drone_export_path
        
        # 1. Export the Blender Scene to URDF
        exporter.export_scene_to_urdf(export_path)
        
        # 2. Ping the Python Simulator to hot-reload
        ipc.ping_reload()
        
        self.report({'INFO'}, "Successfully compiled and hot-reloaded the PyBullet world!")
        return {'FINISHED'}

class DRONE_OT_connect(bpy.types.Operator):
    bl_idname = "drone.connect_telemetry"
    bl_label = "Connect Telemetry"
    
    def execute(self, context):
        ipc.start_telemetry_listener()
        self.report({'INFO'}, "Attempting to connect to PyBullet telemetry...")
        return {'FINISHED'}

class DRONE_OT_disconnect(bpy.types.Operator):
    bl_idname = "drone.disconnect_telemetry"
    bl_label = "Disconnect Telemetry"
    
    def execute(self, context):
        ipc.stop_telemetry_listener()
        self.report({'INFO'}, "Disconnected telemetry.")
        return {'FINISHED'}

# --- 4. Registration ---
classes = (
    DRONE_PT_panel,
    DRONE_OT_compile,
    DRONE_OT_connect,
    DRONE_OT_disconnect,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
        
    # Register a global property for the export path
    bpy.types.Scene.drone_export_path = bpy.props.StringProperty(
        name="URDF Path",
        description="Path to save the compiled URDF",
        default="C:/path/to/export/world.urdf",
        subtype='FILE_PATH'
    )
    
    # Register the timer that will poll the IPC queue and update the 3D viewport
    bpy.app.timers.register(ipc.process_telemetry_queue)

def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)
        
    del bpy.types.Scene.drone_export_path
    
    ipc.stop_telemetry_listener()
    if bpy.app.timers.is_registered(ipc.process_telemetry_queue):
        bpy.app.timers.unregister(ipc.process_telemetry_queue)
