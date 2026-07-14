# PRD - O3 Controlled Route Execution Gate Record

## 用户价值和产品北极星

产品北极星：普通用户最终只需要把垃圾交给小车，小车沿固定路线安全送达垃圾站点，并且每一次路线执行都有可复盘证据链。

本轮用户价值：在 05:02 same-task replay packet 和 06:05 O6/O7 readback 之后，产品不再重复 helper/export/readiness、route-intent、packet packaging 或 readback-only wrapper，而是把同一个 packet 推到真实路线执行前的安全门。`controlled_route_execution_gate_record` 要明确告诉后续 Algorithm 执行者：当前材料是否完整、为什么仍不能控制机器人、下一条 live command gate 需要什么真实准入证据。

本轮不是用户发车功能，不面向普通用户开放控制入口，不声明路线已执行。

## 背景事实

05:02 Product closeout 已接受：

- `packet_id=packet_o3_28_pose_same_task_replay_7d57826142b0c79c`
- `task_id=task_o3_28_pose_fixed_route_consumer_20260713_0402`
- `route_intent_id=route_intent_20260713_0402_from_20260713_0300_28_pose_structured_path`
- `route_csv_row_count=28`
- `replay_jsonl_event_count=28`
- `path_structured_pose_count=28`
- `same_task_identity_verified=true`
- `same_task_replay_packet_ready=true`
- `source_fingerprints.summary_sha256=9948414e1a46b6e78de5503a06d634e24c5e96aff38c1f4c7d756bd20eb0dc93`
- `source_fingerprints.route_csv_sha256=61b4020c93f01e595df4608e8b42545ce1b1d04eaff8798db55b0dda2aae7601`
- `source_fingerprints.replay_jsonl_sha256=530941a7ecb4768f6583cda4abca0d9bc92715ea0266fc96e83d3a860a0400b5`

05:02 和 06:05 均明确拒绝：

- route execution
- fixed-route movement
- NavigateToPose
- controller/BT execution
- `/cmd_vel`
- `/api/base/manual`
- WAVE ROVER UART
- delivery/operator acceptance
- current live HIL
- safe-to-control
- O5 production/external evidence

## OKR 映射和方向判断

- O5：暂停本轮 support-only 推进。O5 约 `85%`，最低但卡在真实 production/external evidence，继续 readiness/checklist/wrapper 不产生外部证据。
- O1：继续保持约 `94%`。本轮只建立 route execution 前 gate，不证明 current live HIL、safe-to-control、Nav2 route execution success、delivery/operator acceptance 或现场验收。
- O3 现场验证 lane：继续。该 lane 不单独计分，但当前最需要把 05:02 packet 连接到受控 route execution 前的 fail-closed gate。
- O6/O7：保持约 `93%`。06:05 已完成 readback-only 增量，本轮不再重复 O6/O7 readback wrapper。
- 方向判断：继续 O3/O1 strict no-motion evidence chain；调整执行抓手为 controlled route execution gate；暂停 O5 support-only wrapper；KR `不归档`；主百分比大概率不调整。

## KR 拆解、更新或历史归档

本轮规划不归档任何 KR。计划拆解如下：

- O3/O1-KR：生成 `controlled_route_execution_gate_record`，证明 same-task packet 可作为受控 route execution 的输入候选。
- O3/O1-KR：校验 identity/count/source hash，避免后续执行消费错误 packet。
- O3/O1-KR：显式输出 next live command gate，列出进入真实路线执行前必须补齐的安全准入。
- O3/O1-KR：固定 fail-closed booleans，防止 gate record 被误读为实跑证据。

已完成 KR 的历史记录位置：本轮没有已完成 KR 可移动到历史区。既有 source evidence 位于：

- `sprints/2026.07.13_05-02_o3_28_pose_same_task_replay_packet/final.md`
- `sprints/2026.07.13_05-02_o3_28_pose_same_task_replay_packet/artifacts/algorithm/same_task_replay_packet_summary.json`
- `sprints/2026.07.13_06-05_o6_o7_same_task_replay_packet_readback/final.md`

剩余风险：05:02 packet 和本轮计划均不是 route execution、delivery、HIL、safe-to-control 或 O5 production/external evidence。

## 本轮核心抓手

核心抓手是同一 packet 的 route execution gate：

```text
05:02 same-task replay packet
  -> identity/count/hash validation
  -> fail-closed controlled_route_execution_gate_record
  -> next_live_command_gate for future controlled route execution
```

不得把这条链包装成 route execution chain。它只回答“能否安全进入下一条 live command gate”，不回答“车是否已经跑完路线”。

## 需要做什么

后续 `robot-algorithm-engineer` 需要：

1. 读取 05:02 `same_task_replay_packet_summary.json`。
2. 校验 `packet_id`、`task_id`、`route_intent_id`。
3. 校验 `route_csv_row_count=28`、`replay_jsonl_event_count=28`、`path_structured_pose_count=28`。
4. 校验 source refs 与 sha256 是否存在、是否和 summary 一致。
5. 生成 machine-readable `controlled_route_execution_gate_record`，包含 gate status、blocking reasons、next live command gate、accepted input facts 和 rejected claims。
6. 固定 safety fields：`route_execution_success=false`、`delivery_success=false`、`hil_pass=false`、`safe_to_control=false`、`robot_control_executed=false`。
7. 补充 targeted tests 或 structured assertions，覆盖 identity/count/hash/no-motion guard。
8. 更新本 sprint `tech-done.md`，记录实际改动、验证结果、失败定位和剩余风险。

## 非目标

- 不执行 Nav2 route。
- 不调用 NavigateToPose。
- 不发送 no /cmd_vel 以外的任何控制路径；本轮要求 no /cmd_vel。
- 不调用 no /api/base/manual 以外的人工底盘控制路径；本轮要求 no /api/base/manual。
- 不使用 WAVE ROVER UART。
- 不声明 route execution success。
- 不声明 delivery success。
- 不声明 HIL pass。
- 不声明 safe-to-control。
- 不接真实 production cloud、DB、queue、OSS/CDN 或公网 HTTPS/TLS。
- 不做 O6/O7 readback-only wrapper。
- 不生成新的 route intent 或 packet packaging 来替代 05:02 packet。

## 优先级和验收口径

优先级：P0 for O3/O1 route execution gate readiness.

验收必须同时满足：

- Artifact: 存在机器可读 `controlled_route_execution_gate_record`。
- Identity: `packet_id=packet_o3_28_pose_same_task_replay_7d57826142b0c79c`、`task_id=task_o3_28_pose_fixed_route_consumer_20260713_0402`、`route_intent_id=route_intent_20260713_0402_from_20260713_0300_28_pose_structured_path` 完全一致。
- Counts: `route_csv_row_count=28`、`replay_jsonl_event_count=28`、`path_structured_pose_count=28` 完全一致。
- Hash: summary、route CSV、replay JSONL source hash 有结构化读回或断言。
- Safety: `route_execution_success=false`、`delivery_success=false`、`hil_pass=false`、`safe_to_control=false`、`robot_control_executed=false`。
- Control guard: record 或 test 明确 no /cmd_vel、no /api/base/manual、no NavigateToPose、no WAVE ROVER UART。
- Next gate: record 列出真实执行缺口和 next live command gate。
- Product boundary: final 只能接受为 fail-closed dry-run execution readiness record，不接受为真实路线执行、送达、HIL 或 safe-to-control。

## 对应责任 Engineer

- 主责：`robot-algorithm-engineer`
- 不需要：`full-stack-software-engineer`，除非后续要把 gate record 读入 O6/O7。
- 不需要：`robot-software-engineer`，除非后续要接 ROS2 route execution runtime。
- 不需要：`rober-hardware-engineer`，除非后续真实硬件准入、WAVE ROVER、UART 或 HIL 事实需要确认。

## 风险、阻塞和需要补齐的证据链

- 风险：gate record 被误解成 route execution readiness complete；必须命名为 fail-closed gate / dry-run execution readiness record。
- 风险：后续 implementation 若复用 execution 字段，可能误把 route packet ready 当成 route execution success；必须固定 `route_execution_success=false`。
- 风险：当前没有明确真实硬件准入；任何 control path 都必须保持禁用。
- 阻塞：缺 current live HIL、safe-to-control、真实 route execution、delivery/operator acceptance、O5 production/external evidence。
- 需要补齐的证据链：真实 safety gate approval、bounded route execution command evidence、Nav2/controller result、operator/delivery acceptance、current live HIL、生产外部证据。

## 已完成 KR 的历史记录位置、证据来源和剩余风险

本轮规划阶段没有完成或归档 KR。已有 source evidence 继续保留在 05:02 和 06:05 sprint closeout 中。本轮完成后，若 Algorithm 交付并通过验收，应在本 sprint `final.md` 记录：

- gate record artifact path
- source packet identity
- identity/count/hash verification
- fixed false safety fields
- next live command gate
- OKR 不调整或调整理由
- KR 不归档或归档理由

剩余风险预期保持：本轮即使实现通过，也只是 `software_proof_o3_o1_fail_closed_controlled_route_execution_gate_record_only`，不是 current live route execution、delivery、HIL、safe-to-control 或 production/external evidence。

## 需要创建或更新的 sprint 文档

本阶段创建：

- `pre_start.md`
- `prd.md`
- `tech-plan.md`

后续实现完成后必须补：

- `tech-done.md`
- `side2side_check.md`
- `final.md`
