# Field Evidence Rerun Acceptance Handoff Intake Follow-Up Escalation Status Pre-Start

Run time: 2026-05-23 03:04 Asia/Shanghai

## Sprint Type

sprint_type: epic

## 用户价值和产品北极星

产品北极星仍是让普通手机用户把垃圾交给小车后，小车可验证地完成固定路线/电梯 assisted delivery 送达；support 必须能用同一 safe `evidence_ref` 判断现场材料是否可进入下一步，而不能把 Docker/local metadata 当成真实送达。

本 sprint 的用户价值很窄：把上一轮 `field_evidence_rerun_execution_result_acceptance_handoff_intake_review_handoff` safe summary 继续推进到 `field_evidence_rerun_execution_result_acceptance_handoff_intake_followup_escalation_status`，输出 owner/support/reviewer follow-up due status：`pending`、`overdue`、`escalated`、`blocked`。它只用于催现场 owner 补真实 task record、Nav2/fixed-route runtime log、route completion signal、电梯门/楼层确认、人工协助记录、dropoff/cancel completion、delivery result、真实 route/elevator field pass 和真实 phone/browser evidence。

本轮不证明真实 delivery、route/elevator pass、true phone/browser、HIL、Objective 5 external proof、verified terminal result 或 PR #5 reviewer resolution。

## 背景证据

- `OKR.md` 4.1 当前 Objective 5 约 68%，是最低；Objective 1 约 81%，Objective 2/3/4 约 99%。
- 当前机器只有 Docker，没有真实硬件、真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/cutover、真实 phone/browser 或 verified terminal result。
- Live GitHub PR #5 review threads：`PRRT_kwDOSWB9286CJ3tQ` resolved，`PRRT_kwDOSWB9286CJ3tU` resolved，`PRRT_kwDOSWB9286CJ3tX` unresolved / `is_resolved=false` / `hardware_material_pending`；评论要求 mandatory sensor assumptions 提供 `docs/vendor/` source。
- 已有 comment `3269642220` 只是 software-proof reply，不是 reviewer resolution，不得写成 PR #5 closure 或 O1 proof。
- 最新 sprint `sprints/2026.05.23_02-03_field-evidence-rerun-acceptance-handoff-intake-review-handoff/final.md` 明确上一轮只完成 `software_proof_docker_field_evidence_rerun_execution_result_acceptance_handoff_intake_review_handoff_gate`，不是真实 route/elevator field pass、verified terminal result、dropoff/cancel completion、delivery success、O5 external proof、O1 HIL、WAVE ROVER/UART proof 或 PR #5 resolution。

## OKR 映射

- Objective 5：最低但本轮不推进完成度。没有真实 external proof，本轮不继续包装 O5/O1 blocker，也不得提高约 68%。
- Objective 1：不推进完成度。PR #5 `PRRT_kwDOSWB9286CJ3tX` 仍 unresolved，真实硬件/HIL/传感器材料仍缺失，约 81% 保持不变。
- Objective 2：本轮只要求真实 task record、dropoff/cancel completion、delivery result 和 route/elevator field pass 的 follow-up due status，不证明真实送达或 `delivery_success=true`。
- Objective 3：本轮只要求真实 Nav2/fixed-route runtime log、route completion signal 和 route evidence 的补料升级状态，不证明路线实跑。
- Objective 4：本轮 mobile/web 只允许 read-only follow-up status panel，必须保留 `primary_actions_enabled=false`，不证明真实手机/browser 或 production app。

## KR 拆解或更新

本轮不修改 OKR/KR 文案，不提升百分比。KR 拆解仅作为当前 sprint 抓手：

1. PC-only gate 消费上一轮 acceptance handoff intake review handoff safe summary，并输出 follow-up due status。
2. Robot diagnostics 提供 safe alias，展示 owner/support/reviewer follow-up status，失败时 fail closed。
3. mobile/web 展示只读 follow-up escalation status panel，普通用户主操作继续禁用。
4. Product closeout 在 A/B/C 完成后更新 `tech-done.md`、`side2side_check.md`、`final.md`、`OKR.md` 和 `docs/process/okr_progress_log.md`，并保持 no OKR percentage lift，除非真实外部/硬件/现场材料出现。

## 本轮核心抓手

Capability:

- `field_evidence_rerun_execution_result_acceptance_handoff_intake_followup_escalation_status`

Evidence boundary:

- `software_proof_docker_field_evidence_rerun_execution_result_acceptance_handoff_intake_followup_escalation_status_gate`

必须保留：

- `source=software_proof`
- `software_proof`
- `not_proven`
- `delivery_success=false`
- `primary_actions_enabled=false`
- `safe_to_control=false`
- 同一 safe `evidence_ref`

## 需要做什么

- Autonomy Engineer 实现 PC-only follow-up escalation status gate、目标测试和 evidence docs。
- Robot Platform Engineer 增加 Robot diagnostics safe alias、目标测试和 runtime docs。
- Full-Stack Engineer 增加 `mobile/web` read-only panel、fixture、目标测试和 mobile docs。
- Product Owner 在三路工程返回后做 closeout，补齐 `tech-done.md`、`side2side_check.md`、`final.md`、`OKR.md`、`docs/process/okr_progress_log.md`，不得提前预生成。

## 优先级和验收口径

P0:

- 同一 safe `evidence_ref` 贯穿上一轮 review handoff safe summary 与 follow-up escalation status。
- 只允许输出 `pending`、`overdue`、`escalated`、`blocked` 这类补料状态，不允许输出真实 success/pass/ready-to-control。
- 任何 missing review handoff、missing required field material、evidence_ref mismatch、unsafe copy、success/control claim、external-proof claim、HIL claim、PR #5 resolution claim 都必须 fail closed。
- Robot/mobile 只消费 safe summary，不暴露 raw artifacts、ROS topics、`/cmd_vel`、串口/UART、WAVE ROVER 细节、credentials、local paths、checksums、tracebacks 或 complete artifacts。
- `delivery_success=false`、`primary_actions_enabled=false`、`safe_to_control=false` 不得被本轮改成 true。

P1:

- 工程文档同步到 `docs/interfaces/` 和 `docs/product/`。
- Product closeout 同步 `OKR.md` 与 `docs/process/okr_progress_log.md`，并说明 no OKR percentage lift。

## 对应责任 Engineer

- A. `autonomy-engineer`：PC-only follow-up escalation status gate + tests + evidence docs。
- B. `robot-software-engineer`：Robot diagnostics safe alias + tests + runtime docs。
- C. `full-stack-software-engineer`：mobile/web read-only panel + fixture + tests + mobile docs。
- D. `product-okr-owner`：A/B/C 完成后的 sprint closeout、OKR/progress narrative 更新和证据边界复核。

## 风险、阻塞和需要补齐的证据链

- O5 blocker：真实 public HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/cutover、真实 phone/browser、verified terminal result materials 仍缺失。
- O1 blocker：真实 WAVE ROVER/UART/HIL、2D LiDAR/ToF SKU/source/receipt、operator HIL report、PR #5 `PRRT_kwDOSWB9286CJ3tX` reviewer resolution 仍缺失。
- O2/O3/O4 真实材料仍缺：真实 task record、Nav2/fixed-route runtime log、route completion signal、真实电梯门状态、目标楼层确认、人工协助记录、dropoff/cancel completion、delivery result、真实 route/elevator field pass、真实 iPhone/Android/browser evidence。
- 本轮只允许进入 `software_proof_docker_field_evidence_rerun_execution_result_acceptance_handoff_intake_followup_escalation_status_gate`，不得写成真实 delivery success、verified terminal result、route/elevator pass、true phone/browser、HIL、O5 external proof 或 PR #5 resolved。

## 需要创建或更新的 sprint 文档

本启动任务创建：

- `sprints/2026.05.23_03-04_field-evidence-rerun-acceptance-handoff-intake-followup-escalation-status/pre_start.md`
- `sprints/2026.05.23_03-04_field-evidence-rerun-acceptance-handoff-intake-followup-escalation-status/prd.md`
- `sprints/2026.05.23_03-04_field-evidence-rerun-acceptance-handoff-intake-followup-escalation-status/tech-plan.md`

工程完成后 Product closeout 才能创建或更新：

- `sprints/2026.05.23_03-04_field-evidence-rerun-acceptance-handoff-intake-followup-escalation-status/tech-done.md`
- `sprints/2026.05.23_03-04_field-evidence-rerun-acceptance-handoff-intake-followup-escalation-status/side2side_check.md`
- `sprints/2026.05.23_03-04_field-evidence-rerun-acceptance-handoff-intake-followup-escalation-status/final.md`
- `OKR.md`
- `docs/process/okr_progress_log.md`
