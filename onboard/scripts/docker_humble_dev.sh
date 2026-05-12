#!/usr/bin/env bash
# Start an interactive ROS2 Humble development shell in Docker on macOS or Linux.
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
image="${ROS_HUMBLE_IMAGE:-ros-rbs-humble:dev}"
container_name="${ROS_HUMBLE_CONTAINER:-trashbot-humble-dev}"
x11_enabled="${ROS_HUMBLE_ENABLE_X11:-0}"

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
    -e "ROS_DOMAIN_ID=${ROS_DOMAIN_ID:-0}"
    -v "$repo_root:/ws"
    -v "$repo_root/.ros_home:/root/.ros"
    -w /ws
)

# X11 is a Linux GUI integration path, not the default Docker Desktop path on
# macOS. Keep it explicit so Mac runs do not inherit stale WSL/Linux bind paths.
if [ "$x11_enabled" = "1" ]; then
    run_args+=(
        -e "DISPLAY=${DISPLAY:-}"
        -e "QT_X11_NO_MITSHM=1"
    )
    if [ -d /tmp/.X11-unix ]; then
        run_args+=(-v /tmp/.X11-unix:/tmp/.X11-unix:rw)
    else
        echo "WARN: ROS_HUMBLE_ENABLE_X11=1 but /tmp/.X11-unix does not exist; continuing without X11 socket mount." >&2
    fi
fi

run_args+=(
    "${extra_args[@]}"
    "$image"
    bash -l
)

docker run "${run_args[@]}"
