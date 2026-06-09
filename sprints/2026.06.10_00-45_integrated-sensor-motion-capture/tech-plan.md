# Integrated Sensor Motion Capture Tech Plan

## 目标

用同一轮真实上位机 capture 覆盖雷达、摄像头、建图、运动四类证据。优先使用现有代码和参数组合，不在本轮修改产品代码。

## OKR 最低优先级核对

`OKR.md` 4.1 当前最低活跃 Objective 是 O7 `~12%`，其次 O6 `~30%`。本 sprint 仍不直接开发 O7 UI，而是继续补真实机器人 route/keyframe/map/motion 输入。

理由：O7 的真实地图、历史回放、标注和手控/寻路都依赖真实路线材料；上一轮已经证明 motion 主链路，本轮把 motion 与 sensor/map/keyframe 合并，能给 O7/O6 后续消费提供更强的真实 artifact packet。

## 文件范围

允许改动：

- `sprints/2026.06.10_00-45_integrated-sensor-motion-capture/**`

禁止默认改动产品代码、launch、driver、API 脚本或硬件配置。如真实联跑暴露必须修复的代码缺陷，硬件 agent 只记录根因，主节点再派软件 owner。

## 远端执行设计

目标主机：

```bash
ssh root@192.168.1.11 -p 37878
```

### 1. 基线与清场

记录：

```bash
date
hostname
ps -ef | grep -E 'upper_robot_api|esp32_bridge|learn.launch|slam_toolbox|route_data_recorder|camera_publisher|lidar_driver|static_transform_publisher|ros2' | grep -v grep || true
curl -sS http://127.0.0.1:8787/api/base/status || true
fuser -v /dev/ttyS5 /dev/ttyACM0 /dev/video1 || true
ros2 node list || true
```

清理上一轮 ROS2 残留，但不要误杀 `upper_robot_api.py`，直到准备接管底盘串口。

### 2. 释放底盘串口

记录原 API command line，停止 `upper_robot_api.py`：

```bash
ps -ef | grep '[u]pper_robot_api.py'
kill <upper_robot_api_pid>
sleep 1
fuser -v /dev/ttyS5 || true
```

### 3. 启动底盘 bridge

单独启动 bridge，避免 `bringup.launch.py` 同时拉起 waypoint/map/task 节点造成重复：

```bash
cd /root/rober/onboard
source /opt/ros/humble/setup.bash
source install/setup.bash
ros2 run ros2_trashbot_hardware esp32_bridge --ros-args \
  -p serial_port:=/dev/ttyS5 \
  -p serial_baudrate:=115200 \
  -p command_mode:=speed
```

### 4. 启动 learn capture

另一个进程启动传感器、SLAM、route recorder：

```bash
cd /root/rober/onboard
source /opt/ros/humble/setup.bash
source install/setup.bash
ros2 launch ros2_trashbot_bringup learn.launch.py \
  lidar_enabled:=true \
  lidar_serial_port:=/dev/ttyACM0 \
  lidar_serial_baudrate:=150000 \
  static_laser_tf_enabled:=true \
  no_motion_static_odom_tf:=true \
  no_motion_mock_odom_enabled:=false \
  camera_enabled:=true \
  camera_device:=/dev/video1 \
  route_recorder:=true \
  waypoint_manager:=false \
  route_min_distance_m:=0.01 \
  route_id:=integrated_sensor_motion_20260610 \
  route_output_dir:=/tmp/trashbot_integrated_sensor_motion_route \
  map_dir:=/tmp/trashbot_integrated_sensor_motion_maps \
  default_map_name:=trashbot_integrated_sensor_motion_map
```

注意：`no_motion_static_odom_tf:=true` 只为 smoke TF 拓扑，不是动态 TF 证据。`no_motion_mock_odom_enabled:=false` 确保 `/odom` 来自 `esp32_bridge`。

### 5. Topic/service 验证

```bash
ros2 node list
ros2 topic info /cmd_vel
ros2 topic echo /scan --once
ros2 topic echo /camera/image_raw --once
ros2 topic echo /odom --once
timeout 15 ros2 topic echo /battery --once || true
timeout 15 ros2 topic echo /imu/data --once || true
ros2 service list | grep /trashbot/stop
```

### 6. 低速运动与停止

```bash
ros2 topic pub --once /cmd_vel geometry_msgs/msg/Twist \
  "{linear: {x: 0.03, y: 0.0, z: 0.0}, angular: {x: 0.0, y: 0.0, z: 0.0}}"
sleep 0.3
ros2 topic pub --once /cmd_vel geometry_msgs/msg/Twist \
  "{linear: {x: 0.0, y: 0.0, z: 0.0}, angular: {x: 0.0, y: 0.0, z: 0.0}}"
ros2 service call /trashbot/stop std_srvs/srv/Trigger "{}"
ros2 topic echo /odom --once
```

### 7. 保存 map 和 route 产物

```bash
ros2 service call /trashbot/save_map std_srvs/srv/Trigger "{}"
find /tmp/trashbot_integrated_sensor_motion_route -maxdepth 3 -type f | sort
find /tmp/trashbot_integrated_sensor_motion_maps -maxdepth 2 -type f | sort
```

把 route、keyframes、manifest、map YAML/PGM、topic samples、bridge/learn logs 拉回本地：

```text
sprints/2026.06.10_00-45_integrated-sensor-motion-capture/artifacts/
```

### 8. 收尾恢复

必须执行：

```bash
ros2 topic pub --once /cmd_vel geometry_msgs/msg/Twist \
  "{linear: {x: 0.0, y: 0.0, z: 0.0}, angular: {x: 0.0, y: 0.0, z: 0.0}}" || true
ros2 service call /trashbot/stop std_srvs/srv/Trigger "{}" || true
```

停止 bridge/learn 相关进程，确认 `/dev/ttyS5` 释放，再恢复 API：

```bash
nohup python3 /root/rober/onboard/scripts/upper_robot_api.py \
  --host 0.0.0.0 \
  --port 8787 \
  --camera-base-url http://127.0.0.1:8088 \
  --base-port /dev/ttyS5 \
  --base-baudrate 115200 \
  --max-speed 0.12 \
  >/tmp/upper_robot_api_restore.log 2>&1 &
sleep 2
curl -sS http://127.0.0.1:8787/api/base/status
fuser -v /dev/ttyS5 /dev/ttyACM0 /dev/video1 || true
ros2 node list || true
```

## 验收命令

硬件 agent 必须至少执行并记录：

```bash
ssh root@192.168.1.11 -p 37878 'true'
ssh root@192.168.1.11 -p 37878 'curl -sS http://127.0.0.1:8787/api/base/status || true'
ssh root@192.168.1.11 -p 37878 'bash -lc '\''source /opt/ros/humble/setup.bash && source /root/rober/onboard/install/setup.bash && ros2 launch ros2_trashbot_bringup learn.launch.py --show-args'\'''
ssh root@192.168.1.11 -p 37878 'bash -lc '\''source /opt/ros/humble/setup.bash && source /root/rober/onboard/install/setup.bash && ros2 run ros2_trashbot_hardware esp32_bridge --ros-args --help'\'''
```

实际 integrated capture 命令按上文步骤执行，并写入 artifact。

## 输出文档

子 agent 必须写：

- `artifacts/integrated_sensor_motion_capture.md`
- `tech-done.md`
- `side2side_check.md`
- `final.md`

其中 `final.md` 必须明确：

- 雷达是否同轮成功。
- 摄像头是否同轮成功。
- map 是否保存成功。
- motion 和 stop 是否同轮成功。
- `/battery`/`/imu/data` 是否有新鲜样本。
- API 是否恢复。
