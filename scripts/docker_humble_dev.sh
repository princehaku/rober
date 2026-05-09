#!/usr/bin/env bash
# Start an interactive ROS2 Humble development shell in Docker on WSL/Linux.
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
image="${ROS_HUMBLE_IMAGE:-ros-rbs-humble:dev}"
container_name="${ROS_HUMBLE_CONTAINER:-trashbot-humble-dev}"

mkdir -p "$repo_root/.ros_home"

extra_args=()
if [ -n "${EXTRA_DOCKER_ARGS:-}" ]; then
    read -r -a extra_args <<< "$EXTRA_DOCKER_ARGS"
fi

run_args=(
    --rm
    -it
    --name "$container_name"
    --network host
    --ipc host
    -e "DISPLAY=${DISPLAY:-}"
    -e "QT_X11_NO_MITSHM=1"
    -e "ROS_DOMAIN_ID=${ROS_DOMAIN_ID:-0}"
    -v "$repo_root:/ws"
    -v "$repo_root/.ros_home:/root/.ros"
    -w /ws
    "${extra_args[@]}"
    "$image"
    bash -lc "source /opt/ros/humble/setup.bash && if [ -f install/setup.bash ]; then source install/setup.bash; fi; exec bash"
)

docker run "${run_args[@]}"
