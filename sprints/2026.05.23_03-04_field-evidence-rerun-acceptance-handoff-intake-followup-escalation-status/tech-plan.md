# Field Evidence Rerun Acceptance Handoff Intake Follow-Up Escalation Status Tech Plan

Run time: 2026-05-23 03:04 Asia/Shanghai

> For implementation workers: use subagent-driven development. This sprint has 3 parallel Engineer owners with disjoint file scopes, plus Product closeout after implementation. The main session must not write product code, tests, hardware config, or runtime implementation.

## Goal

Build `field_evidence_rerun_execution_result_acceptance_handoff_intake_followup_escalation_status`, the follow-up escalation status after `field_evidence_rerun_execution_result_acceptance_handoff_intake_review_handoff`.

The implementation must produce only `software_proof_docker_field_evidence_rerun_execution_result_acceptance_handoff_intake_followup_escalation_status_gate` evidence and must keep `source=software_proof`, `software_proof`, `not_proven`, `safe_to_control=false`, `delivery_success=false`, and `primary_actions_enabled=false`.

## Architecture

- Autonomy owns the PC-only follow-up escalation status gate that consumes the previous safe review-handoff output plus a safe follow-up policy and emits a sanitized owner/support/reviewer due-status artifact.
- Robot owns the operator gateway diagnostics alias that exposes only safe follow-up escalation metadata and fails closed.
- Full-Stack owns the mobile/web read-only panel that shows follow-up escalation status without enabling primary actions.
- Product owns post-implementation closeout only after the three Engineer streams return evidence.

## OKR 最低优先级核对

- 当前 `OKR.md` 4.1 节完成度最低的 Objective：Objective 5，约 68%。
- 本 sprint 是否针对该最低 Objective：不是直接针对 Objective 5，也不提升 Objective 5。
- 不针对 Objective 5 的理由：当前本机只有 Docker/local，没有真实 public HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/cutover、真实 phone/browser 或 verified terminal result materials；继续本地 O5 metadata depth 会重复消费同一外部材料 blocker。
- 当前下一低项 Objective 1 约 81%，但真实 WAVE ROVER/UART/HIL、2D LiDAR/ToF SKU/source/receipt、operator HIL report 和 PR #5 reviewer resolution 仍缺失。Live PR #5 evidence：`PRRT_kwDOSWB9286CJ3tQ` resolved，`PRRT_kwDOSWB9286CJ3tU` resolved，`PRRT_kwDOSWB9286CJ3tX` unresolved / `is_resolved=false` / `hardware_material_pending`；comment `3269642220` 只是 software-proof reply，不是 reviewer resolution。
- 因 O5 真实外部材料不可用、O1 真实硬件材料/PR thread 不可用，本 sprint 推进 Objective 2 / Objective 3 / Objective 4 的 field-evidence acceptance handoff intake follow-up escalation status：它只把 safe review handoff 转成 owner/support/reviewer due-status / escalation packet。
- `final.md` 收口时必须复核：如果没有真实 O5 external proof、真实 O1 hardware/HIL material、PR #5 resolution、真实 route/elevator pass、真实 phone/browser 或 verified terminal result，`OKR.md` 不得提高百分比。

## Shared Contract

All owners must preserve these fields and wording:

- `field_evidence_rerun_execution_result_acceptance_handoff_intake_followup_escalation_status`
- `software_proof_docker_field_evidence_rerun_execution_result_acceptance_handoff_intake_followup_escalation_status_gate`
- Previous capability: `field_evidence_rerun_execution_result_acceptance_handoff_intake_review_handoff`
- Previous boundary: `software_proof_docker_field_evidence_rerun_execution_result_acceptance_handoff_intake_review_handoff_gate`
- `source=software_proof`
- `software_proof`
- `not_proven`
- `safe_to_control=false`
- `delivery_success=false`
- `primary_actions_enabled=false`
- Same safe `evidence_ref`
- PR #5 `PRRT_kwDOSWB9286CJ3tX` remains `is_resolved=false` / `hardware_material_pending`
- Threads `PRRT_kwDOSWB9286CJ3tQ` and `PRRT_kwDOSWB9286CJ3tU` are resolved, but they do not close the pending hardware material thread.

Allowed follow-up escalation states:

- `pending`
- `overdue`
- `escalated`
- `blocked`

Required owner/support/reviewer follow-up checklist:

- true task record
- true Nav2/fixed-route runtime log
- route completion signal
- true elevator door state
- target floor confirmation
- human assistance record
- dropoff/cancel completion or delivery result
- true route/elevator field pass
- true phone/browser evidence
- PR #5 hardware material remains pending unless `PRRT_kwDOSWB9286CJ3tX` is live resolved

Forbidden claims:

- real HIL
- WAVE ROVER/UART proof
- real route/elevator field pass
- real Nav2/fixed-route runtime pass
- real phone/browser proof
- Objective 5 external proof
- verified terminal result
- dropoff/cancel completion
- `delivery_success=true`
- PR #5 reviewer resolution

Forbidden exposure:

- raw ROS topics, `/cmd_vel`, serial/UART paths, baudrate values, WAVE ROVER parameters
- credentials, bearer tokens, Authorization headers, OSS AK/SK, DB/queue URLs
- raw artifacts, complete artifacts, local paths, checksums, tracebacks
- success phrasing, control-enable copy, or hidden primary-action enablement

## Parallel Owner Plan

### Task A: Autonomy PC-Only Follow-Up Escalation Status Gate + Tests + Evidence Docs

Role id: `autonomy-engineer`

Files:

- Create: `pc-tools/evidence/field_evidence_rerun_execution_result_acceptance_handoff_intake_followup_escalation_status.py`
- Create: `pc-tools/evidence/test_field_evidence_rerun_execution_result_acceptance_handoff_intake_followup_escalation_status.py`
- Modify: `pc-tools/README.md`
- Modify: `docs/interfaces/evidence_contracts.md`

Interface impact:

- Adds a PC-only evidence artifact and summary contract. It must not alter ROS2 runtime APIs, cloud APIs, mobile command endpoints, hardware parameters, or existing evidence gate outputs.

Responsibilities:

1. Implement a CLI gate that accepts the previous acceptance handoff intake review handoff artifact, summary, or Robot diagnostics safe alias plus a safe follow-up policy.
2. Require the previous safe output to include `field_evidence_rerun_execution_result_acceptance_handoff_intake_review_handoff`, the same safe `evidence_ref`, and the boundary `software_proof_docker_field_evidence_rerun_execution_result_acceptance_handoff_intake_review_handoff_gate`.
3. Emit status `pending`, `overdue`, `escalated`, or `blocked` only when the prior review handoff is safe, the follow-up packet is safe, same-`evidence_ref` matches, and no unsafe copy, success claim, control-enable state, credentials, raw artifact exposure, external-proof claim, HIL claim, or PR #5 resolution claim appears.
4. Fail closed to `blocked` with structured reasons for missing review handoff, missing required material, evidence-ref mismatch, unsafe copy, or forbidden proof/control claims.
5. Emit only safe summary fields for Robot/mobile and keep `source=software_proof`, `software_proof`, `not_proven`, `safe_to_control=false`, `delivery_success=false`, and `primary_actions_enabled=false`.
6. Add targeted tests for pending, overdue, escalated, blocked missing review handoff, evidence-ref mismatch, and unsafe/success claim rejection.

Risk boundary:

- This gate can package safe follow-up status only. It must not read or validate raw field logs as true proof, must not claim route/elevator pass, and must not unblock controls.

Acceptance commands:

```bash
python3 -m py_compile pc-tools/evidence/field_evidence_rerun_execution_result_acceptance_handoff_intake_followup_escalation_status.py
python3 -m unittest pc-tools/evidence/test_field_evidence_rerun_execution_result_acceptance_handoff_intake_followup_escalation_status.py
python3 pc-tools/evidence/field_evidence_rerun_execution_result_acceptance_handoff_intake_followup_escalation_status.py --help
rg -n "field_evidence_rerun_execution_result_acceptance_handoff_intake_followup_escalation_status|software_proof_docker_field_evidence_rerun_execution_result_acceptance_handoff_intake_followup_escalation_status_gate|source=software_proof|not_proven|delivery_success=false|primary_actions_enabled=false|safe_to_control=false|pending|overdue|escalated|blocked" pc-tools/evidence/field_evidence_rerun_execution_result_acceptance_handoff_intake_followup_escalation_status.py pc-tools/evidence/test_field_evidence_rerun_execution_result_acceptance_handoff_intake_followup_escalation_status.py pc-tools/README.md docs/interfaces/evidence_contracts.md
git diff --check -- pc-tools/evidence/field_evidence_rerun_execution_result_acceptance_handoff_intake_followup_escalation_status.py pc-tools/evidence/test_field_evidence_rerun_execution_result_acceptance_handoff_intake_followup_escalation_status.py pc-tools/README.md docs/interfaces/evidence_contracts.md
```

### Task B: Robot Diagnostics Safe Alias + Tests + Diagnostics Docs

Role id: `robot-software-engineer`

Files:

- Modify: `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py`
- Modify: `onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`
- Modify: `docs/interfaces/ros_runtime_contracts.md`

Interface impact:

- Adds a diagnostics safe alias for existing operator-gateway summary surfaces. It must not add robot commands, change task_orchestrator semantics, expose ROS topics, or change primary action authorization.

Responsibilities:

1. Add Robot diagnostics support for `field_evidence_rerun_execution_result_acceptance_handoff_intake_followup_escalation_status` safe summary.
2. Expose a safe alias such as `robot_diagnostics_field_evidence_rerun_execution_result_acceptance_handoff_intake_followup_escalation_status_summary`.
3. Preserve fail-closed defaults when the summary is missing, malformed, unsupported, unsafe, or contains success/control/external-proof/HIL/PR-resolution wording.
4. Expose only follow-up status, source review handoff status, safe `evidence_ref`, pending/overdue/escalated/blocked reasons, missing required material refs, owner/support/reviewer next step, evidence boundary, `software_proof`, `not_proven`, `source=software_proof`, `safe_to_control=false`, `delivery_success=false`, and `primary_actions_enabled=false`.
5. Do not expose raw manifest contents, local paths, checksums, tracebacks, ROS topics, `/cmd_vel`, serial/UART details, WAVE ROVER details, credentials, DB/queue URLs, or complete artifacts.
6. Add targeted diagnostics tests without broad unrelated regression sweeps.

Risk boundary:

- Diagnostics must remain read-only support metadata. Follow-up statuses are not real delivery/dropoff/cancel proof and must not enable Start/Confirm/Cancel.

Acceptance commands:

```bash
python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py
python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py
rg -n "field_evidence_rerun_execution_result_acceptance_handoff_intake_followup_escalation_status|software_proof_docker_field_evidence_rerun_execution_result_acceptance_handoff_intake_followup_escalation_status_gate|source=software_proof|not_proven|delivery_success=false|primary_actions_enabled=false|safe_to_control=false|pending|overdue|escalated|blocked" onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py docs/interfaces/ros_runtime_contracts.md
git diff --check -- onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py docs/interfaces/ros_runtime_contracts.md
```

### Task C: Full-Stack Mobile/Web Read-Only Panel + Fixture + Tests + Mobile Docs

Role id: `full-stack-software-engineer`

Files:

- Modify: `mobile/web/app.js`
- Create: `mobile/web/fixtures/robot_diagnostics_field_evidence_rerun_execution_result_acceptance_handoff_intake_followup_escalation_status.json`
- Modify: `mobile/web/test_mobile_web_entrypoint.py`
- Modify: `docs/product/mobile_user_flow.md`

Interface impact:

- Adds one read-only mobile panel that consumes existing status/diagnostics summaries. It must not add fetch routes, command routes, ACK/cursor routes, material upload routes, review routes, handoff routes, follow-up routes, or hidden action enablement.

Responsibilities:

1. Add a read-only “现场证据复跑执行结果验收交接回执跟进升级状态” panel for `field_evidence_rerun_execution_result_acceptance_handoff_intake_followup_escalation_status`.
2. Consume `robot_diagnostics_field_evidence_rerun_execution_result_acceptance_handoff_intake_followup_escalation_status_summary` first, then compatible safe summaries from existing status/diagnostics shapes.
3. Show only follow-up status, source review handoff status, safe `evidence_ref`, missing required material refs, pending/overdue/escalated/blocked reasons, owner/support/reviewer next step, evidence boundary, `source=software_proof`, `software_proof`, `not_proven`, `safe_to_control=false`, `delivery_success=false`, and `primary_actions_enabled=false`.
4. Keep Start Delivery, Confirm Dropoff, and Cancel disabled under the fixture.
5. Do not fetch raw artifacts, raw diagnostics, ACK/cursor routes, material routes, callback routes, review routes, handoff routes, follow-up routes, Start/Confirm/Cancel endpoints, or robot command endpoints from this panel.
6. Add a fixture and targeted mobile test for render, fail-closed controls, redaction boundaries, and no success/control copy.

Risk boundary:

- The panel is support-facing read-only status. It must not turn a follow-up escalation into true phone/browser proof, field pass, delivery success, verified terminal result, or control permission.

Acceptance commands:

```bash
node --check mobile/web/app.js
python3 -m json.tool mobile/web/fixtures/robot_diagnostics_field_evidence_rerun_execution_result_acceptance_handoff_intake_followup_escalation_status.json >/tmp/field_evidence_rerun_execution_result_acceptance_handoff_intake_followup_escalation_status_fixture.json
python3 -m unittest mobile/web/test_mobile_web_entrypoint.py
rg -n "field_evidence_rerun_execution_result_acceptance_handoff_intake_followup_escalation_status|software_proof_docker_field_evidence_rerun_execution_result_acceptance_handoff_intake_followup_escalation_status_gate|source=software_proof|not_proven|delivery_success=false|primary_actions_enabled=false|safe_to_control=false|pending|overdue|escalated|blocked" mobile/web/app.js mobile/web/fixtures/robot_diagnostics_field_evidence_rerun_execution_result_acceptance_handoff_intake_followup_escalation_status.json mobile/web/test_mobile_web_entrypoint.py docs/product/mobile_user_flow.md
git diff --check -- mobile/web/app.js mobile/web/fixtures/robot_diagnostics_field_evidence_rerun_execution_result_acceptance_handoff_intake_followup_escalation_status.json mobile/web/test_mobile_web_entrypoint.py docs/product/mobile_user_flow.md
```

### Task D: Product Closeout After A/B/C

Role id: `product-okr-owner`

Files:

- Create or modify: `sprints/2026.05.23_03-04_field-evidence-rerun-acceptance-handoff-intake-followup-escalation-status/tech-done.md`
- Create or modify: `sprints/2026.05.23_03-04_field-evidence-rerun-acceptance-handoff-intake-followup-escalation-status/side2side_check.md`
- Create or modify: `sprints/2026.05.23_03-04_field-evidence-rerun-acceptance-handoff-intake-followup-escalation-status/final.md`
- Modify: `OKR.md`
- Modify: `docs/process/okr_progress_log.md`

Interface impact:

- Product closeout updates sprint evidence and OKR/progress narrative only. It must not modify product code, tests, hardware configuration, mobile runtime, PC gates, or Robot diagnostics implementation.

Responsibilities:

1. Integrate the three Engineer reports and record actual changed files, validation results, deviations, and remaining risks.
2. Confirm A/B/C docs updates landed under `docs/interfaces/` and `docs/product/`.
3. Keep `OKR.md` conservative: Objective 5 remains around 68% unless real O5 external evidence appears; Objective 1 remains around 81% unless real PR #5/hardware/HIL material appears; Objectives 2/3/4 remain unchanged unless real field/mobile/delivery evidence appears.
4. Write final closeout so this sprint is accepted only as `software_proof_docker_field_evidence_rerun_execution_result_acceptance_handoff_intake_followup_escalation_status_gate`.
5. Explicitly state that PR #5 `PRRT_kwDOSWB9286CJ3tX` remains unresolved unless a live reviewer resolution is present.
6. Preserve `delivery_success=false`, `primary_actions_enabled=false`, `safe_to_control=false`, `not_proven`, and no real route/elevator/phone/HIL/O5 claims.

Risk boundary:

- Product closeout may document readiness and no-lift status only. It must not raise OKR completion or imply real field acceptance unless real materials are present.

Acceptance commands:

```bash
test -f sprints/2026.05.23_03-04_field-evidence-rerun-acceptance-handoff-intake-followup-escalation-status/tech-done.md && test -f sprints/2026.05.23_03-04_field-evidence-rerun-acceptance-handoff-intake-followup-escalation-status/side2side_check.md && test -f sprints/2026.05.23_03-04_field-evidence-rerun-acceptance-handoff-intake-followup-escalation-status/final.md
rg -n "software_proof_docker_field_evidence_rerun_execution_result_acceptance_handoff_intake_followup_escalation_status_gate|Objective 5|Objective 1|Objective 2|Objective 3|Objective 4|PRRT_kwDOSWB9286CJ3tX|delivery_success=false|primary_actions_enabled=false|safe_to_control=false|not_proven" sprints/2026.05.23_03-04_field-evidence-rerun-acceptance-handoff-intake-followup-escalation-status OKR.md docs/process/okr_progress_log.md
git diff --check -- sprints/2026.05.23_03-04_field-evidence-rerun-acceptance-handoff-intake-followup-escalation-status OKR.md docs/process/okr_progress_log.md
```

## Dispatch Requirements

Implementation must start 3 parallel Engineer workers in one dispatch set:

- Autonomy Algorithm Engineer for PC evidence follow-up escalation status gate files.
- Robot Platform Engineer for diagnostics/runtime contract files.
- User Touchpoint Full-Stack Engineer for mobile/web files.

Product closeout starts only after the three Engineer workers return. If any owner fails validation, send the failure back to the same owner before closeout.

## Planning Validation Commands

The Product Owner planning task must run:

```bash
test -f sprints/2026.05.23_03-04_field-evidence-rerun-acceptance-handoff-intake-followup-escalation-status/pre_start.md && test -f sprints/2026.05.23_03-04_field-evidence-rerun-acceptance-handoff-intake-followup-escalation-status/prd.md && test -f sprints/2026.05.23_03-04_field-evidence-rerun-acceptance-handoff-intake-followup-escalation-status/tech-plan.md
rg -n "sprint_type: epic|OKR 最低优先级核对|Objective 5|PRRT_kwDOSWB9286CJ3tX|field_evidence_rerun_execution_result_acceptance_handoff_intake_followup_escalation_status|software_proof|not_proven|delivery_success=false|safe_to_control=false" sprints/2026.05.23_03-04_field-evidence-rerun-acceptance-handoff-intake-followup-escalation-status
git diff --check -- sprints/2026.05.23_03-04_field-evidence-rerun-acceptance-handoff-intake-followup-escalation-status
```
