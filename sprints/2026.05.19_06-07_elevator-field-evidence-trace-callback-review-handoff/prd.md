# Sprint 2026.05.19_06-07 Elevator Field Evidence Trace Callback Review Handoff - PRD

## 1. 用户价值和产品北极星

目标用户不是会读 raw artifact 的研发同学，而是需要在手机和现场流程里理解“还缺什么材料、该交给谁补”的现场 owner / 支持人员。上一轮 `elevator_field_evidence_trace_callback_review_decision` 已经能判定 callback 材料是否足以进入 owner handoff；本轮要把判定结果转成可执行 handoff package，减少 PR #4 route/elevator 现场材料回填时的歧义。

产品北极星：普通手机用户最终能完成跨楼层送垃圾，并在失败时得到可解释、可复盘、可恢复的状态说明。本轮只是 support-facing `software_proof`，不把 metadata handoff 写成真实电梯、真实路线、真实投放或 delivery success。

## 2. OKR 映射

| Objective | 本轮关系 |
| --- | --- |
| Objective 1：硬件协议可信底盘 | 不直接推进。当前约 81%，仍缺真实 WAVE ROVER/UART/HIL 与 PR #5 真实 2D LiDAR / ToF material；本轮只在 handoff 的 `not_proven` 中保留该缺口。 |
| Objective 2：可送垃圾任务 + 电梯 assisted delivery 必达闭环 | 主要对齐。PR #4 要求 elevator-assisted delivery mandatory，本轮把 review decision 交接给 owner，明确真实电梯门、楼层确认、人工协助、dropoff/cancel、delivery result 仍需回填。 |
| Objective 3：可验证导航与固定路线 | 主要对齐。handoff 必须把真实 Nav2/fixed-route runtime、route completion signal、field task record 作为 required materials。 |
| Objective 4：手机用户体验与低成本量产边界 | 次要对齐。mobile/web 只读展示 handoff package，保持普通用户/支持人员可读，不暴露 raw JSON/ROS topic，不改变控制 gating。 |
| Objective 5：云中转 + OSS/CDN 数据通路产品化 | 不直接推进。当前约 68%，缺真实 external proof；本轮不重复 O5 blocker 包装。 |

## 3. KR 拆解或更新

- Objective 2 KR5/KR6/KR7：新增 owner handoff package，让同一 safe `evidence_ref` 下的现场证据补齐责任可追踪。
- Objective 3 KR3/KR4/KR5：新增 route runtime / completion / field task record 的 handoff checklist，防止 callback review decision 被误读成 route/elevator pass。
- Objective 4 KR6/KR7：新增 phone-safe handoff 展示，让手机端能解释 `not_proven` 状态和下一步 owner，不暴露底层实现细节。

不更新 KR 完成度：只有真实 route/elevator field material、真实 phone/browser、真实 WAVE ROVER/UART/HIL 或 O5 external proof 到位后，才考虑 OKR 百分比变化。

## 4. 本轮核心抓手

抓手名称：`elevator_field_evidence_trace_callback_review_handoff`。

输入：上一轮 `elevator_field_evidence_trace_callback_review_decision` artifact 或 summary。

输出：safe handoff package，至少包含：

- `handoff_status`
- source review decision schema/status
- safe `evidence_ref`
- owner task groups：Autonomy、Robot、Full-Stack、Field owner
- missing real materials
- rejected material summary
- next required evidence
- evidence boundary
- `software_proof`
- `not_proven`
- `delivery_success=false`
- `primary_actions_enabled=false`

## 5. 需要做什么

Autonomy 需要实现 handoff package gate：从 review decision summary 读取状态，做 schema/boundary/same-ref/unsafe copy 校验，输出 owner handoff package。

Robot 需要把 handoff summary 以 safe diagnostics alias 暴露给 operator gateway，缺字段、unsafe copy 或 status 不支持时 fail closed。

Full-Stack 需要在 mobile/web 中新增只读 handoff panel，展示 owner handoff、missing real materials、next evidence 和 evidence boundary；不增加 copy/export 控制，不发送 ACK/cursor/diagnostics fetch/Start/Confirm/Cancel。

Product 在 worker 完成后负责 closeout，确认 `software_proof` 边界没有被扩大，并按实际结果决定是否更新 OKR 和 process log。

## 6. 优先级和验收口径

P0 验收：

- Handoff package 必须继承上一轮 review decision 的同一 safe `evidence_ref`。
- 所有输出必须保持 `software_proof`、`not_proven`、`delivery_success=false`、`primary_actions_enabled=false`。
- 出现 raw JSON、ROS topic、`/cmd_vel`、serial/UART、WAVE ROVER、credentials、local path、checksum、complete artifact、success/control claim 时必须 fail closed 或过滤。
- 不得把 `ready_for_elevator_field_owner_handoff_not_proven` 写成真实 field pass。

P1 验收：

- Robot diagnostics 和 mobile/web 只能只读消费 summary。
- Full-Stack 不改变 Start Delivery、Confirm Dropoff、Cancel gating。
- 文档同步更新到 interface docs / product flow docs，且 sprint `tech-done.md` 后续记录 worker 验证结果。

## 7. 对应责任 Engineer

- Autonomy Algorithm Engineer：handoff package gate 与 route/elevator material contract。
- Robot Platform Engineer：operator diagnostics safe alias 与 same-ref fail-closed 消费。
- User Touchpoint Full-Stack Engineer：mobile/web phone-safe handoff panel。
- Product Manager / OKR Owner：OKR rerank、验收口径、最终 closeout。

## 8. 风险、阻塞和需要补齐的证据链

- Objective 5 约 68% 但缺真实 external proof；本轮不应把 local handoff package 包装成云端完成度。
- Objective 1 约 81% 但缺真实 WAVE ROVER/UART/HIL 和 PR #5 2D LiDAR / ToF 真材料；本轮不触碰硬件事实，不更新硬件配置。
- PR #4 route/elevator 仍缺真实现场材料；handoff package 只提高材料回填的可执行性。
- 若 source review decision 不存在、schema 不匹配或 safe `evidence_ref` 不一致，必须输出 blocked，而不是生成虚假的 owner handoff。

## 9. 需要创建或更新的 sprint 文档

本 PRD 属于 Epic sprint 三文档启动阶段；本轮同时创建：

- `pre_start.md`
- `prd.md`
- `tech-plan.md`

后续 implementation 完成后再补：

- `tech-done.md`
- `side2side_check.md`
- `final.md`
