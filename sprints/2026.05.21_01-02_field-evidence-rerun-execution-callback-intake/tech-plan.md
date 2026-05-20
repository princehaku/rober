# Field Evidence Rerun Execution Callback Intake Tech Plan

## Sprint Declaration

- sprint_type: epic
- Sprint: `2026.05.21_01-02_field-evidence-rerun-execution-callback-intake`
- Target capability: `field_evidence_rerun_execution_callback_intake`
- Evidence boundary: `software_proof_docker_field_evidence_rerun_execution_callback_intake_gate`
- Required preserved states: `software_proof`, `not_proven`, `safe_to_control=false`, `delivery_success=false`, `primary_actions_enabled=false`
- Planning status: ready for three parallel Engineer workers; this Product planning handoff implements no product code and no test code.

## OKR 最低优先级核对

1. Current lowest Objective in `OKR.md` 4.1: Objective 5 is about 68%, lower than Objective 1 at about 81% and Objectives 2/3/4 at about 99%.
2. This sprint is not targeting Objective 5 directly.
3. Reason: Objective 5 currently needs real external proof unavailable on this Docker-only host: real public HTTPS/TLS, 4G/SIM, OSS/CDN live traffic, production DB/queue, production worker/cutover, or real phone/browser external proof. `OKR.md` §6 explicitly says not to repeat local O5 metadata depth without true external material.
4. Next lowest Objective 1 is about 81%, but PR #5 `PRRT_kwDOSWB9286CJ3tX` remains unresolved / material pending and asks for vendor sources for mandatory sensor assumptions. The latest `hardware_sensor_hil_entry_callback_review_handoff` already consumed a hardware-material wrapper path, and this host still lacks WAVE ROVER/UART/HIL and real 2D LiDAR / ToF materials.
5. Chosen sprint target: O2/O3/O4 `field_evidence_rerun_execution_callback_intake`. PR #6 is docs-only with no runtime/hardware/HIL/true phone/browser/O5 external tests, and the latest `field_evidence_rerun_execution_pack` final says the next actionable material step is to execute the pack and backfill same-safe-`evidence_ref` field materials.

## Evidence Inputs

- `OKR.md` 4.1 current snapshot: Objective 5 about 68%; Objective 1 about 81%; O2/O3/O4 about 99%.
- PR #5 evidence: thread `PRRT_kwDOSWB9286CJ3tX` remains unresolved / material pending for mandatory sensor assumption vendor sources.
- PR #6 evidence: README/docs-only, no runtime, hardware, HIL, true phone/browser, or O5 external tests.
- Previous field sprint: `sprints/2026.05.20_18-19_field-evidence-rerun-execution-pack/final.md`, capability `field_evidence_rerun_execution_pack`, boundary `software_proof_docker_field_evidence_rerun_execution_pack_gate`.
- Mobile/product constraint: `docs/product/mobile_user_flow.md` keeps evidence panels read-only and primary actions fail-closed unless existing command-safety gates allow them.

## Architecture And Contract

The implementation should add one metadata-only contract family:

- Artifact family: `field_evidence_rerun_execution_callback_intake`
- Suggested schema: `trashbot.field_evidence_rerun_execution_callback_intake.v1`
- Suggested summary schema: `trashbot.field_evidence_rerun_execution_callback_intake_summary.v1`
- Suggested Robot safe alias: `robot_diagnostics_field_evidence_rerun_execution_callback_intake_summary`
- Evidence boundary: `software_proof_docker_field_evidence_rerun_execution_callback_intake_gate`

Expected minimum output fields:

- `schema`
- `schema_version`
- `source=software_proof`
- `safe_evidence_ref`
- `source_execution_pack_schema`
- `source_execution_pack_status`
- `callback_packet_schema`
- `callback_packet_status`
- `same_evidence_ref_status`
- `accepted_materials`
- `missing_materials`
- `rejected_materials`
- `blocked_materials`
- `owner_handoff`
- `next_required_evidence`
- `safe_copy`
- `not_proven`
- `safe_to_control=false`
- `delivery_success=false`
- `primary_actions_enabled=false`
- `evidence_boundary=software_proof_docker_field_evidence_rerun_execution_callback_intake_gate`

Required material categories:

- `task_record`
- `nav2_fixed_route_runtime_log`
- `route_completion_signal`
- `elevator_door_state`
- `target_floor_confirmation`
- `human_assistance_record`
- `dropoff_completion`
- `cancel_completion`
- `delivery_result`
- `phone_browser_evidence`

The callback intake may say field-owner callback materials are accepted for later review. It must not say the rerun happened successfully, passed, moved the robot, proved Nav2, proved elevator delivery, proved HIL, proved external cloud, or completed delivery.

## Parallel Worker Plan

### Worker 1: Autonomy Algorithm Engineer

Responsibility: PC gate and canonical callback-intake artifact.

Allowed file range for implementation:

- `pc-tools/evidence/field_evidence_rerun_execution_callback_intake.py`
- `tests/test_field_evidence_rerun_execution_callback_intake.py`
- `pc-tools/README.md`
- `docs/interfaces/evidence_contracts.md`
- current sprint implementation docs after code lands

Implementation requirements:

- Consume `field_evidence_rerun_execution_pack` artifact or `field_evidence_rerun_execution_pack_summary`.
- Consume field owner execution callback packet JSON.
- Validate `source=software_proof`, `not_proven`, `safe_to_control=false`, `delivery_success=false`, `primary_actions_enabled=false`, and the source execution-pack boundary.
- Validate same safe `evidence_ref` and reject unsafe/missing/mismatched refs.
- Emit accepted, missing, rejected, and blocked material groups across all required material categories.
- Emit owner handoff, next required evidence, same-`evidence_ref` status, and safe copy.
- Fail closed on missing execution pack, missing callback packet, unsupported schema, unsafe copy, raw artifact exposure, success/control wording, or any true/proven delivery claim.

Acceptance commands:

```bash
python3 -m py_compile pc-tools/evidence/field_evidence_rerun_execution_callback_intake.py
python3 -m unittest tests.test_field_evidence_rerun_execution_callback_intake
python3 pc-tools/evidence/field_evidence_rerun_execution_callback_intake.py --help
rg -n "field_evidence_rerun_execution_callback_intake|software_proof_docker_field_evidence_rerun_execution_callback_intake_gate|safe_to_control=false|delivery_success=false|primary_actions_enabled=false|not_proven" pc-tools/evidence tests pc-tools/README.md docs/interfaces/evidence_contracts.md sprints/2026.05.21_01-02_field-evidence-rerun-execution-callback-intake
git diff --check -- pc-tools/evidence/field_evidence_rerun_execution_callback_intake.py tests/test_field_evidence_rerun_execution_callback_intake.py pc-tools/README.md docs/interfaces/evidence_contracts.md sprints/2026.05.21_01-02_field-evidence-rerun-execution-callback-intake
```

### Worker 2: Robot Platform Engineer

Responsibility: diagnostics safe alias.

Allowed file range for implementation:

- existing diagnostics files that already host safe aliases
- focused diagnostics tests in the existing diagnostics test location
- `docs/interfaces/ros_runtime_contracts.md`
- current sprint implementation docs after code lands

Implementation requirements:

- Add `robot_diagnostics_field_evidence_rerun_execution_callback_intake_summary` as a safe alias.
- Prefer canonical callback-intake summary and reject raw callback material when it contains unsafe fields.
- Redact or omit raw ROS topics, `/cmd_vel`, serial/UART details, WAVE ROVER parameters, credentials, local paths, complete artifacts, checksums, traceback, HIL/pass wording, and delivery success claims.
- Preserve `software_proof_docker_field_evidence_rerun_execution_callback_intake_gate`.
- Keep existing diagnostics aliases backward compatible.

Acceptance commands:

```bash
python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py
PYTHONPATH=onboard/src/ros2_trashbot_behavior python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py
rg -n "robot_diagnostics_field_evidence_rerun_execution_callback_intake_summary|field_evidence_rerun_execution_callback_intake|software_proof_docker_field_evidence_rerun_execution_callback_intake_gate|safe_to_control=false|delivery_success=false|primary_actions_enabled=false|not_proven" onboard/src/ros2_trashbot_behavior docs/interfaces/ros_runtime_contracts.md sprints/2026.05.21_01-02_field-evidence-rerun-execution-callback-intake
git diff --check -- onboard/src/ros2_trashbot_behavior docs/interfaces/ros_runtime_contracts.md sprints/2026.05.21_01-02_field-evidence-rerun-execution-callback-intake
```

### Worker 3: User Touchpoint Full-Stack Engineer

Responsibility: mobile/web read-only panel.

Allowed file range for implementation:

- `mobile/web/app.js`
- relevant mobile fixture file under `mobile/fixtures/` or `mobile/web/fixtures/`
- focused mobile/web test file
- `docs/product/mobile_user_flow.md`
- current sprint implementation docs after code lands

Implementation requirements:

- Add a read-only "现场证据复跑执行回执入口" panel.
- Prefer `robot_diagnostics_field_evidence_rerun_execution_callback_intake_summary`; fall back only to safe compatible summary fields already present in status/diagnostics payloads.
- Show safe `evidence_ref`, callback-intake status, accepted/missing/rejected/blocked materials, owner handoff, next required evidence, evidence boundary, `not_proven`, `safe_to_control=false`, `delivery_success=false`, and `primary_actions_enabled=false`.
- Never send Start Delivery, Confirm Dropoff, Cancel, ACK, cursor, diagnostics fetch, queue scheduling, execution scheduling, callback submission, or robot command requests from the panel.
- Keep existing Start Delivery, Confirm Dropoff, and Cancel gating unchanged.

Acceptance commands:

```bash
node --check mobile/web/app.js
python3 -m unittest mobile/web/test_mobile_web_entrypoint.py
python3 -m json.tool mobile/web/fixtures/status.json >/dev/null
rg -n "field_evidence_rerun_execution_callback_intake|software_proof_docker_field_evidence_rerun_execution_callback_intake_gate|safe_to_control=false|delivery_success=false|primary_actions_enabled=false|not_proven|现场证据复跑执行回执入口" mobile/web docs/product/mobile_user_flow.md sprints/2026.05.21_01-02_field-evidence-rerun-execution-callback-intake
git diff --check -- mobile/web docs/product/mobile_user_flow.md sprints/2026.05.21_01-02_field-evidence-rerun-execution-callback-intake
```

## Product Closeout Plan

Product closeout runs only after the three Engineer workers return changed files, validation snippets, failures if any, and remaining risk.

Product closeout later owns:

- `OKR.md`
- `docs/process/okr_progress_log.md`
- `sprints/2026.05.21_01-02_field-evidence-rerun-execution-callback-intake/tech-done.md`
- `sprints/2026.05.21_01-02_field-evidence-rerun-execution-callback-intake/side2side_check.md`
- `sprints/2026.05.21_01-02_field-evidence-rerun-execution-callback-intake/final.md`

Closeout duties:

- Confirm all engineering docs under `docs/` were synchronized.
- Confirm code comments added by Engineering are Chinese and satisfy the project comment-density requirement where code was touched.
- Confirm no wording claims real现场复跑、真实 Nav2、真实 route/elevator field pass、HIL、O5 external proof、真实 phone/browser proof、PR #5 resolved, or delivery success.
- Update OKR and progress log conservatively. Do not raise Objective 5 or Objective 1 unless real evidence appears.

Product closeout acceptance commands:

```bash
test -f sprints/2026.05.21_01-02_field-evidence-rerun-execution-callback-intake/tech-done.md
test -f sprints/2026.05.21_01-02_field-evidence-rerun-execution-callback-intake/side2side_check.md
test -f sprints/2026.05.21_01-02_field-evidence-rerun-execution-callback-intake/final.md
rg -n "field_evidence_rerun_execution_callback_intake|software_proof_docker_field_evidence_rerun_execution_callback_intake_gate|safe_to_control=false|delivery_success=false|primary_actions_enabled=false|not_proven|Objective 5|Objective 1|PRRT_kwDOSWB9286CJ3tX|PR #6" OKR.md docs/process/okr_progress_log.md sprints/2026.05.21_01-02_field-evidence-rerun-execution-callback-intake
git diff --check -- OKR.md docs/process/okr_progress_log.md docs sprints/2026.05.21_01-02_field-evidence-rerun-execution-callback-intake
```

## Boundaries And Non-Claims

The implementation must not claim:

- real field rerun
- real Nav2
- real route/elevator field pass
- real task record generation
- real route completion signal generation
- real elevator door/floor/human assistance proof
- real phone/browser validation
- real PWA prompt/userChoice
- WAVE ROVER/UART/HIL
- delivery success
- dropoff completion
- cancel completion
- O5 external proof
- public HTTPS/TLS proof
- 4G/SIM proof
- OSS/CDN live traffic proof
- production DB/queue or worker/cutover proof
- PR #5 `PRRT_kwDOSWB9286CJ3tX` resolved

PR #6 remains README/docs-only with no runtime/hardware/HIL/true phone/browser/O5 external tests.

## Planning Validation Commands

The planning handoff itself must pass:

```bash
test -f sprints/2026.05.21_01-02_field-evidence-rerun-execution-callback-intake/pre_start.md
test -f sprints/2026.05.21_01-02_field-evidence-rerun-execution-callback-intake/prd.md
test -f sprints/2026.05.21_01-02_field-evidence-rerun-execution-callback-intake/tech-plan.md
rg -n "sprint_type: epic|OKR 最低优先级核对|field_evidence_rerun_execution_callback_intake|software_proof_docker_field_evidence_rerun_execution_callback_intake_gate|Objective 5|Objective 1|PRRT_kwDOSWB9286CJ3tX|PR #6|safe_to_control=false|delivery_success=false|primary_actions_enabled=false|not_proven" sprints/2026.05.21_01-02_field-evidence-rerun-execution-callback-intake
git diff --check -- sprints/2026.05.21_01-02_field-evidence-rerun-execution-callback-intake
```
