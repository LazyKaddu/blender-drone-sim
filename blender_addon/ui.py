import bpy
from . import ipc

class DRONE_PT_panel(bpy.types.Panel):
    bl_label = "Drone Simulation Toolkit"
    bl_idname = "DRONE_PT_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Drone Sim"

    def draw(self, context):
        layout = self.layout
        
        # If the user hasn't explicitly started the addon for this specific .blend file
        if not context.scene.drone_sim_enabled:
            layout.label(text="Sim inactive for this file.", icon='INFO')
            layout.operator("drone.enable_sim", text="Start Addon", icon='PLAY')
            return
            
        # --- Export Settings ---
        layout.label(text="Export Settings:")
        layout.prop(context.scene, "drone_export_path")
        layout.separator()
        
        # --- Environment Control ---
        layout.label(text="Environment Control:")
        layout.operator("drone.compile_and_reload", text="Reload Environment", icon='FILE_REFRESH')
        layout.separator()
        
        # --- Telemetry Control ---
        layout.label(text="Telemetry Link:")
        if ipc.is_connected():
            layout.operator("drone.disconnect_telemetry", text="Stop Telemetry", icon='CANCEL')
            layout.label(text="Status: LIVE", icon='PLAY')
        else:
            layout.operator("drone.connect_telemetry", text="Start Telemetry", icon='LINKED')
            layout.label(text="Status: OFFLINE", icon='PAUSE')
            
        layout.separator()
        
        # --- AI / Training Control ---
        layout.label(text="Machine Learning:")
        layout.operator("drone.start_training", text="Start Training", icon='CONSOLE')
