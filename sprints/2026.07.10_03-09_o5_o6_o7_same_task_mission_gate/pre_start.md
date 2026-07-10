# O5/O6/O7 Same Task Mission Gate Pre-start

## Sprint 类型

sprint_type: epic

启动时间：2026-07-10 03:09 CST。

## 最近两轮核对

- `sprints/2026.07.10_01-07_o6_o7_route_delivery_closure_packet/final.md`：完成，未 blocked，但明确要求下一轮转向 production cloud、真实或准现场 live route execution、delivery record/operator confirmation，而不是继续 summary wrapper。
- `sprints/2026.07.10_02-06_o5_o6_cloud_terminal_result_delivery_bridge/final.md`：完成，未 blocked，但最终建议禁止继续做只读 wrapper、decoder、handoff、review surface，下一轮应消费真实或准现场 same-task terminal result + live route execution / production cloud evidence。

本轮不连续消费同一 blocker。真实 production cloud、真实 4G/TLS、真实 live Nav2 与真实 delivery success 仍缺外部条件，因此本轮选择软件可验证的同 task mission gate：只在 O5 cloud terminal result、Nav2 execution evidence、route bag/live pose progress、delivery/operator readiness 属于同一 `task_id` 且来源安全时给出 ready-not-success-proof，否则 fail closed。

## 目标 Objective

- 最低活跃 Objective：O5 与 O7 约 81%，O6 约 82%。
- 本轮覆盖：O5/O6/O7。
- 选择理由：O5/O7 同为最低进度；上一轮已把 O5 terminal result 桥到 O6 delivery evidence，但尚未把同一 `task_id` 的 terminal result 与 route execution materials 做严格 gate。本轮可以在本地/mock 环境消费现有准现场材料和 fixture，把下一轮真实同 task 材料的验收入口落成可测试合同。

## Owner

- `robot-algorithm-engineer`：生成 `same_task_mission_evidence_gate`，只读消费 linked mission artifacts。
- `robot-software-engineer`：O6 archive/readback/include 接住该 gate，保持安全字段 false。
- `full-stack-software-engineer`：O7 consumer detail 与 workstation 展示该 gate 的状态、缺口和 next evidence。
- `product-okr-owner`：工程完成后更新 `tech-done.md`、`side2side_check.md`、`final.md`、`OKR.md` 与 `docs/process/okr_progress_log.md`。

## 验收口径

- Algorithm 产物必须证明：同 task gate 只在 cloud terminal source、Nav2 evidence、route execution readiness、pose progress 与 operator confirmation 全部匹配时 ready；task mismatch、unsafe refs、dangerous true、缺任一材料均 blocked。
- O6 产物必须证明：field evidence、artifact bundle、archive detail、consumer detail、`include=same_task_mission_evidence_gate` 均能安全回读，不泄露路径/token/raw/base64，不打开控制字段。
- O7 产物必须证明：consumer detail 能展示该 gate，artifact bundle readiness 能把 gate 状态纳入缺口判断，并继续显示 not delivery success。

## 证据边界

本轮证据边界预计为 `software_proof_same_task_mission_evidence_gate_only`。即使所有测试通过，也不证明真实 production cloud、真实 HTTPS/TLS/4G、production DB/queue、OSS/CDN live traffic、真实 live Nav2 route execution、真实机器人运动、真实 delivery record、真实 operator confirmation 或真实 delivery success。
