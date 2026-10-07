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

