# Robot Hardware Engineer Owner Note

## sprint_type

sprint_type: epic

## 已读 vendor 来源

- `AGENTS.md`
- `docs/vendor/VENDOR_INDEX.md`
- `docs/vendor/waveshare_wave_rover/ugv_rpi/base_ctrl.py`
- `docs/vendor/waveshare_wave_rover/ugv_rpi/config.yaml`
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/json_cmd.h`
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/uart_ctrl.h`
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/ugv_advance.h`
- `docs/vendor/lidar_pkg_ros2-main/src/lidar_node.cpp`
- `docs/vendor/lidar_pkg_ros2-main/config/lidar_params.yaml`
- `docs/vendor/lidar_pkg_ros2-main/scripts/99-lidar.rules`

## 已证实的硬件结论

- WAVE ROVER vendor 上位机链路是 UART、UTF-8 JSON、newline-delimited frame；vendor Raspberry Pi reference 是 `/dev/ttyAMA0 @115200`，本项目 Orange Pi 底盘口按现场材料使用 `/dev/ttyS5 @115200`，不能把 `/dev/ttyACM0` 当成底盘口。
- `T=1` 是左右轮速度命令，`T=13` 是 ROS velocity 命令；这两个都是运动控制材料，本轮未发送。
- `T=130` 是 vendor base feedback request，`T=131` 是 feedback-flow 状态命令；LiDAR scan proof refresh/readback 不得发送二者。
- `T=1001` 是 vendor `baseInfoFeedback()` 输出，只能作为 feedback material；即使观察到 3/3 samples，也不能写成 robot ACK、HIL pass、`safe_to_control=true`、真实 `/odom`、`/imu/data` 或 `/battery`。
- LiDAR vendor ROS2 资料使用 `/dev/lidar` 或现场 `/dev/ttyACM0 @150000`，packet sync 为 `0xAA 0x55`；LiDAR proof 不得触碰 WAVE ROVER `/dev/ttyS5`。

## SSH 只读边界检查

执行方式：通过 `ssh root@192.168.1.11 -p 37878` 只运行 Python HTTP GET readback，读取 `/health`、`/api/status`、`/api/radar/status`、`/api/radar/scan-proof/latest`、`/api/base/status`、`/api/base/feedback-samples/latest`。本轮没有调用 `/api/base/manual`、`/api/base/feedback-request`、`/api/base/feedback-samples`，没有发送 `T=1/T=13/T=130/T=131`，没有发布 `/cmd_vel`。

关键 readback 结果：

- `/api/radar/scan-proof/latest` HTTP 200，artifact loaded，`evidence_boundary=lidar_scan_proof_artifact_not_base_hil`，latest artifact 内 `sends_commands=false`、`sends_motion_commands=false`、`safe_to_control=false`、`hil_pass=false`、`robot_control_executed=false`、`delivery_success=false`。blocked list 明确包含 `T=1`、`T=13`、`T=130`、`T=131`、`cmd_vel` 和 `A5 60`。
- `/api/status` 和 `/api/radar/status` 的 radar 摘要保持 `sends_commands=false`、`safe_to_control=false`，`scan_status=not_proven`；latest proof 是历史 artifact readback，不是本轮 fresh HTTP refresh 证据。
- `/api/base/feedback-samples/latest` HTTP 200，readback 顶层保持 `readback_sends_commands=false`、`sends_commands=false`、`sends_motion_commands=false`、`safe_to_control=false`、`hil_pass=false`。latest result 内 `t1001_observed_count=3`、`all_samples_observed_t1001=true`，其 `sends_commands=true` 只描述历史 samples collection 曾发送 vendor `T=130`。
- `/api/base/status.feedback_samples_latest` 读到同一 artifact，但 `freshness.status=stale`、`age_ms=6617219`、`stale_after_ms=900000`。这不是和 3/3 `T=1001` 冲突；它只说明历史 feedback material 已过新鲜度窗口。

## 修正建议

- Product/OKR 收口时把当前材料分为 `lidar_scan_proof_latest_readback`、`vendor_feedback_material_stale` 和 `software_guard`，不要写成 `robot_runtime_material` 或 HIL。
- Robot Software 若新增 `POST /api/radar/scan-proof/refresh`，必须保证只运行 `o1_lidar_scan_proof_collector.py --expect-existing-topics` 这一类 read-only topic/TF collector，并固定返回 `sends_commands=false`、`sends_motion_commands=false`、`safe_to_control=false`、`hil_pass=false`。
- Full-Stack 展示 stale/fresh 时应把 `T=1001 observed` 和 `freshness.status=stale` 并列展示为两个维度：历史 feedback material 存在，但当前不可作为 fresh ACK/HIL。

## 剩余风险

- 当前本地 `onboard/scripts/upper_robot_api.py` 读码未看到 `POST /api/radar/scan-proof/refresh` route；如果 Robot Software 并行新增该 route，最终验收必须重新核对 route payload，不得只引用本 note 的 latest readback。
- 远端 readback 证明的是 HTTP GET/status/artifact 边界；没有执行真实底盘 pulse，没有打开 `/dev/ttyS5`，没有新的 `T=130` 采样，没有 HIL。
- `safe_to_control`、HIL、robot ACK、ROS `/odom`、`/imu/data`、`/battery`、Nav2/SLAM 消费和 delivery success 全部仍未证明。
