# O1 Same-Session HIL Acceptance Bundle Pre-Start

## sprint_type

sprint_type: epic

## 背景

本轮自动化先读 `AGENTS.md`、`OKR.md`、最近 sprint `final.md`、automation memory 和 `docs/vendor/VENDOR_INDEX.md`。当前最低 Objective 是 O5 约 85%，但最近 `cloud_production_cutover_readiness_packet` 已固定 `okr_credit_allowed=false`，当前环境没有真实公网 HTTPS/TLS、4G/SIM、production DB/queue、worker cutover、OSS/CDN live traffic 或真实 phone/browser 证据；继续做 local/mock readiness/readback 只能 support-only，不能计主 OKR 增量。

O1 约 92%，仍缺 current live HIL pass、wheel direction、IMU/battery calibration、same-run path generation success、Nav2 route execution success、external video、LiDAR motion delta 与 HIL acceptance record。最近 O1 已消费 bounded motion 和 manual HIL gate 材料，但 composite bundle 尚未把 `2026.06.22_11-00_wheel_lr_samesession_first_jog` 的同会话 L/R 非零轮速材料与 manual gate / motion-map bundle 放在同一个 acceptance 视图里。

## 本轮目标

在不宣称真实 current live HIL 的前提下，新增 O1 same-session HIL acceptance additive material：把历史真实上位机同会话 L/R 非零反馈材料安全接入 `trashbot.wave_rover_motion_map_hil_material_bundle.v1`，并输出 fail-closed acceptance gap summary。

## Owner

- 主责：`robot-hardware-engineer`
- 协作：Product closeout 由主节点在验收后汇总，不单独派发，避免共享 sprint 文档并发冲突。

## 文件范围

Hardware owner 允许改动：

- `onboard/src/ros2_trashbot_hardware/ros2_trashbot_hardware/wave_rover_motion_map_hil_material_bundle.py`
- `onboard/src/ros2_trashbot_hardware/test/test_wave_rover_motion_map_hil_material_bundle.py`
- `docs/hardware/wave_rover_motion_map_hil_material_bundle.md`
- `sprints/2026.07.11_01-33_o1_same_session_hil_acceptance_bundle/tech-done.md`
- `sprints/2026.07.11_01-33_o1_same_session_hil_acceptance_bundle/artifacts/hardware_worker_report.md`

不得改动本轮范围外代码，不得覆盖 `2026.07.11_00-34_o6_o7_pc_live_nav2_execution_material` 的未提交改动。

## blocker 核对

最近 O5 blocker 是缺真实 external production evidence，本轮不继续消费。最近 O1 blocker 是缺 current live HIL/material；本轮不是重复宣称 HIL pass，而是把已经存在但未进入 composite bundle 的 same-session wheel feedback material 接入 HIL acceptance gap view，并保持 OKR 计分保守。

## 验收口径

- 新 additive fields 能证明 same-session wheel feedback material 被安全 intake。
- 顶层 `hil_pass=false`、`safe_to_control=false`、`delivery_success=false`、`primary_actions_enabled=false`、`nav2_route_execution_success=false` 保持不变。
- 不回显 raw endpoint、`/dev/tty*`、baudrate、token、URL、traceback 或 raw frames。
- 如果输入把 HIL/safety/delivery/route success 危险字段升为 true，必须 fail-closed。
- 本轮若没有新 current live artifact，O1 进度不因为合同接线重复上调。
