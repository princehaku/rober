# Field Evidence Rerun Acceptance Backfill Review Decision Pre-Start

Run time: 2026-05-22 22:23 Asia/Shanghai

## Sprint Type

sprint_type: epic

Capability: `field_evidence_rerun_execution_result_acceptance_backfill_review_decision`

Evidence boundary: `software_proof_docker_field_evidence_rerun_execution_result_acceptance_backfill_review_decision_gate`

## 开工证据

- `OKR.md` 4.1 当前最低 Objective 是 Objective 5，约 68%。但第 6 节明确：没有真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/cutover、真实手机/browser 或 verified terminal result 时，不要重复本地 O5 metadata depth。
- Objective 1 约 81%，但本机仍只有 Docker，没有真实 WAVE ROVER/UART/HIL、2D LiDAR/ToF SKU/source/receipt、operator HIL report 或 PR #5 reviewer resolution。
- PR #5 live thread evidence 按当前输入处理：`PRRT_kwDOSWB9286CJ3tX` 仍 `is_resolved=false` / `hardware_material_pending`；`PRRT_kwDOSWB9286CJ3tQ` 和 `PRRT_kwDOSWB9286CJ3tU` 已 resolved。
- 最近 sprint `sprints/2026.05.22_21-22_reviewer-ack-followup-owner-response-intake-bridge/` 已完成 reviewer ACK follow-up source -> owner response intake bridge，边界仍是 `software_proof`，无 OKR percentage lift。
- 前置 route/elevator/phone family 已有 `field_evidence_rerun_execution_result_acceptance_packet` 和 `field_evidence_rerun_execution_result_acceptance_backfill`，但还没有 `field_evidence_rerun_execution_result_acceptance_backfill_review_decision` follow-on。

## 用户价值和产品北极星

用户价值：现场 owner、支持人员和 reviewer 可以把上一轮 acceptance backfill 材料转成明确的 review decision，而不是让八类材料停在“已回填但未判定”的灰区。普通手机用户仍只看到安全、只读、中文优先的状态说明；任何缺材料、错 evidence_ref 或不安全声明都不会启用控制。

产品北极星：低成本 ROS2 垃圾投递机器人必须把路线、电梯、手机和现场证据链做成可复盘、可交接、可阻断的产品闭环。Docker/local metadata 只能服务下一次真实现场复跑，不得冒充真实 route/elevator pass、真实手机/browser、delivery success、Objective 5 external proof、Objective 1 HIL 或 PR #5 resolution。

## 本轮核心抓手

本轮实现 `field_evidence_rerun_execution_result_acceptance_backfill_review_decision`：消费上一轮 acceptance backfill artifact/summary/Robot alias，对八类 field owner backfill 材料给出 review decision：

- `ready_for_field_rerun_result_acceptance_review_handoff`
- `needs_more_material`
- `evidence_ref_mismatch`
- `unsafe_rejected`
- `blocked_missing_backfill`

八类材料必须继续围绕同一 safe `evidence_ref`：task record、Nav2/fixed-route runtime log、route completion signal、elevator door state、target floor confirmation、human assistance record、dropoff/cancel completion or delivery result、true phone/browser evidence。

## OKR 映射

- Objective 2：把送垃圾任务和电梯 assisted delivery 的现场复跑结果材料转成下一步验收交接，支持失败恢复和人工接管证据闭环。
- Objective 3：把 Nav2/fixed-route runtime log、route completion signal 与同一 `evidence_ref` review decision 对齐，服务可验证路线能力。
- Objective 4：让 mobile/web 只读展示 review decision、缺口和安全边界，不启用 Start Delivery、Confirm Dropoff 或 Cancel。
- Objective 5：当前仍最低但外部材料不可用，本轮不推进 O5 metadata depth，不产生 Objective 5 completion lift。
- Objective 1：PR #5 `PRRT_kwDOSWB9286CJ3tX` 仍 unresolved，本轮不处理硬件材料 closure，不产生 HIL 或 reviewer resolution。

## 本轮范围边界

In scope:

- 新增 PC gate、Robot diagnostics safe alias、mobile/web read-only panel/fixture 的实现计划。
- 明确 A/B/C/D 四个 owner 任务、文件范围、接口影响、验收命令和证据边界。
- 后续 Product closeout 要更新 `tech-done.md`、`side2side_check.md`、`final.md`、`OKR.md` 和 `docs/process/okr_progress_log.md`，但本规划任务不改这些文件。

Out of scope:

- 不声明真实 route/elevator field pass。
- 不声明真实手机/browser、真实 iPhone/Android device behavior 或 PWA prompt/userChoice。
- 不声明 delivery success、dropoff completion、cancel completion 或 verified terminal result。
- 不声明 Objective 5 external proof、公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue 或 worker/cutover。
- 不声明 Objective 1 HIL、真实 WAVE ROVER/UART、真实 `/odom`、`/imu/data`、`/battery` 或 PR #5 `PRRT_kwDOSWB9286CJ3tX` resolution。

## Owner 和启动规则

- A Autonomy Algorithm Engineer：PC gate、focused tests、evidence docs。
- B Robot Platform Engineer：Robot diagnostics safe alias、focused tests、diagnostics docs。
- C User Touchpoint Full-Stack Engineer：mobile/web read-only panel、fixture、focused tests、mobile docs。
- D Product Manager / OKR Owner：只在 A/B/C 完成后做 closeout，更新 tech-done/side2side/final/OKR/progress log。

本 sprint 是跨 owner Epic。tech-plan 完成后必须并行启动 A/B/C 三个 Engineer worker；D 不得抢先收口。

## 风险、阻塞和证据缺口

- O5 仍缺真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/cutover、真实手机/browser、verified terminal result。
- O1 仍缺真实 WAVE ROVER/UART/HIL、2D LiDAR/ToF SKU/source/receipt、采购/安装/接线/电源/标定、operator HIL report、PR #5 `PRRT_kwDOSWB9286CJ3tX` reviewer resolution。
- O2/O3/O4 仍缺真实 same-safe-`evidence_ref` field materials：真实 task record、真实 Nav2/fixed-route runtime log、route completion signal、真实电梯门状态、目标楼层确认、人工协助记录、dropoff/cancel completion、delivery result、真实手机/browser evidence。
- 本轮只能形成 `software_proof`。所有 summary 和 UI 必须保留 `not_proven`、`delivery_success=false`、`primary_actions_enabled=false`、`safe_to_control=false`。

## 需要创建或更新的 sprint 文档

本规划任务创建：

- `sprints/2026.05.22_22-23_field-evidence-rerun-acceptance-backfill-review-decision/pre_start.md`
- `sprints/2026.05.22_22-23_field-evidence-rerun-acceptance-backfill-review-decision/prd.md`
- `sprints/2026.05.22_22-23_field-evidence-rerun-acceptance-backfill-review-decision/tech-plan.md`

A/B/C 实现完成后，D 必须创建或更新：

- `sprints/2026.05.22_22-23_field-evidence-rerun-acceptance-backfill-review-decision/tech-done.md`
- `sprints/2026.05.22_22-23_field-evidence-rerun-acceptance-backfill-review-decision/side2side_check.md`
- `sprints/2026.05.22_22-23_field-evidence-rerun-acceptance-backfill-review-decision/final.md`
- `OKR.md`
- `docs/process/okr_progress_log.md`
