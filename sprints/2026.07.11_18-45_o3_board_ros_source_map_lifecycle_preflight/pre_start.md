# O3 Board ROS Source Map Lifecycle Preflight

## Sprint Type

sprint_type: epic

## 上轮未完成项

- `sprints/2026.07.11_17-43_o3_managed_runtime_scan_attempt_recovery/` 已把 latest live blocker 前移到 `map_lifecycle_proof_not_clean` 与 `ros2_command_unavailable_after_bash_source`。
- 上轮 live artifact 证明 `managed_runtime_started=true`，但 `map_server_active=false`、`amcl_active=false`、`/scan.probe.boundary=scan_probe_skipped_without_ros2`，BEST_EFFORT / RELIABLE attempt 均未出现。
- 上轮下一条现场命令要求优先验证 board 侧 sourced shell 是否同时具备 `ros2` CLI 与 `rclpy` Python runtime。

## 本轮目标

本轮不继续扩展 `/scan` QoS 合同，也不回到 O5 support-only readiness packet。目标是把板端 sourced shell、Python `rclpy` site-packages、`ros2` CLI 可用性和 `map_server` lifecycle 失败拆成短窗口、只读、可复跑的 preflight artifact。

## Owner

- Implementation owner: `robot-algorithm-engineer`
- Product closeout: `product-okr-owner`
- 主节点职责：拆解、派单、验收、更新 sprint 收口；不直接修改产品代码或运行验收命令。

## 重复 blocker 检查

最近两轮：

- `2026.07.11_16-43_o3_scan_long_window_reliable_probe`：最新 artifact 停在 `partial_runtime_in_progress`，没有形成 canonical 双 QoS attempt。
- `2026.07.11_17-43_o3_managed_runtime_scan_attempt_recovery`：最新 artifact 收口为 `blocked_with_root_cause`，root cause 为 `map_lifecycle_proof_not_clean` 与 `ros2_command_unavailable_after_bash_source`。

判断：不是同一 root cause 连续两轮原地消费；root cause 已从 `/scan` timeout 前移到 board source/lifecycle 层。本轮允许继续，但验收必须证明拆分后的具体 blocker，不能只复述 `ros2_command_unavailable_after_bash_source`。

## 风险边界

- 本轮只读 ROS/source/lifecycle 诊断，不发送 `/cmd_vel`、manual、NavigateToPose、ComputePathToPose 或底盘串口控制。
- 若真实板不可达，只能得到 local fail-closed 和代码/单测证据，不计 OKR 百分比。
- 若只新增 wrapper 字段而没有更清晰的 source/lifecycle 分类，本轮不能视为 mission progress。
