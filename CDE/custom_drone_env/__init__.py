from gymnasium.envs.registration import register

register(
    id='CustomDrone-v0',
    entry_point='custom_drone_env.env:CustomDroneEnv',
)