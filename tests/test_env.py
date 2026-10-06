import numpy as np
import pytest
from gymnasium import spaces
from custom_drone_env.env import CustomDroneEnv

class DummyDroneEnv(CustomDroneEnv):
    """A concrete implementation of our abstract environment for testing."""
    def _actionSpace(self):
        return spaces.Dict({"0": spaces.Box(low=-1, high=1, shape=(4,))})

    def _observationSpace(self):
        return spaces.Dict({"0": spaces.Box(low=-1, high=1, shape=(12,))})

    def _computeObs(self):
        return {"0": np.zeros(12, dtype=np.float32)}

    def _preprocessAction(self, action):
        # BaseAviary expects the processed action (RPMs) to be a flat array of shape (NUM_DRONES, 4)
        return np.zeros((1, 4), dtype=np.float32)

    def _computeReward(self):
        return 1.0

    def _computeTerminated(self):
        return False

    def _computeTruncated(self):
        return False

    def _computeInfo(self):
        return {"test": True}

def test_environment_initialization():
    """Test that the environment initializes and loads pybullet properly without IPC for isolation."""
    # We run gui=False so tests run headlessly without opening windows
    env = DummyDroneEnv(enable_ipc=False, gui=False)
    obs, info = env.reset()
    
    assert obs is not None
    assert isinstance(info, dict)
    
    # Provide a dummy hover action (RPMs/thrust/PID depending on the action space)
    action = {"0": np.array([0.0, 0.0, 0.0, 0.0])}
    obs, reward, terminated, truncated, info = env.step(action)
    
    assert reward == 1.0
    assert terminated is False
    assert info["test"] is True 
    
    env.close()

def test_environment_telemetry_push():
    """Test that the IPC server boots up and telemetry works."""
    env = DummyDroneEnv(enable_ipc=True, gui=False)
    env.reset()
    
    # Step to push telemetry
    action = {"0": np.array([0.0, 0.0, 0.0, 0.0])}
    env.step(action)
    
    # Check that the IPC object properly parsed and stored the state
    assert env.ipc.drone_state is not None
    assert "location" in env.ipc.drone_state
    assert "rotation" in env.ipc.drone_state
    assert "scale" in env.ipc.drone_state
    
    # Check that location has 3 elements (x, y, z)
    assert len(env.ipc.drone_state["location"]) == 3
    
    env.close()
