# Motion Feedback Alignment Tech Done

## sprint_type: micro

## 目标

前几轮已经完成同轮 LiDAR、camera、map、route/keyframes、`/odom`、dynamic `odom -> base_link` TF、短程 `/cmd_vel` motion 和 `/trashbot/stop` 证据；也已修复 `/api/base/status` 的 fresh `T=1001` feedback ACK。当前剩余核心边界是：运动证据主要来自 ROS-side command integration，缺少“运动期间 WAVE ROVER vendor `T=1001` feedback 与 ROS 运动链同轮对齐”的归档。

本轮目标：在真实上位机执行一次低速、短时、可停止的 motion feedback capture，同轮归档：

- WAVE ROVER `T=1001` feedback readback 或 stream；
- `/odom` 非零 command integration；
- dynamic `/tf` 的 `odom -> base_link` 非零 translation；
- `/trashbot/stop` 成功；
- API restore 后 `/api/base/status.feedback_ack.t1001_observed=true`。

本轮不要求证明导航级实测里程计；若 `T=1001.L/R` 非零，可作为 vendor 运动反馈材料；若仍为零，必须如实记录，不能外推物理位移。

## Owner

- 主责：`robot-hardware-engineer`

## 资料来源

- `docs/vendor/VENDOR_INDEX.md`
- `docs/vendor/waveshare_wave_rover/ugv_rpi/base_ctrl.py`
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/json_cmd.h`
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/uart_ctrl.h`
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/ugv_advance.h`

采用的 vendor 事实：WAVE ROVER UART 是 UTF-8 newline-delimited JSON；当前实测底盘口径为 `/dev/ttyS5 @ 115200`；`T=1` 是左右轮 speed control；`T=130` 请求 base feedback；`T=131` 控制 feedback flow；`T=1001` 是 base feedback，字段包含 `L/R/r/p/y/v`。

## 允许改动范围

- `sprints/2026.06.10_01-35_motion-feedback-alignment/tech-done.md`
- `sprints/2026.06.10_01-35_motion-feedback-alignment/artifacts/`

范围外文件不得改动；本轮是纯证据 capture，不写功能代码。

## 验收命令

```bash
ssh root@192.168.1.11 -p 37878 'python3 --version && test -e /dev/ttyS5'
ssh root@192.168.1.11 -p 37878 'curl -sS http://127.0.0.1:8787/api/base/status'
```

真实上位机 capture 要求：

- 先记录 `status_before.json` 和当前占用 `/dev/ttyS5` 的进程。
- 只在需要接管底盘串口时停止 `upper_robot_api.py`；结束必须恢复。
- 启动 `esp32_bridge`，参数至少包含：
  - `serial_port:=/dev/ttyS5`
  - `serial_baudrate:=115200`
  - `command_mode:=speed`
  - `feedback_interval_ms:=100`
  - `publish_odom_tf:=true`
- 执行一次低速短脉冲：建议 `linear.x=0.03`、`sleep <= 0.3s`、零速、`/trashbot/stop`。
- 归档：
  - `artifacts/remote_capture/status_before.json`
  - `artifacts/remote_capture/esp32_bridge.log`
  - `artifacts/remote_capture/pulse_and_stop.log`
  - `artifacts/remote_capture/odom_after_motion.txt`
  - `artifacts/remote_capture/tf_after_motion.txt`
  - `artifacts/remote_capture/battery_once.txt`
  - `artifacts/remote_capture/imu_once.txt`
  - `artifacts/remote_capture/status_after.json`
  - 如可行，归档 raw/vendor `T=1001` 行或从 ROS feedback 推导的 `feedback_motion_summary.json`
- `status_after.json` 必须证明 API 已恢复且 `feedback_ack.t1001_observed=true`；否则定位并至少重试一次。
- `tech-done.md` 必须写清楚：`T=1001.L/R` 在运动窗口是否非零；如果未能证明非零，明确剩余风险。

## 实际改动

- 纯证据归档；未改产品代码、测试代码、launch 参数或硬件配置。
- 新增/更新 `artifacts/remote_capture/`：
  - `status_before.json`
  - `esp32_bridge.log`
  - `pulse_and_stop.log`
  - `odom_after_motion.txt`
  - `tf_after_motion.txt`
  - `battery_once.txt`
  - `imu_once.txt`
  - `status_after.json`
  - `feedback_motion_summary.json`
  - `preflight.log`
  - `upper_robot_api_pids_stopped.txt`
  - `upper_robot_api_restored.log`
  - `upper_robot_api_restored.pid`
  - `status_after_attempt_1.json`
- 远端执行时只在接管 `/dev/ttyS5` 期间停止 `upper_robot_api.py`；最终已停止遗留 `esp32_bridge` 进程，并恢复 `upper_robot_api.py` 为唯一串口 owner。

## 验证结果

已读资料来源：

- `AGENTS.md`
- `OKR.md`
- `docs/vendor/VENDOR_INDEX.md`
- `docs/vendor/waveshare_wave_rover/ugv_rpi/base_ctrl.py`
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/json_cmd.h`
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/uart_ctrl.h`
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/ugv_advance.h`

已证实的 vendor/硬件结论：

- WAVE ROVER UART 采用 UTF-8 newline-delimited JSON；本轮采用 `/dev/ttyS5 @ 115200`。
- `T=1` 是左右轮 speed control；`T=130` 请求 base feedback；`T=131` 控制 feedback flow；`T=142` 设置 feedback interval；`T=143` 设置 UART echo；`T=1001` feedback 字段包含 `L/R/r/p/y/v`。
- 真实上位机 `python3 --version && test -e /dev/ttyS5` 通过，输出 `Python 3.10.12`。
- `status_before.json` 证明 API 运行且 fresh `T=1001` readback 正常：`feedback_ack.t1001_observed=true`、`t1001_feedback_status=observed`、`read_line_count=13`、`parsed_json_count=13`、`invalid_json_count=0`。
- 最终 `status_after.json` 证明 API 已恢复且 fresh `T=1001` readback 正常：`feedback_ack.t1001_observed=true`、`t1001_feedback_status=observed`、`read_line_count=13`、`parsed_json_count=13`、`invalid_json_count=0`。

真实上位机 capture 结果：

- `esp32_bridge.log` 证明 `esp32_bridge` 以要求参数打开底盘串口：`Connected to WAVE ROVER ESP32 on /dev/ttyS5 @ 115200`，并记录 `command_mode=speed; publish_odom_tf=True`。
- 最终 bounded run 使用 inline `rclpy` 等到 `/cmd_vel` subscription count 为 `1` 后执行 `linear.x=0.03` 脉冲；`pulse_and_stop.log` 记录 `nonzero_duration_s=0.260472`，满足 `<= 0.3s`。
- `pulse_and_stop.log` 记录 `/trashbot/stop` 成功：`stop_success=True`、`stop_message=Motors stopped`。
- `battery_once.txt` 和 `imu_once.txt` 均有 topic 样本；`/battery` 电压样本约 `12.41V`，`/imu/data` 有 `imu_link` orientation 样本。
- 最终 bounded run 的 `/odom` 和 dynamic `/tf` 未出现非零 translation：`odom_after_motion.txt` 中 `position.x=0.0`，`tf_after_motion.txt` 中 `translation.x=0.0`。
- `feedback_motion_summary.json` 已归档机器可读结论：最终 bounded run 证明 bridge 启动、feedback topic、safe stop 和 API restore；未证明 bounded-run `/odom`/`/tf` 非零，也未证明 `T=1001.L/R` 在运动窗口非零。

定位与重试记录：

- 第一次 capture 失败原因：远端脚本在 `set -u` 下 source ROS setup，触发 `AMENT_TRACE_SETUP_FILES: unbound variable`，未启动 ROS capture；已修正为 `set +u` 后重试。
- 一次 ROS CLI retry 产生了非零 `/odom` 和 dynamic `/tf`，但 `ros2 topic pub --once` CLI latency 使非零命令窗口约为 3 秒，不满足本 sprint 的 `sleep <= 0.3s` 安全边界，因此只作为诊断事实，不作为 bounded safety 证据。
- direct raw UART retry 用映射后的 `T=1 L/R=0.023077` 低速短脉冲尝试抓 raw `T=1001`，但串口行出现 corrupted/incomplete JSON，未得到有效非零 `T=1001.L/R` 运动窗口样本。
- 最终 bounded discovery-wait run 满足 `<=0.3s` 和 stop/API restore，但 `/odom`/`/tf` 仍为零；这说明当前短脉冲与 ROS-side command integration 的采样/处理时序仍未形成同轮非零证据。

## 剩余风险

- `T=1001.L/R` 在运动窗口是否非零：未证明。最终结论必须保持为 `left_nonzero_proven=false`、`right_nonzero_proven=false`，不得外推物理位移。
- bounded safety 窗口内 `/odom` 和 dynamic `odom -> base_link` TF 非零：未证明。已有一次长 CLI pulse 诊断能触发非零 command integration，但不满足本轮安全窗口。
- `status_after.json` 已证明 API 恢复和 fresh `T=1001` ACK；但 API status 只证明 non-motion `T=130` readback，不等于实测轮速里程计或 HIL pass。
- 下一步建议由 Robot Software/Hardware 联合补一个不扩大运动窗口的测试入口：让 `esp32_bridge` 在 evidence 模式下临时记录 raw `T=1001` 行或发布包含 `L/R` 的诊断 topic，并用同一个 bounded pulse 同时捕获 `/cmd_vel`、raw feedback、`/odom`、`/tf`。
