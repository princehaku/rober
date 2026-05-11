#!/usr/bin/env bash
# WSL/Linux helper for Docker-based ROS2 Humble build validation.
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
image="${ROS_HUMBLE_IMAGE:-ros-rbs-humble:dev}"
dockerfile="$repo_root/docker/humble/Dockerfile"
base_image="$(awk 'toupper($1) == "FROM" {print $2; exit}' "$dockerfile")"
ubuntu_apt_mirror="${UBUNTU_APT_MIRROR:-https://mirrors.tuna.tsinghua.edu.cn/ubuntu}"
ros_apt_mirror="${ROS_APT_MIRROR:-https://mirrors.tuna.tsinghua.edu.cn/ros2/ubuntu}"
pip_index_url="${PIP_INDEX_URL:-https://pypi.tuna.tsinghua.edu.cn/simple}"
rosdep_source_mirror="${ROSDEP_SOURCE_MIRROR:-https://mirrors.tuna.tsinghua.edu.cn/github-raw/ros/rosdistro/master/rosdep}"
rosdistro_index_url="${ROSDISTRO_INDEX_URL:-https://mirrors.tuna.tsinghua.edu.cn/rosdistro/index-v4.yaml}"
skip_colcon="${SKIP_COLCON:-0}"
build_progress="${DOCKER_BUILD_PROGRESS:-plain}"

docker_diag_log=""

cleanup() {
    if [ -n "$docker_diag_log" ] && [ -f "$docker_diag_log" ]; then
        rm -f "$docker_diag_log"
    fi
}
trap cleanup EXIT

print_proxy_state() {
    # Do not print proxy values: they may include credentials. Set/unset is
    # enough to explain whether proxy routing can affect Docker registry fetch.
    local name
    for name in HTTP_PROXY HTTPS_PROXY ALL_PROXY NO_PROXY http_proxy https_proxy all_proxy no_proxy; do
        if [ -n "${!name:-}" ]; then
            printf '  %s=set\n' "$name"
        else
            printf '  %s=unset\n' "$name"
        fi
    done
}

print_docker_preflight() {
    echo "== Docker/Humble preflight =="
    echo "repo_root=$repo_root"
    echo "dockerfile=$dockerfile"
    echo "target_image=$image"
    echo "base_image=$base_image"
    echo "skip_colcon=$skip_colcon"
    echo "build_progress=$build_progress"
    echo "-- docker version --"
    docker version || true
    echo "-- docker context --"
    docker context ls || true
    echo "-- docker builder --"
    docker buildx version || true
    docker buildx ls || true
    echo "-- docker host storage / registry mirrors --"
    docker info --format 'ServerVersion={{.ServerVersion}} Driver={{.Driver}} DockerRootDir={{.DockerRootDir}} RegistryMirrors={{json .RegistryConfig.Mirrors}}' || true
    echo "-- proxy env state --"
    print_proxy_state
    echo "== End Docker/Humble preflight =="
}

classify_build_failure() {
    local log_file="$1"
    local category="unknown"
    local next_step="Capture the full log and rerun on a known-good Docker host or network."

    if grep -Eiq 'Cannot connect to the Docker daemon|Is the docker daemon running|error during connect|permission denied.*docker.sock|docker daemon is not running' "$log_file"; then
        category="Docker daemon"
        next_step="Start Docker Desktop/Engine, verify docker context, then rerun SKIP_COLCON=1 bash scripts/docker_humble_build.sh."
    elif grep -Eiq 'buildx|BuildKit|builder.*inactive|no builder|failed to dial gRPC|context deadline exceeded.*builder' "$log_file"; then
        category="Docker builder"
        next_step="Run docker buildx ls, select or recreate a working builder, then rerun the preflight."
    elif grep -Eiq 'unknown type text/html|unexpected media type text/html|encountered unknown type text/html' "$log_file"; then
        category="registry mirror/proxy"
        next_step="A registry path returned HTML while fetching base image metadata/layers. Disable or change Docker registry mirror/proxy, clear the affected builder cache if needed, then rerun."
    elif grep -Eiq 'failed to resolve source metadata|failed to load metadata|no matching manifest|manifest unknown|pull access denied|repository does not exist' "$log_file"; then
        category="base image"
        next_step="Verify docker pull ${base_image}, Docker Hub reachability, and any configured registry mirror before rebuilding."
    elif grep -Eiq 'proxyconnect|407 Proxy Authentication Required|CONNECT tunnel failed|certificate signed by unknown authority|TLS handshake timeout|i/o timeout|connection reset by peer|temporary failure in name resolution|lookup .* no such host' "$log_file"; then
        category="proxy"
        next_step="Fix host DNS/proxy/certificate settings for Docker registry traffic, then rerun the preflight."
    elif grep -Eiq 'failed to compute cache key|cache.*corrupt|failed to prepare extraction snapshot|failed to extract layer|failed to copy.*sha256|content digest .* not found' "$log_file"; then
        category="cache"
        next_step="Clean the Docker builder cache for this host with docker builder prune after confirming no other builds need it, then rerun."
    fi

    echo "== Docker build failure classification =="
    echo "category=$category"
    echo "base_image=$base_image"
    echo "operator_next_step=$next_step"
    echo "-- last 80 log lines --"
    tail -n 80 "$log_file" || true
    echo "== End Docker build failure classification =="
}

print_docker_preflight

docker_diag_log="$(mktemp -t ros_rbs_humble_build.XXXXXX.log)"
set +e
docker build \
    --progress="$build_progress" \
    --build-arg "UBUNTU_APT_MIRROR=$ubuntu_apt_mirror" \
    --build-arg "ROS_APT_MIRROR=$ros_apt_mirror" \
    --build-arg "PIP_INDEX_URL=$pip_index_url" \
    --build-arg "ROSDEP_SOURCE_MIRROR=$rosdep_source_mirror" \
    --build-arg "ROSDISTRO_INDEX_URL=$rosdistro_index_url" \
    -t "$image" \
    "$repo_root/docker/humble" 2>&1 | tee "$docker_diag_log"
build_rc=${PIPESTATUS[0]}
set -e
if [ "$build_rc" -ne 0 ]; then
    classify_build_failure "$docker_diag_log"
    exit "$build_rc"
fi

if [ "$skip_colcon" = "1" ]; then
    echo "Docker image is ready: $image"
    exit 0
fi

docker run --rm \
    -v "$repo_root:/ws" \
    -w /ws \
    "$image" \
    bash -lc "unset AMENT_PREFIX_PATH CMAKE_PREFIX_PATH COLCON_PREFIX_PATH && source /opt/ros/humble/setup.bash && rm -rf build install log && colcon build --symlink-install"
