# No-Motion Learn Capture Clean Artifact

## 执行时间

- 本地日期：2026-06-10
- 实板：`root@192.168.1.11:37878`
- 目标：在不触碰 `upper_robot_api.py`、不发布 `/cmd_vel` 的前提下，清场后复跑一次干净的 no-motion `learn.launch.py` 证据链

## 采用的现场硬件事实来源

- LiDAR 串口与波特率：`docs/vendor/VENDOR_INDEX.md`
  - WAVE ROVER / Orange Pi 相关约束要求现场确认真实 Linux 设备名，不能沿用 Raspberry Pi 默认串口路径。
  - 本次现场复跑沿用已探测到的 `lidar_serial_port:=/dev/ttyACM0`、`lidar_serial_baudrate:=150000`。
- 相机设备号：现场 `v4l2-ctl --list-devices` 与 `/dev/video1` 探测结果。

## 清场前盘点

清场前 `ps -ef` 显示存在三轮残留 no-motion 相关进程，主要包括：

- `slam_toolbox`
- `map_recorder`
- `waypoint_manager`
- `camera_publisher`
- `lidar_driver`
- `static_laser_tf`
- `no_motion_static_odom_tf`
- `no_motion_mock_odom_pub`
- `route_data_recorder`

清场前设备占用：

- `/dev/video1`：被残留 `camera_publisher` 占用
- `/dev/ttyACM0`：被残留 `lidar_driver` 占用

明确未触碰的常驻进程：

- `python3 /root/rober/onboard/scripts/upper_robot_api.py --host 0.0.0.0 --port 8787 --camera-base-url http://127.0.0.1:8088 --base-port /dev/ttyS5 --base-baudrate 115200 --max-speed 0.12`

## 清场动作

仅清理本轮 no-motion capture 残留：

1. 精确 kill 残留 `slam_toolbox`、`map_recorder`、`waypoint_manager`、`camera_publisher`、`lidar_driver`、`static_transform_publisher`、`route_data_recorder`、`no_motion_mock_odom_pub`
2. `ros2 daemon stop && ros2 daemon start`
3. 复查：
   - `ps -ef | grep -E 'slam|lidar|camera_publisher|route_data_recorder|static_transform|topic pub'`
   - `ros2 node list`
   - `fuser -v /dev/video1 /dev/ttyACM0`

清场后基线：

- 相关 `ps` 输出为空
- `ros2 node list` 为空
- `fuser /dev/video1 /dev/ttyACM0` 无占用

## 清场后复跑命令

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
  route_output_dir:=/tmp/trashbot_no_motion_route_clean
```

## 清场后 graph 与 topic 结果

复跑在线阶段 `ros2 node list`：

- `/camera_publisher`
- `/lidar_driver`
- `/map_recorder`
- `/no_motion_mock_odom_pub`
- `/no_motion_static_odom_tf`
- `/route_data_recorder`
- `/slam_toolbox`
- `/static_laser_tf`
- `/waypoint_manager`

本轮未再出现重复同名节点。

### `/scan`

成功，单帧关键字段：

- `frame_id=laser_frame`
- `range_max=8.0`
- `ranges` 已返回 8 个样本值

### `/camera/image_raw`

成功，单帧关键字段：

- `frame_id=camera`
- `height=480`
- `width=640`
- `encoding=bgr8`

### `/tf_static`

成功，单帧关键字段：

- `base_link -> laser_frame`
- 平移全零
- 四元数为单位姿态

### `/odom`

成功，单帧关键字段：

- `frame_id=odom`
- `child_frame_id=base_link`
- 位姿与 twist 全零

## 文件结果

远端最小 clean capture 产物均已生成并拷回本地：

- `route.csv`
- `manifest.json`
- `keyframes/000.jpg`
- `keyframes/000.json`
- `trashbot_map.yaml`
- `trashbot_map.pgm`
- `launch.log`

本地 artifact 目录：

- `sprints/2026.06.10_00-25_no-motion-map-route-evidence/artifacts/board_no_motion_capture_clean_20260610/remote_capture/`

### route.csv

```csv
index,sec,nanosec,frame_id,x,y,z,qx,qy,qz,qw,frame
0,1781022360,318861516,map,0.0,0.0,0.0,0.0,0.0,0.0,1.0,000.jpg
```

### manifest.json

关键结论：

- `schema=trashbot.vision_samples.v1`
- `sample_count=1`
- `sample_ref=vision_sample://keyframes/000.json`
- `event_type=route_keyframe`

### keyframe 000

关键结论：

- `sample_id=route_keyframe_000`
- `detector=route_data_recorder`
- `route_pose=(0,0,0; 0,0,0,1)`

### save_map / map.yaml

`ros2 service call /trashbot/save_map std_srvs/srv/Trigger` 返回：

```text
success=True, message='Map saved to /root/.ros/trashbot_maps/trashbot_map.pgm'
```

`trashbot_map.yaml` 关键字段：

- `image=trashbot_map.pgm`
- `resolution=0.05000000074505806`
- `origin=[0.0, 0.0, 0.0]`

## 复跑后清理

复跑取证完成后，使用前台 `Ctrl-C` 结束本轮 launch，再次确认：

- no-motion 相关 `ps` 输出为空
- `ros2 node list` 为空
- `upper_robot_api.py` 仍保持运行

## 当前结论

- **清场动作成功**：残留重复节点已消除，复跑时 graph 干净
- **`/scan` 成功**
- **camera 成功**
- **`/tf_static` 成功**
- **`/odom` 成功**
- **`route.csv` / `manifest` / `keyframe` 成功**
- **`save_map` / `map.yaml` 成功**

## 剩余风险

1. 本轮 `route.csv` 只有 1 条样本，且 `/odom` 为 synthetic zero odom；这只证明 route/keyframe/manifest 软件链路，不代表真实路线。
2. 本轮 `waypoint_manager` 在 no-motion 期间持续追加 `auto_000x` 零位航点，说明后续若要让 clean capture 更收敛，最好在现场 no-motion 采集中关闭 `waypoint_manager`。
3. `Ctrl-C` 收尾时多处节点打印 `rcl_shutdown already called`，属于收尾噪声，不影响本轮证据，但后续可单独修复节点退出路径。
