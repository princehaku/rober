#!/usr/bin/env bash
# WSL/Linux helper for Docker-based ROS2 Humble build validation.
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

docker build -t ros-rbs-humble:dev "$repo_root/docker/humble"
docker run --rm \
    -v "$repo_root:/ws" \
    -w /ws \
    ros-rbs-humble:dev \
    bash -lc "source /opt/ros/humble/setup.bash && rm -rf build install log && colcon build --symlink-install"
