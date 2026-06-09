# No-Motion Map Route Evidence Tech Plan

## sprint_type: epic

## OKR 最低优先级核对

- 当前最低 Objective 仍按上一轮记录视为 O7，其次 O6。
- 本 sprint 直接补 O7 所需的真实 route/keyframe/manifest 输入，并继续为 O3 实板验证提供 map/route evidence。
- 若 `map.yaml` 仍失败，本 sprint 也必须产出可复现失败材料，避免下轮继续猜 SLAM/TF 根因。

## 设计

### 1. 接管当前未提交改动

当前工作区已有两处未提交改动：

- `onboard/src/ros2_trashbot_bringup/launch/learn.launch.py`
  - 已新增 camera/LiDAR/static TF/no-motion odom 参数和节点。
- `onboard/src/ros2_trashbot_nav/ros2_trashbot_nav/route_data_recorder.py`
  - 已将 `cv_bridge`、`cv2`、`numpy` 变成可选依赖，并增加 `convert_image_msg_to_bgr8_without_cv_bridge`。

子 agent 必须先读当前 diff，在现有基础上修补；不得回滚或重写成旧设计。

### 2. Learn Launch No-Motion 入口

`learn.launch.py` 应保留正常学习默认值不变，新增入口全部默认关闭：

- `camera_enabled=false`
- `lidar_enabled=false`
- `static_laser_tf_enabled=false`
- `no_motion_static_odom_tf=false`
- `no_motion_mock_odom_enabled=false`

现场命令显式启用后，应同时启动：

- `slam_toolbox`
- `map_recorder`
- `camera_publisher`
- `lidar_driver`
- `static_transform_publisher base_link -> laser_frame`
- `static_transform_publisher odom -> base_link`
- synthetic zero `/odom`
- `route_data_recorder`

### 3. Route Data Recorder 降级

`route_data_recorder` 的目标不是伪造硬件，而是让软件链路不因板上缺 `cv_bridge` 卡死：

- 有 `cv_bridge`：沿用 `imgmsg_to_cv2(..., desired_encoding='bgr8')`。
- 无 `cv_bridge`：支持 `bgr8`、`rgb8`、`mono8`、`bgra8`、`rgba8` 的 raw buffer 转 BGR。
- 图像无法转换：仍记录 `route.csv`，并写 `image_conversion_status.json`；不崩溃。
- 有图像和 odom：写 keyframe jpg、keyframe json 和 `manifest.json`。

### 4. 实板验证

禁止 `/cmd_vel`。使用当前已验证设备参数：

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

## 文件范围

允许改动：

- `onboard/src/ros2_trashbot_bringup/launch/learn.launch.py`
- `onboard/src/ros2_trashbot_bringup/test/**`
- `onboard/src/ros2_trashbot_nav/ros2_trashbot_nav/route_data_recorder.py`
- `onboard/src/ros2_trashbot_nav/test/**`
- `docs/navigation/**`
- `sprints/2026.06.10_00-25_no-motion-map-route-evidence/**`

不得改动：

- `docs/vendor/**`
- WAVE ROVER firmware/factory files
- 运动控制映射、速度默认值、串口默认值
- 与本轮 map/route/no-motion evidence 无关的前端或产品代码

## 验收命令

本地必须执行：

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile \
  onboard/src/ros2_trashbot_bringup/launch/learn.launch.py \
  onboard/src/ros2_trashbot_nav/ros2_trashbot_nav/route_data_recorder.py
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest \
  onboard/src/ros2_trashbot_bringup/test/test_launch_contract_static.py \
  onboard/src/ros2_trashbot_nav/test/test_route_data_recorder_manifest.py \
  onboard/src/ros2_trashbot_nav/test/test_route_data_recorder_static.py
bash onboard/scripts/docker_humble_build.sh
```

如果 `test_route_data_recorder_static.py` 不存在，创建它覆盖：

- `cv_bridge` 可选 import；
- raw `bgr8/rgb8/mono8/bgra8/rgba8` 转换；
- unsupported encoding fail-closed；
- 无图像时仍写 route.csv。

上板必须执行并保存 artifact：

```bash
ssh -p 37878 root@192.168.1.11 'bash -lc "source /opt/ros/humble/setup.bash; source /root/rober/onboard/install/setup.bash; ros2 launch ros2_trashbot_bringup learn.launch.py --show-args"'
```

以及 no-motion capture：

- `/scan` echo once
- `/camera/image_raw` echo once
- `/tf_static` echo once
- `/odom` echo once
- `route.csv` / `keyframes` / `manifest.json` 检查
- `save_map` 调用和 `map.yaml` 检查
- 失败时保存日志

## 成功标准

- 本地测试和 Docker build 通过。
- 板上 `learn.launch.py --show-args` 可见新增参数。
- `route_data_recorder` 不再因缺 `cv_bridge` 退出。
- no-motion 条件下至少生成 `route.csv` 一条样本；若图像转换成功，同时生成 keyframe 与 manifest。
- `map.yaml` 若仍未生成，必须有明确 SLAM/TF/map service 日志证据。
