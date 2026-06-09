# ESP32 Feedback Debug Log Tech Done

## sprint_type: micro

## 目标

上一轮 `motion-feedback-alignment` 证明了 API restore、`/battery`、`/imu/data`、安全短脉冲和 stop，但没有在 bounded motion 窗口中证明 `T=1001.L/R` 非零。原因之一是 `esp32_bridge` 当前只把 `T=1001` 派生为 `/imu/data` 和 `/battery`，没有把原始 `L/R` 以可归档形式暴露；direct raw UART 抢读又容易和 bridge 串口 owner 冲突并产生 corrupted/incomplete JSON。

本轮目标：为 `esp32_bridge` 增加一个默认关闭的 evidence/debug 入口：`feedback_debug_log_path`。当该参数为空时保持现有行为；当参数为非空路径时，在收到并解析 vendor `T=1001` 后追加 JSONL，记录同帧 `left_speed/right_speed/roll/pitch/yaw/voltage` 以及 yaw 是否可用。下一轮上车可用同一个 bounded pulse 同时抓 `/cmd_vel`、debug JSONL、`/odom`、`/tf`。

## Owner

- 主责：`robot-software-engineer`

## 资料来源

- `docs/vendor/VENDOR_INDEX.md`
- `docs/vendor/waveshare_wave_rover/ugv_rpi/base_ctrl.py`
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/json_cmd.h`
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/uart_ctrl.h`
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/ugv_advance.h`

## 允许改动范围

- `onboard/src/ros2_trashbot_hardware/ros2_trashbot_hardware/bridge_config.py`
- `onboard/src/ros2_trashbot_hardware/ros2_trashbot_hardware/esp32_bridge_node.py`
- `onboard/src/ros2_trashbot_hardware/test/test_waveshare_json_bridge.py`
- `docs/hardware/wave_rover_json_bridge.md`
- `sprints/2026.06.10_01-50_esp32-feedback-debug-log/tech-done.md`

范围外文件不得改动；本轮先完成软件入口与离线测试，不直接跑上车运动。

## 功能要求

- 新增 `feedback_debug_log_path` 参数，默认 `""`，默认行为不写文件。
- 参数非空时，`esp32_bridge` 每收到一个有效 `T=1001` feedback，就追加一行 JSONL。
- JSONL 单行至少包含：
  - `schema`
  - `observed_at_unix_s`
  - `source`
  - `left_speed`
  - `right_speed`
  - `roll`
  - `pitch`
  - `yaw`
  - `yaw_available`
  - `voltage`
- 日志写入失败不能阻塞 `/imu/data`、`/battery` 或安全 stop；必须打 warning。
- 不改变 `/odom`、dynamic TF、`/imu/data`、`/battery` 现有 topic 行为。
- 文档必须明确该日志是 evidence/debug 材料，不代表导航级实测里程计；`L/R` 字段采用 vendor `T=1001` 原始反馈口径。

## 验收命令

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest onboard/src/ros2_trashbot_hardware/test/test_waveshare_json_bridge.py
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile \
  onboard/src/ros2_trashbot_hardware/ros2_trashbot_hardware/bridge_config.py \
  onboard/src/ros2_trashbot_hardware/ros2_trashbot_hardware/esp32_bridge_node.py
```

如环境允许，可补 `colcon build --symlink-install --packages-select ros2_trashbot_hardware`；否则说明原因。

## 实际改动

- `onboard/src/ros2_trashbot_hardware/ros2_trashbot_hardware/bridge_config.py`
  - 新增 `feedback_debug_log_path` 参数声明，默认 `""`。
  - `BridgeConfig` 读取并保存该路径；未把它纳入硬件启动数值校验，因为它只是 evidence/debug 文件开关。
- `onboard/src/ros2_trashbot_hardware/ros2_trashbot_hardware/esp32_bridge_node.py`
  - `ESP32Bridge` 读取 `feedback_debug_log_path`，启动日志展示是否启用 debug log。
  - `_publish_feedback()` 仍先发布 `/imu/data` 与 `/battery`，随后仅在路径非空时追加 JSONL。
  - JSONL schema 为 `trashbot.wave_rover.feedback_debug.v1`，字段包含 `observed_at_unix_s`、`source=wave_rover_uart_t1001`、`left_speed`、`right_speed`、`roll`、`pitch`、`yaw`、`yaw_available`、`voltage`。
  - 文件追加失败只打 warning，不影响 topic 发布或后续 stop/service 路径。
- `onboard/src/ros2_trashbot_hardware/test/test_waveshare_json_bridge.py`
  - 增加默认参数断言。
  - 增加 debug JSONL 成功写入测试。
  - 增加写入失败时仍发布 `/imu/data`、`/battery` 且记录 warning 的测试。
- `docs/hardware/wave_rover_json_bridge.md`
  - 增加 `feedback_debug_log_path` 参数说明、JSONL 字段说明、evidence/debug 边界和写入失败行为。

采用资料来源：

- `docs/vendor/VENDOR_INDEX.md`
- `docs/vendor/waveshare_wave_rover/ugv_rpi/base_ctrl.py`
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/json_cmd.h`
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/uart_ctrl.h`
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/ugv_advance.h`

## 验证结果

通过：

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest onboard/src/ros2_trashbot_hardware/test/test_waveshare_json_bridge.py
```

结果：

```text
.....................
----------------------------------------------------------------------
Ran 21 tests in 0.010s

OK
```

通过：

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile \
  onboard/src/ros2_trashbot_hardware/ros2_trashbot_hardware/bridge_config.py \
  onboard/src/ros2_trashbot_hardware/ros2_trashbot_hardware/esp32_bridge_node.py
```

结果：命令退出码 `0`，无 stderr/stdout。

补充上位机验证通过：

- 2026-06-10 01:54 CST，在真实上位机 `root@192.168.1.11:37878` 的 `/root/rober/onboard` 中同步当前本地 `ros2_trashbot_hardware` 包后运行：

```bash
source /opt/ros/humble/setup.bash
cd /root/rober/onboard
colcon build --symlink-install --packages-select ros2_trashbot_hardware
```

结果归档于 `artifacts/remote_capture/board_build.log`：

```text
Starting >>> ros2_trashbot_hardware
Finished <<< ros2_trashbot_hardware [5.86s]

Summary: 1 package finished [7.13s]
```

## 真实上位机硬件验证

### 已读 vendor 来源

- `docs/vendor/VENDOR_INDEX.md`
- `docs/vendor/waveshare_wave_rover/ugv_rpi/base_ctrl.py`
- `docs/vendor/waveshare_wave_rover/ugv_rpi/config.yaml`
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/json_cmd.h`
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/uart_ctrl.h`
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/ugv_advance.h`

采用事实：

- UART 是 UTF-8 JSON newline-delimited transport。
- vendor Raspberry Pi 参考默认 `115200`，本次真实 Orange Pi 上位机实际验证设备是 `/dev/ttyS5`。
- `T=1` 是左右轮 speed control，`T=130` 请求 base feedback，`T=131` 控制 feedback flow，`T=142` 控制 feedback interval，`T=143` 控制 UART echo。
- `T=1001` 是 `FEEDBACK_BASE_INFO`，`ugv_advance.h` 中 `baseInfoFeedback()` 写出 `L/R/r/p/y/v` 字段。

### 上位机验收命令

通过：

```bash
ssh root@192.168.1.11 -p 37878 'python3 --version && test -e /dev/ttyS5'
```

结果：

```text
Python 3.10.12
```

通过：

```bash
ssh root@192.168.1.11 -p 37878 'curl -sS http://127.0.0.1:8787/api/base/status'
```

结果摘要：

```json
{
  "port": "/dev/ttyS5",
  "baudrate": 115200,
  "feedback_ack": {
    "t1001_observed": true,
    "source": "fresh_readback"
  },
  "feedback_readback": {
    "observed_feedback_types": [1001],
    "invalid_json_count": 0
  }
}
```

### 接管、pulse 与恢复

- 接管前状态归档于 `artifacts/remote_capture/status_before.json`，API 可 fresh readback 到 `T=1001`。
- 第一次接管发现有一个不受 systemd 当前状态约束的 `upper_robot_api.py` 旧进程，导致 API 与 bridge 可能同时竞争 `/dev/ttyS5`；该次证据不作为最终 clean capture。
- 已恢复 API 后重试：停止 `trashbot-upper-robot-api.service`，确认无 `upper_robot_api.py` / `esp32_bridge` 进程后启动：

```bash
ros2 run ros2_trashbot_hardware esp32_bridge --ros-args \
  -p serial_port:=/dev/ttyS5 \
  -p serial_baudrate:=115200 \
  -p command_mode:=speed \
  -p feedback_interval_ms:=50 \
  -p feedback_debug_log_path:=/tmp/trashbot_feedback_debug.jsonl
```

- bounded pulse 采用 `/cmd_vel`：`linear.x=0.03`，非零窗口 `0.25s`，随后连续零速并调用 `/trashbot/stop`。
- `artifacts/remote_capture/pulse_and_stop.log` 显示 `/cmd_vel` 订阅数为 `1`，`/trashbot/stop` 返回 `success=True, message='Motors stopped'`。
- `artifacts/remote_capture/odom_after_motion.txt` 有命令积分 `/odom` 样本，`x=0.007494837359999999`，采样时 twist 已为零。
- `artifacts/remote_capture/tf_after_motion.txt` 有同源 `odom -> base_link` TF 样本，`x=0.007494837359999999`。
- `artifacts/remote_capture/status_after.json` 证明 API 已恢复，`feedback_ack.t1001_observed=true`，fresh readback `observed_feedback_types=[1001]`，`invalid_json_count=0`。
- `artifacts/remote_capture/upper_robot_api_restore.log` 记录恢复后 `trashbot-upper-robot-api.service` 为 `active (running)`。

### feedback_debug JSONL 结论

`artifacts/remote_capture/feedback_debug_summary.json`：

```json
{
  "capture_attempt": "retry_clean_api_stopped_before_bridge",
  "record_count": 1592,
  "valid_t1001_feedback_rows": 1592,
  "invalid_line_count": 0,
  "nonzero_lr_count": 0,
  "status_after_feedback_ack_t1001_observed": true,
  "bounded_pulse": {
    "linear_x_mps": 0.03,
    "nonzero_window_s": 0.25,
    "stop_service": "/trashbot/stop"
  }
}
```

结论：

- `feedback_debug_log_path` 在真实上位机 `/dev/ttyS5` + WAVE ROVER feedback stream 下能写入有效 JSONL。
- JSONL 行的 `schema=trashbot.wave_rover.feedback_debug.v1` 且 `source=wave_rover_uart_t1001`，这是由 `esp32_bridge` 仅在成功解析 vendor `T=1001` 后写入的证据。
- 本次 1592 行有效记录中 `left_speed=0.0` 且 `right_speed=0.0`，没有抓到非零 L/R。
- 电压样本范围约 `12.403V` 到 `12.415V`；`yaw_available=false`，`yaw=null`，roll/pitch 有样本。

### 归档 artifacts

- `artifacts/remote_capture/status_before.json`
- `artifacts/remote_capture/board_build.log`
- `artifacts/remote_capture/esp32_bridge.log`
- `artifacts/remote_capture/feedback_debug.jsonl`
- `artifacts/remote_capture/feedback_debug_summary.json`
- `artifacts/remote_capture/pulse_and_stop.log`
- `artifacts/remote_capture/odom_after_motion.txt`
- `artifacts/remote_capture/tf_after_motion.txt`
- `artifacts/remote_capture/status_after.json`
- `artifacts/remote_capture/upper_robot_api_restore.log`

## 剩余风险

- 本轮已补真实上位机 `/dev/ttyS5` 与 WAVE ROVER `T=1001` feedback JSONL 证据，但 `left_speed/right_speed` 在 bounded pulse 中仍为 `0.0/0.0`；这说明 debug log 写入可用，不证明 vendor L/R 能反映短脉冲轮速。
- `/odom` 与 `/tf` 是 ROS-side command integration，不是实测编码器里程计；本次 `x=0.007494837359999999` 只证明 `/cmd_vel` 被 bridge 接收后积分发布。
- `esp32_bridge` 在 SIGINT 停止时记录 `ExternalShutdownException` / `rcl_shutdown already called` traceback；它发生在 pulse、零速、`/trashbot/stop` 和 JSONL 归档之后，未影响 API 恢复，但后续软件侧可优化 shutdown handler。
- 上车使用非空 `feedback_debug_log_path` 前，需要 operator 确认目录存在、权限可写、磁盘空间足够。
- 写入失败会 warning 但不会阻塞 topic；如果路径长期不可写，bounded motion evidence 会缺失，需要从 warning 和空文件定位。
- 后续若必须证明 L/R 非零，应拉长但仍安全的低速窗口，或同步抓原始 UART/firmware speedGetA/B 更新节奏；不能把本次 `L/R=0` 写成实测轮速已通过。
