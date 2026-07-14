# Side-to-Side Check - O3 TF Receipt-Time Freshness Recovery

## Sprint Metadata

- `sprint_type: epic`
- Sprint：`sprints/2026.07.15_05-55_o3_tf_receipt_time_freshness_recovery/`
- Product status：`accepted_offline_contract_repair_rejected_live_mission_credit`
- Proof boundary：`software_proof_o3_tf_receipt_time_freshness_contract_only`
- Delivery owner：`robot-algorithm-engineer`

## 对照结论

Product 接受本轮离线 TF receipt-time freshness 合同修复。helper 已为 TF transform 保留 receipt time，
artifact 合同同时表达 header、receipt/evaluation time 与 `header_age_at_receipt_ms`、
`receipt_age_at_evaluation_ms`、`header_age_at_evaluation_ms`。current observation 的 decision basis 是
callback receipt 时刻计算的 header age，即 `header_age_at_receipt_ms`，不是简单“receipt age”；后两项
继续诊断 collector evaluation delay 与最终 header age。missing/invalid receipt 保持 fail-closed，固定
threshold 仍为 `3000ms`。

Product 拒绝把该结果解释为 live localization、Mission 或 OKR credit。只读 SSH `date` + `ps` 预检显示
localization runtime inactive，因此本轮没有部署、没有 live capture、没有写 topic、没有启停 runtime，
也没有 control、route、delivery 或 HIL 行为。

## PRD / 实现 / 验收对照

| 验收项 | 结果 | Product 判断 |
| --- | --- | --- |
| TF transform 记录 `received_at_ms` | 离线结构与回归通过 | 接受合同实现 |
| header 与 receipt/evaluation time 同时保留 | 离线结构断言通过 | 接受 |
| 三项 actual age 字段同时保留 | 离线结构断言通过 | 接受 |
| decision 使用 `header_age_at_receipt_ms` | targeted regression 通过 | 接受 |
| missing/invalid receipt fail-closed | targeted regression 通过 | 接受 |
| threshold 维持 `3000ms` | required `rg` / regression 通过 | 接受 |
| Python compile | exit `0` | 接受 |
| Helper unittest | `Ran 160 tests in 2.244s`，`OK` | 接受 |
| offline structural / required `rg` / scoped diff | 全部通过 | 接受 |
| 最多一次 live receipt capture | runtime inactive，未执行 | 拒绝 live claim，保留下一步 |
| Mission / OKR credit | 无 live artifact | `okr_credit=false`，KR `不归档` |

## Delta 与证据边界

- `current_run_artifact_delta=false`
- `external_artifact_delta=false`
- `live_control_delta=false`
- `user_action_delta=false`
- `mission_objective_0_satisfied=false`
- `okr_credit=false`
- KR：`不归档`

本轮离线代码、测试和文档改动属于合同修复证据，不构成这里用于 Mission Objective 0 的 current live
artifact delta。Proof boundary 固定为 `software_proof_o3_tf_receipt_time_freshness_contract_only`。

## OKR / KR 判断

- 方向：继续保持 O5 no-repeat；O5 production/public-cloud 外部证据 blocker 未解除，不回到 wrapper。
- O5 约 `85%`、O6/O7 各约 `93%`、O1 约 `94%`，全部保持。
- 本轮不提升任何 Objective 主百分比，不归档任何 KR。
- 已完成 KR 历史记录：本轮没有满足归档条件的 KR，因此没有新增历史记录；证据留在本 sprint
  `tech-done.md`、本文件、`final.md` 与 Product acceptance JSON。

## Safety Acceptance

- `safe_to_control=false`
- `robot_control_executed=false`
- `route_execution_success=false`
- `delivery_success=false`
- `hil_pass=false`
- `publishes_cmd_vel=false`
- `calls_base_manual=false`
- `uses_base_uart=false`
- `initialpose_published=false`
- `runtime_started_by_this_run=false`
- `runtime_stopped_by_this_run=false`

## 剩余风险与下一步

1. 离线回归不能证明真实 ROS/DDS 消息上的 receipt 字段、真实 callback 时序或 current TF freshness。
2. `header_age_at_receipt_ms` 只证明消息在 callback receipt 时相对 header 的 age，不证明 header clock、
   物理位姿或地图坐标正确；`receipt_age_at_evaluation_ms` 只诊断 collector 收口延迟。
3. 下一步只允许在 existing localization runtime 已 active 后，或 CEO/operator 新授权 strict no-motion
   localization-only runtime 后，由 `robot-algorithm-engineer` 采一次 live receipt artifact。
4. 禁止再包装离线合同；仍禁止 `/initialpose`、planner/controller/path、NavigateToPose、`/cmd_vel`、
   `/api/base/manual`、UART、运动、route、delivery 和 HIL。
