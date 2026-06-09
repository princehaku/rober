# Sensor Stack Smoke Artifact

时间：2026-06-09 23:51 CST  
目标板：`root@192.168.1.11:37878`

## 1. `bringup.launch.py --show-args`

确认新增参数已经在实板安装包中可见：

- `base_enabled`，默认 `true`
- `lidar_enabled`，默认 `false`
- `lidar_serial_port`，默认 `/dev/ttyACM0`
- `lidar_serial_baudrate`，默认 `150000`
- `lidar_frame_id`，默认 `laser_frame`
- `lidar_scan_topic`，默认 `/scan`
- `static_laser_tf_enabled`，默认 `false`
- `base_frame_id`，默认 `base_link`
- `laser_tf_x/y/z/roll/pitch/yaw`，默认 `0.0`

## 2. sensor-only smoke 命令

```bash
timeout 30s ros2 launch ros2_trashbot_bringup bringup.launch.py \
  base_enabled:=false \
  lidar_enabled:=true \
  lidar_serial_port:=/dev/ttyACM0 \
  lidar_serial_baudrate:=150000 \
  static_laser_tf_enabled:=true \
  camera_enabled:=true \
  camera_device:=/dev/video1
```

## 3. 关键 topic 结果

`ros2 topic list` 关键输出：

```text
/camera/image_raw
/map
/scan
/tf_static
/trashbot/waypoints
```

`ros2 topic echo --once /scan` 关键片段：

```text
frame_id: laser_frame
angle_min: 5.05709171295166
angle_max: 5.175719261169434
ranges:
- 5.418499946594238
- 1.6710000038146973
- 1.687000036239624
```

`ros2 topic echo --once /camera/image_raw` 关键片段：

```text
frame_id: camera
height: 480
width: 640
encoding: bgr8
```

`ros2 topic echo --once /tf_static` 关键片段：

```text
frame_id: base_link
child_frame_id: laser_frame
translation:
  x: 0.0
  y: 0.0
  z: 0.0
```

## 4. launch 日志尾部

```text
[INFO] [lidar_driver]: LiDAR serial started: /dev/ttyACM0 @ 150000
[INFO] [camera_publisher]: camera_publisher streaming /dev/video1 to /camera/image_raw with frame_id=camera, requested 640x480@15.00fps
[INFO] [static_laser_tf]: Spinning until stopped - publishing transform
[WARN] [waypoint_manager]: nav2_simple_commander is unavailable; waypoint navigation disabled: No module named 'nav2_simple_commander'
[INFO] [task_orchestrator]: TaskOrchestrator ready. Awaiting learning or patrol command.
```

## 5. 结论边界

- 本次证明了传感器-only bringup 链路可用：`/scan`、`/camera/image_raw`、`/tf_static`、`/map` 可同时进入 ROS graph。
- `base_enabled:=false` 生效，本轮未启动 `esp32_bridge`，未碰 `/dev/ttyS5`，未发布 `/cmd_vel`。
- `tf_static` 仅是 smoke/拓扑 TF，不代表 `base_link -> laser_frame` 已完成机械标定。
- 本次不宣称底盘运动、WAVE ROVER HIL、建图完成或固定路线已标定完成。
