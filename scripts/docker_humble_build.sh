#!/usr/bin/env bash
# WSL/Linux helper for Docker-based ROS2 Humble build validation.
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
image="${ROS_HUMBLE_IMAGE:-ros-rbs-humble:dev}"
dockerfile="$repo_root/docker/humble/Dockerfile"
dockerfile_base_default="$(awk -F= '/^ARG[[:space:]]+ROS_HUMBLE_BASE_IMAGE=/{print $2; exit}' "$dockerfile")"
dockerfile_base_default="${dockerfile_base_default:-osrf/ros:humble-desktop}"
base_image="${ROS_HUMBLE_BASE_IMAGE:-$dockerfile_base_default}"
base_image_override="default"
ubuntu_apt_mirror="${UBUNTU_APT_MIRROR:-https://mirrors.tuna.tsinghua.edu.cn/ubuntu}"
ros_apt_mirror="${ROS_APT_MIRROR:-https://mirrors.tuna.tsinghua.edu.cn/ros2/ubuntu}"
pip_index_url="${PIP_INDEX_URL:-https://pypi.tuna.tsinghua.edu.cn/simple}"
rosdep_source_mirror="${ROSDEP_SOURCE_MIRROR:-https://mirrors.tuna.tsinghua.edu.cn/github-raw/ros/rosdistro/master/rosdep}"
rosdistro_index_url="${ROSDISTRO_INDEX_URL:-https://mirrors.tuna.tsinghua.edu.cn/rosdistro/index-v4.yaml}"
skip_colcon="${SKIP_COLCON:-0}"
skip_docker_build="${SKIP_DOCKER_BUILD:-0}"
build_progress="${DOCKER_BUILD_PROGRESS:-plain}"
image_tar=""
image_tar_state="unset"

docker_diag_log=""

print_image_tar_operator_help() {
    cat <<EOF
Docker image tar reuse notes:
  - The tar should come from a trusted machine that exported a runnable '$image' image.
  - The tar's internal tag must match ROS_HUMBLE_IMAGE='$image'; docker load success alone is not enough.
  - Docker daemon must be running before tar load or local image validation can succeed.
  - If tar reuse is not intended, unset ROS_HUMBLE_IMAGE_TAR and remove SKIP_DOCKER_BUILD after fixing the registry mirror/proxy, then rebuild.
EOF
}

print_image_tar_fast_fail_context() {
    echo "evidence_scope=software_proof_docker_only" >&2
    echo "target_image=$image" >&2
    echo "skip_docker_build=$skip_docker_build" >&2
    echo "image_tar_state=$image_tar_state" >&2
    if [ -n "$image_tar" ]; then
        echo "image_tar_path=$image_tar" >&2
    fi
    print_image_tar_operator_help >&2
}

if [ -n "${ROS_HUMBLE_BASE_IMAGE+x}" ]; then
    if [ -z "$ROS_HUMBLE_BASE_IMAGE" ]; then
        echo "ERROR: ROS_HUMBLE_BASE_IMAGE is set but empty. Provide a base image, or unset it to use $dockerfile_base_default." >&2
        exit 2
    fi
    base_image_override="env"
fi

if [ -n "${ROS_HUMBLE_IMAGE_TAR+x}" ]; then
    if [ -z "$ROS_HUMBLE_IMAGE_TAR" ]; then
        image_tar_state="empty_error"
        echo "ERROR: ROS_HUMBLE_IMAGE_TAR is set but empty. Provide a Docker image tar path, or unset it." >&2
        print_image_tar_fast_fail_context
        exit 2
    fi

    image_tar="$ROS_HUMBLE_IMAGE_TAR"
    image_tar_state="provided"

    if [ "$skip_docker_build" != "1" ]; then
        echo "ERROR: ROS_HUMBLE_IMAGE_TAR requires SKIP_DOCKER_BUILD=1. Tar reuse is only allowed on the explicit local-image reuse path." >&2
        print_image_tar_fast_fail_context
        exit 2
    fi

    if [ ! -f "$image_tar" ]; then
        image_tar_state="missing_error"
        echo "ERROR: ROS_HUMBLE_IMAGE_TAR does not point to an existing file: $image_tar" >&2
        print_image_tar_fast_fail_context
        exit 2
    fi
fi

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

target_image_present() {
    docker image inspect "$image" >/dev/null 2>&1
}

print_skip_build_missing_image_help() {
    cat <<EOF
ERROR: SKIP_DOCKER_BUILD=1 was requested, but target image '$image' is not present locally.

To continue on this Docker-only host, choose one:
  docker pull $image
  ROS_HUMBLE_IMAGE_TAR=/path/to/ros-rbs-humble-dev.tar SKIP_DOCKER_BUILD=1 bash scripts/docker_humble_build.sh
  unset SKIP_DOCKER_BUILD and rerun this script to build from base image '$base_image'

evidence_scope=software_proof_docker_only
EOF
}

print_skip_build_unusable_image_help() {
    cat <<EOF
ERROR: SKIP_DOCKER_BUILD=1 found target image '$image', but it is not runnable as a ROS Humble build image.

The local tag may point to an incomplete, corrupt, or wrong-platform image. Replace it with one valid target image:
  docker pull $image
  ROS_HUMBLE_IMAGE_TAR=/path/to/ros-rbs-humble-dev.tar SKIP_DOCKER_BUILD=1 bash scripts/docker_humble_build.sh
  unset SKIP_DOCKER_BUILD and rerun this script to rebuild from base image '$base_image'

evidence_scope=software_proof_docker_only
EOF
}

validate_target_image_for_reuse() {
    # SKIP_DOCKER_BUILD is only useful if the local tag can actually start a
    # Humble build container. A tag can pass docker image inspect while still
    # pointing at an incomplete manifest, so run a tiny container-side probe.
    docker run --rm --entrypoint /bin/bash "$image" -lc 'test -f /opt/ros/humble/setup.bash' >/dev/null
}

print_docker_preflight() {
    local local_target_image_present="unknown"
    local local_image_reuse="disabled"

    if target_image_present; then
        local_target_image_present="yes"
        if [ "$skip_docker_build" = "1" ]; then
            local_image_reuse="inspect_present_validation_pending"
        else
            local_image_reuse="available_for_explicit_skip_validation_pending"
        fi
    else
        local_target_image_present="no"
        if [ "$skip_docker_build" = "1" ]; then
            local_image_reuse="missing"
        fi
    fi

    echo "== Docker/Humble preflight =="
    echo "evidence_scope=software_proof_docker_only"
    echo "repo_root=$repo_root"
    echo "dockerfile=$dockerfile"
    echo "target_image=$image"
    echo "base_image=$base_image"
    echo "base_image_override=$base_image_override"
    echo "skip_docker_build=$skip_docker_build"
    echo "skip_colcon=$skip_colcon"
    echo "image_tar_state=$image_tar_state"
    if [ -n "$image_tar" ]; then
        echo "image_tar_path=$image_tar"
    fi
    echo "local_target_image_present=$local_target_image_present"
    echo "local_image_reuse=$local_image_reuse"
    echo "build_progress=$build_progress"
    if [ -n "${ROS_HUMBLE_IMAGE_TAR+x}" ] || [ "$skip_docker_build" = "1" ]; then
        print_image_tar_operator_help
    fi
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

if [ "$skip_docker_build" = "1" ]; then
    if [ -n "$image_tar" ]; then
        echo "ROS_HUMBLE_IMAGE_TAR: loading Docker image tar before local image reuse: $image_tar"
        docker load -i "$image_tar"
    fi
    if ! target_image_present; then
        print_skip_build_missing_image_help
        exit 3
    fi
    if ! validate_target_image_for_reuse; then
        print_skip_build_unusable_image_help
        exit 4
    fi
    echo "local_image_reuse=validated_runnable"
    echo "SKIP_DOCKER_BUILD=1: reusing local Docker image: $image"
else
    docker_diag_log="$(mktemp -t ros_rbs_humble_build.XXXXXX.log)"
    set +e
    docker build \
        --progress="$build_progress" \
        --build-arg "ROS_HUMBLE_BASE_IMAGE=$base_image" \
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
fi

if [ "$skip_colcon" = "1" ]; then
    echo "Docker image is ready: $image"
    echo "evidence_scope=software_proof_docker_only"
    exit 0
fi

docker run --rm \
    -v "$repo_root:/ws" \
    -w /ws \
    "$image" \
    bash -lc "unset AMENT_PREFIX_PATH CMAKE_PREFIX_PATH COLCON_PREFIX_PATH && source /opt/ros/humble/setup.bash && rm -rf build install log && colcon build --symlink-install"
