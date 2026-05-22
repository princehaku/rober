# Field Evidence Rerun Acceptance Owner Response Intake Tech Plan

Run time: 2026-05-23 05:06 Asia/Shanghai

> For implementation workers: use subagent-driven development. This sprint has 3 parallel Engineer owners with disjoint file scopes, plus Product closeout after implementation. The main session must not write product code, tests, hardware config, or runtime implementation.

## Goal

Build `field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_intake`, the owner response intake after `field_evidence_rerun_execution_result_acceptance_handoff_intake_followup_escalation_status`.

The implementation must produce only `software_proof_docker_field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_intake_gate` evidence and must keep `source=software_proof`, `software_proof`, `not_proven`, `safe_to_control=false`, `delivery_success=false`, `primary_actions_enabled=false`, and no OKR percentage lift.

## Architecture

- Autonomy owns the PC-only owner response intake gate that consumes the previous safe follow-up escalation status output plus a safe owner response packet and emits accepted / missing / rejected / blocked safe metadata.
- Robot owns the operator gateway diagnostics safe alias that exposes only safe owner response intake metadata and fails closed.
- Full-Stack owns the `mobile/web` read-only panel that shows owner response intake status without enabling primary actions.
- Product owns post-implementation closeout only after the three Engineer streams return evidence.

## OKR 最低优先级核对

- 当前 `OKR.md` 4.1 节完成度最低的 Objective：Objective 5，约 68%。
- 本 sprint 是否针对该最低 Objective：不是直接针对 Objective 5，也不提升 Objective 5。
- 不针对 Objective 5 的理由：当前本机只有 Docker，没有真实 public HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/cutover、真实手机/browser 或 verified terminal result materials；继续把本地 metadata 写成 O5 external proof 会重复消费同一外部材料 blocker。
- 当前下一低项 Objective 1 约 81%，但 PR #5 live thread `PRRT_kwDOSWB9286CJ3tX` 仍 unresolved / `is_resolved=false` / `hardware_material_pending`，`PRRT_kwDOSWB9286CJ3tQ` 与 `PRRT_kwDOSWB9286CJ3tU` resolved 不能关闭 X；无真实 2D LiDAR/ToF/WAVE ROVER/UART/HIL 材料。
- 因 O5 真实外部材料不可用、O1 真实硬件材料/PR thread resolution 不可用，本 sprint 推进 Objective 2 / Objective 3 / Objective 4 的现场 owner response intake，让现场 owner 对同一 safe `evidence_ref` 回填真实 task record、真实 Nav2/fixed-route runtime log、route completion signal、电梯门状态、目标楼层确认、人工协助记录、dropoff/cancel completion、delivery result、真实 route/elevator field pass 和 true phone/browser evidence。
- `final.md` 收口时必须复核：如果没有真实 O5 external proof、真实 O1 hardware/HIL material、PR #5 resolution、真实 route/elevator pass、真实 phone/browser 或 verified terminal result，`OKR.md` 不得提高百分比，必须保留 no OKR percentage lift。

## Shared Contract

All owners must preserve these fields and wording:

- `field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_intake`
- `software_proof_docker_field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_intake_gate`
- Previous capability: `field_evidence_rerun_execution_result_acceptance_handoff_intake_followup_escalation_status`
- Previous boundary: `software_proof_docker_field_evidence_rerun_execution_result_acceptance_handoff_intake_followup_escalation_status_gate`
- `source=software_proof`
- `software_proof`
- `not_proven`
- `safe_to_control=false`
- `delivery_success=false`
- `primary_actions_enabled=false`
- Same safe `evidence_ref`
- no OKR percentage lift
- PR #5 `PRRT_kwDOSWB9286CJ3tX` remains unresolved / `is_resolved=false` / `hardware_material_pending`
- Threads `PRRT_kwDOSWB9286CJ3tQ` and `PRRT_kwDOSWB9286CJ3tU` are resolved, but they do not close the pending hardware material thread.
- PR #7 is open but has no review comments/threads; do not route this sprint to PR #7 document rules except as process background.

Allowed owner response intake states:

- `accepted`
- `missing`
- `rejected`
- `blocked`

Required owner response material checklist:

- true task record
- true Nav2/fixed-route runtime log
- route completion signal
- true elevator door state
- target floor confirmation
- human assistance record
- dropoff/cancel completion
- delivery result
- true route/elevator field pass
- true phone/browser evidence
- PR #5 hardware material remains pending unless `PRRT_kwDOSWB9286CJ3tX` is live resolved by reviewer

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

### Task A: Autonomy PC-Only Owner Response Intake Gate + Tests + Evidence Docs

Role id: `autonomy-engineer`

Files:

- Create: `pc-tools/evidence/field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_intake.py`
- Create: `pc-tools/evidence/test_field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_intake.py`
- Modify: `pc-tools/README.md`
- Modify: `docs/interfaces/evidence_contracts.md`

Interface impact:

- Adds a PC-only evidence artifact and summary contract. It must not alter ROS2 runtime APIs, cloud APIs, mobile command endpoints, hardware parameters, or existing evidence gate outputs.

Responsibilities:

1. Implement a CLI gate that accepts the previous acceptance handoff intake follow-up escalation status artifact, summary, or Robot diagnostics safe alias plus a safe owner response packet.
2. Require the previous safe output to include `field_evidence_rerun_execution_result_acceptance_handoff_intake_followup_escalation_status`, the same safe `evidence_ref`, and `software_proof_docker_field_evidence_rerun_execution_result_acceptance_handoff_intake_followup_escalation_status_gate`.
3. Require owner response packets to classify required materials as accepted, missing, rejected, or blocked under the same safe `evidence_ref`.
4. Fail closed to `blocked` with structured reasons for missing previous status, missing required material, evidence-ref mismatch, unsafe copy, forbidden success/control claims, O5 external-proof claims, O1 HIL claims, or PR #5 resolution claims.
5. Emit only safe summary fields for Robot/mobile and keep `source=software_proof`, `software_proof`, `not_proven`, `safe_to_control=false`, `delivery_success=false`, `primary_actions_enabled=false`, and no OKR percentage lift.
6. Add targeted tests for accepted complete safe packet, missing required materials, rejected unsafe material refs, blocked missing previous status, evidence-ref mismatch, and unsafe/success claim rejection.

Risk boundary:

- This gate can package owner response intake only. It must not read or validate raw field logs as true proof, must not claim route/elevator pass, must not close PR #5, and must not unblock controls.

Acceptance commands:

```bash
python3 -m py_compile pc-tools/evidence/field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_intake.py
python3 -m unittest pc-tools/evidence/test_field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_intake.py
python3 pc-tools/evidence/field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_intake.py --help
rg -n "field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_intake|software_proof_docker_field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_intake_gate|source=software_proof|not_proven|delivery_success=false|primary_actions_enabled=false|safe_to_control=false|accepted|missing|rejected|blocked" pc-tools/evidence/field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_intake.py pc-tools/evidence/test_field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_intake.py pc-tools/README.md docs/interfaces/evidence_contracts.md
git diff --check -- pc-tools/evidence/field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_intake.py pc-tools/evidence/test_field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_intake.py pc-tools/README.md docs/interfaces/evidence_contracts.md
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

1. Add Robot diagnostics support for `field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_intake` safe summary.
2. Expose a safe alias such as `robot_diagnostics_field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_intake_summary`.
3. Preserve fail-closed defaults when the summary is missing, malformed, unsupported, unsafe, or contains success/control/external-proof/HIL/PR-resolution wording.
4. Expose only owner response intake status, source follow-up escalation status, safe `evidence_ref`, accepted/missing/rejected/blocked material refs, owner/support/reviewer next step, evidence boundary, `software_proof`, `not_proven`, `source=software_proof`, `safe_to_control=false`, `delivery_success=false`, and `primary_actions_enabled=false`.
5. Do not expose raw manifest contents, local paths, checksums, tracebacks, ROS topics, `/cmd_vel`, serial/UART details, WAVE ROVER details, credentials, DB/queue URLs, or complete artifacts.
6. Add targeted diagnostics tests without broad unrelated regression sweeps.

Risk boundary:

- Diagnostics must remain read-only support metadata. Owner response intake states are not real delivery/dropoff/cancel proof and must not enable Start/Confirm/Cancel.

Acceptance commands:

```bash
python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py
python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py
rg -n "field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_intake|software_proof_docker_field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_intake_gate|source=software_proof|not_proven|delivery_success=false|primary_actions_enabled=false|safe_to_control=false|accepted|missing|rejected|blocked" onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py docs/interfaces/ros_runtime_contracts.md
git diff --check -- onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py docs/interfaces/ros_runtime_contracts.md
```

### Task C: Full-Stack Mobile/Web Read-Only Panel + Fixture + Tests + Mobile Docs

Role id: `full-stack-software-engineer`

Files:

- Modify: `mobile/web/app.js`
- Create: `mobile/web/fixtures/robot_diagnostics_field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_intake.json`
- Modify: `mobile/web/test_mobile_web_entrypoint.py`
- Modify: `docs/product/mobile_user_flow.md`

Interface impact:

- Adds one read-only mobile panel that consumes existing status/diagnostics summaries. It must not add fetch routes, command routes, ACK/cursor routes, material upload routes, review routes, handoff routes, follow-up routes, owner-response routes, or hidden action enablement.

Responsibilities:

1. Add a read-only “现场证据复跑执行结果验收交接回执 owner response intake” panel for `field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_intake`.
2. Consume `robot_diagnostics_field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_intake_summary` first, then compatible safe summaries from existing status/diagnostics shapes.
3. Show only owner response intake status, source follow-up escalation status, safe `evidence_ref`, accepted/missing/rejected/blocked material refs, owner/support/reviewer next step, evidence boundary, `source=software_proof`, `software_proof`, `not_proven`, `safe_to_control=false`, `delivery_success=false`, and `primary_actions_enabled=false`.
4. Keep Start Delivery, Confirm Dropoff, and Cancel disabled under the fixture.
5. Do not fetch raw artifacts, raw diagnostics, ACK/cursor routes, material routes, callback routes, review routes, handoff routes, follow-up routes, owner-response routes, Start/Confirm/Cancel endpoints, or robot command endpoints from this panel.
6. Add a fixture and targeted mobile test for render, fail-closed controls, redaction boundaries, and no success/control copy.

Risk boundary:

- The panel is support-facing read-only status. It must not turn owner response intake into true phone/browser proof, field pass, delivery success, verified terminal result, or control permission.

Acceptance commands:

```bash
node --check mobile/web/app.js
python3 -m json.tool mobile/web/fixtures/robot_diagnostics_field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_intake.json >/tmp/field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_intake_fixture.json
python3 -m unittest mobile/web/test_mobile_web_entrypoint.py
rg -n "field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_intake|software_proof_docker_field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_intake_gate|source=software_proof|not_proven|delivery_success=false|primary_actions_enabled=false|safe_to_control=false|accepted|missing|rejected|blocked" mobile/web/app.js mobile/web/fixtures/robot_diagnostics_field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_intake.json mobile/web/test_mobile_web_entrypoint.py docs/product/mobile_user_flow.md
git diff --check -- mobile/web/app.js mobile/web/fixtures/robot_diagnostics_field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_intake.json mobile/web/test_mobile_web_entrypoint.py docs/product/mobile_user_flow.md
```

### Task D: Product Closeout After A/B/C

Role id: `product-okr-owner`

Files:

- Create or modify: `sprints/2026.05.23_05-06_field-evidence-rerun-acceptance-owner-response-intake/tech-done.md`
- Create or modify: `sprints/2026.05.23_05-06_field-evidence-rerun-acceptance-owner-response-intake/side2side_check.md`
- Create or modify: `sprints/2026.05.23_05-06_field-evidence-rerun-acceptance-owner-response-intake/final.md`
- Modify: `OKR.md`
- Modify: `docs/process/okr_progress_log.md`

Interface impact:

- Product closeout updates sprint evidence and OKR/progress narrative only. It must not modify product code, tests, hardware configuration, mobile runtime, PC gates, or Robot diagnostics implementation.

Responsibilities:

1. Integrate the three Engineer reports and record actual changed files, validation results, deviations, and remaining risks.
2. Confirm A/B/C docs updates landed under `docs/interfaces/` and `docs/product/`.
3. Keep Objective 5 around 68%, Objective 1 around 81%, Objective 2/3/4 around 99% unless real external, hardware, route/elevator, terminal result, or phone/browser evidence appears.
4. Preserve `source=software_proof`, `software_proof`, `not_proven`, `delivery_success=false`, `primary_actions_enabled=false`, `safe_to_control=false`, and no OKR percentage lift.
5. Explicitly state that PR #5 `PRRT_kwDOSWB9286CJ3tX` is still unresolved / `is_resolved=false` / `hardware_material_pending` unless live reviewer evidence changes.

Acceptance commands:

```bash
test -f sprints/2026.05.23_05-06_field-evidence-rerun-acceptance-owner-response-intake/tech-done.md && test -f sprints/2026.05.23_05-06_field-evidence-rerun-acceptance-owner-response-intake/side2side_check.md && test -f sprints/2026.05.23_05-06_field-evidence-rerun-acceptance-owner-response-intake/final.md
rg -n "field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_intake|software_proof_docker_field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_intake_gate|Objective 5|Objective 1|PRRT_kwDOSWB9286CJ3tX|source=software_proof|not_proven|delivery_success=false|primary_actions_enabled=false|safe_to_control=false|no OKR percentage lift" sprints/2026.05.23_05-06_field-evidence-rerun-acceptance-owner-response-intake OKR.md docs/process/okr_progress_log.md
git diff --check -- sprints/2026.05.23_05-06_field-evidence-rerun-acceptance-owner-response-intake OKR.md docs/process/okr_progress_log.md
```

## Sprint Planning Verification

Planning-only verification for this Product task:

```bash
test -f sprints/2026.05.23_05-06_field-evidence-rerun-acceptance-owner-response-intake/pre_start.md && test -f sprints/2026.05.23_05-06_field-evidence-rerun-acceptance-owner-response-intake/prd.md && test -f sprints/2026.05.23_05-06_field-evidence-rerun-acceptance-owner-response-intake/tech-plan.md
rg -n "sprint_type: epic|OKR 最低优先级核对|Objective 5|Objective 1|PRRT_kwDOSWB9286CJ3tX|field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_intake|software_proof_docker_field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_intake_gate|source=software_proof|not_proven|delivery_success=false|primary_actions_enabled=false|safe_to_control=false|no OKR percentage lift" sprints/2026.05.23_05-06_field-evidence-rerun-acceptance-owner-response-intake
git diff --check -- sprints/2026.05.23_05-06_field-evidence-rerun-acceptance-owner-response-intake
```

## Execution Notes for Main Session

- After this plan is accepted, start 3 parallel worker agents for Task A/B/C because file scopes are disjoint.
- Do not serialize A/B/C unless one worker reports an interface blocker.
- Do not start Task D until all three implementation streams return changed files and validation output.
- Do not commit planning docs as product proof; they are only the executable plan for the next sprint phase.
