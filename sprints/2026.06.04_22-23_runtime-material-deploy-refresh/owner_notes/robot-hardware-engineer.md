# Hardware Infra Engineer Owner Note

## sprint_type

sprint_type: epic owner note for `2026.06.04_22-23_runtime-material-deploy-refresh`.

## 已读本地资料

- `AGENTS.md`
- `OKR.md`
- `docs/vendor/VENDOR_INDEX.md`
- `docs/vendor/waveshare_wave_rover/ugv_rpi/base_ctrl.py`
- `docs/vendor/waveshare_wave_rover/ugv_rpi/config.yaml`
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/json_cmd.h`
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/uart_ctrl.h`
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/movtion_module.h`
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/ugv_advance.h`
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/IMU_ctrl.h`
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/battery_ctrl.h`
- `docs/vendor/lidar_pkg_ros2-main/README.md`
- `docs/vendor/lidar_pkg_ros2-main/src/lidar_node.cpp`
- `docs/vendor/lidar_pkg_ros2-main/config/lidar_params.yaml`
- `sprints/2026.06.04_22-23_runtime-material-deploy-refresh/tech-plan.md`
- `sprints/2026.06.04_22-23_runtime-material-deploy-refresh/tech-done.md`
- `sprints/2026.06.04_22-23_runtime-material-deploy-refresh/final.md`
- `sprints/2026.06.04_22-23_runtime-material-deploy-refresh/owner_notes/robot-software-engineer.md`
- `sprints/2026.06.04_22-23_runtime-material-deploy-refresh/owner_notes/full-stack-software-engineer.md`
- `onboard/scripts/upper_robot_api.py`
- `onboard/scripts/o1_lidar_scan_proof_collector.py`
- `docs/interfaces/lidar_ros2_closed_loop.md`
- `docs/hardware/o1_wave_rover_serial_feedback_probe.md`
- `docs/hardware/o1_pc_manual_lidar_hil_boundary.md`

## Vendor 硬件结论

- WAVE ROVER vendor 链路是 UART newline-delimited JSON；`base_ctrl.py` 的 `process_commands()` 写入 `json.dumps(data) + "\n"`。
- `json_cmd.h` 定义 `CMD_SPEED_CTRL=1`、`CMD_ROS_CTRL=13`、`CMD_BASE_FEEDBACK=130`、`CMD_BASE_FEEDBACK_FLOW=131` 和 `FEEDBACK_BASE_INFO=1001`。
- `uart_ctrl.h` 中 `T=1` 会调用 `setGoalSpeed()`，`T=13` 会调用 `rosCtrl()`，二者都进入底盘运动路径。
- `uart_ctrl.h` 中 `T=130` 只调用 `baseInfoFeedback()`；`ugv_advance.h` 中 `baseInfoFeedback()` 输出 `T=1001` 及 `L/R/r/p/y/v` 等 vendor feedback 字段。
- `T=1001` 只能作为 vendor feedback material，不能单独写成 robot ACK、HIL pass、真实 `/odom`、`/imu/data`、`/battery`，也不能把 `safe_to_control` 转为 true。
- 当前 ROS2/STC LiDAR vendor 来源是 `docs/vendor/lidar_pkg_ros2-main/`；`src/lidar_node.cpp` 使用 `150000` baud、`A5 60` 启动 LiDAR、解析 `0xAA 0x55` packet 并发布 `/scan`。该链路不是 WAVE ROVER 底盘 UART。

## 本轮只读复核动作

- 只读查看本地代码、文档和 sprint owner notes。
- 只读调用 live upper：
  - `curl -sS http://192.168.1.11:8787/api/status`
  - `curl -sS http://192.168.1.11:8787/api/base/status`
- 未 SSH 执行运动命令。
- 未调用 `POST /api/base/manual`。
- 未发布 `/cmd_vel`。
- 未打开或写入 `/dev/ttyS5`。
- 未发送 WAVE ROVER `T=1`、`T=13`、`T=130`、`T=131`。
- 未执行低速 pulse、turn smoke、急停演练或任何 HIL。

## scan-proof refresh 安全边界

- `onboard/scripts/upper_robot_api.py` 的 `/api/radar/scan-proof/refresh` 回包构造固定标注：
  - `mode=read_only_expect_existing_topics`
  - `starts_driver=false`
  - `opens_lidar_serial=false`
  - `sends_lidar_start_command=false`
  - `blocked_devices_not_opened=["/dev/ttyS5","/dev/ttyACM0","/dev/lidar"]`
  - `blocked_commands_not_sent=["A5 60","T=1","T=13","T=130","T=131","/cmd_vel","/api/base/manual"]`
  - `safe_to_control=false`
  - `robot_control_executed=false`
  - `hil_pass=false`
- `onboard/scripts/o1_lidar_scan_proof_collector.py` 固定声明并实现只读 topic proof：不启动 LiDAR driver、不打开 LiDAR 串口、不读取或写入 WAVE ROVER `/dev/ttyS5`、不发送 `T=1/T=13/T=130/T=131`、不发布 `/cmd_vel`。
- Robot Software owner note 记录 live `POST /api/radar/scan-proof/refresh` 已从 HTTP 405 变为 HTTP 200，但 proof 仍是 `blocked_or_not_observed`，blockers 为 `ros2_command_unavailable` 和 `upper_api_scan_not_proven`。

## live GET 复核结果

- `GET /api/status` 返回 HTTP payload 中：
  - top-level `safe_to_control=false`
  - top-level `robot_control_executed=false`
  - radar `scan_status=not_proven`
  - radar scan proof latest `latest_proof_status=blocked_or_not_observed`
  - radar scan proof latest `readback_sends_commands=false`
  - radar scan proof latest `sends_motion_commands=false`
  - radar scan proof latest `robot_control_executed=false`
  - radar scan proof latest `hil_pass=false`
  - radar scan proof latest `safe_to_control=false`
  - base `port=/dev/ttyS5`
  - base `baudrate=115200`
  - base `sends_commands=false`
  - base `safe_to_control=false`
  - base `robot_control_executed=false`
- `GET /api/base/status` 返回 HTTP payload 中：
  - `port=/dev/ttyS5`
  - `baudrate=115200`
  - `sends_commands=false`
  - `safe_to_control=false`
  - `robot_control_executed=false`
  - `feedback_samples_latest.readback_sends_commands=false`
  - `feedback_samples_latest.sends_motion_commands=false`
  - `feedback_samples_latest.hil_pass=false`
  - `feedback_samples_latest.safe_to_control=false`
  - `feedback_samples_latest` 当前只是 stale artifact readback，不能转成 HIL 或 robot ACK。

## 复核结论

- 本轮 `scan-proof refresh` 只证明 8787 route 部署状态和只读 collector blocker readback；它不证明 fresh `/scan`、SLAM、Nav2、底盘可控或 HIL。
- 基于本地实现、Robot Software owner note 和 live GET status，本轮没有证据显示触碰 `/dev/ttyS5`、`/cmd_vel`、WAVE ROVER JSON 运动命令、`/api/base/manual` 或 HIL。
- 本轮安全结论保持：
  - `safe_to_control=false`
  - `robot_control_executed=false`
  - `hil_pass=false`
  - `field_hil_material=false`
- 不允许把 stale `T=1001` samples、radar latest artifact 或 HTTP 200 route readback 写成 robot ACK、HIL pass 或 O1/O7 可运动完成。

## 验证命令

已运行：

```bash
git diff --check -- docs/hardware/o1_wave_rover_serial_feedback_probe.md docs/hardware/o1_pc_manual_lidar_hil_boundary.md docs/interfaces/lidar_ros2_closed_loop.md sprints/2026.06.04_22-23_runtime-material-deploy-refresh/owner_notes/robot-hardware-engineer.md
```

结果：通过，无输出。

## 剩余风险和下一步

- 上位机 ROS2 runtime/collector command path 仍未修复；当前 blocker 仍是 `ros2_command_unavailable` / `upper_api_scan_not_proven`。
- 未证明 fresh `/scan` once/hz、`/lidar/raw_packet`、TF、SLAM `/map`、AMCL、Nav2 消费或固定路线。
- 未证明 PC WASD、底盘 HIL、急停演练、robot ACK、真实 `/odom`、`/imu/data`、`/battery` 或 `safe_to_control=true`。
- 任何进入 `POST /api/base/manual`、低速 pulse、turn smoke 或 stop-first HIL 的动作，都需要 CEO/现场明确授权、操作员看护、物理净空、急停可用、同一 evidence ref 和执行后现场记录。
