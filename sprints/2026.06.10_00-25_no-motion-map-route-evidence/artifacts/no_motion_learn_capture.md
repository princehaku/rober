# No-Motion Learn Capture Artifact

## 执行时间

- 本地日期：2026-06-10
- 实板：`root@192.168.1.11:37878`

## 远端同步与构建

已同步到板上：

- `onboard/src/ros2_trashbot_bringup/launch/learn.launch.py`
- `onboard/src/ros2_trashbot_nav/ros2_trashbot_nav/route_data_recorder.py`

远端构建命令：

```bash
cd /root/rober/onboard
source /opt/ros/humble/setup.bash
colcon build --symlink-install --base-paths src --packages-select ros2_trashbot_nav ros2_trashbot_bringup
```

结果：通过。

## show-args 结果

首次 `--show-args` 发现板上仍是旧 launch 参数集；同步并重建后复查，新增参数已经可见：

- `camera_enabled`
- `camera_device`
- `static_laser_tf_enabled`
- `no_motion_mock_odom_enabled`
- `no_motion_mock_odom_topic`
- `no_motion_mock_odom_rate`
- `no_motion_odom_frame_id`

## no-motion capture 命令

```bash
ros2 launch ros2_trashbot_bringup learn.launch.py \
  lidar_enabled:=true \
  lidar_serial_port:=/dev/ttyACM0 \
  lidar_serial_baudrate:=150000 \
  static_laser_tf_enabled:=true \
  no_motion_static_odom_tf:=true \
  no_motion_mock_odom_enabled:=true \
  camera_enabled:=true \
  camera_device:=/dev/video1 \
  route_recorder:=true \
  route_output_dir:=/tmp/trashbot_no_motion_route
```

日志：`/tmp/trashbot_no_motion_learn.log`

## 观察结果

### 成功

- `/odom` 可拿到单帧，`frame_id=odom`，`child_frame_id=base_link`。
- `/tf_static` 可拿到单帧，至少包含 `base_link -> laser_frame`。
- `route.csv` 已生成：
  - `/tmp/trashbot_no_motion_route/route.csv`
- `keyframes/000.jpg`、`keyframes/000.json`、`manifest.json` 已生成：
  - `/tmp/trashbot_no_motion_route/keyframes/000.jpg`
  - `/tmp/trashbot_no_motion_route/keyframes/000.json`
  - `/tmp/trashbot_no_motion_route/manifest.json`
- `/trashbot/save_map` 返回：

```text
success=True, message='Map saved to /root/.ros/trashbot_maps/trashbot_map.pgm'
```

- 地图文件已落盘：
  - `/root/.ros/trashbot_maps/trashbot_map.pgm`
  - `/root/.ros/trashbot_maps/trashbot_map.yaml`

### 失败/异常

1. `/scan`
   - `ros2 topic info /scan` 显示 `Publisher count: 1`
   - 但 `timeout 15s ros2 topic echo --once /scan` 本轮超时，未拿到单帧

2. `camera_publisher`
   - launch 日志中当前实例报错：

```text
RuntimeError: Failed to open camera device /dev/video1; camera_publisher fails closed and will not fabricate frames
```

3. 节点图污染
   - `ros2 node list` 存在同名重复 node：
     - `/camera_publisher`
     - `/route_data_recorder`
     - `/slam_toolbox`
     - `/static_laser_tf`
     - `/no_motion_static_odom_tf`
     - `/waypoint_manager`
   - 这说明板上存在历史残留进程；当前 `keyframe/manifest` 虽已存在，但证据可能混入残留 publisher，不够干净。

## 关键文件快照

### route.csv

```csv
index,sec,nanosec,frame_id,x,y,z,qx,qy,qz,qw,frame
0,1781021910,348167126,map,0.0,0.0,0.0,0.0,0.0,0.0,1.0,000.jpg
```

### manifest.json 结论

- `schema=trashbot.vision_samples.v1`
- `sample_count=1`
- `sample_ref=vision_sample://keyframes/000.json`
- `event_type=route_keyframe`

### map.yaml 结论

- `image=trashbot_map.pgm`
- `resolution=0.05000000074505806`
- `origin=[-2.226749159725621, -5.182901393586501, 0.0]`

## 当前结论

- **map.yaml：成功**
- **route.csv：成功**
- **manifest/keyframe：文件存在，但受残留进程污染，需清场后复跑确认**
- **/scan：未成功拿到单帧，仍需继续定位**
