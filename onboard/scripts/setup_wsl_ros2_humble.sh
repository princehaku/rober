#!/usr/bin/env bash
set -euo pipefail

if ! grep -q "Ubuntu 22.04" /etc/os-release; then
  echo "This script targets Ubuntu 22.04 for ROS2 Humble." >&2
  cat /etc/os-release >&2
  exit 2
fi

export DEBIAN_FRONTEND=noninteractive

apt-get update
apt-get install -y software-properties-common curl gnupg lsb-release locales
locale-gen en_US en_US.UTF-8
update-locale LC_ALL=en_US.UTF-8 LANG=en_US.UTF-8
export LANG=en_US.UTF-8

add-apt-repository universe -y
curl -sSL https://raw.githubusercontent.com/ros/rosdistro/master/ros.key \
  -o /usr/share/keyrings/ros-archive-keyring.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/ros-archive-keyring.gpg] http://packages.ros.org/ros2/ubuntu $(. /etc/os-release && echo "$UBUNTU_CODENAME") main" \
  > /etc/apt/sources.list.d/ros2.list

apt-get update
apt-get install -y \
  python3-colcon-common-extensions \
  python3-pip \
  python3-rosdep \
  python3-yaml \
  ros-humble-desktop \
  ros-humble-navigation2 \
  ros-humble-nav2-bringup \
  ros-humble-nav2-simple-commander \
  ros-humble-slam-toolbox \
  ros-humble-cv-bridge \
  ros-humble-vision-opencv

if ! rosdep version >/dev/null 2>&1; then
  echo "rosdep command is unavailable after installation." >&2
  exit 3
fi

if [ ! -e /etc/ros/rosdep/sources.list.d/20-default.list ]; then
  rosdep init
fi
rosdep update

echo "ROS2 Humble WSL environment is ready."
