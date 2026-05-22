# Field Evidence Material Resolution Reviewer ACK Review Handoff Tech Plan

Run time: 2026-05-22 19:20 Asia/Shanghai

## Sprint Type

sprint_type: epic

Capability: `field_evidence_material_resolution_reviewer_ack_review_handoff`

Evidence boundary: `software_proof_docker_field_evidence_material_resolution_reviewer_ack_review_handoff_gate`

## Goal

Add the next material-governance rung after reviewer ACK review-decision: a support/field-owner/reviewer handoff package that is visible across PC, Robot diagnostics, and mobile/web while staying Docker-only software proof.

## Architecture

The PC gate is the source of the artifact and redacted summary. Robot diagnostics consumes that summary through a safe alias. Mobile/web consumes the Robot safe summary only and renders a read-only panel. Product closes the sprint after engineers return validation evidence.

All surfaces must preserve `source=software_proof`, `not_proven`, `delivery_success=false`, `primary_actions_enabled=false`, and `safe_to_control=false`.

## OKR 最低优先级核对

1. 当前 `OKR.md` 4.1 完成度最低的 Objective 是 Objective 5，约 68%。Objective 1 约 81%，Objective 2/3/4 约 99%。
2. 本 sprint 不直接推进真实 O5 external proof；它推进 Objective 5 相关证据治理链路的 `field_evidence_material_resolution_reviewer_ack_review_handoff`。
3. 不直接做真实 O5 的理由：本机没有真实 4G/SIM、公网 HTTPS/TLS、OSS/CDN live traffic、production DB/queue、production worker/cutover 或真实手机/browser。继续本地 O5 metadata depth 不能提高 Objective 5；本轮只把已存在的 reviewer ACK review-decision 安全转成可交接 handoff，no OKR percentage lift。
4. PR #5 thread `PRRT_kwDOSWB9286CJ3tX` 仍 unresolved / `hardware_material_pending`；本 sprint 不得写成 PR #5 resolved。

## Owner Tasks

### Task A: Autonomy Owner - PC Handoff Gate

Owner: Autonomy Algorithm Engineer

Allowed files:

- `pc-tools/evidence/field_evidence_material_resolution_reviewer_ack_review_handoff.py`
- `pc-tools/evidence/test_field_evidence_material_resolution_reviewer_ack_review_handoff.py`
- `pc-tools/README.md`
- `docs/interfaces/evidence_contracts.md`

Implementation requirements:

- Create a PC-only CLI gate `field_evidence_material_resolution_reviewer_ack_review_handoff.py`.
- Input should consume the previous `field_evidence_material_resolution_reviewer_ack_review_decision` artifact or summary plus Robot safe summary when useful.
- Output artifact schema should be `trashbot.field_evidence_material_resolution_reviewer_ack_review_handoff.v1`.
- Output summary schema should be `trashbot.field_evidence_material_resolution_reviewer_ack_review_handoff_summary.v1`.
- Preserve a single safe `evidence_ref`.
- Include handoff fields for `handoff_status`, source review decision, reviewer ACK status, field owner handoff, reviewer handoff, support handoff, missing required evidence, rejected/unsafe reasons, next required evidence, and phone-safe copy.
- Reject or fail closed on missing source review-decision, mismatched `evidence_ref`, unsafe raw artifacts, raw paths, credentials, bearer tokens, signed URLs, ROS topics, `/cmd_vel`, serial/UART details, WAVE ROVER details, tracebacks, raw checksums, success/control claims, or any `delivery_success=true`.
- Preserve `source=software_proof`, `not_proven`, `delivery_success=false`, `primary_actions_enabled=false`, and `safe_to_control=false`.
- Update `pc-tools/README.md` and `docs/interfaces/evidence_contracts.md` with the new artifact/summary and non-claim boundary.

Acceptance commands:

```bash
python3 -m py_compile pc-tools/evidence/field_evidence_material_resolution_reviewer_ack_review_handoff.py
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest pc-tools.evidence.test_field_evidence_material_resolution_reviewer_ack_review_handoff
python3 pc-tools/evidence/field_evidence_material_resolution_reviewer_ack_review_handoff.py --help
rg -n "field_evidence_material_resolution_reviewer_ack_review_handoff|software_proof_docker_field_evidence_material_resolution_reviewer_ack_review_handoff_gate|delivery_success=false|safe_to_control=false|primary_actions_enabled=false|not_proven" pc-tools/evidence pc-tools/README.md docs/interfaces/evidence_contracts.md
git diff --check -- pc-tools/evidence/field_evidence_material_resolution_reviewer_ack_review_handoff.py pc-tools/evidence/test_field_evidence_material_resolution_reviewer_ack_review_handoff.py pc-tools/README.md docs/interfaces/evidence_contracts.md
```

### Task B: Robot Owner - Diagnostics Safe Alias

Owner: Robot Platform Engineer

Allowed files:

- `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py`
- `onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`
- `docs/interfaces/operator_gateway_diagnostics.md`

Implementation requirements:

- Add the diagnostics alias `robot_diagnostics_field_evidence_material_resolution_reviewer_ack_review_handoff_summary`.
- Consume the PC summary schema `trashbot.field_evidence_material_resolution_reviewer_ack_review_handoff_summary.v1`.
- Emit a phone-safe summary schema `trashbot.robot_diagnostics_field_evidence_material_resolution_reviewer_ack_review_handoff_summary.v1`.
- Include only sanitized fields: capability, schema, evidence boundary, source, safe `evidence_ref`, `handoff_status`, source review decision, handoff owner hints, missing required evidence, next required evidence, phone-safe copy, and fail-closed flags.
- Do not expose raw artifacts, local paths, credentials, bearer tokens, signed URLs, ROS topics, `/cmd_vel`, serial/UART details, WAVE ROVER details, raw tracebacks, raw checksums, or complete internal logs.
- Preserve `delivery_success=false`, `primary_actions_enabled=false`, `safe_to_control=false`, and `not_proven`.
- Update diagnostics docs with the new alias and proof boundary.

Acceptance commands:

```bash
python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest onboard.src.ros2_trashbot_behavior.test.test_operator_gateway_diagnostics
rg -n "robot_diagnostics_field_evidence_material_resolution_reviewer_ack_review_handoff_summary|field_evidence_material_resolution_reviewer_ack_review_handoff|software_proof_docker_field_evidence_material_resolution_reviewer_ack_review_handoff_gate|delivery_success=false|safe_to_control=false|primary_actions_enabled=false|not_proven" onboard/src/ros2_trashbot_behavior docs/interfaces/operator_gateway_diagnostics.md
git diff --check -- onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py docs/interfaces/operator_gateway_diagnostics.md
```

### Task C: Full-Stack Owner - Mobile/Web Read-Only Panel

Owner: User Touchpoint Full-Stack Engineer

Allowed files:

- `mobile/web/app.js`
- `mobile/web/fixtures/robot_diagnostics_field_evidence_material_resolution_reviewer_ack_review_handoff_summary.json`
- `mobile/web/test_mobile_web_entrypoint.py`
- `docs/product/mobile_user_flow.md`

Implementation requirements:

- Add a read-only mobile/web panel for `field_evidence_material_resolution_reviewer_ack_review_handoff`.
- Prefer `robot_diagnostics_field_evidence_material_resolution_reviewer_ack_review_handoff_summary`; allow compatible summary fallback only if existing local patterns already support it.
- Show only `handoff_status`, source review decision, safe `evidence_ref`, field-owner/reviewer/support handoff hints, missing required evidence, next required evidence, evidence boundary, `software_proof`, `not_proven`, `delivery_success=false`, `primary_actions_enabled=false`, and `safe_to_control=false`.
- Keep Start Delivery, Confirm Dropoff, and Cancel disabled; do not add copy/export controls, ACK/cursor fetch, diagnostics fetch, replay, resubmit, handoff routes, review routes, material routes, or robot command endpoints.
- Do not expose raw JSON, raw review artifacts, raw ACK artifacts, local paths, credentials, bearer tokens, signed URLs, ROS topics, `/cmd_vel`, serial/UART details, WAVE ROVER details, tracebacks, raw checksums, Objective 5 external proof, true phone/browser proof, HIL, route/elevator field pass, dropoff/cancel completion, verified terminal result, or delivery success.
- Add a fixture and focused test coverage.
- Update `docs/product/mobile_user_flow.md` with the new read-only panel and non-claim boundary.

Acceptance commands:

```bash
node --check mobile/web/app.js
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest mobile.web.test_mobile_web_entrypoint
python3 -m json.tool mobile/web/fixtures/robot_diagnostics_field_evidence_material_resolution_reviewer_ack_review_handoff_summary.json
rg -n "field_evidence_material_resolution_reviewer_ack_review_handoff|software_proof_docker_field_evidence_material_resolution_reviewer_ack_review_handoff_gate|delivery_success=false|safe_to_control=false|primary_actions_enabled=false|not true phone/browser|not_proven" mobile/web docs/product/mobile_user_flow.md
git diff --check -- mobile/web/app.js mobile/web/fixtures/robot_diagnostics_field_evidence_material_resolution_reviewer_ack_review_handoff_summary.json mobile/web/test_mobile_web_entrypoint.py docs/product/mobile_user_flow.md
```

### Task D: Product Owner - Post-Implementation Closeout Only

Owner: Product Manager / OKR Owner

Allowed files:

- `sprints/2026.05.22_19-20_field-evidence-material-resolution-reviewer-ack-review-handoff/tech-done.md`
- `sprints/2026.05.22_19-20_field-evidence-material-resolution-reviewer-ack-review-handoff/side2side_check.md`
- `sprints/2026.05.22_19-20_field-evidence-material-resolution-reviewer-ack-review-handoff/final.md`
- `OKR.md`
- `docs/process/okr_progress_log.md`

Implementation requirements:

- Do this task only after Tasks A/B/C return implementation and validation evidence.
- Record actual changed files, validation results, deviations, failures, and remaining risks.
- Keep Objective 5 about 68%, Objective 1 about 81%, Objective 2/3/4 about 99% unless real external, hardware, or field materials arrive.
- Explicitly record no OKR percentage lift for Docker-only software proof.
- Preserve `PRRT_kwDOSWB9286CJ3tX` as unresolved / `hardware_material_pending` unless live GitHub evidence changes.

Acceptance commands:

```bash
test -f sprints/2026.05.22_19-20_field-evidence-material-resolution-reviewer-ack-review-handoff/tech-done.md && test -f sprints/2026.05.22_19-20_field-evidence-material-resolution-reviewer-ack-review-handoff/side2side_check.md && test -f sprints/2026.05.22_19-20_field-evidence-material-resolution-reviewer-ack-review-handoff/final.md
rg -n "field_evidence_material_resolution_reviewer_ack_review_handoff|software_proof_docker_field_evidence_material_resolution_reviewer_ack_review_handoff_gate|Objective 5|no OKR percentage lift|delivery_success=false|safe_to_control=false|primary_actions_enabled=false|not true phone/browser|PRRT_kwDOSWB9286CJ3tX" sprints/2026.05.22_19-20_field-evidence-material-resolution-reviewer-ack-review-handoff OKR.md docs/process/okr_progress_log.md
git diff --check -- sprints/2026.05.22_19-20_field-evidence-material-resolution-reviewer-ack-review-handoff OKR.md docs/process/okr_progress_log.md
```

## Integration Rules

- Tasks A, B, and C are intended for parallel execution by separate owner subagents because their write scopes are distinct.
- Task D must wait for A/B/C evidence and must not be pre-generated during planning.
- If a validation command fails, the owning engineer must inspect the failure, fix root cause within scope, and rerun the focused command.
- Do not revert unrelated worktree changes.

## Non-Claims

This sprint is not PR #5 resolution, not `PRRT_kwDOSWB9286CJ3tX` resolution, not O5 external proof, not public HTTPS/TLS, not 4G/SIM, not OSS/CDN live traffic, not production DB/queue, not worker/cutover, not true phone/browser proof, not O1 HIL, not WAVE ROVER/UART proof, not route/elevator field pass, not Nav2/fixed-route proof, not verified terminal result, not dropoff/cancel completion, not delivery success, and not OKR percentage lift.

## Planning Validation

Run before dispatching implementation:

```bash
test -f sprints/2026.05.22_19-20_field-evidence-material-resolution-reviewer-ack-review-handoff/pre_start.md && test -f sprints/2026.05.22_19-20_field-evidence-material-resolution-reviewer-ack-review-handoff/prd.md && test -f sprints/2026.05.22_19-20_field-evidence-material-resolution-reviewer-ack-review-handoff/tech-plan.md
rg -n "sprint_type: epic|field_evidence_material_resolution_reviewer_ack_review_handoff|software_proof_docker_field_evidence_material_resolution_reviewer_ack_review_handoff_gate|OKR 最低优先级核对|Objective 5|PRRT_kwDOSWB9286CJ3tX|no OKR percentage lift" sprints/2026.05.22_19-20_field-evidence-material-resolution-reviewer-ack-review-handoff
git diff --check -- sprints/2026.05.22_19-20_field-evidence-material-resolution-reviewer-ack-review-handoff
```
