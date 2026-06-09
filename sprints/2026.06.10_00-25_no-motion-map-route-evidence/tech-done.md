# No-Motion Map Route Evidence Tech Done

## sprint_type: epic

## 实际改动

- `onboard/src/ros2_trashbot_bringup/launch/learn.launch.py`
  - 新增默认关闭的 `camera_enabled`、`lidar_enabled`、`static_laser_tf_enabled`、`no_motion_static_odom_tf`、`no_motion_mock_odom_enabled` 参数，让真实上位机可以用同一个 `learn.launch.py` 启动 sensor + SLAM + map recorder + route recorder 的 no-motion 证据链。
  - 新增 `waypoint_manager` 开关，现场 no-motion 采集可避免航点学习自动追加重复零位点。
  - 新增 `slam_map_frame`、`slam_odom_frame`、`slam_base_frame`、`map_dir`、`default_map_name` 参数，确保 `slam_toolbox` 和 `map_recorder` 的现场输出路径可控。
  - 新增 synthetic zero `/odom` publisher，仅用于 no-motion route/keyframe/manifest 软件链路验证；不代表真实运动、里程计标定或 HIL。
- `onboard/src/ros2_trashbot_nav/ros2_trashbot_nav/route_data_recorder.py`
  - 将 `cv_bridge` 改为可选依赖，避免 Orange Pi 缺包时节点在订阅 `/odom` 前崩溃。
  - 缺 `cv_bridge` 时用 `numpy` + `cv2` 支持 `bgr8`、`rgb8`、`mono8`、`bgra8`、`rgba8` raw buffer 转换。
  - 图像转换失败时写 `image_conversion_status.json` 并继续写 `route.csv`，避免图片链路拖垮路线链路。
- `onboard/src/ros2_trashbot_bringup/test/test_launch_contract_static.py`
  - 新增 learn launch no-motion 参数、默认关闭、SLAM frame/map 输出、synthetic `/odom` 的静态契约断言。
- `onboard/src/ros2_trashbot_nav/test/test_route_data_recorder_static.py`
  - 新增 `cv_bridge` 可选 import、常见图像编码 fallback、unsupported encoding fail-closed、无图像仍写 `route.csv` 的测试。
- `docs/navigation/field_route_evidence_preflight.md`
  - 补充 2026-06-10 no-motion learn launch capture 的命令、证据边界和风险说明。
- `docs/navigation/fixed_route_workflow.md`
  - 补充 no-motion route/map/keyframe 采集命令和 expected outputs。
- `sprints/2026.06.10_00-25_no-motion-map-route-evidence/artifacts/board_no_motion_capture_20260610/**`
  - 保存真实上位机 `learn.launch.py --show-args`、topic samples、map/route/keyframe/manifest、launch log、LiDAR/camera 失败诊断材料。

## 验证结果

### 本地静态与单元测试

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile \
  onboard/src/ros2_trashbot_bringup/launch/learn.launch.py \
  onboard/src/ros2_trashbot_nav/ros2_trashbot_nav/route_data_recorder.py
```

- 结果：通过。

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest \
  onboard/src/ros2_trashbot_bringup/test/test_launch_contract_static.py \
  onboard/src/ros2_trashbot_nav/test/test_route_data_recorder_static.py
```

- 结果：通过，`19` 个测试通过。

额外回归：

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest \
  onboard/src/ros2_trashbot_nav/test/test_route_data_recorder_manifest.py
```

- 结果：通过，`5` 个测试通过。

### Docker/Humble 构建

```bash
bash onboard/scripts/docker_humble_build.sh
```

- 结果：通过。
- 关键日志：`Summary: 6 packages finished [54.8s]`
- 中途曾失败一次：`rm: cannot remove 'install/ros2_trashbot_interfaces/share/ros2_trashbot_interfaces': Directory not empty`。定位为 macOS/Docker bind-mounted `onboard/install` 半清理残留，不是源码错误；仅清理 `onboard/build`、`onboard/install`、`onboard/log` 后重跑通过。

### 真实上位机构建

- 同步 `learn.launch.py` 和 `route_data_recorder.py` 到 `root@192.168.1.11:37878`。
- 清理板上旧的 duplicate package 目录 `/root/rober/onboard/ros2_trashbot_*`。
- 板上增量构建通过：`Summary: 2 packages finished [8.41s]`。
- `ros2 launch ros2_trashbot_bringup learn.launch.py --show-args` 通过，输出保存到：
  - `artifacts/board_no_motion_capture_20260610/learn_show_args_after_sync.txt`

### no-motion 上板采集

运行命令保持禁止 `/cmd_vel`：

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
  route_output_dir:=/tmp/trashbot_no_motion_route \
  map_dir:=/tmp/trashbot_no_motion_maps \
  default_map_name:=trashbot_no_motion_map
```

主要产物：

- `route_output/route.csv`：`75` 行。
- `route_output/keyframes/`：`148` 个文件，包含 JPG 和 JSON keyframe。
- `route_output/manifest.json`：已生成，schema 为 `trashbot.vision_samples.v1`。
- `map_output/trashbot_no_motion_map.yaml` 和 `trashbot_no_motion_map.pgm`：已生成。
- `/trashbot/save_map`：`success=True`，message 为 `Map saved to /tmp/trashbot_no_motion_maps/trashbot_no_motion_map.pgm`。
- `/camera/image_raw`、`/tf_static`、`/odom`、`/map` samples 已保存。

### 远端清理

```bash
ssh -p 37878 root@192.168.1.11 '...'
```

- 结果：通过。
- 清理前残留包括 `learn.launch.py`、`slam_toolbox`、`map_recorder`、`waypoint_manager`、`camera_publisher`、`lidar_driver`、`static_laser_tf`、`no_motion_static_odom_tf`、`no_motion_mock_odom_pub`、`route_data_recorder`。
- 清理后：`ros2 node list` 为空，相关 `ps` 输出为空。
- 证据：`artifacts/board_no_motion_capture_20260610/remote_cleanup.txt`

清场后补充执行了一次短 no-motion smoke，证据保存在：

- `artifacts/board_no_motion_capture_clean_20260610/remote_capture/`
- 该目录包含最小 `route.csv`、`manifest.json`、`keyframes/000.*`、`map_output_trashbot_map.yaml` 和 `.pgm`。
- 这次 clean capture 只作为清场后最小复跑材料，不替代上方完整 `board_no_motion_capture_20260610` 证据包。

## 失败定位

1. `/scan` sample 未完成：`scan_once.txt` 为空。
2. `learn_launch.log` 显示 `lidar_driver` 已启动 `/dev/ttyACM0 @ 150000`，随后因串口读返回空数据崩溃：

```text
serial.serialutil.SerialException: device reports readiness to read but returned no data (device disconnected or multiple access on port?)
```

3. `ttyacm0_diagnostics.txt` 显示现场 ROS graph 存在重复 no-motion 节点和残留 `lidar_driver` 进程，`/dev/ttyACM0` 当时被 PID `33143` 占用。这说明本轮 `/scan` 失败更像现场进程/串口占用问题，不能判定 LiDAR 硬件本身不可用。
4. 本轮 `camera_publisher` 在当前 launch 内打开 `/dev/video1` 失败并 fail closed，但 `/camera/image_raw` sample 和 keyframes 仍产出。诊断显示现场已有残留 `camera_publisher` 进程，因此本轮只能证明 camera topic/keyframe 数据存在，不能证明本次 launch 独占启动了相机。

## 剩余风险

- no-motion `route.csv` 全部为 `0,0` synthetic `/odom` 样本，只证明 route/keyframe/manifest 软件链路，不代表真实运动路线、里程计或 HIL。
- `map.yaml` 是 no-motion SLAM/map recorder 产物，可作为建图链路 smoke，但没有真实移动覆盖，不可作为可导航地图。
- LiDAR 和 camera 的本轮 launch ownership 不干净，下一轮现场验证前必须先清理残留 ROS 进程和串口占用。
- `static_transform_publisher` 仍使用 old-style 参数，后续可单独切换为新式参数消除 warning。
- 本轮没有发布 `/cmd_vel`，也没有提升 `safe_to_control`、`primary_actions_enabled` 或 delivery success。
