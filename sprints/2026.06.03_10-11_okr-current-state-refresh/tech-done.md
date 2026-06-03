# OKR Current State Refresh Tech Done

## Sprint Type

sprint_type: micro

## Actual Changes

- 更新 `OKR.md` 当前状态：
  - O1 从约 93% 调整为约 94%，新增口径 `LiDAR ttyACM0 ROS2 contract ready + remote 8787 unified status live`。
  - O7 从约 98% 调整为约 98.5%，新增口径 `PC Live Operator consuming unified upper API live status`。
  - 4.1 当前 OKR 快照和第 5 节最高优先级同步改成两条后续主线：LiDAR `/scan` 验收线、底盘 `T=1001/ACK` 验收线。
- 更新 `docs/process/okr_progress_log.md`，新增本轮 Product/OKR closeout，记录为什么只小幅上调 O1/O7，以及哪些证据仍不能算 HIL 或真实控制。

## Verification

- 只读核对当前上位机与 PC 状态：
  - `curl http://192.168.1.11:8787/api/radar/status` 已返回 `observed_lidar_port=/dev/ttyACM0`、`baudrate=150000`、`start_command_hex=a5 60`、`scan_status=not_proven`。
  - `curl http://127.0.0.1:5173/api/o7/live-operator-panel` 已返回 `workstation_api_8787_status=ready`、`lidar_radar.dev_lidar=/dev/ttyACM0`、`camera.health_status=ready`、`control.base_boundary.observed_write_device=/dev/ttyS5`。
- 文档检查：
  - `rg` 已确认 `OKR.md` 当前快照包含 O1 `约 94%`、O7 `约 98.5%`、`LiDAR ttyACM0`、`remote 8787 unified status live`。
  - `git diff --check -- OKR.md docs/process/okr_progress_log.md sprints/2026.06.03_10-11_okr-current-state-refresh/tech-done.md` 通过，无 whitespace error。

## Remaining Risks

- 本轮是 OKR 和进度口径调整，不新增代码能力。
- 真实 ROS2 `/scan`、TF/SLAM/Nav2、`T=1001`、robot ACK、HIL、真实 `/odom`、`/imu/data`、`/battery` 和完整上车任务仍为 `not_proven`。
- O1 仍是最低 Objective；下一轮不能继续只写状态展示，应推进 LiDAR `/scan` 或底盘 ACK/HIL 的真实证据。
