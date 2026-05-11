ARG ROS_HUMBLE_BASE_IMAGE=osrf/ros:humble-desktop
FROM ${ROS_HUMBLE_BASE_IMAGE}

ARG UBUNTU_APT_MIRROR=https://mirrors.tuna.tsinghua.edu.cn/ubuntu
ARG ROS_APT_MIRROR=https://mirrors.tuna.tsinghua.edu.cn/ros2/ubuntu
ARG PIP_INDEX_URL=https://pypi.tuna.tsinghua.edu.cn/simple
ARG ROSDEP_SOURCE_MIRROR=https://mirrors.tuna.tsinghua.edu.cn/github-raw/ros/rosdistro/master/rosdep
ARG ROSDISTRO_INDEX_URL=https://mirrors.tuna.tsinghua.edu.cn/rosdistro/index-v4.yaml

ENV DEBIAN_FRONTEND=noninteractive \
    LANG=C.UTF-8 \
    LC_ALL=C.UTF-8 \
    PIP_INDEX_URL=${PIP_INDEX_URL} \
    ROSDISTRO_INDEX_URL=${ROSDISTRO_INDEX_URL} \
    ROS_DISTRO=humble

SHELL ["/bin/bash", "-c"]

RUN set -eux; \
    source /etc/os-release; \
    codename="${VERSION_CODENAME:-jammy}"; \
    { \
      echo "deb ${UBUNTU_APT_MIRROR} ${codename} main restricted universe multiverse"; \
      echo "deb ${UBUNTU_APT_MIRROR} ${codename}-updates main restricted universe multiverse"; \
      echo "deb ${UBUNTU_APT_MIRROR} ${codename}-backports main restricted universe multiverse"; \
      echo "deb ${UBUNTU_APT_MIRROR} ${codename}-security main restricted universe multiverse"; \
    } > /etc/apt/sources.list; \
    if [ -f /usr/share/ros-apt-source/ros2.sources ]; then \
      sed -i "s#^Types: .*#Types: deb#" /usr/share/ros-apt-source/ros2.sources; \
      sed -i "s#^URIs: .*#URIs: ${ROS_APT_MIRROR}#" /usr/share/ros-apt-source/ros2.sources; \
      sed -i "s#^Suites: .*#Suites: ${codename}#" /usr/share/ros-apt-source/ros2.sources; \
    else \
      rm -f /etc/apt/sources.list.d/ros2*.list; \
      ros_keyring="/usr/share/keyrings/ros2-archive-keyring.gpg"; \
      if [ ! -f "${ros_keyring}" ]; then ros_keyring="/usr/share/keyrings/ros-archive-keyring.gpg"; fi; \
      echo "deb [arch=$(dpkg --print-architecture) signed-by=${ros_keyring}] ${ROS_APT_MIRROR} ${codename} main" \
        > /etc/apt/sources.list.d/ros2.list; \
    fi; \
    rm -rf /var/lib/apt/lists/*; \
    apt-get clean; \
    apt-get update -o Acquire::Retries=3; \
    apt-get install -y --no-install-recommends \
      bash-completion \
      build-essential \
      ca-certificates \
      curl \
      git \
      iproute2 \
      less \
      nano \
      net-tools \
      openssh-client \
      python3-colcon-common-extensions \
      python3-numpy \
      python3-opencv \
      python3-pip \
      python3-rosdep \
      python3-serial \
      python3-yaml \
      ros-humble-cv-bridge \
      ros-humble-nav2-bringup \
      ros-humble-nav2-simple-commander \
      ros-humble-navigation2 \
      ros-humble-slam-toolbox \
      ros-humble-tf-transformations \
      ros-humble-vision-opencv; \
    mkdir -p /etc/ros/rosdep/sources.list.d /root/.pip /etc/profile.d; \
    { \
      echo "yaml ${ROSDEP_SOURCE_MIRROR}/osx-homebrew.yaml osx"; \
      echo "yaml ${ROSDEP_SOURCE_MIRROR}/base.yaml"; \
      echo "yaml ${ROSDEP_SOURCE_MIRROR}/python.yaml"; \
      echo "yaml ${ROSDEP_SOURCE_MIRROR}/ruby.yaml"; \
    } > /etc/ros/rosdep/sources.list.d/20-default.list; \
    printf '[global]\nindex-url = %s\ntrusted-host = %s\n' "${PIP_INDEX_URL}" "$(echo "${PIP_INDEX_URL}" | sed -E 's#^https?://([^/]+)/?.*$#\1#')" > /root/.pip/pip.conf; \
    rosdep update --rosdistro humble; \
    echo 'source /opt/ros/humble/setup.bash' > /etc/profile.d/10-ros-humble.sh; \
    echo 'if [ -f /ws/install/setup.bash ]; then source /ws/install/setup.bash; fi' > /etc/profile.d/20-trashbot-ws.sh; \
    rm -rf /var/lib/apt/lists/*

WORKDIR /ws

CMD ["bash"]
