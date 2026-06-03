#!/usr/bin/env bash
# O1 上位机 ROS2 Humble arm64 bootstrap，只处理 runtime 与 onboard 构建。
# 本脚本不打开任何串口，不写 /dev/ttyS5，不调用 8787 控制 API。
# LiDAR 真机证据由 o1_lidar_ros2_scan_smoke.sh 负责采集，避免安装脚本触碰硬件。

set -Eeuo pipefail

REPO_ROOT="/root/rober"
ONBOARD_ROOT="/root/rober/onboard"
ROS_APT_REPO="${ROS_APT_REPO:-http://packages.ros.org/ros2/ubuntu}"
UBUNTU_APT_MIRROR="${UBUNTU_APT_MIRROR:-https://mirrors.tuna.tsinghua.edu.cn/ubuntu-ports}"
SKIP_APT_INSTALL=0
SKIP_COLCON=0

usage() {
  cat <<'USAGE'
Usage: o1_ros2_humble_arm64_bootstrap.sh [options]

Options:
  --repo-root PATH       rober repo root, default /root/rober
  --onboard-root PATH    onboard workspace path, default /root/rober/onboard
  --ros-apt-repo URL     ROS2 apt repo URL, default http://packages.ros.org/ros2/ubuntu
  --ubuntu-apt-mirror URL Ubuntu ports mirror, default https://mirrors.tuna.tsinghua.edu.cn/ubuntu-ports
  --skip-apt-install     do not install ROS2 packages; only validate and build
  --skip-colcon          install/validate runtime but do not build onboard
  -h, --help             show this help
USAGE
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --repo-root)
      REPO_ROOT="$2"
      shift 2
      ;;
    --onboard-root)
      ONBOARD_ROOT="$2"
      shift 2
      ;;
    --ros-apt-repo)
      ROS_APT_REPO="$2"
      shift 2
      ;;
    --ubuntu-apt-mirror)
      UBUNTU_APT_MIRROR="$2"
      shift 2
      ;;
    --skip-apt-install)
      SKIP_APT_INSTALL=1
      shift
      ;;
    --skip-colcon)
      SKIP_COLCON=1
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "unknown argument: $1" >&2
      usage >&2
      exit 2
      ;;
  esac
done

log() {
  printf '[o1-bootstrap] %s\n' "$*"
}

require_root() {
  # apt 和 /opt/ros 写入需要 root；非 root 时直接失败，避免半安装状态。
  if [[ "$(id -u)" != "0" ]]; then
    echo "must run as root on the upper computer" >&2
    exit 10
  fi
}

check_platform() {
  # 本轮只支持用户指定的 Orange Pi Ubuntu 22.04 arm64 目标，不把其他 OS 写成可行。
  . /etc/os-release
  ARCH="$(dpkg --print-architecture)"
  log "os=${ID:-unknown} version=${VERSION_ID:-unknown} codename=${UBUNTU_CODENAME:-unknown} arch=${ARCH}"
  if [[ "${ID:-}" != "ubuntu" || "${VERSION_ID:-}" != "22.04" ]]; then
    echo "unsupported OS for ROS2 Humble apt bootstrap: ${ID:-unknown} ${VERSION_ID:-unknown}" >&2
    exit 20
  fi
  if [[ "$ARCH" != "arm64" ]]; then
    echo "unsupported architecture for this O1 upper-computer bootstrap: $ARCH" >&2
    exit 21
  fi
}

install_ros2_runtime() {
  # ROS2 apt 源只用于 Humble runtime；脚本不拉 Docker 镜像，避免 arm64/amd64 漂移。
  export DEBIAN_FRONTEND=noninteractive
  configure_ubuntu_apt_mirror
  apt-get update
  apt-get install -y curl gnupg lsb-release locales software-properties-common
  locale-gen en_US en_US.UTF-8 || true
  update-locale LC_ALL=en_US.UTF-8 LANG=en_US.UTF-8 || true
  add-apt-repository -y universe

  # keyring 路径固定，便于后续人工审查 apt source 是否来自 ROS2 官方 key。
  curl -fsSL https://raw.githubusercontent.com/ros/rosdistro/master/ros.key \
    -o /usr/share/keyrings/ros-archive-keyring.gpg
  . /etc/os-release
  echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/ros-archive-keyring.gpg] ${ROS_APT_REPO} ${UBUNTU_CODENAME} main" \
    > /etc/apt/sources.list.d/ros2.list

  # ros-base 足够运行 topic/driver smoke；tf2_ros 用于 base_link -> laser_frame 证据。
  apt-get update
  apt-get install -y \
    ros-humble-ros-base \
    ros-humble-tf2-ros \
    python3-colcon-common-extensions \
    python3-rosdep \
    python3-serial \
    python3-pip
}

configure_ubuntu_apt_mirror() {
  # 远端曾启用 armhf foreign arch，坏镜像会额外拉 armhf 索引并阻塞本轮 arm64 ROS2 bootstrap。
  # 这里仅把 Ubuntu ports 源限定为 arm64，不移除 foreign arch，降低对既有系统状态的影响。
  if [[ -z "$UBUNTU_APT_MIRROR" ]]; then
    log "ubuntu apt mirror rewrite disabled"
    return
  fi
  . /etc/os-release
  local sources="/etc/apt/sources.list"
  local backup="/etc/apt/sources.list.o1-bootstrap.bak"
  if [[ ! -f "$backup" ]]; then
    cp "$sources" "$backup"
    log "backed up $sources to $backup"
  fi
  cat >"$sources" <<EOF
deb [arch=arm64] ${UBUNTU_APT_MIRROR} ${UBUNTU_CODENAME} main restricted universe multiverse
deb [arch=arm64] ${UBUNTU_APT_MIRROR} ${UBUNTU_CODENAME}-security main restricted universe multiverse
deb [arch=arm64] ${UBUNTU_APT_MIRROR} ${UBUNTU_CODENAME}-updates main restricted universe multiverse
deb [arch=arm64] ${UBUNTU_APT_MIRROR} ${UBUNTU_CODENAME}-backports main restricted universe multiverse
EOF
  log "configured Ubuntu apt mirror=$UBUNTU_APT_MIRROR arch=arm64"
}

validate_source_tree() {
  # 远端源码必须包含当前 LiDAR driver；旧 checkout 缺 entrypoint 时先要求同步源码。
  if [[ ! -d "$ONBOARD_ROOT" ]]; then
    echo "onboard workspace missing: $ONBOARD_ROOT" >&2
    exit 30
  fi
  if [[ ! -f "$ONBOARD_ROOT/src/ros2_trashbot_hardware/ros2_trashbot_hardware/lidar_driver.py" ]]; then
    echo "lidar_driver.py missing; sync current onboard source before building" >&2
    exit 31
  fi
  if ! grep -q 'lidar_driver = ros2_trashbot_hardware.lidar_driver:main' \
      "$ONBOARD_ROOT/src/ros2_trashbot_hardware/setup.py"; then
    echo "lidar_driver console_scripts entry missing; sync current setup.py before building" >&2
    exit 32
  fi
}

build_onboard_workspace() {
  # 构建只面向 ROS2 workspace，不启动节点、不打开串口、不触发 LiDAR 或底盘动作。
  source /opt/ros/humble/setup.bash
  cd "$ONBOARD_ROOT"
  rm -rf build install log
  colcon build --symlink-install
}

main() {
  require_root
  check_platform
  if [[ "$SKIP_APT_INSTALL" != "1" ]]; then
    install_ros2_runtime
  else
    log "skip apt install requested"
  fi
  validate_source_tree
  if [[ "$SKIP_COLCON" != "1" ]]; then
    build_onboard_workspace
  else
    log "skip colcon requested"
  fi
  source /opt/ros/humble/setup.bash
  log "ros2=$(command -v ros2)"
  log "install_setup=$ONBOARD_ROOT/install/setup.bash"
  test -f "$ONBOARD_ROOT/install/setup.bash"
  log "bootstrap complete; run o1_lidar_ros2_scan_smoke.sh for LiDAR-only evidence"
}

main "$@"
