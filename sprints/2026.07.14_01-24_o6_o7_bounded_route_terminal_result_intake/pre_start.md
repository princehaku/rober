# Pre Start - O6/O7 Bounded Route Terminal Result Intake

## Sprint Metadata

- sprint_type: epic
- Sprint: `sprints/2026.07.14_01-24_o6_o7_bounded_route_terminal_result_intake/`
- Start time: 2026-07-14 01:24 CST
- Product owner: `product-okr-owner`
- Implementation owners: `robot-software-engineer`, `full-stack-software-engineer`
- Planned proof boundary: `software_proof_o6_o7_bounded_route_terminal_result_intake_only`

## 上轮状态

最近收口：

- `sprints/2026.07.14_00-24_o5_bounded_route_terminal_result_bridge/` 已把 O3 bounded route mock execution summary 写入 O5 local/mock command/result/reconciliation 主路径。
- 接受 artifact：`sprints/2026.07.14_00-24_o5_bounded_route_terminal_result_bridge/artifacts/o5_bounded_route_terminal_result_bridge_summary.json`
- 关键身份保持：`task_id=task_o3_28_pose_fixed_route_consumer_20260713_0402`、`packet_id=packet_o3_28_pose_same_task_replay_7d57826142b0c79c`、`route_intent_id=route_intent_20260713_0402_from_20260713_0300_28_pose_structured_path`
- 上轮仍是 local/mock 软件证明，`delivery_success=false`、`route_execution_success=false`、`safe_to_control=false`、`hil_pass=false`、`robot_control_executed=false`。

## 本轮目标

把 00:24 O5 bounded route terminal result bridge 作为新的 same-task mission material，接入：

1. O6 archive / field-evidence / consumer detail 的安全 readback section。
2. O7 selected-task intake endpoint、receipt 和 PC 只读展示。

目标是形成可复验的 O6/O7 local/mock terminal-result intake/readback 闭环，不声明真实 route execution、delivery、HIL、safe-to-control 或 production cloud。

## Blocker 与切换理由

当前 `OKR.md` 最低 Objective 是 O5，约 `85%`。O5 仍缺真实公网 HTTPS/TLS success-class、production DB/queue、worker cutover、OSS/CDN live traffic、4G/SIM 或 real phone/browser production evidence。

最近 O5 sprint 已连续落在 support-only local tooling / terminal bridge：

- `2026.07.13_22-20_o5_cloud_external_review_decision`
- `2026.07.14_00-24_o5_bounded_route_terminal_result_bridge`

本轮不继续做 O5 本地包装，避免重复消费“无真实 production/external evidence”的同根 blocker。改为转向次低 O6/O7，消费一个新产生的 same-task terminal result material。

## Owner

- `robot-software-engineer`：O6 archive/readback 事实源。
- `full-stack-software-engineer`：O7 selected-task intake/receipt/UI/API。

两个 owner 文件范围互不重叠，implementation 阶段并行派发。主节点只负责拆解、派单、验收和 sprint closeout。

## 验收口径

必须满足：

- O6 新增 terminal-result material section，schema 固定为 `trashbot.o6.bounded_route_terminal_result_material.v1`。
- O7 新增 endpoint `POST /api/o7/consumer-read/tasks/:taskId/bounded-route-terminal-result/intake?baseUrl=<local-loopback-url>`。
- O7 receipt schema 固定为 `trashbot.pc_tools_workstation.o7_bounded_route_terminal_result_intake_result.v1`。
- 只接受同一 `task_id`、同一 `packet_id`、同一 `route_intent_id` 和 00:24 O5 source schema。
- 固定 false fields 不得变成 true。

不得声明：

- route execution success
- delivery success
- operator acceptance
- current live HIL
- safe-to-control
- robot control execution
- production cloud / production DB / worker cutover / OSS-CDN / 4G-SIM
