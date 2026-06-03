# 2026.06.04 00-01 O1 Upper ROS2 Bootstrap Continue

sprint_type: micro

## 已读 vendor 来源

- `AGENTS.md`
- `OKR.md`
- `docs/vendor/VENDOR_INDEX.md`
- `docs/vendor/waveshare_wave_rover/ugv_rpi/base_ctrl.py`
- `docs/vendor/waveshare_wave_rover/ugv_rpi/config.yaml`
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/json_cmd.h`
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/uart_ctrl.h`
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/movtion_module.h`
- `docs/vendor/lidar_pkg_ros2-main/README.md`
- `docs/vendor/lidar_pkg_ros2-main/src/lidar_node.cpp`
- `docs/vendor/lidar_pkg_ros2-main/config/lidar_params.yaml`
- `docs/vendor/lidar_pkg_ros2-main/scripts/99-lidar.rules`
- `docs/vendor/lidar_pkg_ros2-main/launch/lidar.launch.py`

本轮采用的硬件事实：WAVE ROVER 底盘 UART 为 newline-delimited UTF-8 JSON；
`T=1`/`T=13` 属于运动控制，`T=130` 是底盘反馈请求。LiDAR 当前 source of
truth 是 `docs/vendor/lidar_pkg_ros2-main/`：`150000` baud、`A5 60` 启动、
`A5 00 A5 65 A5 65` 停止、`0xAA55` packet sync、`/scan`。本轮允许 LiDAR
start/stop bytes；禁止底盘运动命令。

## 实际改动

- `onboard/scripts/o1_ros2_humble_arm64_bootstrap.sh`
  - 新增 `source_ros_setup()`，在 source ROS2 setup 时临时关闭 `nounset`，修复
    `/opt/ros/humble/setup.bash` 访问未定义 `AMENT_TRACE_SETUP_FILES` 时导致的
    bootstrap 误失败。
  - `colcon build` 改为 `colcon build --symlink-install --base-paths src`，避免
    远端历史顶层包目录与 `src/` 下同名包重复导致构建失败。
- `onboard/scripts/o1_lidar_ros2_scan_smoke.sh`
  - 新增 `source_ros_setups()`，同样只在 source ROS2/colcon setup 阶段放宽
    `nounset`，保持 LiDAR-only smoke 的安全边界不变。
- `docs/interfaces/lidar_ros2_closed_loop.md`
  - 记录远端 ROS2 runtime/build 已完成，以及 LiDAR-only smoke 首次观察到
    `/scan`、`/lidar/raw_packet` 和 TF。
- `docs/hardware/o1_upper_computer_readiness_probe.md`
  - 更新上位机 readiness 状态：ROS2 Humble runtime 与 onboard install 已出现，
    当前不再 blocked 在 apt/dpkg/locales。
- `docs/process/okr_progress_log.md`
  - 追加 O1 事实记录；不调整 OKR 产品方向或百分比。
- `sprints/2026.06.04_00-01_o1-upper-ros2-bootstrap-continue/tech-done.md`
  - 记录本轮远端 bootstrap/smoke、验证和剩余风险。

同时复核上一轮 O1 manual feedback ACK dirty diff：

- `onboard/scripts/upper_robot_api.py`
  - `/api/base/manual` 只在方向写入和 auto-stop 写入都成功后追加一次
    vendor `T=130` feedback request；写失败时跳过 feedback 并保留失败证据。
- `onboard/scripts/test_upper_robot_api.py`
  - fake serial 已覆盖 `T=1 -> stop -> T=130` 顺序和写失败不追加 `T=130`。

本轮未改 PC workstation 文件，未改 `OKR.md`，未改 `AGENTS.md`。

## 远端 bootstrap 与 scan smoke 结果

远端入口：

```bash
ssh root@192.168.1.11 -p 37878
```

只读状态确认：

- `apt/dpkg/localedef/locale-gen` 已自然结束；`dpkg --audit` 无输出。
- `/opt/ros/humble/setup.bash` 已存在。
- `/root/rober/onboard/install/setup.bash` 初始缺失。
- source `/opt/ros/humble/setup.bash` 后，`ros2=/opt/ros/humble/bin/ros2`，
  `colcon=/usr/bin/colcon`。
- 远端旧源码缺 `src/ros2_trashbot_hardware/ros2_trashbot_hardware/lidar_driver.py`；
  已同步当前 `onboard/src` 与 `onboard/scripts` 到远端。

bootstrap 执行：

```bash
bash /root/rober/onboard/scripts/o1_ros2_humble_arm64_bootstrap.sh --skip-apt-install
```

结果：

```text
[o1-bootstrap] os=ubuntu version=22.04 codename=jammy arch=arm64
[o1-bootstrap] skip apt install requested
Summary: 6 packages finished [2min 8s]
[o1-bootstrap] ros2=/opt/ros/humble/bin/ros2
[o1-bootstrap] install_setup=/root/rober/onboard/install/setup.bash
[o1-bootstrap] bootstrap complete; run o1_lidar_ros2_scan_smoke.sh for LiDAR-only evidence
```

LiDAR-only smoke 执行：

```bash
bash /root/rober/onboard/scripts/o1_lidar_ros2_scan_smoke.sh \
  --serial-port /dev/ttyACM0 \
  --serial-baudrate 150000 \
  --frame-id laser_frame \
  --output-dir /tmp/o1_lidar_ros2_scan_smoke_current
```

结果摘要：

```json
{
  "output_dir": "/tmp/o1_lidar_ros2_scan_smoke_current",
  "scan_once_observed": true,
  "scan_hz_observed": true,
  "raw_packet_once_observed": true,
  "tf_observed": true,
  "all_required_observations_observed": true,
  "driver_started_by_smoke": true,
  "lidar_start_command_sent_by_smoke": true,
  "lidar_start_command_hex": "A5 60",
  "refuses_base_uart_ttyS5": true,
  "safe_to_control": false,
  "sends_base_motion_commands": false,
  "calls_base_manual": false,
  "publishes_cmd_vel": false
}
```

关键 evidence：

- `/scan` once：`frame_id=laser_frame`，`range_min=0.05`，`range_max=8.0`，
  `ranges` 出现真实数值，例如 `6.2295`、`0.5020`、`0.5070`。
- `/scan` hz：稳定输出 `average rate`，窗口内约 `295-300 Hz`。
- `/lidar/raw_packet` once：`data` 以 `170, 85` 开头，即 `0xAA,0x55`。
- TF：`tf2_echo base_link laser_frame` 输出零位姿 `Translation [0,0,0]`
  与单位四元数。
- topic list：`/scan`、`/lidar/raw_packet`、`/tf_static`、`/rosout`、
  `/parameter_events`。
- `lidar_driver.log` 在 summary 生成后、cleanup 阶段仍出现 ROS context shutdown
  error，因此该问题保留为后续 driver 优雅退出风险。

安全边界确认：

- 未发现 `/cmd_vel`、`/api/base/manual`、`/dev/ttyS5` 或 `esp32_bridge` 相关进程。
- 未运行 `dpkg --configure -a`，未叠加并发 apt。
- 本轮没有写 `/dev/ttyS5`，没有发送 WAVE ROVER `T=1/T=13/T=130/T=131`，
  没有调用 `/api/base/manual`，没有发布 `/cmd_vel`。
- LiDAR smoke 发送了 LiDAR vendor `A5 60` start 与退出 stop sequence；这是
  本轮目标行为，不属于底盘运动命令。

## 本地验证

```text
python3 -m unittest onboard/scripts/test_upper_robot_api.py onboard/scripts/test_o1_lidar_scan_proof_collector.py onboard/scripts/test_o1_upper_computer_readiness_probe.py
Ran 30 tests in 3.178s
OK
```

```text
python3 -m compileall -q onboard/scripts/upper_robot_api.py onboard/scripts/test_upper_robot_api.py onboard/scripts/o1_lidar_scan_proof_collector.py onboard/scripts/o1_upper_computer_readiness_probe.py
passed
```

```text
bash -n onboard/scripts/o1_ros2_humble_arm64_bootstrap.sh onboard/scripts/o1_lidar_ros2_scan_smoke.sh
passed
```

```text
git diff --check -- <touched files>
passed
```

## Hardware Owner 验收补记

2026-06-04 Hardware Infra Engineer 复核 dirty worktree 中允许范围内的 O1 LiDAR
bootstrap/smoke 与 8787 scan proof summary 改动，结论如下：

- vendor 来源已按 `AGENTS.md` 要求复读：LiDAR 依据
  `docs/vendor/lidar_pkg_ros2-main/`，WAVE ROVER 底盘 JSON/UART 依据
  `docs/vendor/waveshare_wave_rover/ugv_rpi/base_ctrl.py`、
  `docs/vendor/waveshare_wave_rover/ugv_rpi/config.yaml` 与
  `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/json_cmd.h`。
- 本轮可以把 O1 LiDAR 从 `ROS2 runtime missing` 推进到
  `real LiDAR ROS2 smoke observed`：证据覆盖 `/scan` once、`/scan` hz、
  `/lidar/raw_packet` once 和 `base_link -> laser_frame` 静态 TF。
- 只读 SSH 回放 `root@192.168.1.11:37878` 确认 `ros_setup=exists`、
  `onboard_install=exists`，并读取
  `/tmp/o1_lidar_ros2_scan_smoke_current/summary.json`：四项
  `required_observations` 均为 `observed=true`，
  `all_required_observations_observed=true`，同时 `safe_to_control=false`。
- 8787 scan proof summary 新增 `latest_scan_hz_observed`、
  `latest_scan_hz_average_rate_hz`、`latest_tf_observed`、
  `latest_all_required_observations_observed` 和 compact
  `latest_required_observations`，且只读 artifact，不启动 ROS2、不打开串口、
  不发送 LiDAR `A5 60` 或 WAVE ROVER `T` 命令。
- `o1_lidar_ros2_scan_smoke.sh` 显式拒绝 `/dev/ttyS5`，只允许 LiDAR-looking
  串口；summary 固定 `safe_to_control=false`、`sends_base_motion_commands=false`、
  `calls_base_manual=false`、`publishes_cmd_vel=false`。
- `/api/base/manual` 的新反馈读取只在方向写入和 auto-stop 均成功后追加
  `T=130`，写失败时跳过反馈；即使观察到 `T=1001`，也仍固定
  `robot_ack_connected=false`、`safe_to_control=false`、`hil_pass=false`。
- 本次验收未修改 PC workstation 文件；当前 PC 相关 dirty diff 不是本轮硬件 owner
  验收范围。

验收边界：这是 LiDAR ROS2 smoke evidence，不是 WAVE ROVER HIL，不是
`safe_to_control=true`，也不证明真实 `/odom`、`/imu/data`、`/battery`、SLAM/Nav2
消费、长稳运行、生产 udev `/dev/lidar` 或完整送达闭环。

## 剩余风险

- 本轮证明真实 ROS2 LiDAR `/scan`、`/lidar/raw_packet` 和静态 TF 的首个 smoke，
  但不等于 SLAM/Nav2 消费、长稳运行、建图质量或量产 udev `/dev/lidar` 完成。
- `lidar_driver.log` 在 smoke 退出阶段出现 ROS context shutdown error；证据已采到，
  但 driver 优雅退出还需后续在允许文件范围内修复或单独立项。
- 本轮没有执行底盘 HIL、没有真实 `/odom`、`/imu/data`、`/battery`，也没有证明
  WAVE ROVER robot ACK、运动控制安全、人工急停演练或 `safe_to_control=true`。
- 远端仍存在历史顶层包目录；bootstrap 通过 `--base-paths src` 规避重复包名，
  但没有清理远端旧目录。
