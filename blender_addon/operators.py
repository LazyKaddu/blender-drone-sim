import bpy
import os
import subprocess
from . import exporter
from . import ipc

class DRONE_OT_enable(bpy.types.Operator):
    bl_idname = "drone.enable_sim"
    bl_label = "Enable Drone Sim"
    bl_description = "Activates the Drone Simulation UI and features for this specific Blender file."
    
    def execute(self, context):
        print("[DEBUG Blender Addon] Enabling Drone Simulation UI...")
        context.scene.drone_sim_enabled = True
        self.report({'INFO'}, "Drone Simulation active for this file!")
        return {'FINISHED'}

class DRONE_OT_compile(bpy.types.Operator):
    bl_idname = "drone.compile_and_reload"
    bl_label = "Compile and Reload"
    bl_description = "Exports the scene to URDF and pings PyBullet to hot-reload."
    
    def execute(self, context):
        export_path = context.scene.drone_export_path
        print(f"[DEBUG Blender Addon] Compiling and reloading URDF to: {export_path}")
        
        # 1. Export the Blender Scene to URDF
        exporter.export_scene_to_urdf(export_path)
        
        # 2. Ping the Python Simulator to hot-reload
        ipc.ping_reload()
        
        self.report({'INFO'}, "Successfully compiled and hot-reloaded the PyBullet world!")
        return {'FINISHED'}

class DRONE_OT_connect(bpy.types.Operator):
    bl_idname = "drone.connect_telemetry"
    bl_label = "Connect Telemetry"
    bl_description = "Starts listening for live drone coordinates from PyBullet."
    
    def execute(self, context):
        print("[DEBUG Blender Addon] Connecting Telemetry...")
        ipc.start_telemetry_listener()
        self.report({'INFO'}, "Connecting to telemetry...")
        return {'FINISHED'}

class DRONE_OT_disconnect(bpy.types.Operator):
    bl_idname = "drone.disconnect_telemetry"
    bl_label = "Disconnect Telemetry"
    bl_description = "Stops the telemetry link."
    
    def execute(self, context):
        print("[DEBUG Blender Addon] Disconnecting Telemetry...")
        ipc.stop_telemetry_listener()
        self.report({'INFO'}, "Disconnected telemetry.")
        return {'FINISHED'}

class DRONE_OT_train(bpy.types.Operator):
    bl_idname = "drone.start_training"
    bl_label = "Start Training"
    bl_description = "Launches the AI training script in the background."
    
    def execute(self, context):
        # TODO: Hook this up to run python train.py 
        # e.g., subprocess.Popen([sys.executable, "train.py"])
        self.report({'INFO'}, "Training placeholder triggered! We will hook this up later.")
        return {'FINISHED'}
