# Field Evidence Material Resolution Reviewer ACK Followup Escalation Status Tech Plan

Run time: 2026-05-22 20:21 Asia/Shanghai

## Sprint Type

sprint_type: epic

Capability: `field_evidence_material_resolution_reviewer_ack_followup_escalation_status`

Evidence boundary: `software_proof_docker_field_evidence_material_resolution_reviewer_ack_followup_escalation_status_gate`

## Goal

Add the next follow-through rung after `field_evidence_material_resolution_reviewer_ack_review_handoff`: a PC -> Robot diagnostics -> mobile/web follow-up escalation status that tells support whether reviewer ACK handoff still needs field-owner action, escalation, or real-material response intake.

All work remains Docker/local `software_proof`; it does not change robot control authorization.

## Architecture

The PC gate is the source of truth for the sanitized artifact and summary. Robot diagnostics consumes that summary and exposes a phone-safe alias. Mobile/web consumes the Robot safe summary and renders a read-only panel. Product closes out only after A/B/C implementation evidence returns.

All surfaces must preserve `source=software_proof`, `not_proven`, `delivery_success=false`, `primary_actions_enabled=false`, and `safe_to_control=false`.

## OKR 最低优先级核对

1. 当前 `OKR.md` 4.1 完成度最低的 Objective 是 Objective 5，约 68%。Objective 1 约 81%，Objective 2/3/4 约 99%。
2. 本 sprint 不直接推进真实 Objective 5 external proof；它推进 Objective 5 相关证据治理链路的 `field_evidence_material_resolution_reviewer_ack_followup_escalation_status`。
3. 不直接做真实 O5 的理由：最新 closeout 明确缺真实 public HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/cutover、真实手机/browser、verified terminal result material 时，不要继续堆 O5 external-proof claim。本机只有 Docker，不能产出这些真实材料。
4. 下一低项 Objective 1 约 81%，但 PR #5 `PRRT_kwDOSWB9286CJ3tX` 仍 `is_resolved=false` / `hardware_material_pending`；`PRRT_kwDOSWB9286CJ3tQ` 与 `PRRT_kwDOSWB9286CJ3tU` 已 resolved。本 sprint 不得写成 O1 HIL、PR #5 resolved、真实 2D LiDAR / ToF material ready 或 OKR percentage lift。

## Owner Tasks

### Task A: Autonomy Owner - PC Followup Escalation Status Gate

Owner: Autonomy Algorithm Engineer

Allowed files:

- `pc-tools/evidence/field_evidence_material_resolution_reviewer_ack_followup_escalation_status.py`
- focused unittest for the gate
- `pc-tools/README.md`
- `docs/interfaces/evidence_contracts.md`

Implementation requirements:

- Add a PC-only CLI gate named `field_evidence_material_resolution_reviewer_ack_followup_escalation_status.py`.
- Consume the prior `field_evidence_material_resolution_reviewer_ack_review_handoff` artifact/summary and optional Robot safe alias when useful.
- Emit artifact schema `trashbot.field_evidence_material_resolution_reviewer_ack_followup_escalation_status.v1`.
- Emit summary schema `trashbot.field_evidence_material_resolution_reviewer_ack_followup_escalation_status_summary.v1`.
- Preserve the same safe `evidence_ref` from reviewer ACK review-handoff.
- Include safe fields for `followup_status`, `due_status`, `source_handoff_status`, reviewer ACK status, field owner handoff, support escalation owner, missing required evidence, rejected/unsafe reasons, next required evidence, and phone-safe copy.
- Recommended status vocabulary: `owner_response_pending_not_proven`, `owner_response_overdue_escalate_not_proven`, `blocked_missing_required_materials_not_proven`, `blocked_unsafe_material_claims_not_proven`, `accepted_for_owner_response_intake_not_proven`, and `blocked_missing_reviewer_ack_handoff_not_proven`.
- Reject or fail closed on missing source handoff, mismatched `evidence_ref`, unsafe raw artifacts, raw paths, credentials, bearer tokens, signed URLs, ROS topics, `/cmd_vel`, serial/UART details, WAVE ROVER details, tracebacks, raw checksums, success/control claims, true phone/browser claims, Objective 5 external-proof claims, or any `delivery_success=true`.
- Preserve `source=software_proof`, `not_proven`, `delivery_success=false`, `primary_actions_enabled=false`, and `safe_to_control=false`.
- Update `pc-tools/README.md` and `docs/interfaces/evidence_contracts.md` with schema, status vocabulary, and non-claim boundary.

Acceptance commands:

```bash
python3 -m py_compile pc-tools/evidence/field_evidence_material_resolution_reviewer_ack_followup_escalation_status.py
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest pc-tools.evidence.test_field_evidence_material_resolution_reviewer_ack_followup_escalation_status
python3 pc-tools/evidence/field_evidence_material_resolution_reviewer_ack_followup_escalation_status.py --help
rg -n "field_evidence_material_resolution_reviewer_ack_followup_escalation_status|software_proof_docker_field_evidence_material_resolution_reviewer_ack_followup_escalation_status_gate|delivery_success=false|safe_to_control=false|primary_actions_enabled=false|not_proven" pc-tools/evidence pc-tools/README.md docs/interfaces/evidence_contracts.md
git diff --check -- pc-tools/evidence/field_evidence_material_resolution_reviewer_ack_followup_escalation_status.py pc-tools/evidence/test_field_evidence_material_resolution_reviewer_ack_followup_escalation_status.py pc-tools/README.md docs/interfaces/evidence_contracts.md
```

### Task B: Robot Owner - Diagnostics Safe Summary Alias

Owner: Robot Platform Engineer

Allowed files:

- `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py`
- focused diagnostics test
- `docs/interfaces/operator_gateway_diagnostics.md`

Implementation requirements:

- Add diagnostics alias `robot_diagnostics_field_evidence_material_resolution_reviewer_ack_followup_escalation_status_summary`.
- Consume PC summary schema `trashbot.field_evidence_material_resolution_reviewer_ack_followup_escalation_status_summary.v1`.
- Emit phone-safe summary schema `trashbot.robot_diagnostics_field_evidence_material_resolution_reviewer_ack_followup_escalation_status_summary.v1`.
- Include only sanitized fields: capability, schema, evidence boundary, source, safe `evidence_ref`, `followup_status`, `due_status`, source handoff status, owner handoff hints, missing required evidence, next required evidence, phone-safe copy, and fail-closed flags.
- Do not expose raw artifacts, local paths, credentials, bearer tokens, signed URLs, ROS topics, `/cmd_vel`, serial/UART details, WAVE ROVER details, raw tracebacks, raw checksums, complete internal logs, success claims, or control permissions.
- Preserve `delivery_success=false`, `primary_actions_enabled=false`, `safe_to_control=false`, and `not_proven`.
- Update `docs/interfaces/operator_gateway_diagnostics.md` with the alias and proof boundary.

Acceptance commands:

```bash
python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest onboard.src.ros2_trashbot_behavior.test.test_operator_gateway_diagnostics
rg -n "robot_diagnostics_field_evidence_material_resolution_reviewer_ack_followup_escalation_status_summary|field_evidence_material_resolution_reviewer_ack_followup_escalation_status|software_proof_docker_field_evidence_material_resolution_reviewer_ack_followup_escalation_status_gate|delivery_success=false|safe_to_control=false|primary_actions_enabled=false|not_proven" onboard/src/ros2_trashbot_behavior docs/interfaces/operator_gateway_diagnostics.md
git diff --check -- onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py docs/interfaces/operator_gateway_diagnostics.md
```

### Task C: Full-Stack Owner - Mobile/Web Read-Only Panel And Fixture

Owner: User Touchpoint Full-Stack Engineer

Allowed files:

- `mobile/web/app.js`
- `mobile/web/test_mobile_web_entrypoint.py`
- fixture JSON for `field_evidence_material_resolution_reviewer_ack_followup_escalation_status`
- `docs/product/mobile_user_flow.md`

Implementation requirements:

- Add a read-only mobile/web panel for `field_evidence_material_resolution_reviewer_ack_followup_escalation_status`.
- Prefer `robot_diagnostics_field_evidence_material_resolution_reviewer_ack_followup_escalation_status_summary`; allow compatible summary fallback only if existing local patterns already support it.
- Show only `followup_status`, `due_status`, source handoff status, safe `evidence_ref`, field-owner/support escalation hints, missing required evidence, next required evidence, evidence boundary, `software_proof`, `not_proven`, `delivery_success=false`, `primary_actions_enabled=false`, and `safe_to_control=false`.
- Keep Start Delivery, Confirm Dropoff, and Cancel disabled.
- Do not add copy/export controls, ACK/cursor fetch, diagnostics fetch, replay, resubmit, handoff routes, review routes, material routes, owner-response routes, or robot command endpoints.
- Do not expose raw JSON, raw handoff artifacts, raw ACK artifacts, local paths, credentials, bearer tokens, signed URLs, ROS topics, `/cmd_vel`, serial/UART details, WAVE ROVER details, tracebacks, raw checksums, Objective 5 external proof, true phone/browser proof, HIL, route/elevator field pass, dropoff/cancel completion, verified terminal result, or delivery success.
- Add a safe fixture JSON and focused test coverage.
- Update `docs/product/mobile_user_flow.md` with the new read-only panel and non-claim boundary, including `not true phone/browser`.

Acceptance commands:

```bash
node --check mobile/web/app.js
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest mobile.web.test_mobile_web_entrypoint
python3 -m json.tool mobile/web/fixtures/robot_diagnostics_field_evidence_material_resolution_reviewer_ack_followup_escalation_status_summary.json
rg -n "field_evidence_material_resolution_reviewer_ack_followup_escalation_status|software_proof_docker_field_evidence_material_resolution_reviewer_ack_followup_escalation_status_gate|delivery_success=false|safe_to_control=false|primary_actions_enabled=false|not true phone/browser|not_proven" mobile/web docs/product/mobile_user_flow.md
git diff --check -- mobile/web/app.js mobile/web/fixtures/robot_diagnostics_field_evidence_material_resolution_reviewer_ack_followup_escalation_status_summary.json mobile/web/test_mobile_web_entrypoint.py docs/product/mobile_user_flow.md
```

### Task D: Product Owner - Post-Implementation Closeout Only

Owner: Product Manager / OKR Owner

Allowed files after A/B/C finish:

- `sprints/2026.05.22_20-21_field-evidence-material-resolution-reviewer-ack-followup-escalation-status/tech-done.md`
- `sprints/2026.05.22_20-21_field-evidence-material-resolution-reviewer-ack-followup-escalation-status/side2side_check.md`
- `sprints/2026.05.22_20-21_field-evidence-material-resolution-reviewer-ack-followup-escalation-status/final.md`
- `OKR.md`
- `docs/process/okr_progress_log.md`

Implementation requirements:

- Do this task only after Tasks A/B/C return actual implementation and validation evidence.
- Record changed files, validation results, failures, deviations, and remaining risks.
- Keep Objective 5 about 68%, Objective 1 about 81%, Objective 2/3/4 about 99% unless real external, hardware, phone/browser, field, or verified terminal result materials arrive.
- Preserve `PRRT_kwDOSWB9286CJ3tX` as unresolved / `hardware_material_pending` unless live GitHub evidence changes.
- Record explicitly that `software_proof_docker_field_evidence_material_resolution_reviewer_ack_followup_escalation_status_gate` is not true phone/browser proof and not delivery success.

Acceptance commands:

```bash
test -f sprints/2026.05.22_20-21_field-evidence-material-resolution-reviewer-ack-followup-escalation-status/tech-done.md && test -f sprints/2026.05.22_20-21_field-evidence-material-resolution-reviewer-ack-followup-escalation-status/side2side_check.md && test -f sprints/2026.05.22_20-21_field-evidence-material-resolution-reviewer-ack-followup-escalation-status/final.md
rg -n "field_evidence_material_resolution_reviewer_ack_followup_escalation_status|software_proof_docker_field_evidence_material_resolution_reviewer_ack_followup_escalation_status_gate|Objective 5|no OKR percentage lift|delivery_success=false|safe_to_control=false|primary_actions_enabled=false|not true phone/browser|PRRT_kwDOSWB9286CJ3tX" sprints/2026.05.22_20-21_field-evidence-material-resolution-reviewer-ack-followup-escalation-status OKR.md docs/process/okr_progress_log.md
git diff --check -- sprints/2026.05.22_20-21_field-evidence-material-resolution-reviewer-ack-followup-escalation-status OKR.md docs/process/okr_progress_log.md
```

## Integration Rules

- Tasks A, B, and C must be dispatched in parallel because their write scopes are distinct.
- Task D must wait for A/B/C evidence and must not be pre-generated during planning.
- If a validation command fails, the owning engineer must inspect the failure, fix root cause within scope, and rerun the focused command.
- Do not run broad suites; use only fenced validation.
- Do not revert unrelated worktree changes.

## Non-Claims

This sprint is not PR #5 resolution, not `PRRT_kwDOSWB9286CJ3tX` resolution, not Objective 5 external proof, not public HTTPS/TLS, not 4G/SIM, not OSS/CDN live traffic, not production DB/queue, not worker/cutover, not true phone/browser proof, not O1 HIL, not WAVE ROVER/UART proof, not route/elevator field pass, not Nav2/fixed-route proof, not verified terminal result, not dropoff/cancel completion, not delivery success, and not OKR percentage lift.

## Planning Validation

Run before dispatching implementation:

```bash
test -f sprints/2026.05.22_20-21_field-evidence-material-resolution-reviewer-ack-followup-escalation-status/pre_start.md && test -f sprints/2026.05.22_20-21_field-evidence-material-resolution-reviewer-ack-followup-escalation-status/prd.md && test -f sprints/2026.05.22_20-21_field-evidence-material-resolution-reviewer-ack-followup-escalation-status/tech-plan.md
rg -n "field_evidence_material_resolution_reviewer_ack_followup_escalation_status|sprint_type: epic|OKR 最低优先级核对|Objective 5|PRRT_kwDOSWB9286CJ3tX|software_proof|not true phone/browser|delivery_success=false|primary_actions_enabled=false|safe_to_control=false" sprints/2026.05.22_20-21_field-evidence-material-resolution-reviewer-ack-followup-escalation-status
git diff --check -- sprints/2026.05.22_20-21_field-evidence-material-resolution-reviewer-ack-followup-escalation-status
```
