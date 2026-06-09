# Board Bringup Blocker Fix Tech Done

## sprint_type: epic

## 实际改动

- `onboard/src/ros2_trashbot_bringup/launch/bringup.launch.py`
  - 为 `task_orchestrator` 的 `elevator_assist_target_floor` 改用 `ParameterValue(..., value_type=str)`，避免 launch YAML 将楼层值误解析成整数。
  - 新增 `camera_enabled`、`camera_device`、`camera_topic`、`camera_frame_id`、`camera_width`、`camera_height`、`camera_fps` 参数；仅在显式启用时启动 `ros2_trashbot_vision/camera_publisher`。
  - 新增 `base_enabled`，让现场 sensor-only smoke 可以跳过 `esp32_bridge`，避免与 `upper_robot_api.py` 对 `/dev/ttyS5` 的占用冲突。
  - 新增 `lidar_enabled`、`lidar_serial_port`、`lidar_serial_baudrate`、`lidar_frame_id`、`lidar_scan_topic`、`lidar_raw_packet_topic`、`lidar_publish_raw_packets`、`lidar_mock_packets`、`lidar_mock_scan`，显式纳入 `ros2_trashbot_hardware/lidar_driver`。
  - 新增 `static_laser_tf_enabled`、`base_frame_id` 和 `laser_tf_*` 参数；显式启用时发布 smoke-only `base_link -> laser_frame` 静态 TF。
- `onboard/src/ros2_trashbot_bringup/test/test_launch_contract_static.py`
  - 新增静态断言，覆盖 `base_enabled`、LiDAR node 参数面和 smoke-only 静态 TF 发布者。
- `onboard/src/ros2_trashbot_hardware/ros2_trashbot_hardware/lidar_driver.py`
  - 同步实板已验证的 LiDAR ROS2 驱动，保留真实串口路径与 mock packet 路径双入口。
  - 真实串口模式使用 `/dev/ttyACM0 @ 150000` 风格参数；mock 模式明确不触碰真实串口。
- `onboard/src/ros2_trashbot_hardware/ros2_trashbot_hardware/lidar_packets.py`
  - 同步 vendor 风格 packet 解析、重同步和 mock packet 生成逻辑，供 LiDAR 驱动与单测复用。
- `onboard/src/ros2_trashbot_hardware/setup.py`
  - 注册 `lidar_driver` console script。
- `onboard/src/ros2_trashbot_hardware/test/test_lidar_driver_stubs.py`
  - 新增 fake serial 单测，覆盖启停命令、分片重同步、mock 模式和异常关闭路径。
- `onboard/src/ros2_trashbot_hardware/test/test_lidar_packets.py`
  - 新增 packet 长度、角度/距离转换和坏 header/长度拒绝测试。
- `onboard/src/ros2_trashbot_nav/ros2_trashbot_nav/waypoint_manager.py`
  - 将 `nav2_simple_commander` 改为可选依赖。
  - 缺依赖时保留航点学习、航点服务和航点 topic；执行导航时 fail closed，并输出可读原因。
- `onboard/src/ros2_trashbot_nav/test/test_waypoint_manager_learn_mode_static.py`
  - 调整静态断言，覆盖 Nav2 可选依赖和 fail-closed 日志。
- `onboard/src/ros2_trashbot_vision/ros2_trashbot_vision/camera_publisher.py`
  - 新增最小真实相机 publisher，基于 OpenCV `VideoCapture` 发布 `sensor_msgs/Image` 到 `/camera/image_raw`。
  - 无法打开设备或读帧失败时 fail closed，不伪造图像。
- `onboard/src/ros2_trashbot_vision/setup.py`
  - 注册 `camera_publisher` console script。
- `onboard/src/ros2_trashbot_vision/test/test_camera_publisher_static.py`
  - 新增静态测试，覆盖参数声明、fail-closed 文案和 console script 注册。
- `onboard/scripts/field_route_evidence_preflight.py`
  - SSH 模式下远端 ROS2 检查统一通过 `bash -lc` 执行。
  - 先 source `/opt/ros/humble/setup.bash`，再优先 source `/root/rober/onboard/install/setup.bash`，并保留候选 workspace 回退。
- `onboard/tests/test_field_route_evidence_preflight.py`
  - 新增远端 `bash -lc` + source 链路断言。
- `docs/navigation/field_route_evidence_preflight.md`
  - 记录 SSH 模式修复后的环境恢复逻辑和 `blocked_ros2_cli_missing` 假阴性根因。
  - 补充 `/scan`、`/tf_static` 的 topic gate 分层和新的 sensor-only bringup 命令。
- `docs/hardware/board_sensor_stack_smoke.md`
  - 新增实板传感器-only bringup 说明，明确 `base_enabled:=false`、LiDAR 参数、静态 TF 和风险边界。
- `docs/vision/board_camera_publisher.md`
  - 记录真实相机 publisher 的参数、启用方式、sensor-only smoke 组合、fail-closed 约束和本地资料来源。
- `sprints/2026.06.09_23-20_board-bringup-blocker-fix/artifacts/sensor_stack_smoke.md`
  - 落地 `--show-args`、sensor-only smoke topic 采样与关键日志。

## 验证结果

### 本地静态验证

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile \
  onboard/src/ros2_trashbot_hardware/ros2_trashbot_hardware/lidar_packets.py \
  onboard/src/ros2_trashbot_hardware/ros2_trashbot_hardware/lidar_driver.py \
  onboard/src/ros2_trashbot_bringup/launch/bringup.launch.py
```

- 结果：通过。

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest \
  onboard/src/ros2_trashbot_hardware/test/test_lidar_packets.py \
  onboard/src/ros2_trashbot_hardware/test/test_lidar_driver_stubs.py
```

- 结果：通过，`11` 个测试通过。

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest \
  onboard/src/ros2_trashbot_bringup/test/test_launch_contract_static.py
```

- 结果：通过，`14` 个测试通过。
- 中途曾出现 1 次失败：`test_launch_contract_static.py` 仍按旧 launch 结构断言 `# --- Behavior ---` 和旧的 `elevator_assist_target_floor` 传参形式；修正静态断言后重跑通过。

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile \
  onboard/src/ros2_trashbot_nav/ros2_trashbot_nav/waypoint_manager.py \
  onboard/src/ros2_trashbot_vision/ros2_trashbot_vision/camera_publisher.py \
  onboard/scripts/field_route_evidence_preflight.py
```

- 结果：通过。

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest \
  onboard/tests/test_field_route_evidence_preflight.py \
  onboard/src/ros2_trashbot_nav/test/test_waypoint_manager_learn_mode_static.py
```

- 结果：通过，`11` 个测试通过。
- 中途曾出现 1 次失败：`test_waypoint_manager_learn_mode_static.py` 仍按旧实现断言；修正测试后重跑通过。

### Docker 构建

```bash
bash onboard/scripts/docker_humble_build.sh
```

- 结果：通过。
- 关键日志：`Summary: 6 packages finished [54.6s]`

### 远端 SSH 验证

```bash
ssh -p 37878 root@192.168.1.11 'bash -lc "source /opt/ros/humble/setup.bash; source /root/rober/onboard/install/setup.bash; ros2 launch ros2_trashbot_bringup bringup.launch.py --show-args"'
```

- 结果：通过。
- 说明：远端 `bringup.launch.py --show-args` 正常输出参数列表，说明 `source` 链和新增 camera 参数均可见。

```bash
python3 onboard/scripts/field_route_evidence_preflight.py \
  --mode ssh \
  --ssh-target root@192.168.1.11 \
  --ssh-port 37878 \
  --timeout-s 8 \
  --output sprints/2026.06.09_23-20_board-bringup-blocker-fix/artifacts/preflight_ssh_after_fix.json
```

- 结果：通过并生成 JSON。
- 关键结论：
  - 已不再出现 `blocked_ros2_cli_missing`。
  - 当前状态为 `blocked_required_topics_missing`。
  - 根因不是 ROS2 CLI 丢失，而是预检时未运行 bringup，远端仅有 `/parameter_events` 和 `/rosout`。

### 板上增量构建与短时 bringup smoke

- 板上工作区增量构建：通过。
- 关键日志：`Summary: 2 packages finished [7.68s]`
- 中途曾出现 1 次失败：同步文件时误把包目录 rsync 到 `/root/rober/onboard/ros2_trashbot_*`，触发远端 duplicate package names。删除该临时错误目录并重新同步到 `/root/rober/onboard/src/...` 后，重建通过。
- 短时 bringup 观察结果：
  - `task_orchestrator` 的 `elevator_assist_target_floor` 参数类型崩溃已消失。
  - `waypoint_manager` 在缺 `nav2_simple_commander` 时按预期降级启动，没有因 import 崩溃退出。
  - `base_enabled:=false` 生效，sensor-only smoke 未启动 `esp32_bridge`，未碰 `/dev/ttyS5`，未发布 `/cmd_vel`。
  - `lidar_driver` 已通过 `bringup.launch.py` 启动，日志显示：`LiDAR serial started: /dev/ttyACM0 @ 150000`。
  - `camera_publisher` 已通过 `camera_device:=/dev/video1` 成功发布 `/camera/image_raw`。
  - `static_transform_publisher` 已发布 `base_link -> laser_frame` 的 smoke-only 静态 TF。
  - 可见 topic：`/camera/image_raw`、`/map`、`/scan`、`/tf_static`、`/trashbot/waypoints`
  - `/scan`、`/camera/image_raw`、`/tf_static` 均已成功 `echo --once`，关键证据见 `artifacts/sensor_stack_smoke.md`。
  - 本轮未发布 `/cmd_vel`

## 失败定位

- 已修复的 blocker：
  1. `task_orchestrator` 的 `elevator_assist_target_floor` 类型错误。
  2. `waypoint_manager` 因缺 `nav2_simple_commander` 的启动即崩溃。
  3. `field_route_evidence_preflight.py --mode ssh` 的 ROS2 CLI 假阴性。
  4. `bringup.launch.py` 缺少 LiDAR node、sensor-only 跳 base 开关和 smoke-only 静态 TF，导致 `/scan` / `/tf_static` 无法在统一 bringup 中采样。
  5. `bringup.launch.py` 默认使用 `/dev/video0` 时，当前实板无法获得图像；改为现场显式传 `camera_device:=/dev/video1` 后，`/camera/image_raw` 恢复可采样。
- 本轮额外定位到但已自行修正的问题：
  1. 板上同步路径错误导致 duplicate package names。

## 硬件入口排查补充（2026-06-09 23:41 CST）

- 新增 artifact：`sprints/2026.06.09_23-20_board-bringup-blocker-fix/artifacts/hardware_device_probe.md`
- 实板结论补充：
  1. `/dev/video0` 不是摄像头，而是 Orange Pi `cedrus` 编解码设备。
  2. `DV20 USB` 的主图像节点是 `/dev/video1`；OpenCV 已实测可读帧。
  3. `/dev/video2` 是 metadata 节点，不适合作为 `camera_publisher` 输入。
  4. `ttyACM0` 的 USB 身份为 `34bf:ff0a`，与项目内 LiDAR 参考线索一致；单独启动 `lidar_driver` 后可成功产出 `/scan`。
  5. 当前 `bringup.launch.py` 不包含 `lidar_driver`、`robot_state_publisher` 或 `static_transform_publisher`，因此本轮 `/scan` 与 `/tf_static` 缺失不能再按“短时没采到”表述，根因已收敛为 launch 组成边界。
  6. 同一次 smoke 中，`esp32_bridge` 默认仍尝试 `/dev/ttyUSB0`，与实板现有 `/dev/ttyS5` / `/dev/ttyACM0` 不符。

## 剩余风险

- `static_transform_publisher` 当前使用 old-style 参数，日志会给出 deprecated warning；它不影响 smoke 结果，但后续可切到新式参数写法以消除告警。
- `base_link -> laser_frame` 仍是 `0 0 0 / 0 0 0` 的 smoke-only 拓扑 TF，不代表机械安装标定完成，不能直接拿去做长期导航结论。
- `camera_device:=/dev/video1` 与 `lidar_serial_port:=/dev/ttyACM0` 是当前这块板的现场命令参数，不应写死回 launch 默认值。
- 本轮只验证了传感器链路和 bringup 组成，不等于底盘 UART/HIL、运动链路、建图或固定路线已完成。
- 本文件仅收口当前阶段结果；`side2side_check.md` 与 `final.md` 尚未更新，因为本轮虽然传感器 smoke 已恢复，但完整 Epic 收口仍需结合后续真实路线/地图/manifest 证据判断。

## 追加验证：2026-06-10 no-motion map / route / keyframe 证据采集

### 执行目标

- 在 `base_enabled:=false` 的前提下继续保持 no-motion；
- 采集短时 rosbag；
- 尝试 `save_map`；
- 尝试 `route_data_recorder`；
- 若 route.csv 仍无法产生，至少落一份真实相机 keyframe 样本。

### 实际命令与证据

新增 artifact：

- `sprints/2026.06.09_23-20_board-bringup-blocker-fix/artifacts/no_motion_mapping_capture.md`
- `sprints/2026.06.09_23-20_board-bringup-blocker-fix/artifacts/no_motion_sensor_20260609_235445/**`
- `sprints/2026.06.09_23-20_board-bringup-blocker-fix/artifacts/no_motion_map_retry_20260610_0000/**`

核心远端命令仍使用：

```bash
ros2 launch ros2_trashbot_bringup bringup.launch.py \
  base_enabled:=false \
  lidar_enabled:=true \
  lidar_serial_port:=/dev/ttyACM0 \
  lidar_serial_baudrate:=150000 \
  static_laser_tf_enabled:=true \
  camera_enabled:=true \
  camera_device:=/dev/video1
```

并在同一 RUN 下执行：

- `/scan` echo once
- `/camera/image_raw` echo once
- `/tf_static` echo once
- `/map` echo once
- `/odom` echo once
- `ros2 bag record -o $RUN/route_bag /scan /camera/image_raw /tf_static /map`
- `ros2 service call /trashbot/save_map std_srvs/srv/Trigger`
- `ros2 run ros2_trashbot_nav route_data_recorder ...`
- OpenCV 直接抓取 `/dev/video1` 样本图

### 结果

1. **rosbag 成功**
   - 产物：`route_bag/metadata.yaml`、`route_bag_0.db3`
   - `metadata.yaml` 显示录到：
     - `/scan`：1470 条
     - `/camera/image_raw`：2 条
     - `/tf_static`：1 条
   - 本轮 bag 中**没有 `/map` 消息**。

2. **topic 证据成功**
   - `/scan`、`/camera/image_raw`、`/tf_static` 都成功 `echo --once`
   - `/odom` 返回：
     - `topic [/odom] does not appear to be published yet`

3. **save_map 明确失败**
   - 第一轮综合脚本内调用只得到 ROS context 失效错误；
   - 随后单独重试，节点侧明确返回：
     - `success=False, message='No map data received'`
   - 结论：本轮没有可保存的 map 数据，`map.yaml` 未产出。

4. **route.csv 未产出，根因已收敛**
   - `route_data_recorder` 启动即失败：
     - `ModuleNotFoundError: No module named 'cv_bridge'`
   - 即便补齐该依赖，当前 no-motion bringup 也没有 `/odom`，所以仍不会形成有效轨迹点。

5. **keyframe fallback 成功**
   - 为避免本轮没有任何视觉材料，额外用 OpenCV 从 `/dev/video1` 保存：
     - `keyframe_sample.jpg`
     - `keyframe_sample.json`
   - `keyframe_sample.json` 记录：
     - `opened=true`
     - `read=true`
     - `shape=[480, 640, 3]`

### 追加失败定位

1. `bringup.launch.py` 当前只把 `map_recorder` 纳入图谱，没有把 `slam_toolbox` 纳入 no-motion 组合，因此 `/trashbot/save_map` service 可见不等于已有 `/map` 数据。
2. 板上 `ros2_trashbot_nav route_data_recorder` 运行依赖 `cv_bridge`，当前实板环境缺包，导致 route recorder 在订阅 `/odom` 之前就已退出。
3. `/odom` 在 no-motion sensor-only bringup 下不存在，符合本轮不启用底盘桥的边界；因此 route.csv 无法在真实 no-motion 条件下产生。

### 追加风险边界

- 本轮新增的是**no-motion 传感器证据**，不是地图完成、路线完成或运动完成证据。
- 若下一轮需要 `map.yaml`，必须把 mapping node 明确纳入现场 launch，并确认 `/map` 持续发布。
- 若下一轮需要 `route.csv` / `manifest.json`，必须先解决板上 `cv_bridge` 依赖，再决定是真实运动采集还是 mock `/odom` 软件链路验证。

## 交接：2026-06-10 no-motion map/route sprint

本轮末尾的 no-motion map/route blocker 已转入并收口于 `sprints/2026.06.10_00-25_no-motion-map-route-evidence/`。该后续 sprint 已把 `learn.launch.py` 作为统一 no-motion capture 入口，解决 `cv_bridge` 缺失导致 `route_data_recorder` 启动即崩溃的问题，并在真实上位机产出 `map.yaml`、`route.csv`、keyframes 与 manifest。剩余 `/scan` 和 camera launch ownership 风险以新 sprint 的 `final.md` 为准。

## 追加验证：2026-06-10 低速运动 Gate

### 新增 artifact

- `sprints/2026.06.09_23-20_board-bringup-blocker-fix/artifacts/motion_gate.md`

### 实际命令与结果

1. 远端 API 根与底盘状态查询：
   - `curl http://127.0.0.1:8787/`
   - `curl http://127.0.0.1:8787/api/base/status`
   - 结果：`safe_to_control=false`、`primary_actions_enabled=false`，但 API 已暴露 `/api/base/manual`、`/api/base/stop`，且 `base_status.control_policy` 明确声明 `low_speed_pulse_with_auto_stop`、`max_speed=0.12`、`max_pulse_ms=800`。
2. feedback before：
   - `POST /api/base/feedback-samples`
   - 结果：`2/2` 样本观测到 `T=1001`。
3. 低速 manual 点动：
   - `POST /api/base/manual`
   - body：`{"direction":"forward","speed":0.03,"duration_ms":200,"read_timeout_s":0.2,"read_window_s":0.8}`
   - 结果：
     - `accepted=true`
     - `command_result.command={"T":1,"L":0.03,"R":0.03}`
     - `stop_result.command={"T":1,"L":0,"R":0}`
     - `auto_stop_attempted=true`
     - `auto_stop_executed=true`
     - `t1001_feedback_status=observed`
4. 顺序补一次显式 stop + feedback after：
   - `POST /api/base/stop`
   - `POST /api/base/feedback-samples`
   - 结果：显式 stop 写入成功；after feedback 仍为 `2/2` 样本观测到 `T=1001`。

### Gate 结论

1. 远端 `upper_robot_api.py` 的 `manual_control()` 并**没有**因为 `safe_to_control=false` 或 `primary_actions_enabled=false` 而拒绝请求。
2. 本轮因此按 API 明确定义执行了一次最小低速点动，并只通过 `/api/base/manual` / `/api/base/stop` 完成，没有绕过到裸串口 `T=1/T=13`。
3. 但该 API 回包和源码仍固定声明：
   - `safe_to_control=false`
   - `primary_actions_enabled=false`
   - `T=1001` 仅是 vendor feedback material，不是 project robot ACK，也不是 HIL pass
4. 因此本轮新增的是**受控低速运动 gate 材料**，不是底盘主链路放行结论。

### 追加剩余风险

1. 当前 manual gate 证明的是 `/dev/ttyS5 @ 115200` 上位机 API 脉冲控制可调用，不等于 ROS2 `esp32_bridge`、`/cmd_vel`、`/odom` 主链路已通过。
2. 由于 `safe_to_control` 仍为 `false`，后续产品面或运营面仍必须继续 fail-closed，不能把这轮点动视作“现在可以随便开”。
3. 本轮只做了单次 `forward speed=0.03 duration_ms=200` 的极短点动；未覆盖后退、转向、持续运动、急停竞争、人工现场视频或更完整 HIL 证据。
