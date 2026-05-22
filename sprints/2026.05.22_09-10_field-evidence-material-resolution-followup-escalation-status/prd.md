# Field Evidence Material Resolution Followup Escalation Status PRD

Run time: 2026-05-22 09:00 Asia/Shanghai

## 用户价值和产品北极星

用户价值：CEO、field owner 和支持同学需要看清上一轮 handoff 之后到底卡在哪里。当前缺的不是又一个本地包装，而是真实 owner response material；产品必须把“谁该补材料、补什么、是否逾期、是否需要升级 CEO 决策”说清楚。

产品北极星：机器人只有在真实外部云、真实手机/browser、真实 route/elevator field pass、verified terminal result、真实硬件/HIL 和 reviewer resolution 都能被同一 safe `evidence_ref` 串起来时，才算接近可运营闭环。在那之前，产品要把缺口变成可追责的 owner action，不允许把 local Docker metadata 写成成功。

## Product Problem

08-09 sprint 已经把 `field_evidence_material_resolution_review_decision` 转成 `field_evidence_material_resolution_review_handoff`。但 handoff 后没有真实 owner response material：

- Owner 是否已经收到、是否逾期、是否需要 CEO 升级动作还没有机器可读状态。
- 如果继续增加本地 wrapper，会违反上一轮 final 的提醒：another local-only wrapper should not be counted as OKR movement。
- PR #5 `PRRT_kwDOSWB9286CJ3tX` 仍 unresolved / `is_resolved=false` / `hardware_material_pending`；comment `3269642220` 只是 software-proof reply，不是 reviewer resolution。
- 当前主机没有真实硬件、真实 cloud/4G/OSS/CDN/DB/queue、真实手机/browser、verified terminal result、route/elevator field pass 或 HIL，所以不能把本轮写成完成度提升。

## OKR 映射

| Objective | Current status from `OKR.md` 4.1 | This sprint's relationship |
| --- | --- | --- |
| Objective 5: 云中转 + OSS/CDN 数据通路产品化 | About 68%, still the lowest Objective. Missing real public HTTPS/TLS, 4G/SIM, OSS/CDN live traffic, production DB/queue, production worker/cutover, true phone/browser, and verified terminal delivery/dropoff/cancel result. | Primary target because it is lowest, but no percentage lift is allowed. This sprint only escalates the missing real material response into owner/CEO action status. |
| Objective 1: 硬件协议可信底盘 | About 81%. PR #5 `PRRT_kwDOSWB9286CJ3tX` remains unresolved / hardware_material_pending; no real 2D LiDAR / ToF or WAVE ROVER HIL material exists. | Hardware boundary must remain pending. Hardware Engineer only consults source boundaries and must not change hardware configuration. |
| Objective 2/3/4 | About 99%. Still missing real task record, Nav2/fixed-route runtime, route/elevator field pass, true phone/browser proof, dropoff/cancel completion, and delivery success. | This sprint can ask for those real materials in `next_required_evidence`, but must not claim field pass, phone acceptance, or delivery success. |

## KR 拆解或更新

- KR-A Autonomy / PC evidence gate: create `field_evidence_material_resolution_followup_escalation_status` under `pc-tools/evidence/`, consuming the previous review-handoff summary from `43a3f01` and preserving the review-decision lineage from `a384c84`.
- KR-B Robot diagnostics safe alias: expose `robot_diagnostics_field_evidence_material_resolution_followup_escalation_status_summary` under `onboard/src/ros2_trashbot_behavior/` as read-only diagnostics metadata.
- KR-C Full-Stack mobile/web panel: render a read-only escalation panel under `mobile/web/` that shows pending/overdue/escalated owner action, missing owner response material, and fail-closed proof boundary.
- KR-D Hardware boundary consultation: confirm vendor/PR #5 wording only, anchored by `docs/vendor/VENDOR_INDEX.md` if hardware facts are mentioned; no hardware config changes.
- KR-E Product closeout after implementation: update sprint closeout docs and progress log, review whether `OKR.md` changes are justified, and preserve current percentages unless real materials appear. Expected result: no OKR percentage increase.

## 本轮核心抓手

Build a followup escalation status, not another handoff. The artifact should answer:

- What prior handoff is being followed up?
- What owner response material is missing?
- Is the followup pending, overdue, or escalated?
- Which owner or CEO action is required next?
- Which exact evidence categories must arrive before OKR movement is allowed?
- Which proof boundary and fail-closed flags make this safe to show on Robot diagnostics and mobile/web?

## Product Requirements

The status package must include:

- Capability: `field_evidence_material_resolution_followup_escalation_status`.
- Proof boundary: `software_proof_docker_field_evidence_material_resolution_followup_escalation_status_gate`.
- Source and status: `source=software_proof`, `not_proven`.
- Control flags: `safe_to_control=false`, `delivery_success=false`, `primary_actions_enabled=false`.
- Input trace: previous handoff `43a3f01 Add field evidence resolution handoff gate` and previous review decision `a384c84 Add field evidence resolution review decision`.
- PR/review state: `PRRT_kwDOSWB9286CJ3tQ` resolved, `PRRT_kwDOSWB9286CJ3tU` resolved, `PRRT_kwDOSWB9286CJ3tX` unresolved / `is_resolved=false` / `hardware_material_pending`, and comment `3269642220` as software-proof reply only.
- Escalation fields: `handoff_status`, `followup_status`, `due_status`, `escalation_status`, `owner_response_material_status`, `blocked_reason`, `next_required_evidence`, `owner_action`, `ceo_escalation_recommendation`, safe `evidence_ref`, and phone-safe copy.

The status package must not include:

- Raw credentials, local paths, complete internal logs, checksums, raw JSON artifacts, raw ROS topic dumps, `/cmd_vel`, UART device names, WAVE ROVER parameters, raw vendor material, or GitHub tokens.
- Any claim of real external cloud proof, production DB/queue proof, OSS/CDN live traffic, real phone/browser proof, route/elevator field pass, HIL, verified terminal result, dropoff/cancel completion, delivery success, PR #5 reviewer resolution, or OKR percentage lift.

## Priority And Owner Routing

P0:

- Autonomy Engineer owns the PC evidence CLI/gate because it consumes the field-evidence handoff artifact.
- Robot Platform Engineer owns the diagnostics safe alias because Robot must expose only fail-closed status metadata.
- Full-Stack Engineer owns the mobile/web read-only panel because phone users and support need to see escalation status without control enablement.

P1:

- Hardware Engineer owns read-only vendor/PR #5 boundary consultation. No hardware config changes are expected.
- Product Owner owns closeout docs, OKR/progress log after implementation, and the final decision that no percentage should rise without real evidence.

## 验收口径

- PC evidence gate emits `field_evidence_material_resolution_followup_escalation_status` with `software_proof_docker_field_evidence_material_resolution_followup_escalation_status_gate`.
- Robot and mobile surfaces preserve `source=software_proof`, `not_proven`, `safe_to_control=false`, `delivery_success=false`, and `primary_actions_enabled=false`.
- The status explicitly says owner response material is missing or pending; if no response exists, status must be escalation-ready rather than accepted/successful.
- Mobile/web stays read-only and does not enable Start Delivery, Confirm Dropoff, Cancel, ACK mutation, cursor mutation, diagnostics fetch side effects, or robot command routes.
- Hardware consultation states PR #5 `PRRT_kwDOSWB9286CJ3tX` remains unresolved / hardware_material_pending unless live reviewer evidence changes.
- `OKR.md` percentages remain unchanged unless real external, terminal, field, phone, hardware, HIL, or reviewer-resolution evidence appears.

## Risks, Blockers, And Evidence Chain Gaps

- Risk: this becomes another local wrapper. Mitigation: status must be framed as owner/CEO escalation, not handoff completion or OKR movement.
- Risk: pending owner response looks like review acceptance. Mitigation: require `owner_response_material_status=missing` or equivalent until real material exists.
- Risk: mobile/web copy overpromises. Mitigation: phone-safe copy must use not-proven wording and keep primary actions disabled.
- Risk: PR #5 status drifts. Mitigation: Hardware consultation must call out that `PRRT_kwDOSWB9286CJ3tX` is unresolved and comment `3269642220` is only a software-proof reply.
- Remaining evidence gaps: real public cloud/4G/OSS/CDN/DB/queue, true phone/browser, verified terminal result, route/elevator field pass, real owner response material, WAVE ROVER/UART/HIL, installed/procured/calibrated 2D LiDAR / ToF, and reviewer resolution.

## Sprint Documents To Create Or Update

Planning pass creates:

- `pre_start.md`
- `prd.md`
- `tech-plan.md`

Implementation and closeout must later create or update:

- `tech-done.md`
- `side2side_check.md`
- `final.md`
- `docs/` files touched by implementation owners, if contracts or product surfaces change
- `OKR.md` and `docs/process/okr_progress_log.md` only if closeout evidence justifies the change; expected result is conservative no-percentage-lift wording
