# Field Evidence Rerun Acceptance Handoff Intake Review Handoff PRD

Run time: 2026-05-23 02:03 Asia/Shanghai

## 用户价值和产品北极星

北极星：普通手机用户不需要懂 ROS2、串口、云服务或现场材料格式，也能通过支持人员的安全证据链判断小车送垃圾任务是否可以进入下一步现场验收、返工或补材料。

本轮产品价值：在上一轮 owner/support intake review decision 后，新增一个 review handoff 层，把“决策是否可继续”变成“交给 owner/support/reviewer 的下一步包是否安全、完整、同 evidence_ref、且不会被误读为真实送达”。这样 support 不会把 review decision 误当真实 field pass，也不会在材料缺失、evidence_ref 不一致或出现成功/控制 claims 时继续推进。

## 问题定义

上一轮 `field_evidence_rerun_execution_result_acceptance_handoff_intake_review_decision` 证明了 Docker/local 环境下 owner/support intake 可以被安全复核并给出下一步 decision。但 decision 只回答“能否进入下一步”，不回答“下一步交给谁、补什么、哪些材料仍然不能被当成真实 proof”。如果没有 review handoff，后续现场 owner、support、reviewer 和 mobile panel 容易把 ready/rework/rejected 状态混成一个完成结论。

## OKR 映射

- Objective 5 仍最低，约 68%。本轮不直接针对 O5，因为没有真实 public HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/cutover、真实 phone/browser 或 verified terminal result materials。
- Objective 1 约 81%。本轮不提升 O1，因为缺真实 WAVE ROVER/UART/HIL、2D LiDAR/ToF SKU/source/receipt、operator HIL report，且 PR #5 `PRRT_kwDOSWB9286CJ3tX` 仍 unresolved / `is_resolved=false` / `hardware_material_pending`。
- Objective 2/3/4：本轮只推进 field-evidence rerun acceptance handoff 的 software-proof review handoff readiness，作为后续真实 route/elevator/phone/browser 材料回填前的安全交接层。

## KR 拆解或更新

本轮不改 OKR/KR，只对现有 KR 做 sprint-level 拆解：

- KR-A：PC gate 给出 review handoff：ready for owner/support/reviewer handoff、needs owner rework、evidence_ref mismatch、unsafe rejected、blocked missing review decision。
- KR-B：Robot diagnostics 只暴露 safe summary alias，保持 `safe_to_control=false`。
- KR-C：mobile/web 只显示 read-only panel，保持 Start Delivery、Confirm Dropoff、Cancel 禁用。
- KR-D：Product closeout 记录 no OKR percentage lift，并把 `software_proof` 与真实现场/HIL/O5 proof 分开。

## 范围内

- Capability 名称：`field_evidence_rerun_execution_result_acceptance_handoff_intake_review_handoff`。
- Evidence boundary：`software_proof_docker_field_evidence_rerun_execution_result_acceptance_handoff_intake_review_handoff_gate`。
- PC-only review handoff artifact and summary。
- Robot diagnostics safe alias。
- mobile/web read-only review handoff panel and fixture。
- Targeted unit tests、fixture validation、scoped docs updates。
- Sprint closeout、OKR/progress log narrative update after engineering completion。

## 范围外

- 不证明真实 delivery、delivery result、dropoff/cancel completion 或 `delivery_success=true`。
- 不证明真实 route/elevator field pass、Nav2/fixed-route runtime pass 或 route completion signal。
- 不证明 true phone/browser、真实 iPhone/Android behavior、production app 或 PWA prompt/userChoice。
- 不证明 HIL、WAVE ROVER/UART、真实 `/odom`、`/imu/data`、`/battery`。
- 不证明 Objective 5 external proof、public HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue 或 worker/cutover。
- 不解决 PR #5 `PRRT_kwDOSWB9286CJ3tX`，除非 reviewer live thread 实际 resolved。
- 不新增机器人控制 endpoint、material upload route、ACK/cursor route、review route、handoff route 或 hidden primary-action enablement。

## 用户/支持人员流程

1. Field owner/support/reviewer 提供上一轮 review decision 的 safe summary 和同一 safe `evidence_ref` 的 handoff packet。
2. PC-only gate 判断 handoff packet 是否足够交给下一步 owner/support/reviewer，或是否需要返工。
3. Robot diagnostics 暴露 safe alias，support 可在 diagnostics 中看到 handoff 状态和缺口。
4. mobile/web 只读 panel 让 phone/support 视角看到状态，但主操作保持禁用。
5. Product closeout 记录本轮只完成 Docker/local software proof，等待真实现场材料或硬件/external evidence。

## 验收口径

必须满足：

- 输出中包含 `field_evidence_rerun_execution_result_acceptance_handoff_intake_review_handoff`。
- 输出中包含 `software_proof_docker_field_evidence_rerun_execution_result_acceptance_handoff_intake_review_handoff_gate`。
- 所有 summary 保留 `source=software_proof`、`software_proof`、`not_proven`、`delivery_success=false`、`primary_actions_enabled=false`、`safe_to_control=false`。
- Evidence-ref mismatch、missing review decision、missing required material、unsafe wording、success/control wording、external-proof/HIL/PR-resolution claim 均 fail closed。
- `mobile/web` Start Delivery、Confirm Dropoff、Cancel 在 fixture 下保持禁用。
- Product closeout 不提高 OKR 百分比，除非真实材料出现。

## 责任 Engineer

- `autonomy-engineer`：PC-only review handoff gate + tests + evidence docs。
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
