# custom_drone_env/env.py
import os
import pybullet as p
from gym_pybullet_drones.envs.HoverAviary import HoverAviary
from gym_pybullet_drones.utils.enums import DroneModel, Physics

# Import our new helper
from custom_drone_env.server import SimulationIPC 

class CustomDroneEnv(HoverAviary):
    def __init__(self, urdf_path="C:/path/to/export/world.urdf", enable_ipc=True, **kwargs):
        print(f"[DEBUG CustomDroneEnv] __init__ called with urdf_path={urdf_path}, enable_ipc={enable_ipc}")
        self.urdf_path = urdf_path
        self.world_id = None
        self.enable_ipc = enable_ipc
        
        # 1. Start the Base PyBullet Physics
        super().__init__(drone_model=DroneModel.CF2X, physics=Physics.PYB, **kwargs)

        # 2. Boot up the background servers (HTTP & WebSockets)
        if self.enable_ipc:
            print("[INFO] Booting IPC Servers (Port 5000 & 8765)...")
            self.ipc = SimulationIPC(reload_callback=self._hot_reload_world)

    def _addObstacles(self):
        """Called automatically during env.reset(). Loads the Blender world."""
        print("[DEBUG CustomDroneEnv] _addObstacles() called")
        super()._addObstacles() 
        self._load_blender_urdf()

    def _load_blender_urdf(self):
        if os.path.exists(self.urdf_path):
            self.world_id = p.loadURDF(self.urdf_path, basePosition=[0, 0, 0], useFixedBase=True, physicsClientId=self.CLIENT)
            print(f"[INFO] Loaded Blender world: {self.urdf_path}")
        else:
            print("[WARNING] No compiled URDF found.")

    def _hot_reload_world(self):
        """Called by the HTTP server when Blender clicks 'Compile'."""
        print("[INFO] Hot-Reload Triggered by Blender!")
        if self.world_id is not None:
            p.removeBody(self.world_id, physicsClientId=self.CLIENT) # Delete old world
        self._load_blender_urdf() # Load the new one instantly

    def step(self, action):
        """The main physics step. We override it to push telemetry."""
        # 1. Step the PyBullet physics engine
        obs, reward, terminated, truncated, info = super().step(action)
        
        # 2. Push telemetry to the WebSocket helper
        if self.enable_ipc:
            kin = obs["0"] # Assuming obs="kin"
            state = {
                "x": float(kin[0]), "y": float(kin[1]), "z": float(kin[2]),
                "r": float(kin[7]), "p": float(kin[8]), "y_rot": float(kin[9])
            }
            self.ipc.update_state(state)
            print("State: ", state)
        return obs, reward, terminated, truncated, info

    # Mandatory Gym/Aviary Overrides (To be implemented by specific tasks)
    def _computeReward(self):
        raise NotImplementedError("Child classes must implement this to define custom reward functions.")

    def _computeTerminated(self):
        raise NotImplementedError("Child classes must implement this to define custom termination conditions.")

    def _computeTruncated(self):
        raise NotImplementedError("Child classes must implement this to define custom truncation conditions.")

    def _computeInfo(self):
        raise NotImplementedError("Child classes must implement this to define custom info dictionaries.")