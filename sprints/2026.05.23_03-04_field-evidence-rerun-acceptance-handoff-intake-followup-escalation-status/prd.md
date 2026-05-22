# Field Evidence Rerun Acceptance Handoff Intake Follow-Up Escalation Status PRD

Run time: 2026-05-23 03:04 Asia/Shanghai

## 用户价值和产品北极星

北极星：普通手机用户不需要懂 ROS2、串口、云服务或现场材料格式，也能通过支持人员的安全证据链判断小车送垃圾任务是否可以进入下一步现场验收、补料升级或阻塞升级。

本轮产品价值：在上一轮 owner/support/reviewer review handoff 后，新增一个 follow-up escalation status 层，把“已经交接给谁”继续变成“谁逾期、谁需要补什么、是否应升级、是否仍 blocked”。这样 support 不会把 review handoff 误当真实 field pass，也不会在材料迟迟缺失时继续堆 O5/O1 本地 blocker wrapper。

## 问题定义

上一轮 `field_evidence_rerun_execution_result_acceptance_handoff_intake_review_handoff` 证明了 Docker/local 环境下 review handoff metadata 可以被 PC/Robot/mobile 三端安全展示。但 handoff 只回答“下一步交给谁”，不回答“是否已到期、是否逾期、是否需要升级、哪些真实材料仍未补齐”。如果没有 follow-up escalation status，现场 owner、support、reviewer 容易把交接状态长期悬空，或者误把 pending handoff 当成 acceptance completed。

## OKR 映射

- Objective 5 仍最低，约 68%。本轮不直接针对 O5，因为没有真实 public HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/cutover、真实 phone/browser 或 verified terminal result materials。
- Objective 1 约 81%。本轮不提升 O1，因为缺真实 WAVE ROVER/UART/HIL、2D LiDAR/ToF SKU/source/receipt、operator HIL report，且 PR #5 `PRRT_kwDOSWB9286CJ3tX` 仍 unresolved / `is_resolved=false` / `hardware_material_pending`。
- Objective 2/3/4：本轮推进 field-evidence rerun acceptance handoff 的 software-proof follow-up escalation readiness，作为后续真实 route/elevator/phone/browser 材料回填前的安全催办层。

## KR 拆解或更新

本轮不改 OKR/KR，只对现有 KR 做 sprint-level 拆解：

- KR-A：PC gate 给出 follow-up due status：`pending`、`overdue`、`escalated`、`blocked`。
- KR-B：Robot diagnostics 只暴露 safe summary alias，保持 `safe_to_control=false`。
- KR-C：mobile/web 只显示 read-only follow-up escalation status panel，保持 Start Delivery、Confirm Dropoff、Cancel 禁用。
- KR-D：Product closeout 记录 no OKR percentage lift，并把 `software_proof` 与真实现场/HIL/O5 proof 分开。

## 范围内

- Capability 名称：`field_evidence_rerun_execution_result_acceptance_handoff_intake_followup_escalation_status`。
- Evidence boundary：`software_proof_docker_field_evidence_rerun_execution_result_acceptance_handoff_intake_followup_escalation_status_gate`。
- PC-only follow-up escalation status artifact and summary。
- Robot diagnostics safe alias。
- mobile/web read-only follow-up escalation status panel and fixture。
- Targeted unit tests、fixture validation、scoped docs updates。
- Sprint closeout、OKR/progress log narrative update after engineering completion。

## 范围外

- 不证明真实 delivery、delivery result、dropoff/cancel completion 或 `delivery_success=true`。
- 不证明真实 route/elevator field pass、Nav2/fixed-route runtime pass 或 route completion signal。
- 不证明 true phone/browser、真实 iPhone/Android behavior、production app 或 PWA prompt/userChoice。
- 不证明 HIL、WAVE ROVER/UART、真实 `/odom`、`/imu/data`、`/battery`。
- 不证明 Objective 5 external proof、public HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue 或 worker/cutover。
- 不解决 PR #5 `PRRT_kwDOSWB9286CJ3tX`，除非 reviewer live thread 实际 resolved。
- 不新增机器人控制 endpoint、material upload route、ACK/cursor route、review route、handoff route、follow-up route 或 hidden primary-action enablement。

## 用户/支持人员流程

1. Field owner/support/reviewer 提供上一轮 review handoff safe summary，以及同一 safe `evidence_ref` 的 follow-up policy。
2. PC-only gate 判断真实材料是否仍 pending、是否 overdue、是否应 escalated、或是否 blocked 在缺少 review handoff / evidence_ref mismatch / unsafe copy。
3. Robot diagnostics 暴露 safe alias，support 可在 diagnostics 中看到 follow-up 状态和缺口。
4. mobile/web 只读 panel 让 phone/support 视角看到催办状态，但主操作保持禁用。
5. Product closeout 记录本轮只完成 Docker/local software proof，等待真实现场材料或硬件/external evidence。

## 需要催补的真实材料

所有材料必须绑定同一 safe `evidence_ref`：

- 真实 task record。
- 真实 Nav2/fixed-route runtime log。
- route completion signal。
- 电梯门状态确认。
- 目标楼层确认。
- 人工协助记录。
- dropoff/cancel completion。
- delivery result。
- 真实 route/elevator field pass。
- 真实 phone/browser evidence。
- PR #5 hardware material 仍 pending，除非 `PRRT_kwDOSWB9286CJ3tX` live resolved。

## 验收口径

必须满足：

- 输出中包含 `field_evidence_rerun_execution_result_acceptance_handoff_intake_followup_escalation_status`。
- 输出中包含 `software_proof_docker_field_evidence_rerun_execution_result_acceptance_handoff_intake_followup_escalation_status_gate`。
- 所有 summary 保留 `source=software_proof`、`software_proof`、`not_proven`、`delivery_success=false`、`primary_actions_enabled=false`、`safe_to_control=false`。
- Follow-up status 只能表达 `pending`、`overdue`、`escalated`、`blocked`，不能表达完成、通过、可控制或送达成功。
- Evidence-ref mismatch、missing review handoff、missing required material、unsafe wording、success/control wording、external-proof/HIL/PR-resolution claim 均 fail closed。
- `mobile/web` Start Delivery、Confirm Dropoff、Cancel 在 fixture 下保持禁用。
- Product closeout 不提高 OKR 百分比，除非真实材料出现。

## 责任 Engineer

- `autonomy-engineer`：PC-only follow-up escalation status gate + tests + evidence docs。
- `robot-software-engineer`：Robot diagnostics safe alias + tests + runtime docs。
- `full-stack-software-engineer`：mobile/web read-only panel + fixture + tests + mobile docs。
- `product-okr-owner`：工程完成后的 `tech-done.md`、`side2side_check.md`、`final.md`、`OKR.md`、`docs/process/okr_progress_log.md`。

## 风险与证据链缺口

- 本轮仍可能被误读为 acceptance pass；文案必须使用 `not_proven` 和 fail-closed 状态，避免 “pass/success/ready to control”。
- 如果 owner/support/reviewer packet 包含 raw logs、local paths、credentials、serial/UART details、ROS topics 或 complete artifacts，PC/Robot/mobile 必须拒绝或过滤。
- 当前没有真实 O5/O1/O2/O3/O4 材料，Product closeout 必须保守写 no OKR percentage lift。

## 需要创建或更新的 sprint 文档

启动阶段创建：

- `pre_start.md`
- `prd.md`
- `tech-plan.md`

工程完成后再创建或更新：

- `tech-done.md`
- `side2side_check.md`
- `final.md`
- `OKR.md`
- `docs/process/okr_progress_log.md`
