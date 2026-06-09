# ESP32 Bridge Dynamic Odom TF Tech Done

## sprint_type: micro

## 目标

上一轮 integrated capture 为了让 `slam_toolbox` 有 TF 拓扑，仍启用了 `no_motion_static_odom_tf:=true`。这能证明 smoke 级 `/scan -> /map` 链路，但不能代表运动时动态 `odom -> base_link` 正确。本轮目标是在 `esp32_bridge` 发布 ROS-side command integration `/odom` 的同时发布同源动态 `odom -> base_link` TF，使下一轮上车 capture 可以关闭 `no_motion_static_odom_tf`。

## Owner

- 主责：`robot-software-engineer`

## 允许改动范围

- `onboard/src/ros2_trashbot_hardware/package.xml`
- `onboard/src/ros2_trashbot_hardware/ros2_trashbot_hardware/bridge_config.py`
- `onboard/src/ros2_trashbot_hardware/ros2_trashbot_hardware/esp32_bridge_node.py`
- `onboard/src/ros2_trashbot_hardware/test/test_waveshare_json_bridge.py`
- `docs/hardware/wave_rover_json_bridge.md`
- `sprints/2026.06.10_01-15_esp32-bridge-dynamic-odom-tf/tech-done.md`

## 功能要求

- `esp32_bridge` 发布动态 `odom -> base_link` TF，内容与当前 `/odom` 的 command integration 位姿一致。
- 增加参数控制，例如 `publish_odom_tf`，默认建议 `true`，但必须记录这是 ROS-side command integration，不是实测轮速/编码器。
- 保持 `/odom` 原 topic 行为不破坏。
- 测试覆盖：TF broadcaster 被创建；`_publish_odom()` 发布 `/odom` 时也发送同源 Transform；可通过参数关闭 TF。
- 文档同步说明：该 TF 解除 smoke capture 对 `no_motion_static_odom_tf` 的依赖，但不提升为导航级实测里程计。

## 验收命令

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest onboard/src/ros2_trashbot_hardware/test/test_waveshare_json_bridge.py
python3 -m py_compile \
  onboard/src/ros2_trashbot_hardware/ros2_trashbot_hardware/bridge_config.py \
  onboard/src/ros2_trashbot_hardware/ros2_trashbot_hardware/esp32_bridge_node.py
```

如环境允许，可补板上单包 build 或 Docker/Humble build；否则写明原因。

## 实际改动

- `onboard/src/ros2_trashbot_hardware/ros2_trashbot_hardware/bridge_config.py`
  - 新增 `publish_odom_tf` 参数声明与加载，默认 `true`。
- `onboard/src/ros2_trashbot_hardware/ros2_trashbot_hardware/esp32_bridge_node.py`
  - 在 `ESP32Bridge` 中按参数创建 `TransformBroadcaster`。
  - `_publish_odom()` 在发布 `/odom` 后，同周期发送与 `/odom` pose 完全一致的 `odom -> base_link` Transform。
  - 启动日志新增 `publish_odom_tf` 状态，并继续明确 `odom source=ROS-side command integration`。
- `onboard/src/ros2_trashbot_hardware/package.xml`
  - 增加 `tf2_ros` 依赖。
- `onboard/src/ros2_trashbot_hardware/test/test_waveshare_json_bridge.py`
  - 补充 `TransformStamped`/`Odometry`/`tf2_ros` 离线 stub。
  - 新增 `publish_odom_tf` 默认值测试、TF 开启/关闭测试，以及 Transform 与 `/odom` frame/pose 一致性测试。
- `docs/hardware/wave_rover_json_bridge.md`
  - 补充 `publish_odom_tf` 参数说明。
  - 明确动态 `odom -> base_link` TF 仅为 command integration，同步解除下一轮 capture 对 `no_motion_static_odom_tf` 的依赖，但不提升为导航级实测里程计。

## 验证结果

- 通过：

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest onboard/src/ros2_trashbot_hardware/test/test_waveshare_json_bridge.py
```

输出：

```text
...................
----------------------------------------------------------------------
Ran 19 tests in 0.011s

OK
```

- 通过：

```bash
python3 -m py_compile \
  onboard/src/ros2_trashbot_hardware/ros2_trashbot_hardware/bridge_config.py \
  onboard/src/ros2_trashbot_hardware/ros2_trashbot_hardware/esp32_bridge_node.py
```

输出：无输出，返回码 0。

- 未补 Docker/Humble build：
  - 本轮改动仅涉及 Python runtime、参数层与离线单测，用户给定的强制验收命令已全部通过。
  - 若下一轮要做 integrated capture，建议再由对应 owner 在 Docker/Humble 或车上环境补一次 package 级 smoke。

## 剩余风险

- 当前 `odom -> base_link` TF 与 `/odom` 一样，仍是 ROS-side command integration，只反映最近一次 `/cmd_vel` 的积分结果，不含真实编码器、轮速闭环或 slip 校正。
- 因此，本轮证据边界仅能支持“关闭 `learn.launch.py` 的 `no_motion_static_odom_tf` 并保持 TF 拓扑连通”，不能支持“导航级实测里程计可用”这一结论。
- 真实上车 integrated capture 仍需把 `/odom` topic 与动态 TF 一起留证，并在 run 记录中明确标注 `source=command_integration`。

## 2026-06-10 上位机复测补证

### 资料来源

- `docs/vendor/VENDOR_INDEX.md`
- `docs/vendor/waveshare_wave_rover/ugv_rpi/base_ctrl.py`
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/json_cmd.h`

以上资料用于复核 WAVE ROVER 上位机/下位机 UART JSON 口径：`/dev/ttyS5`、`115200`、newline-delimited JSON、`command_mode:=speed` 对应差速速度指令；本轮继续**不启用 `T=13`**。

### 上板范围

- 目标机：`root@192.168.1.11:37878`
- 远端同步文件：
  - `onboard/src/ros2_trashbot_hardware/package.xml`
  - `onboard/src/ros2_trashbot_hardware/ros2_trashbot_hardware/bridge_config.py`
  - `onboard/src/ros2_trashbot_hardware/ros2_trashbot_hardware/esp32_bridge_node.py`
- 本地回传产物：
  - `sprints/2026.06.10_01-15_esp32-bridge-dynamic-odom-tf/artifacts/remote_capture/`
  - `sprints/2026.06.10_01-15_esp32-bridge-dynamic-odom-tf/artifacts/route/`
  - `sprints/2026.06.10_01-15_esp32-bridge-dynamic-odom-tf/artifacts/map/`

### 板上执行与结果

- `ssh true`：通过。
- API before：
  - 通过 `curl http://127.0.0.1:8787/api/base/status` 取回 `trashbot.upper_robot_api.v1.base_status`。
  - 状态显示 `port=/dev/ttyS5`、`baudrate=115200`、`safe_to_control=false`、`feedback_ack.t1001_observed=false`。
- 板上单包 build：通过。

```bash
cd /root/rober/onboard
source /opt/ros/humble/setup.bash
colcon build --symlink-install --packages-select ros2_trashbot_hardware
```

输出：

```text
Starting >>> ros2_trashbot_hardware
Finished <<< ros2_trashbot_hardware [5.96s]

Summary: 1 package finished [7.25s]
```

- 启动 `esp32_bridge`：
  - 参数：`serial_port:=/dev/ttyS5`、`serial_baudrate:=115200`、`command_mode:=speed`、`feedback_interval_ms:=100`、`publish_odom_tf:=true`
  - 日志见 `artifacts/remote_capture/esp32_bridge.log`
  - 关键证据：

```text
Connected to WAVE ROVER ESP32 on /dev/ttyS5 @ 115200
ESP32Bridge ready: ... command_mode=speed; publish_odom_tf=True; odom source=ROS-side command integration until measured wheel odometry is validated
```

- 启动 `learn.launch.py`，显式关闭：
  - `no_motion_static_odom_tf:=false`
  - `no_motion_mock_odom_enabled:=false`
  - 运行期 topics / services 包含 `/tf`、`/odom`、`/scan`、`/camera/image_raw`、`/battery`、`/imu/data`、`/trashbot/stop`、`/trashbot/save_map`

### 动态 TF / odom 证据

- `/tf` 由 `esp32_bridge` 发布 `odom -> base_link`，证据见 `artifacts/remote_capture/tf_after_motion2.txt`
  - 已观测到 `header.frame_id: odom`
  - 已观测到 `child_frame_id: base_link`
  - 非零积分样本存在，首次若干 `translation.x` 为：
    - `0.00150020097`
    - `0.00299997072`
    - `0.0045066879`
    - `0.006002118900000001`
    - `0.007504607370000001`

- `/odom` 证据见 `artifacts/remote_capture/odom_after_motion2.txt`
  - 已观测到 `frame_id: odom`
  - 已观测到 `child_frame_id: base_link`
  - 非零积分样本存在；`position.x` 与 `/tf` 同步增长，`twist.linear.x` 取到 `0.03`

- 证据边界：
  - 本轮只能证明 `esp32_bridge` 在 ROS 侧 command integration `/odom` 的**同周期**发布了动态 `odom -> base_link` TF。
  - 这**不是**实测编码器/轮速里程计，不得外推为导航级 odom。

### integrated capture 结果

- LiDAR：通过  
  证据：`artifacts/remote_capture/scan_once.txt`
- Camera：通过  
  证据：`artifacts/remote_capture/camera_once.txt`
- Battery：通过  
  证据：`artifacts/remote_capture/battery_once.txt`
- IMU：通过  
  证据：`artifacts/remote_capture/imu_once.txt`
- motion：通过  
  安全边界采用单次 `linear.x=0.03`，随后 `sleep 0.2s`、零速、`/trashbot/stop`；日志见 `artifacts/remote_capture/pulse_and_stop2.log`
- stop service：通过  
  返回：`success=True, message='Motors stopped'`
- save_map：通过  
  返回：`success=True, message='Map saved to /tmp/trashbot_dynamic_odom_tf_maps/trashbot_dynamic_odom_tf_map.pgm'`

### route / keyframe / map 产物

- route：
  - `artifacts/route/route.csv`
  - `artifacts/route/manifest.json`
- keyframes：
  - `artifacts/route/keyframes/001.jpg` ~ `016.jpg`
  - 对应 `001.json` ~ `016.json`
- map：
  - `artifacts/map/trashbot_dynamic_odom_tf_map.pgm`
  - `artifacts/map/trashbot_dynamic_odom_tf_map.yaml`

`route.csv` 已记录非零位移，样本从 `x=0.01050082056` 增长到 `x=0.1679980841099999`，说明 integrated capture 中的短程 motion 已被 route recorder 接收到。

### cleanup / API 恢复

- 结束前已清理本轮 ROS2 进程，并确认 `lsof /dev/ttyS5` 不再残留 `esp32_bridge`
- `upper_robot_api.py` 已恢复为：

```bash
python3 /root/rober/onboard/scripts/upper_robot_api.py \
  --host 0.0.0.0 \
  --port 8787 \
  --camera-base-url http://127.0.0.1:8088 \
  --base-port /dev/ttyS5 \
  --base-baudrate 115200 \
  --max-speed 0.12
```

- API after：本轮回传证据为 `artifacts/remote_capture/upper_robot_api_restore.log`，内容显示 `upper_robot_api.py` 已按原端口 `8787` 重新启动；未回传完整 `base_status` JSON，因此本轮不把 API status 作为新增闭环证据。

### 复测剩余风险

- `learn_launch.log` 持续出现 `slam_toolbox` 的 `Message Filter dropping message ... queue is full`，本轮不阻塞 `/scan`、route、map 和动态 TF 验证，但会影响后续长时建图质量，需要独立收敛。
- 本轮 motion 证据来自 command integration，route 上的位移也建立在同一 odom 来源之上；它证明的是“动态 TF 与 `/odom` 同源联通并可驱动上层记录”，不是“底盘真实位移闭环已校准”。
- `upper_robot_api.py` 已有进程恢复日志，但缺少回传的 API after status JSON；下一轮若继续占用 `/dev/ttyS5`，应把 restore 后的 `/api/base/status` 响应一并归档。
