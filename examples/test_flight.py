import time
import os
import numpy as np
from gymnasium import spaces
from custom_drone_env.env import CustomDroneEnv

class TestFlightEnv(CustomDroneEnv):
    """
    A simple testing environment subclassing CustomDroneEnv.
    We implement the mandatory methods so BaseAviary doesn't complain.
    """
    def _actionSpace(self):
        return spaces.Dict({"0": spaces.Box(low=-1, high=1, shape=(4,))})

    def _observationSpace(self):
        # We need to accommodate the state vector from _getDroneStateVector
        return spaces.Dict({"0": spaces.Box(low=-np.inf, high=np.inf, shape=(20,))})

    def _computeObs(self):
        # Return the actual drone state so Blender gets the real physics!
        # _getDroneStateVector(0) returns a 20-element numpy array with pos, quat, rpy, vel, etc.
        return {"0": self._getDroneStateVector(0)}

    def _preprocessAction(self, action):
        # Just return zero RPMs for all 4 motors so it simply falls due to gravity (perfect for testing)
        return np.zeros((1, 4), dtype=np.float32)

    def _computeReward(self):
        return 0.0

    def _computeTerminated(self):
        return False

    def _computeTruncated(self):
        return False

    def _computeInfo(self):
        return {}

def run_test():
    urdf_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "custom_drone_env", "urdfs", "scene.urdf"))
    
    print("========================================")
    print("Starting Test Drone Environment...")
    print(f"Loading URDF from: {urdf_path}")
    print("========================================")

    # Initialize environment
    env = TestFlightEnv(urdf_path=urdf_path, enable_ipc=True)
    
    obs, info = env.reset()
    
    print("\n[INFO] Environment is running. Waiting for Blender connections...")
    print("[INFO] Press Ctrl+C to stop.\n")
    
    try:
        while True:
            action = env.action_space.sample() 
            
            obs, reward, terminated, truncated, info = env.step(action)
            
            # Sleep to roughly match real-time (usually 240Hz for PyBullet)
            time.sleep(1.0 / env.CTRL_FREQ)
            
            if terminated or truncated:
                obs, info = env.reset()
                
    except KeyboardInterrupt:
        print("\nStopping test flight environment...")
    finally:
        env.close()

if __name__ == "__main__":
    run_test()
