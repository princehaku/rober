# Sprint 2026.05.19_06-07 Elevator Field Evidence Trace Callback Review Handoff - Pre Start

## sprint_type: epic

Start time: 2026-05-19 06:07 Asia/Shanghai.

## 1. 用户价值和产品北极星

用户价值：把 PR #4 route/elevator 现场证据链从上一轮 `elevator_field_evidence_trace_callback_review_decision` 的“可判定”推进到 owner handoff package。现场 owner、Autonomy、Robot、Full-Stack 后续不再靠口头转述判断缺口，而是拿到同一 safe `evidence_ref` 下的 handoff package，明确谁补真实门状态、目标楼层确认、人工协助、Nav2/fixed-route runtime、route completion signal、field task record、dropoff/cancel completion 和 delivery result。

产品北极星仍是面向普通手机用户的可解释送垃圾机器人。本轮只推进 `software_proof` 的现场证据交接，不证明真实电梯、真实 Nav2/fixed-route、真实手机、WAVE ROVER/UART/HIL、Objective 5 external proof 或 delivery success。

## 2. OKR 映射与 rerank 证据

Live `OKR.md` 4.1 证据：

- Objective 5 约 68%，当前最低；但仍缺真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue connectivity、production worker/migration/cutover 和真实 phone/browser external proof。本轮不重复 O5 local metadata 包装。
- Objective 1 约 81%，次低；但仍缺真实 WAVE ROVER/UART/HIL、`feedback_T1001.log`、真实 `/odom`、`/imu/data`、`/battery`、operator HIL report，以及 PR #5 真实 2D LiDAR / ToF SKU/source/receipt/procurement/installation/wiring/power/calibration/HIL-entry。本机没有真实硬件，不重复消费同一 blocker。
- Objective 2 / Objective 3 约 99%，但 PR #4 route/elevator field materials 仍缺真实现场材料；PR #4 / PR #5 review 证据共同说明 elevator-assisted delivery mandatory，硬件 baseline/source/material 仍是缺口。
- 最近两轮已经完成 `elevator_field_evidence_trace_callback_intake` 与 `elevator_field_evidence_trace_callback_review_decision`，下一步可执行抓手是 `elevator_field_evidence_trace_callback_review_handoff`，不是重复 intake、review decision、O5 blocker 或 O1 hardware blocker 包装。

本 sprint 对齐 Objective 2 KR5/KR6/KR7、Objective 3 KR3/KR4/KR5、Objective 4 KR6/KR7；Objective 5 与 Objective 1 只记录 blocker 和 rerank 理由，不提升完成度。

## 3. KR 拆解或更新

- Objective 2：把 review decision 的 `ready_for_elevator_field_owner_handoff_not_proven` 或 backfill decision 转成 owner handoff package，保留真实电梯门、目标楼层、人工协助、dropoff/cancel、delivery result 的待补证据清单。
- Objective 3：把真实 Nav2/fixed-route runtime log、route completion signal、field task record 和 same `evidence_ref` 复账作为 handoff 的 hard requirements，避免 handoff 被误读成 route pass。
- Objective 4：手机端只读展示 owner handoff package，继续隐藏 raw JSON/ROS topic/硬件细节，不改变 Start Delivery、Confirm Dropoff、Cancel gating。

## 4. 本轮核心抓手

核心抓手：`elevator_field_evidence_trace_callback_review_handoff`。

本轮不是创建另一个复核决策，也不是继续把缺失外部材料重新包装；它要把上一轮 review decision 的结论变成三方 owner 可执行的交接包：

- Autonomy owner 接收 route runtime、route completion 和 field-material backfill checklist。
- Robot owner 接收 field task record、diagnostics same-ref 复账和 fail-closed summary contract。
- Full-Stack owner 接收 phone-safe handoff 展示边界，继续保持控制动作 fail-closed。
- Product closeout 后置，等 implementation 证据回来后再更新 `tech-done.md`、`side2side_check.md`、`final.md`、`OKR.md` 或进展日志。

## 5. 需要做什么

1. Autonomy：新增 PC handoff package gate，消费上一轮 `elevator_field_evidence_trace_callback_review_decision` summary，输出 safe owner handoff package。
2. Robot：新增 diagnostics safe alias，只读消费 handoff summary；缺 summary 或 unsafe copy 时 fail closed。
3. Full-Stack：新增 mobile/web 只读 panel，展示 handoff status、owner tasks、missing real materials、same safe `evidence_ref` 和 evidence boundary，不触发任何命令。
4. Product：实现完成后做阶段验收和 OKR closeout；本启动 sprint 只创建 `pre_start.md`、`prd.md`、`tech-plan.md`。

## 6. 优先级和验收口径

优先级：

1. P0：handoff package 必须从上一轮 review decision 读取同一 safe `evidence_ref`，并保留 `software_proof`、`not_proven`、`delivery_success=false`、`primary_actions_enabled=false`。
2. P0：缺失真实 route/elevator 材料时输出 backfill owner handoff，不得写成 pass、success、HIL 或真实 delivery。
3. P1：Robot/mobile 只读消费 summary，任何 raw artifact、credential、local path、ROS topic、`/cmd_vel`、serial/UART、WAVE ROVER、checksum、success/control claim 都必须 fail closed 或过滤。
4. P1：所有 worker 只做各自文件范围，不改硬件配置，不新增硬件事实。

验收口径：

- 新 sprint 三份 planning 文档存在，并包含 Objective 5、Objective 1、Objective 2、Objective 3、PR #4、PR #5、`elevator_field_evidence_trace_callback_review_handoff`、`elevator_field_evidence_trace_callback_review_decision`、`software_proof`、`not_proven`、`delivery_success=false`、`primary_actions_enabled=false` 和 `OKR 最低优先级核对`。
- `tech-plan.md` 写清 3 个并行 owner：Autonomy、Robot、Full-Stack；Product closeout 后置。
- 本轮 planning 不修改产品代码或测试。

## 7. 对应责任 Engineer

- Autonomy Algorithm Engineer：PC handoff package gate、route/elevator material handoff contract、focused unit test、interface docs。
- Robot Platform Engineer：operator diagnostics safe alias、same-ref summary 只读消费、focused diagnostics tests、interface docs。
- User Touchpoint Full-Stack Engineer：mobile/web 只读 handoff panel、fixtures、focused UI contract tests、product flow docs。
- Product Manager / OKR Owner：planning、阶段验收、OKR closeout 和 blocker 重复消费控制；不在 implementation 前更新 OKR 百分比。

## 8. 风险、阻塞和需要补齐的证据链

- O5 blocker：缺真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/cutover、真实 phone/browser external proof。
- O1 blocker：缺真实 WAVE ROVER/UART/HIL、真实 serial feedback、真实 `/odom`、`/imu/data`、`/battery`、operator HIL report、PR #5 真实 2D LiDAR / ToF material。
- PR #4 blocker：缺真实电梯门状态、目标楼层确认、人工协助记录、Nav2/fixed-route runtime log、route completion signal、field task record、dropoff/cancel completion、delivery result。
- 本轮 handoff package 只能降低现场 owner 执行歧义，不替代真实 field evidence，不提升 O5 external proof 或 O1 HIL completion。

## 9. 需要创建或更新的 sprint 文档

本 planning 任务创建：

- `pre_start.md`
- `prd.md`
- `tech-plan.md`

后续 implementation 完成后必须继续创建/更新：

- `tech-done.md`
- `side2side_check.md`
- `final.md`
- 必要时更新 `OKR.md` 和 `docs/process/okr_progress_log.md`，但只能基于实际验证证据。
