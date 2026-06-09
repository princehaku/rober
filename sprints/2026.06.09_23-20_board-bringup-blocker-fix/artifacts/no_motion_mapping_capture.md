# No-Motion Mapping Capture

更新时间：2026-06-10 00:05 CST

## 目标

在已恢复的 sensor-only bringup 基础上，执行一次**不发布 `/cmd_vel`** 的 no-motion 证据采集，尝试获得：

1. `/scan`、`/camera/image_raw`、`/tf_static`、`/map` topic 证据；
2. 短时 rosbag；
3. `save_map` 结果；
4. route/keyframe 证据或准确失败根因。

## 已读资料与边界

- `docs/vendor/VENDOR_INDEX.md`
  - 确认 Orange Pi 设备名不能按 Raspberry Pi 习惯猜测，现场必须以实际 `/dev/video1`、`/dev/ttyACM0` 为准。
- `docs/navigation/field_route_evidence_preflight.md`
  - 本轮沿用 sensor-only bringup，不启动底盘桥，不触碰 `/dev/ttyS5`，不发布运动命令。
- `docs/vision/board_camera_publisher.md`
  - 当前实板真实相机采样设备为 `/dev/video1`。

## RUN 目录

- 远端 RUN：`/root/.ros/trashbot_live_runs/no_motion_sensor_20260609_235445`
- 本地拉回：`sprints/2026.06.09_23-20_board-bringup-blocker-fix/artifacts/no_motion_sensor_20260609_235445/no_motion_sensor_20260609_235445/`
- 补充 map save retry：`sprints/2026.06.09_23-20_board-bringup-blocker-fix/artifacts/no_motion_map_retry_20260610_0000/no_motion_map_retry_20260610_0000/`

## 实际命令

### 1. 创建 RUN 目录

```bash
ssh -p 37878 root@192.168.1.11 'bash -lc "source /opt/ros/humble/setup.bash; source /root/rober/onboard/install/setup.bash; RUN=\$HOME/.ros/trashbot_live_runs/no_motion_sensor_\$(date +%Y%m%d_%H%M%S); mkdir -p \$RUN; echo \$RUN"'
```

关键输出：

```text
/root/.ros/trashbot_live_runs/no_motion_sensor_20260609_235445
```

### 2. sensor-only bringup + topic echo + rosbag + save_map + route/keyframe 尝试

```bash
ssh -p 37878 root@192.168.1.11 'bash -lc "
source /opt/ros/humble/setup.bash
source /root/rober/onboard/install/setup.bash
timeout 45s ros2 launch ros2_trashbot_bringup bringup.launch.py \
  base_enabled:=false \
  lidar_enabled:=true \
  lidar_serial_port:=/dev/ttyACM0 \
  lidar_serial_baudrate:=150000 \
  static_laser_tf_enabled:=true \
  camera_enabled:=true \
  camera_device:=/dev/video1
"'
```

同一 RUN 下执行并落盘：

- `ros2 topic list`
- `ros2 topic echo --once /scan`
- `ros2 topic echo --once /camera/image_raw`
- `ros2 topic echo --once /tf_static`
- `ros2 topic echo --once /map`
- `ros2 topic echo --once /odom`
- `ros2 bag record -o $RUN/route_bag /scan /camera/image_raw /tf_static /map`
- `ros2 service call /trashbot/save_map std_srvs/srv/Trigger`
- `ros2 run ros2_trashbot_nav route_data_recorder --ros-args -p output_dir:=$RUN/route_data -p route_id:=no_motion_sensor -p min_distance_m:=0.0`
- `python3 + cv2.VideoCapture('/dev/video1')` 保存 `keyframe_sample.jpg`

### 3. map save 重试

```bash
ssh -p 37878 root@192.168.1.11 'bash -lc "
source /opt/ros/humble/setup.bash
source /root/rober/onboard/install/setup.bash
timeout 35s ros2 launch ros2_trashbot_bringup bringup.launch.py \
  base_enabled:=false \
  lidar_enabled:=true \
  lidar_serial_port:=/dev/ttyACM0 \
  lidar_serial_baudrate:=150000 \
  static_laser_tf_enabled:=true \
  camera_enabled:=true \
  camera_device:=/dev/video1
"'
```

bringup 预热 18 秒后，单独重试：

```bash
ros2 topic echo --once /map
ros2 service call /trashbot/save_map std_srvs/srv/Trigger
```

## 关键输出

### topic gate

`topic_list.txt`：

```text
/amcl_pose
/camera/image_raw
/map
/parameter_events
/rosout
/scan
/tf_static
/trashbot/waypoints
```

`/scan`：

```text
frame_id: laser_frame
range_max: 8.0
ranges:
- 7.488500118255615
- 1.5950000286102295
- 1.5880000591278076
```

`/camera/image_raw`：

```text
frame_id: camera
height: 480
width: 640
encoding: bgr8
```

`/tf_static`：

```text
frame_id: base_link
child_frame_id: laser_frame
translation:
  x: 0.0
  y: 0.0
  z: 0.0
```

`/odom`：

```text
WARNING: topic [/odom] does not appear to be published yet
Could not determine the type for the passed topic
```

`/map`：

- `topic list` 中可见 `/map`
- 但 `map_once.txt` 没有拿到消息
- 额外执行 `ros2 topic info /map` 返回 `Unknown topic '/map'`

结论：这轮 no-motion bringup 没有稳定的 `/map` publisher 或有效 map 消息，不能宣称建图材料已产出。

### rosbag

`route_bag/metadata.yaml` 关键字段：

```text
duration: 4.964996929s
message_count: 1473
topics_with_message_count:
  /camera/image_raw: 2
  /scan: 1470
  /tf_static: 1
```

结论：

- rosbag 录制成功；
- 这次 bag 里没有 `/map` 消息；
- `/odom` 本轮未录，因为实板没有该 topic。

### save_map

第一次在综合采集脚本里调用：

```text
waiting for service to become available...
failed to check service availability: rcl node's context is invalid
```

重试后得到节点侧明确返回：

```text
response:
std_srvs.srv.Trigger_Response(success=False, message='No map data received')
```

结论：`map_recorder` service 存在，但因没有收到 `/map` 数据，不能生成 `trashbot_map.yaml` / `trashbot_map.pgm`。本轮 `map_save/` 为空目录。

### route/keyframe

`route_data_recorder.log`：

```text
ModuleNotFoundError: No module named 'cv_bridge'
```

结论：

1. route recorder 这次不是先卡在 `/odom`，而是在板上直接因为 `cv_bridge` 缺失而启动失败；
2. 即使补上 `cv_bridge`，当前 no-motion bringup 仍没有 `/odom`，所以 route.csv 也不会得到有效轨迹点。

### keyframe fallback

为避免本轮没有任何视觉材料，额外直接读取 `/dev/video1` 保存：

- `keyframe_sample.jpg`
- `keyframe_sample.json`

`keyframe_sample.json` 关键字段：

```json
{
  "device": "/dev/video1",
  "opened": true,
  "read": true,
  "shape": [480, 640, 3]
}
```

## 产出 artifacts

### 本地绝对路径

- `/Users/m1/apps/rober/sprints/2026.06.09_23-20_board-bringup-blocker-fix/artifacts/no_motion_mapping_capture.md`
- `/Users/m1/apps/rober/sprints/2026.06.09_23-20_board-bringup-blocker-fix/artifacts/no_motion_sensor_20260609_235445/no_motion_sensor_20260609_235445/route_bag/metadata.yaml`
- `/Users/m1/apps/rober/sprints/2026.06.09_23-20_board-bringup-blocker-fix/artifacts/no_motion_sensor_20260609_235445/no_motion_sensor_20260609_235445/route_bag/route_bag_0.db3`
- `/Users/m1/apps/rober/sprints/2026.06.09_23-20_board-bringup-blocker-fix/artifacts/no_motion_sensor_20260609_235445/no_motion_sensor_20260609_235445/keyframe_sample.jpg`
- `/Users/m1/apps/rober/sprints/2026.06.09_23-20_board-bringup-blocker-fix/artifacts/no_motion_sensor_20260609_235445/no_motion_sensor_20260609_235445/keyframe_sample.json`
- `/Users/m1/apps/rober/sprints/2026.06.09_23-20_board-bringup-blocker-fix/artifacts/no_motion_sensor_20260609_235445/no_motion_sensor_20260609_235445/scan_once.txt`
- `/Users/m1/apps/rober/sprints/2026.06.09_23-20_board-bringup-blocker-fix/artifacts/no_motion_sensor_20260609_235445/no_motion_sensor_20260609_235445/camera_once.txt`
- `/Users/m1/apps/rober/sprints/2026.06.09_23-20_board-bringup-blocker-fix/artifacts/no_motion_sensor_20260609_235445/no_motion_sensor_20260609_235445/tf_static_once.txt`
- `/Users/m1/apps/rober/sprints/2026.06.09_23-20_board-bringup-blocker-fix/artifacts/no_motion_map_retry_20260610_0000/no_motion_map_retry_20260610_0000/save_map_call.txt`

## 未完成项 / 失败定位

1. **未得到 `map.yaml`**
   - `save_map` 重试明确返回 `No map data received`。
   - 当前 sensor-only bringup 没有可复用的 mapping node 在持续发布有效 `/map`。
2. **未得到 `route.csv`**
   - 板上 `route_data_recorder` 启动即报 `ModuleNotFoundError: No module named 'cv_bridge'`。
   - 同时 `/odom` 不存在，即使补齐依赖，no-motion 条件下也不会形成真实路线点。
3. **未得到 keyframe manifest / route manifest**
   - 依赖 `route_data_recorder` 正常启动并消费 `/odom`；当前条件不满足。
4. **本轮仍然不是建图完成证明**
   - 只有 `/scan`、`/camera/image_raw`、`/tf_static` 与短 rosbag、单帧相机样本。

## 下一步建议

1. 若目标是**最小 map 证据**，下一轮应转到 `learn.launch.py`，确认板上已安装 `slam_toolbox`，并给出 no-motion 或轻微人工推动下的 `/map` 输出条件。
2. 若目标是**route.csv / keyframe manifest**，先修板上 `cv_bridge` 依赖，再决定是否允许非运动条件下用 mock `/odom` 做软件链路验证；真实 route 仍需运动或回放里程计。
3. 若只是继续积累现场材料，当前这轮 bag + keyframe 已可作为 O3/O7 的 no-motion 传感器证据输入，但不能替代地图、路线或 Nav2 实跑证据。
