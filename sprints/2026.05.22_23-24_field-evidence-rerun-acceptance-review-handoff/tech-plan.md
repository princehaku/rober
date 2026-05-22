# Field Evidence Rerun Acceptance Review Handoff Tech Plan

Run time: 2026-05-22 23:04 Asia/Shanghai

> For implementation workers: use subagent-driven development. This sprint has 3 parallel Engineer owners with disjoint file scopes, plus Product closeout after implementation. Do not let the main session write product code, tests, hardware config, or runtime implementation.

## Goal

Build `field_evidence_rerun_execution_result_acceptance_review_handoff`, the handoff follow-on after `field_evidence_rerun_execution_result_acceptance_backfill_review_decision`.

The implementation must produce only `software_proof_docker_field_evidence_rerun_execution_result_acceptance_review_handoff_gate` evidence and must keep `source=software_proof`, `not_proven`, `safe_to_control=false`, `delivery_success=false`, and `primary_actions_enabled=false`.

## Architecture

- Autonomy owns the PC-only evidence handoff gate that consumes the previous acceptance backfill review-decision safe output and emits a sanitized handoff package.
- Robot owns the operator gateway diagnostics alias that exposes only safe handoff metadata and fails closed.
- Full-Stack owns the mobile/web read-only panel that shows the handoff package without enabling primary actions.
- Product owns post-implementation closeout only after the three Engineer streams return evidence.

## OKR 最低优先级核对

- 当前 `OKR.md` 4.1 节完成度最低的 Objective：Objective 5，约 68%。
- 本 sprint 是否针对该最低 Objective：不是直接针对 Objective 5，也不提升 Objective 5。
- 不针对 Objective 5 的理由：`OKR.md` 第 6 节明确，若没有真实 public HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/cutover、真实手机/browser 或 verified terminal result material，不要重复本地 O5 metadata depth。本机当前仍只有 Docker/local 证据，继续 O5 wrapper 会重复消费同一外部材料 blocker。
- Objective 1 约 81%，但真实 WAVE ROVER/UART/HIL、2D LiDAR/ToF SKU/source/receipt、operator HIL report 和 PR #5 reviewer resolution 仍缺失。Live PR #5 evidence：`PRRT_kwDOSWB9286CJ3tQ` resolved，`PRRT_kwDOSWB9286CJ3tU` resolved，`PRRT_kwDOSWB9286CJ3tX` unresolved / `is_resolved=false` / `hardware_material_pending`。
- 本 sprint 转向 Objective 2 / Objective 3 / Objective 4 的 route/elevator/phone real-material review follow-through：它只把上一轮 `ready_for_field_rerun_result_acceptance_review_handoff` 转成 handoff package，为后续真实 field rerun result acceptance review 做准备。
- final.md 收口时必须复核：如果没有真实 O5 external proof、真实 O1 hardware/HIL material、PR #5 resolution、真实 route/elevator pass、真实 phone/browser 或 verified terminal result，`OKR.md` 不得提高百分比。

## Shared Contract

All owners must preserve these fields and wording:

- `field_evidence_rerun_execution_result_acceptance_review_handoff`
- `software_proof_docker_field_evidence_rerun_execution_result_acceptance_review_handoff_gate`
- `source=software_proof`
- `not_proven`
- `safe_to_control=false`
- `delivery_success=false`
- `primary_actions_enabled=false`
- Previous ready state: `ready_for_field_rerun_result_acceptance_review_handoff`
- PR #5 `PRRT_kwDOSWB9286CJ3tX` remains `is_resolved=false` / `hardware_material_pending`
- Threads `PRRT_kwDOSWB9286CJ3tQ` and `PRRT_kwDOSWB9286CJ3tU` are resolved, but they do not close the pending hardware material thread.

Allowed handoff states:

- `ready_for_field_owner_support_reviewer_handoff_not_proven`
- `handoff_needs_more_material`
- `handoff_evidence_ref_mismatch`
- `handoff_unsafe_rejected`
- `blocked_missing_review_decision`

Required handoff material checklist:

- true task record
- true Nav2/fixed-route runtime log
- route completion signal
- true elevator door state
- target floor confirmation
- human assistance record
- dropoff/cancel completion or delivery result
- true phone/browser evidence

Forbidden claims:

- real HIL
- WAVE ROVER/UART proof
- real route/elevator field pass
- real Nav2/fixed-route runtime pass
- real phone/browser proof
- Objective 5 external proof
- verified terminal result
- dropoff/cancel completion
- delivery_success
- PR #5 reviewer resolution

Forbidden exposure:

- raw ROS topics, `/cmd_vel`, serial/UART paths, baudrate values, WAVE ROVER parameters
- credentials, bearer tokens, Authorization headers, OSS AK/SK, DB/queue URLs
- raw artifacts, complete artifacts, local paths, checksums, tracebacks
- success phrasing, control-enable copy, or hidden primary-action enablement

## Parallel Owner Plan

### Task A: Autonomy PC-Only Handoff Gate + Tests + Evidence Docs

Role id: `autonomy-engineer`

Files:

- Create: `pc-tools/evidence/field_evidence_rerun_execution_result_acceptance_review_handoff.py`
- Create: `pc-tools/evidence/test_field_evidence_rerun_execution_result_acceptance_review_handoff.py`
- Modify: `pc-tools/README.md`
- Modify: `docs/interfaces/evidence_contracts.md`

Responsibilities:

1. Implement a CLI gate that accepts the previous acceptance backfill review-decision artifact, summary, or Robot diagnostics safe alias and writes a sanitized handoff package for `field_evidence_rerun_execution_result_acceptance_review_handoff`.
2. Require the previous safe output to include `ready_for_field_rerun_result_acceptance_review_handoff`, the same safe `evidence_ref`, and the boundary `software_proof_docker_field_evidence_rerun_execution_result_acceptance_backfill_review_decision_gate`.
3. Emit `ready_for_field_owner_support_reviewer_handoff_not_proven` only when the prior decision is safe, the handoff checklist is internally consistent, and no unsafe copy, success claim, control-enable state, credentials, raw artifact exposure, external-proof claim, HIL claim, or PR #5 resolution claim appears.
4. Emit `handoff_needs_more_material`, `handoff_evidence_ref_mismatch`, `handoff_unsafe_rejected`, or `blocked_missing_review_decision` for the corresponding failure classes.
5. Emit only safe summary fields for Robot/mobile and keep `source=software_proof`, `not_proven`, `safe_to_control=false`, `delivery_success=false`, and `primary_actions_enabled=false`.
6. Add targeted tests for ready handoff-not-proven, missing material, evidence-ref mismatch, unsafe/success claim rejection, and missing review decision.

Acceptance commands:

```bash
python3 -m py_compile pc-tools/evidence/field_evidence_rerun_execution_result_acceptance_review_handoff.py
python3 -m unittest pc-tools/evidence/test_field_evidence_rerun_execution_result_acceptance_review_handoff.py
python3 pc-tools/evidence/field_evidence_rerun_execution_result_acceptance_review_handoff.py --help
rg -n "field_evidence_rerun_execution_result_acceptance_review_handoff|software_proof_docker_field_evidence_rerun_execution_result_acceptance_review_handoff_gate|source=software_proof|not_proven|delivery_success=false|primary_actions_enabled=false|safe_to_control=false|ready_for_field_owner_support_reviewer_handoff_not_proven|handoff_needs_more_material|handoff_evidence_ref_mismatch|handoff_unsafe_rejected|blocked_missing_review_decision" pc-tools/evidence/field_evidence_rerun_execution_result_acceptance_review_handoff.py pc-tools/evidence/test_field_evidence_rerun_execution_result_acceptance_review_handoff.py pc-tools/README.md docs/interfaces/evidence_contracts.md
git diff --check -- pc-tools/evidence/field_evidence_rerun_execution_result_acceptance_review_handoff.py pc-tools/evidence/test_field_evidence_rerun_execution_result_acceptance_review_handoff.py pc-tools/README.md docs/interfaces/evidence_contracts.md
```

### Task B: Robot Diagnostics Safe Alias + Tests + Diagnostics Docs

Role id: `robot-software-engineer`

Files:

- Modify: `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py`
- Modify: `onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`
- Modify: `docs/interfaces/ros_runtime_contracts.md`

Responsibilities:

1. Add Robot diagnostics support for `field_evidence_rerun_execution_result_acceptance_review_handoff` safe summary.
2. Expose a safe alias such as `robot_diagnostics_field_evidence_rerun_execution_result_acceptance_review_handoff_summary`.
3. Preserve fail-closed defaults when the summary is missing, malformed, unsupported, unsafe, or contains success/control/external-proof/HIL/PR-resolution wording.
4. Expose only handoff status, safe `evidence_ref`, required material checklist, blocked/rejected categories, owner/support/reviewer next step, evidence boundary, `not_proven`, `source=software_proof`, `safe_to_control=false`, `delivery_success=false`, and `primary_actions_enabled=false`.
5. Do not expose raw manifest contents, local paths, checksums, tracebacks, ROS topics, `/cmd_vel`, serial/UART details, WAVE ROVER details, credentials, DB/queue URLs, or complete artifacts.
6. Add targeted diagnostics tests without broad unrelated regression sweeps.

Acceptance commands:

```bash
python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py
python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py
rg -n "field_evidence_rerun_execution_result_acceptance_review_handoff|software_proof_docker_field_evidence_rerun_execution_result_acceptance_review_handoff_gate|source=software_proof|not_proven|delivery_success=false|primary_actions_enabled=false|safe_to_control=false|ready_for_field_owner_support_reviewer_handoff_not_proven|handoff_needs_more_material|handoff_evidence_ref_mismatch|handoff_unsafe_rejected|blocked_missing_review_decision" onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py docs/interfaces/ros_runtime_contracts.md
git diff --check -- onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py docs/interfaces/ros_runtime_contracts.md
```

### Task C: Full-Stack Mobile/Web Read-Only Panel + Fixture + Tests + Mobile Docs

Role id: `full-stack-software-engineer`

Files:

- Modify: `mobile/web/app.js`
- Create: `mobile/web/fixtures/robot_diagnostics_field_evidence_rerun_execution_result_acceptance_review_handoff.json`
- Modify: `mobile/web/test_mobile_web_entrypoint.py`
- Modify: `docs/product/mobile_user_flow.md`

Responsibilities:

1. Add a read-only “现场证据复跑执行结果验收交接” panel for `field_evidence_rerun_execution_result_acceptance_review_handoff`.
2. Consume `robot_diagnostics_field_evidence_rerun_execution_result_acceptance_review_handoff_summary` first, then compatible safe summaries from existing status/diagnostics shapes.
3. Show only handoff status, safe `evidence_ref`, required material checklist, blocked/rejected categories, owner/support/reviewer next step, evidence boundary, `source=software_proof`, `not_proven`, `safe_to_control=false`, `delivery_success=false`, and `primary_actions_enabled=false`.
4. Keep Start Delivery, Confirm Dropoff, and Cancel disabled under the fixture.
5. Do not fetch raw artifacts, raw diagnostics, ACK/cursor routes, material routes, callback routes, review routes, handoff routes, Start/Confirm/Cancel endpoints, or robot command endpoints from this panel.
6. Add a fixture and targeted mobile test for render, fail-closed controls, redaction boundaries, and no success/control copy.

Acceptance commands:

```bash
node --check mobile/web/app.js
python3 -m json.tool mobile/web/fixtures/robot_diagnostics_field_evidence_rerun_execution_result_acceptance_review_handoff.json >/tmp/field_evidence_rerun_execution_result_acceptance_review_handoff_fixture.json
python3 -m unittest mobile/web/test_mobile_web_entrypoint.py
rg -n "field_evidence_rerun_execution_result_acceptance_review_handoff|software_proof_docker_field_evidence_rerun_execution_result_acceptance_review_handoff_gate|source=software_proof|not_proven|delivery_success=false|primary_actions_enabled=false|safe_to_control=false|ready_for_field_owner_support_reviewer_handoff_not_proven|handoff_needs_more_material|handoff_evidence_ref_mismatch|handoff_unsafe_rejected|blocked_missing_review_decision" mobile/web/app.js mobile/web/fixtures/robot_diagnostics_field_evidence_rerun_execution_result_acceptance_review_handoff.json mobile/web/test_mobile_web_entrypoint.py docs/product/mobile_user_flow.md
git diff --check -- mobile/web/app.js mobile/web/fixtures/robot_diagnostics_field_evidence_rerun_execution_result_acceptance_review_handoff.json mobile/web/test_mobile_web_entrypoint.py docs/product/mobile_user_flow.md
```

### Task D: Product Closeout After A/B/C

Role id: `product-okr-owner`

Files:

- Create or modify: `sprints/2026.05.22_23-24_field-evidence-rerun-acceptance-review-handoff/tech-done.md`
- Create or modify: `sprints/2026.05.22_23-24_field-evidence-rerun-acceptance-review-handoff/side2side_check.md`
- Create or modify: `sprints/2026.05.22_23-24_field-evidence-rerun-acceptance-review-handoff/final.md`
- Modify: `OKR.md`
- Modify: `docs/process/okr_progress_log.md`

Responsibilities:

1. Integrate the three Engineer reports and record actual changed files, validation results, deviations, and remaining risks.
2. Confirm A/B/C docs updates landed under `docs/interfaces/` and `docs/product/`.
3. Keep `OKR.md` conservative: Objective 5 remains around 68% unless real O5 external evidence appears; Objective 1 remains around 81% unless real PR #5/hardware/HIL material appears; Objectives 2/3/4 remain unchanged unless real field/mobile/delivery evidence appears.
4. Write final closeout so this sprint is accepted only as `software_proof_docker_field_evidence_rerun_execution_result_acceptance_review_handoff_gate`.
5. Explicitly state that PR #5 `PRRT_kwDOSWB9286CJ3tX` remains unresolved unless a live reviewer resolution is present.
6. Preserve `delivery_success=false`, `primary_actions_enabled=false`, `safe_to_control=false`, `not_proven`, and no real route/elevator/phone/HIL/O5 claims.

Acceptance commands:

```bash
test -f sprints/2026.05.22_23-24_field-evidence-rerun-acceptance-review-handoff/tech-done.md && test -f sprints/2026.05.22_23-24_field-evidence-rerun-acceptance-review-handoff/side2side_check.md && test -f sprints/2026.05.22_23-24_field-evidence-rerun-acceptance-review-handoff/final.md
rg -n "software_proof_docker_field_evidence_rerun_execution_result_acceptance_review_handoff_gate|Objective 5|Objective 1|Objective 2|Objective 3|Objective 4|PRRT_kwDOSWB9286CJ3tX|delivery_success=false|primary_actions_enabled=false|safe_to_control=false|not_proven" sprints/2026.05.22_23-24_field-evidence-rerun-acceptance-review-handoff OKR.md docs/process/okr_progress_log.md
git diff --check -- sprints/2026.05.22_23-24_field-evidence-rerun-acceptance-review-handoff OKR.md docs/process/okr_progress_log.md
```

## Dispatch Requirements

Implementation must start 3 parallel Engineer workers in one dispatch set:

- Autonomy Algorithm Engineer for PC evidence handoff gate files.
- Robot Platform Engineer for diagnostics/runtime contract files.
- User Touchpoint Full-Stack Engineer for mobile/web files.

Product closeout starts only after the three Engineer workers return. If any owner fails validation, send the failure back to the same owner before closeout.

## Planning Validation Commands

The Product Owner planning task must run:

```bash
test -f sprints/2026.05.22_23-24_field-evidence-rerun-acceptance-review-handoff/pre_start.md && test -f sprints/2026.05.22_23-24_field-evidence-rerun-acceptance-review-handoff/prd.md && test -f sprints/2026.05.22_23-24_field-evidence-rerun-acceptance-review-handoff/tech-plan.md
rg -n "sprint_type: epic|field_evidence_rerun_execution_result_acceptance_review_handoff|software_proof_docker_field_evidence_rerun_execution_result_acceptance_review_handoff_gate|OKR 最低优先级核对|Objective 5|Objective 1|PRRT_kwDOSWB9286CJ3tX|delivery_success=false|primary_actions_enabled=false|safe_to_control=false|not_proven" sprints/2026.05.22_23-24_field-evidence-rerun-acceptance-review-handoff
git diff --check -- sprints/2026.05.22_23-24_field-evidence-rerun-acceptance-review-handoff
```
