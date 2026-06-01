# lidar_ros Source Snapshot

## Upstream

- URL: `https://github.com/sudreamcarver/lidar_ros`
- Snapshot commit: `a88fcec0a207e0a2765fb4542ffbc8b1913f60ee`
- Retrieved at: `2026-06-01T01:46:25Z`
- Retrieval method: `git clone --depth 1`

## Snapshot Scope

This directory is a source reference snapshot for the rober LiDAR integration
planning work. It intentionally excludes upstream `.git/`, `.clangd/`,
`compile_commands.json`, and `.catkin_workspace` files.

Included files:

- `README.md`
- `LICENSE`
- `plot.py`
- `src/lidar_pkg/CMakeLists.txt`
- `src/lidar_pkg/package.xml`
- `src/lidar_pkg/launch/lidar_vi.xml`
- `src/lidar_pkg/rviz/lidar_config.rviz`
- `src/lidar_pkg/scripts/lidar_driver.py`
- `src/lidar_pkg/src/lidar_driver.cpp`

## Use Boundary

This is not vendored production ROS2 code. Treat it as protocol and ROS topic
reference material for the拆机 YDLIDAR currently mounted on the robot. Any
runtime integration into `onboard/` must be implemented separately and verified
with ROS2 Humble and target hardware.
