#!/usr/bin/env bash
# WSL/Linux helper for Docker-based ROS2 Humble build validation.
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
image="${ROS_HUMBLE_IMAGE:-ros-rbs-humble:dev}"
ubuntu_apt_mirror="${UBUNTU_APT_MIRROR:-https://mirrors.tuna.tsinghua.edu.cn/ubuntu}"
ros_apt_mirror="${ROS_APT_MIRROR:-https://mirrors.tuna.tsinghua.edu.cn/ros2/ubuntu}"
pip_index_url="${PIP_INDEX_URL:-https://pypi.tuna.tsinghua.edu.cn/simple}"

build_args=(
    --build-arg "UBUNTU_APT_MIRROR=$ubuntu_apt_mirror"
    --build-arg "ROS_APT_MIRROR=$ros_apt_mirror"
    --build-arg "PIP_INDEX_URL=$pip_index_url"
    -t "$image"
    "$repo_root/docker/humble"
)

docker build "${build_args[@]}"

run_args=(
    --rm
    -v "$repo_root:/ws"
    -w /ws
    "$image"
    bash -lc "source /opt/ros/humble/setup.bash && rm -rf build install log && colcon build --symlink-install"
)

docker run "${run_args[@]}"
