# Pre Start - O3 Bounded Route Command Plan

## Sprint Metadata

- sprint_type: epic
- Sprint: `sprints/2026.07.13_08-09_o3_bounded_route_command_plan/`
- Start time: 2026-07-13 08:09 CST
- Product owner: `product-okr-owner`
- Implementation owner: `robot-algorithm-engineer`
- Execution model: single owner closed loop
- Proof boundary: `software_proof_o3_o1_no_motion_bounded_route_command_plan_only`

## 上轮未完成项和本轮切入

上一轮 `sprints/2026.07.13_07-07_o3_controlled_route_execution_gate_record/` 已接受为 O3/O1 fail-closed controlled route execution gate record。它证明同一 28-pose packet 的 identity、counts 和 source hashes 可复核，但 `next_live_command_gate` 仍阻塞在：

- explicit safety operator approval or equivalent recorded safety gate
- current live HIL / stop path / controlled environment material
- bounded route execution command plan with abort criteria
- LiDAR/localization/TF readiness in the same live window
- Nav2/controller execution result, not only planner path proof
- delivery/operator acceptance evidence

本轮只推进当前环境可完成、且不重复上一轮 packet/gate 包装的缺口：生成同一 `packet_id` / `route_intent_id` 的 bounded route command plan with abort criteria。该计划必须是 strict no-motion artifact，不发车、不调用控制 API、不宣称 route execution。

## 当前最低 OKR 和切换原因

当前 `OKR.md` 数字完成度最低的 Objective 是 O5，约 `85%`。本轮不继续 O5，因为 O5 主要缺真实公网 HTTPS/TLS、4G/SIM、production DB/queue、production worker/cutover、OSS/CDN live traffic、真实手机/browser 和 external production evidence；继续 readiness、checklist、handoff 或 support-only wrapper 会重复消费同一 external-evidence blocker。

O6/O7 约 `93%`，06:05 已完成 same-task replay packet readback-only increment；继续做 O6/O7 readback-only wrapper 也会重复消费 readback 边界。

因此本轮转向 O3/O1 现场验证链路中的可推进前置项，并保持 O3 strict no-motion 红线：no `/cmd_vel`、no `/api/base/manual`、no NavigateToPose、no WAVE ROVER UART。

## Owner 和边界

- `robot-algorithm-engineer`：实现 bounded command plan 生成器、离线单测、生成 algorithm artifact、更新 navigation 文档和 `tech-done.md`。
- 主节点：只负责计划、派单、验收、`side2side_check.md`、`final.md` 和最终汇总。

## 阻塞和风险

- 缺真实 operator approval、current live HIL、stop path、同窗口 LiDAR/localization/TF 和 Nav2/controller execution result。
- 本轮不得把 bounded command plan 解读为实际 route execution、fixed-route movement、delivery、HIL、safe-to-control 或 O5 production/external evidence。
- 若 source gate record 或 source packet identity/hash/count 漂移，必须 fail closed，不能重写 source artifact 来制造通过。
