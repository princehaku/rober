FROM osrf/ros:humble-desktop

ARG UBUNTU_APT_MIRROR=https://mirrors.tuna.tsinghua.edu.cn/ubuntu
ARG ROS_APT_MIRROR=https://mirrors.tuna.tsinghua.edu.cn/ros2/ubuntu
ARG PIP_INDEX_URL=https://pypi.tuna.tsinghua.edu.cn/simple

ENV DEBIAN_FRONTEND=noninteractive \
    LANG=C.UTF-8 \
    LC_ALL=C.UTF-8 \
    PIP_INDEX_URL=${PIP_INDEX_URL}

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
      echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/ros2-archive-keyring.gpg] ${ROS_APT_MIRROR} ${codename} main" \
        > /etc/apt/sources.list.d/ros2.list; \
    fi; \
    rm -rf /var/lib/apt/lists/*; \
    apt-get clean; \
    apt-get update -o Acquire::Retries=3; \
    apt-get install -y --no-install-recommends \
      bash-completion \
      build-essential \
      git \
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
    rm -rf /var/lib/apt/lists/*

WORKDIR /ws

CMD ["bash"]
