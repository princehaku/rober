#!/usr/bin/env bash

set -euo pipefail

# 这个脚本只负责本轮远端收尾，防止 learn/bridge orphan 持续占串口。
for pid in 47543 47558 47560 47562 47564 47566 47568 47570 47574; do
  kill "${pid}" 2>/dev/null || true
done

# 额外按进程名兜底，避免 launch 子进程脱离父进程。
pkill -f 'ros2_trashbot_hardware/lib/ros2_trashbot_hardware/esp32_bridge' || true
pkill -f 'ros2_trashbot_bringup learn.launch.py' || true
pkill -f 'async_slam_toolbox_node' || true
pkill -f 'map_recorder' || true
pkill -f 'camera_publisher' || true
pkill -f 'lidar_driver' || true
pkill -f 'route_data_recorder' || true
pkill -f 'static_transform_publisher' || true

sleep 3

ps -ef | grep -E 'upper_robot_api|esp32_bridge|learn.launch|slam_toolbox|camera_publisher|lidar_driver|route_data_recorder' | grep -v grep || true
fuser -v /dev/ttyS5 /dev/ttyACM0 /dev/video1 || true

# 恢复 API，验证底盘状态接口重新可访问。
nohup python3 /root/rober/onboard/scripts/upper_robot_api.py \
  --host 0.0.0.0 \
  --port 8787 \
  --camera-base-url http://127.0.0.1:8088 \
  --base-port /dev/ttyS5 \
  --base-baudrate 115200 \
  --max-speed 0.12 \
  >/tmp/upper_robot_api_restore.log 2>&1 &

sleep 4
curl -sS http://127.0.0.1:8787/api/base/status || true
