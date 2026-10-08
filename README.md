# Blender Drone Sim (`custom-drone-env`)

A modular, lightweight robotics simulation framework and level compiler that bridges Blender and PyBullet via Gymnasium. Designed specifically for training high-frequency AI policies—such as Diffusion Policies (Action Chunking) and Deep Reinforcement Learning—without the heavy hardware overhead of enterprise simulation suites.

## Architecture Overview

```plaintext
┌───────────────────────────────┐
│        Blender Viewport       │ ◄─── Telemetry (WebSocket :8765) ───┐
│ (Level Editor / Digital Twin) │ ──── Compile Event (HTTP :5000) ──┐ │
└───────────────────────────────┘                                   │ │
                                                                    ▼ │
┌───────────────────────────────┐                             ┌────────────────┐
│      PyBullet Backend         │ ◄── Parse URDF / Meshes ────┤  Local Export  │
│ (CustomDroneEnv : BaseAviary) │                             │ (.urdf / .obj) │
└──────────────┬────────────────┘                             └────────────────┘
               │
               ▼
┌───────────────────────────────┐
│     Gymnasium Interface       │ ◄── Action Chunks [16, 4] ─── Diffusion Policy /
│   `gym.make("CustomDrone-v0")`│ ─── Observations (RGB / Kin) ── RL Model
└───────────────────────────────┘
```

The system decouples visual level design, rigid-body physics, and policy inference into three non-blocking asynchronous processes:

1. **Blender Level Compiler (Add-on)**: Treat Blender as a visual CAD/game-engine IDE. Tag meshes as obstacles or spawn zones, click compile, and dynamically serialize geometry into a unified URDF specification with accompanying `.obj` meshes.
2. **PyBullet Physics Engine (`CustomDroneEnv`)**: Built on top of `gym-pybullet-drones`'s `BaseAviary`. Handles quadcopter aerodynamics, propeller wash, motor dynamics, and hardware-accelerated OpenGL/EGL camera synthesis.
3. **IPC Bridge & Digital Twin Synchronization**:
   - A background HTTP listener on `localhost:5000` enables zero-restart hot-reloading of scene geometry directly into the active simulation loop.
   - A non-blocking WebSocket stream on `localhost:8765` broadcasts drone kinematics (`[x, y, z, roll, pitch, yaw]`) back to Blender, driving a real-time digital twin preview in the viewport.

## Features

- **Blender as an IDE**: Visually place obstacles, spawn points, and waypoints; export directly to PyBullet-ready URDFs.
- **Zero-Restart Hot Reloading**: Modify geometry in Blender, recompile, and reset the simulation physics without killing the training run or clearing CUDA memory.
- **Bi-directional Live Telemetry**: Stream simulation state back into Blender to drive real-time camera rigs and 3D drone previews at ~60 FPS.
- **Gymnasium Standard Compliance**: Fully registered under Gymnasium (`CustomDrone-v0`), ready for drop-in vectorization via `gym.vector.AsyncVectorEnv`.
- **Diffusion Policy Ready**: Pre-configured action spaces and sensory modalities tailored for continuous action-chunking architectures ($T_a = 16$).
- **Dual Observation Modes**:
  - `obs="kin"`: High-speed kinematics (linear/angular velocities, orientation, positions) for fast CPU-bound iteration.
  - `obs="rgb"`: EGL/OpenGL hardware-accelerated synthetic camera feeds ($224 \times 224$) for end-to-end vision policies.

## Project Structure

```plaintext
blender-drone-sim/
├── pyproject.toml               # Package specifications & dependency definitions
├── README.md                    # Project documentation
├── blender_addon/               # Blender integration package
│   └── drone_compiler.py        # Viewport UI panel, URDF serializer & WS client
├── custom_drone_env/            # Core Python package
│   ├── __init__.py              # Registers "CustomDrone-v0" with Gymnasium
│   ├── env.py                   # CustomDroneEnv subclassing BaseAviary
│   └── server.py                # Asynchronous HTTP hot-reload & WebSocket servers
└── examples/
    ├── test_flight.py           # Basic physics sanity check
    └── parallel_vector_demo.py  # High-throughput AsyncVectorEnv demonstration
```

## Installation

### Prerequisites
- Python 3.8+
- Blender 3.6 LTS or Blender 4.x
- An environment with OpenGL / EGL rendering drivers (NVIDIA drivers recommended for visual observations)

### 1. Install the Simulation Environment
Install the published Python package directly using pip:
```bash
pip install kaddulive-blender-custom-drone-sim==0.1.1
```

### 2. Install the Blender Add-on
1. Use the provided `blender-addon.zip` archive containing the Blender integration.
2. In Blender, navigate to: `Edit -> Preferences -> Add-ons -> Install...`.
3. Select the `blender-addon.zip` file, and check the box to enable "Drone Sim Link".
4. Press `N` in the 3D Viewport to find the Drone Sim sidebar tab.

## Quickstart

### Step 1: Run the Environment
Run the baseline environment to initialize the PyBullet physics server and local IPC listeners:
```python
import time
import os
import numpy as np
from gymnasium import spaces
from CDE.custom_drone_env.env import CustomDroneEnv

class TestFlightEnv(CustomDroneEnv):
    def _actionSpace(self):
        return spaces.Dict({"0": spaces.Box(low=-1, high=1, shape=(4,))})

    def _observationSpace(self):
        return spaces.Dict({"0": spaces.Box(low=-np.inf, high=np.inf, shape=(20,))})

    def _computeObs(self):
        # Return the actual drone state so Blender gets the real physics!
        return {"0": self._getDroneStateVector(0)}

    def _preprocessAction(self, action):
        # Provide enough RPM to all 4 motors to make it fly upwards
        return np.array([[16000, 16000, 16000, 16000]], dtype=np.float32)

    def _computeReward(self): return 0.0
    def _computeTerminated(self): return False
    def _computeTruncated(self): return False
    def _computeInfo(self): return {}

# Path to the exported URDF from Blender
urdf_path = os.path.abspath("path/to/your/scene.urdf")

# Initialize environment, spawning the drone 5 meters in the air
env = TestFlightEnv(
    urdf_path=urdf_path, 
    enable_ipc=True,
    initial_xyzs=np.array([[0.0, 0.0, 5.0]])
)
obs, info = env.reset()

print("[INFO] Environment is running. Waiting for Blender connections...")
try:
    while True:
        action = env.action_space.sample() 
        obs, reward, terminated, truncated, info = env.step(action)
        time.sleep(1.0 / env.CTRL_FREQ)
except KeyboardInterrupt:
    print("Stopping test flight environment...")
finally:
    env.close()
```

### Step 2: Build and Compile in Blender
1. Open a new or existing scene in Blender.
2. Select any mesh object (e.g., walls, pillars, obstacles).
3. Under the Drone Sim sidebar panel, tag the mesh with **Is Obstacle**.
4. Set the **URDF Path** in the UI to match where your script is looking.
5. Click **Reload Environment**.
6. Set the **GLB Path** and click **Start Telemetry** to view the live digital twin in Blender!

## High-Throughput Training with Vectorization
To train a Diffusion Policy or RL agent without rendering bottlenecks, use Gymnasium's native asynchronous multiprocessing wrapper:
```python
import gymnasium as gym
import custom_drone_env

# Spin up 16 isolated, parallel simulation workers across CPU threads
envs = gym.make_vec("CustomDrone-v0", num_envs=16, vectorization_mode="async")
obs, info = envs.reset()

# obs is a batched tensor: [16, observation_dim]
# Output action chunks: [16, action_dim]
```

## Coordinate Systems & Units

| Domain | Standard | Forward | Up | Units |
| :--- | :--- | :--- | :--- | :--- |
| Blender | Right-Handed | $+Y$ | $+Z$ | Meters (m), Radians |
| PyBullet | Right-Handed | $+X$ or $+Y$ (Model defined) | $+Z$ | Meters (m), Radians |
| Action Space | Normalized Continuous | Linear/Angular | $[-1.0, 1.0]$ | |

## Roadmap
- [x] Initial repository structure and `pyproject.toml` setup.
- [x] Blender mesh to URDF serialization parser.
- [ ] Non-blocking IPC HTTP listener for in-place resets.
- [ ] Bidirectional WebSocket telemetry streaming to Blender viewport objects.
- [ ] End-to-end integration examples for Hugging Face `lerobot` and Diffusion Policy chunking.

## License
MIT License. Feel free to adapt and expand for both academic robotics research and custom game-AI pipelines.
