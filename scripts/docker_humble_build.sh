#!/usr/bin/env bash
# WSL/Linux helper for Docker-based ROS2 Humble build validation.
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
image="${ROS_HUMBLE_IMAGE:-ros-rbs-humble:dev}"
ubuntu_apt_mirror="${UBUNTU_APT_MIRROR:-https://mirrors.tuna.tsinghua.edu.cn/ubuntu}"
ros_apt_mirror="${ROS_APT_MIRROR:-https://mirrors.tuna.tsinghua.edu.cn/ros2/ubuntu}"
pip_index_url="${PIP_INDEX_URL:-https://pypi.tuna.tsinghua.edu.cn/simple}"
rosdep_source_mirror="${ROSDEP_SOURCE_MIRROR:-https://mirrors.tuna.tsinghua.edu.cn/github-raw/ros/rosdistro/master/rosdep}"
rosdistro_index_url="${ROSDISTRO_INDEX_URL:-https://mirrors.tuna.tsinghua.edu.cn/rosdistro/index-v4.yaml}"
skip_colcon="${SKIP_COLCON:-0}"

docker build \
    --build-arg "UBUNTU_APT_MIRROR=$ubuntu_apt_mirror" \
    --build-arg "ROS_APT_MIRROR=$ros_apt_mirror" \
    --build-arg "PIP_INDEX_URL=$pip_index_url" \
    --build-arg "ROSDEP_SOURCE_MIRROR=$rosdep_source_mirror" \
    --build-arg "ROSDISTRO_INDEX_URL=$rosdistro_index_url" \
    -t "$image" \
    "$repo_root/docker/humble"

if [ "$skip_colcon" = "1" ]; then
    echo "Docker image is ready: $image"
    exit 0
fi

docker run --rm \
    -v "$repo_root:/ws" \
    -w /ws \
    "$image" \
    bash -lc "unset AMENT_PREFIX_PATH CMAKE_PREFIX_PATH COLCON_PREFIX_PATH && source /opt/ros/humble/setup.bash && rm -rf build install log && colcon build --symlink-install"
