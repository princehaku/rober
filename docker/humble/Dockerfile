FROM osrf/ros:humble-desktop

ENV DEBIAN_FRONTEND=noninteractive

RUN rm -rf /var/lib/apt/lists/* \
    && apt-get clean \
    && apt-get update -o Acquire::Retries=3 \
    && apt-get install -y --no-install-recommends \
      python3-colcon-common-extensions \
      python3-yaml \
      ros-humble-navigation2 \
      ros-humble-nav2-bringup \
      ros-humble-nav2-simple-commander \
      ros-humble-slam-toolbox \
      ros-humble-cv-bridge \
      ros-humble-vision-opencv \
    && rm -rf /var/lib/apt/lists/*
