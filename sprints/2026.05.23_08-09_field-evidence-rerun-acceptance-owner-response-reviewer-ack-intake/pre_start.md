# Field Evidence Rerun Acceptance Owner Response Reviewer ACK Intake Pre-Start

Run time: 2026-05-23 08:09 Asia/Shanghai

## Sprint Type

sprint_type: epic

## 用户价值和产品北极星

产品北极星仍是让普通手机用户最终可验证地完成垃圾投递闭环。本 sprint 不交付真实送达，也不把 Docker-only metadata 当成现场通过；它把上一轮 owner-response review handoff safe metadata 加 reviewer ACK packet 转成 reviewer ACK intake metadata，让后续 reviewer ACK review decision 有同一 safe `evidence_ref` 下的入口材料。

用户价值是减少 reviewer ACK 阶段的责任不清：当真实 O5/O1/O2/O3/O4 证据仍缺失时，系统至少能把 reviewer 的 ACK、需补材料、重分配或不安全拒绝状态以 read-only、fail-closed、可审计的方式传给 PC、Robot diagnostics 和手机页面，避免把 happy path、本地 fixture 或 GitHub 部分 resolved thread 误写成产品闭环。

## 证据基线

- `OKR.md` 4.1 显示最新 sprint 是 `2026.05.23_07-08_field-evidence-rerun-acceptance-owner-response-review-handoff`。
- Objective 5 约 68%，仍是完成度最低项；当前 Docker-only 主机没有真实 public HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/cutover、真实手机/browser 或 verified terminal result materials。
- Objective 1 约 81%。PR #5 live review evidence 仍是 `PRRT_kwDOSWB9286CJ3tQ` resolved、`PRRT_kwDOSWB9286CJ3tU` resolved、`PRRT_kwDOSWB9286CJ3tX` unresolved / `is_resolved=false` / `hardware_material_pending`；不能写成 O1 进度提升或 PR #5 resolution。
- Objective 2 / Objective 3 / Objective 4 约 99%，但仍缺真实 route/elevator field pass、Nav2/fixed-route runtime pass、verified terminal result、dropoff/cancel completion、delivery result 和 true phone/browser proof。
- 上一轮 capability: `field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_review_handoff`。
- 上一轮 boundary: `software_proof_docker_field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_review_handoff_gate`。
- 本轮 capability: `field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_intake`。
- 本轮 proof boundary: `software_proof_docker_field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_intake_gate`。

## OKR 映射

- Objective 5：本轮不直接推进真实 O5 external proof，保持约 68%，no OKR percentage lift。
- Objective 1：PR #5 `PRRT_kwDOSWB9286CJ3tX` 未 resolved，且没有真实 2D LiDAR / ToF、WAVE ROVER、UART 或 HIL 材料，保持约 81%，no OKR percentage lift。
- Objective 2 / Objective 3：本轮只推进 reviewer ACK intake metadata，不证明 route/elevator field pass、Nav2/fixed-route runtime pass、dropoff/cancel completion、delivery result、delivery_success=true 或 verified terminal result。
- Objective 4：本轮可增加手机 read-only 可见性，但不证明 true phone/browser proof，也不启用主操作。

## KR 拆解或更新

本轮不新增 KR，不提升 OKR 百分比，只完成下一段 software-proof reviewer ACK intake:

- KR artifact: reviewer ACK intake summary for field evidence rerun execution result acceptance handoff intake owner response.
- Required state: `source=software_proof`, `software_proof`, `not_proven`。
- Required safety flags: `delivery_success=false`, `primary_actions_enabled=false`, `safe_to_control=false`。
- Closeout wording: no OKR percentage lift。

## 本轮核心抓手

把上一轮 `field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_review_handoff` 的 safe owner/support/reviewer handoff 转成 reviewer ACK intake：

- acknowledged path: reviewer 明确 ACK，但仍是 `not_proven`，只进入后续 review decision。
- reassign path: reviewer 要求 field owner / support 重分配或补负责人。
- mismatch path: `evidence_ref` 不一致时 fail closed。
- unsafe path: 出现 success/control/O5 external/O1 HIL/PR resolution claim 时 reject。
- missing-source path: 缺上一轮 owner-response review handoff summary 时 blocked。

## 需要做什么

1. Autonomy 建 PC-only reviewer ACK intake gate，消费上一轮 owner-response review handoff safe summary 和 reviewer ACK packet。
2. Robot 在 operator gateway diagnostics 增加 reviewer ACK intake safe alias，只暴露 phone-safe / diagnostics-safe metadata。
3. Full-Stack 在 `mobile/web` 增加 read-only reviewer ACK intake panel、fixture、focused tests 和产品文档同步。
4. Product 在 A/B/C 完成后更新 closeout docs、`OKR.md` 和 `docs/process/okr_progress_log.md`，做集成验证和 commit/push 交接。

## 优先级和验收口径

P0 是证据边界正确：必须保留 `software_proof_docker_field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_intake_gate`、`source=software_proof`、`not_proven`、`delivery_success=false`、`primary_actions_enabled=false`、`safe_to_control=false`。

P1 是三个 Engineer 文件范围互不重叠并可并行启动；验收只做围栏，不做大规模测试。

P2 是 sprint 留档真实更新：本规划先创建 `pre_start.md`、`prd.md`、`tech-plan.md`，实现后必须补 `tech-done.md`、`side2side_check.md`、`final.md`。

## 对应责任 Engineer

- Task A Autonomy: `autonomy-engineer`
- Task B Robot: `robot-software-engineer`
- Task C Full-Stack: `full-stack-software-engineer`
- Task D Product: `product-okr-owner`

## 风险、阻塞和需要补齐的证据链

- O5 阻塞：缺真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/cutover、真实手机/browser、verified terminal result。
- O1 阻塞：缺真实 2D LiDAR / ToF SKU/source/receipt/procurement/installation/wiring/power/calibration/HIL-entry，缺真实 WAVE ROVER powered bench/UART/HIL logs，PR #5 `PRRT_kwDOSWB9286CJ3tX` 仍 unresolved。
- O2/O3/O4 仍缺：同一 safe `evidence_ref` 的真实 task record、Nav2/fixed-route runtime log、route completion signal、真实电梯门状态、目标楼层确认、人工协助记录、dropoff/cancel completion、delivery result、真实 route/elevator field pass、真实手机/browser 证据。
- 本轮不得声称 O5 external proof、O1 HIL/PR #5 resolution、true phone/browser proof、route/elevator field pass、delivery/dropoff/cancel success。

## 需要创建或更新的 sprint 文档

- 本 planning 任务创建：`pre_start.md`、`prd.md`、`tech-plan.md`。
- implementation 完成后更新：`tech-done.md`、`side2side_check.md`、`final.md`。
