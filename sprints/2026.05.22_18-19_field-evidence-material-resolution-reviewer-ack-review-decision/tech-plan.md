# Field Evidence Material Resolution Reviewer ACK Review Decision Tech Plan

Run time: 2026-05-22 18:19 Asia/Shanghai

## Scope

Implement `field_evidence_material_resolution_reviewer_ack_review_decision` as a cross-owner Epic sprint. This is a software-proof reviewer ACK review-decision gate after `field_evidence_material_resolution_reviewer_ack_intake`.

Required boundary:

- `software_proof_docker_field_evidence_material_resolution_reviewer_ack_review_decision_gate`
- `source=software_proof`
- `not_proven`
- `delivery_success=false`
- `safe_to_control=false`
- `primary_actions_enabled=false`
- no OKR percentage lift

## OKR 最低优先级核对

当前 `OKR.md` 4.1 中完成度最低的是 Objective 5，约 68%。Objective 5 的主要缺口仍是真实 public HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/cutover、true phone/browser 和 verified terminal result material。

本 sprint 不直接针对 Objective 5 external proof。理由：当前主机只有 Docker，本轮没有真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/cutover、true phone/browser 或 verified terminal result material，继续添加 O5 本地 wrapper 会重复消费同一类 blocker，无法形成 OKR percentage lift。

本 sprint 针对当前可推进的 field-evidence material-resolution chain：最近 `2026.05.22_16-17_field-evidence-material-resolution-reviewer-ack-intake` 已完成 reviewer/support/field-owner ACK intake；下一步应推进 `field_evidence_material_resolution_reviewer_ack_review_decision`。该 sprint 只产出 software-proof/not_proven 决策，不提升 Objective 5、Objective 1 或其他 Objective 百分比。

## Product Requirements

The decision gate must classify reviewer ACK intake into phone-safe decisions. Suggested decision names:

- `accepted_for_material_review_not_proven`
- `needs_reassignment_not_proven`
- `needs_field_owner_supplement_not_proven`
- `rejected_unsafe_ack_not_proven`
- `blocked_missing_reviewer_ack_intake_not_proven`

All summaries must avoid raw artifacts, local paths, credentials, ROS topic names, `/cmd_vel`, serial/UART details, baudrate values, WAVE ROVER parameters, DB/queue URLs, OSS AK/SK, checksums, complete artifacts, tracebacks, and success claims.

## Task Split

### Task A: Autonomy Owner

Role: `autonomy-engineer`

Allowed files:

- `pc-tools/evidence/field_evidence_material_resolution_reviewer_ack_review_decision.py`
- focused unittest for the gate under the existing `pc-tools` test pattern
- `pc-tools/README.md`
- `docs/interfaces/evidence_contracts.md`

Implementation requirements:

- Add a PC evidence gate that consumes reviewer ACK intake safe summary/artifact inputs.
- Emit a safe decision artifact and summary with `capability=field_evidence_material_resolution_reviewer_ack_review_decision`.
- Preserve `source=software_proof`, `not_proven`, `delivery_success=false`, `safe_to_control=false`, `primary_actions_enabled=false`.
- Cover accepted, reassignment, field-owner supplement, unsafe ACK, and missing intake branches.
- Keep comments in Chinese for new code comments and maintain the project comment-quality requirement.

Acceptance commands:

```bash
python3 -m py_compile pc-tools/evidence/field_evidence_material_resolution_reviewer_ack_review_decision.py
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest <focused_autonomy_unittest_module>
rg -n "field_evidence_material_resolution_reviewer_ack_review_decision|software_proof_docker_field_evidence_material_resolution_reviewer_ack_review_decision_gate|accepted_for_material_review_not_proven|needs_reassignment_not_proven|needs_field_owner_supplement_not_proven|rejected_unsafe_ack_not_proven|blocked_missing_reviewer_ack_intake_not_proven" pc-tools docs/interfaces
git diff --check -- pc-tools/evidence/field_evidence_material_resolution_reviewer_ack_review_decision.py pc-tools/README.md docs/interfaces/evidence_contracts.md <focused_autonomy_unittest_file>
```

### Task B: Robot Owner

Role: `robot-software-engineer`

Allowed files:

- Robot diagnostics/status summary files that currently host safe aliases
- focused diagnostics unittest
- `docs/interfaces/operator_gateway_diagnostics.md`

Required alias:

- `robot_diagnostics_field_evidence_material_resolution_reviewer_ack_review_decision_summary`

Implementation requirements:

- Add a diagnostics safe alias that exposes only phone-safe reviewer ACK review-decision summary fields.
- Keep all control fields fail-closed: `delivery_success=false`, `safe_to_control=false`, `primary_actions_enabled=false`.
- Do not expose raw ACK artifacts, complete artifact contents, local paths, low-level robot controls, serial/UART details, WAVE ROVER parameters, credentials, checksums, or tracebacks.
- Keep comments in Chinese for new code comments and maintain the project comment-quality requirement.

Acceptance commands:

```bash
python3 -m py_compile <touched_robot_diagnostics_files>
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest <focused_robot_diagnostics_unittest_module>
rg -n "robot_diagnostics_field_evidence_material_resolution_reviewer_ack_review_decision_summary|field_evidence_material_resolution_reviewer_ack_review_decision|software_proof_docker_field_evidence_material_resolution_reviewer_ack_review_decision_gate|delivery_success=false|safe_to_control=false|primary_actions_enabled=false" onboard pc-tools docs/interfaces
git diff --check -- <touched_robot_diagnostics_files> <focused_robot_diagnostics_unittest_file> docs/interfaces/operator_gateway_diagnostics.md
```

### Task C: Full-Stack Owner

Role: `full-stack-software-engineer`

Allowed files:

- `mobile/web/` panel code and fixture files
- focused mobile unittest
- `docs/product/mobile_user_flow.md`

Implementation requirements:

- Add a read-only mobile panel for reviewer ACK review decision.
- Consume `field_evidence_material_resolution_reviewer_ack_review_decision`, `field_evidence_material_resolution_reviewer_ack_review_decision_summary`, or compatible Robot diagnostics safe alias.
- Keep Start Delivery, Confirm Dropoff, and Cancel disabled unless existing independent command-safety gates allow them; this panel must never enable primary actions.
- Show safe decision, safe evidence ref, blocker/next-step summary, boundary, `not_proven`, `delivery_success=false`, and `primary_actions_enabled=false`.
- Do not fetch raw diagnostics, ACK artifacts, local files, credentials, checksums, traces, or add command/ACK/cursor endpoints.
- Keep comments in Chinese for new code comments and maintain the project comment-quality requirement.

Acceptance commands:

```bash
node --check mobile/web/app.js
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest <focused_mobile_unittest_module>
python3 -m json.tool <new_or_updated_mobile_fixture>
rg -n "field_evidence_material_resolution_reviewer_ack_review_decision|software_proof_docker_field_evidence_material_resolution_reviewer_ack_review_decision_gate|delivery_success=false|safe_to_control=false|primary_actions_enabled=false|not true phone/browser" mobile docs/product
git diff --check -- mobile/web docs/product/mobile_user_flow.md <focused_mobile_unittest_file>
```

### Task D: Product Owner

Role: `product-okr-owner`

Allowed files after Engineers finish:

- `sprints/2026.05.22_18-19_field-evidence-material-resolution-reviewer-ack-review-decision/tech-done.md`
- `sprints/2026.05.22_18-19_field-evidence-material-resolution-reviewer-ack-review-decision/side2side_check.md`
- `sprints/2026.05.22_18-19_field-evidence-material-resolution-reviewer-ack-review-decision/final.md`
- `OKR.md`
- `docs/process/okr_progress_log.md`

Closeout requirements:

- Record actual Engineer file changes and verification evidence.
- Keep `OKR.md` conservative: no OKR percentage lift.
- Preserve all non-claims: not O5 external proof, not O1 HIL, not route/elevator field pass, not true phone/browser, not delivery success.
- Confirm docs under `docs/` were synchronized by Engineers.

Acceptance commands:

```bash
test -f sprints/2026.05.22_18-19_field-evidence-material-resolution-reviewer-ack-review-decision/tech-done.md && test -f sprints/2026.05.22_18-19_field-evidence-material-resolution-reviewer-ack-review-decision/side2side_check.md && test -f sprints/2026.05.22_18-19_field-evidence-material-resolution-reviewer-ack-review-decision/final.md
rg -n "field_evidence_material_resolution_reviewer_ack_review_decision|software_proof_docker_field_evidence_material_resolution_reviewer_ack_review_decision_gate|Objective 5|no OKR percentage lift|delivery_success=false|safe_to_control=false|primary_actions_enabled=false" sprints/2026.05.22_18-19_field-evidence-material-resolution-reviewer-ack-review-decision OKR.md docs/process/okr_progress_log.md
git diff --check -- sprints/2026.05.22_18-19_field-evidence-material-resolution-reviewer-ack-review-decision OKR.md docs/process/okr_progress_log.md
```

## Interface Impact

- PC gate adds a new local evidence artifact/schema for reviewer ACK review-decision.
- Robot diagnostics adds a phone-safe alias only; it must not change ROS2 behavior, hardware commands, command safety, `/cmd_vel`, serial configuration, or route/elevator runtime.
- `mobile/web` adds a read-only support panel only; it must not add a robot command route or enable primary controls.
- Docs update interface contracts and mobile flow copy to describe the new summary and its proof boundary.

## Verification Fence

Engineer verification is intentionally focused:

- `py_compile` for new Python gates/diagnostics files.
- focused unittests only for new decision branches and UI rendering.
- `node --check` for `mobile/web/app.js` if touched.
- `json.tool` for new fixtures.
- scoped `rg` checks for capability/boundary/fail-closed strings.
- scoped `git diff --check` for touched files only.

No broad regression sweep is required unless a focused command exposes shared breakage.

## Risks And Boundaries

- If reviewer ACK intake input is absent, the gate must return `blocked_missing_reviewer_ack_intake_not_proven`, not infer acceptance.
- If ACK text or metadata includes unsafe success claims, credentials, raw control material, or sensitive internals, the gate must return `rejected_unsafe_ack_not_proven`.
- If owner identity or reassignment is ambiguous, prefer `needs_reassignment_not_proven` or `needs_field_owner_supplement_not_proven` instead of acceptance.
- All outputs remain software proof only. They do not prove delivery success, cancel/dropoff completion, route/elevator field pass, public cloud readiness, real phone/browser behavior, WAVE ROVER/UART/HIL, PR #5 resolution, or OKR percentage lift.

## Required Planning Validation

```bash
test -f sprints/2026.05.22_18-19_field-evidence-material-resolution-reviewer-ack-review-decision/pre_start.md && test -f sprints/2026.05.22_18-19_field-evidence-material-resolution-reviewer-ack-review-decision/prd.md && test -f sprints/2026.05.22_18-19_field-evidence-material-resolution-reviewer-ack-review-decision/tech-plan.md
rg -n "sprint_type: epic|field_evidence_material_resolution_reviewer_ack_review_decision|software_proof_docker_field_evidence_material_resolution_reviewer_ack_review_decision_gate|OKR 最低优先级核对|Objective 5|no OKR percentage lift" sprints/2026.05.22_18-19_field-evidence-material-resolution-reviewer-ack-review-decision
git diff --check -- sprints/2026.05.22_18-19_field-evidence-material-resolution-reviewer-ack-review-decision
```
