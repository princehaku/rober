# Field Evidence Rerun Execution Pack Tech Plan

## Sprint Declaration

- sprint_type: epic
- Sprint: `2026.05.20_18-19_field-evidence-rerun-execution-pack`
- Target capability: `field_evidence_rerun_execution_pack`
- Evidence boundary: `software_proof_docker_field_evidence_rerun_execution_pack_gate`
- Required preserved states: `software_proof`, `not_proven`, `safe_to_control=false`, `delivery_success=false`, `primary_actions_enabled=false`
- Planning status: ready for three parallel Engineer workers; this Product planning handoff implements no product code and no test code.

## OKR 最低优先级核对

1. Current lowest Objective in `OKR.md` 4.1: Objective 5 is about 68%, lower than Objective 1 at about 81% and Objectives 2/3/4 at about 99%.
2. This sprint is not targeting Objective 5 directly.
3. Reason: Objective 5 currently needs real external proof unavailable on this Docker-only host: real public HTTPS/TLS, 4G/SIM, OSS/CDN live traffic, production DB/queue, production worker/cutover, or real phone/browser external proof. Continuing local O5 metadata would repeat a blocked path and must not be counted as O5 progress.
4. Next lowest Objective 1 is about 81%, but PR #5 `PRRT_kwDOSWB9286CJ3tX` remains unresolved / `is_resolved=false` / `hardware_material_pending`; manual reply `3269642220` is not hardware proof. This host still lacks WAVE ROVER/UART/HIL and real 2D LiDAR / ToF materials.
5. Chosen sprint target: O2/O3/O4 field-evidence rerun execution pack. PR #6 is README docs-only with no runtime/hardware/HIL/true phone/browser/O5 external tests, and the latest `field_evidence_rerun_queue` final says the next actionable material step is a same-safe-`evidence_ref` field owner package for real task record, Nav2/fixed-route runtime log, route completion signal, elevator evidence, dropoff/cancel completion, delivery result, and real phone/browser evidence.

## Evidence Inputs

- `OKR.md` 4.1 current snapshot: Objective 5 about 68%; Objective 1 about 81%; O2/O3/O4 about 99%.
- PR #5 evidence: merged, but thread `PRRT_kwDOSWB9286CJ3tX` remains unresolved / `is_resolved=false` / `hardware_material_pending`; comment `3269642220` is a manual reply only, not material proof.
- PR #6 evidence: merged README docs-only, no runtime, hardware, HIL, true phone/browser, or O5 external tests.
- Previous sprint final: `sprints/2026.05.20_17-18_field-evidence-rerun-queue/final.md`, capability `field_evidence_rerun_queue`, boundary `software_proof_docker_field_evidence_rerun_queue_gate`.
- Mobile/product constraint: `docs/product/mobile_user_flow.md` keeps evidence panels read-only and primary actions fail-closed unless existing command-safety gates allow them.

## Architecture And Contract

The implementation should add one metadata-only contract family:

- Artifact family: `field_evidence_rerun_execution_pack`
- Suggested schema: `trashbot.field_evidence_rerun_execution_pack.v1`
- Suggested summary schema: `trashbot.field_evidence_rerun_execution_pack_summary.v1`
- Suggested Robot safe alias: `robot_diagnostics_field_evidence_rerun_execution_pack_summary`
- Evidence boundary: `software_proof_docker_field_evidence_rerun_execution_pack_gate`

Expected minimum output fields:

- `schema`
- `schema_version`
- `source=software_proof`
- `safe_evidence_ref`
- `source_queue_schema`
- `source_queue_status`
- `same_evidence_ref_status`
- `execution_steps`
- `material_templates`
- `owner_handoff`
- `fail_thresholds`
- `pass_thresholds`
- `backfill_instructions`
- `safe_copy`
- `not_proven`
- `safe_to_control=false`
- `delivery_success=false`
- `primary_actions_enabled=false`
- `evidence_boundary=software_proof_docker_field_evidence_rerun_execution_pack_gate`

The execution pack may say a field owner has a package ready for real-world rerun execution. It must not say the rerun happened, passed, moved the robot, proved Nav2, proved elevator delivery, proved HIL, proved external cloud, or completed delivery.

## Parallel Worker Plan

### Worker 1: Autonomy Algorithm Engineer

Responsibility: PC gate and canonical execution-pack artifact.

Allowed file range for implementation:

- `pc-tools/evidence/field_evidence_rerun_execution_pack.py`
- `tests/test_field_evidence_rerun_execution_pack.py`
- `pc-tools/README.md`
- `docs/interfaces/evidence_contracts.md`
- current sprint implementation docs after code lands

Implementation requirements:

- Consume `field_evidence_rerun_queue` artifact or `field_evidence_rerun_queue_summary`.
- Validate `source=software_proof`, `not_proven`, `safe_to_control=false`, `delivery_success=false`, `primary_actions_enabled=false`, and the source queue boundary.
- Validate same safe `evidence_ref` and reject unsafe/missing/mismatched refs.
- Emit ordered execution steps, material templates, owner handoff, same-`evidence_ref` rule, fail/pass thresholds, and backfill instructions.
- Fail closed on missing queue input, unsupported schema, unsafe copy, raw artifact exposure, success/control wording, or any true/proven delivery claim.

Acceptance commands:

```bash
python3 -m py_compile pc-tools/evidence/field_evidence_rerun_execution_pack.py
python3 -m unittest tests.test_field_evidence_rerun_execution_pack
python3 pc-tools/evidence/field_evidence_rerun_execution_pack.py --help
rg -n "field_evidence_rerun_execution_pack|software_proof_docker_field_evidence_rerun_execution_pack_gate|safe_to_control=false|delivery_success=false|primary_actions_enabled=false|not_proven" pc-tools/evidence tests pc-tools/README.md docs/interfaces/evidence_contracts.md sprints/2026.05.20_18-19_field-evidence-rerun-execution-pack
git diff --check -- pc-tools/evidence/field_evidence_rerun_execution_pack.py tests/test_field_evidence_rerun_execution_pack.py pc-tools/README.md docs/interfaces/evidence_contracts.md sprints/2026.05.20_18-19_field-evidence-rerun-execution-pack
```

### Worker 2: Robot Platform Engineer

Responsibility: diagnostics safe alias.

Allowed file range for implementation:

- existing diagnostics files that already host safe aliases
- focused diagnostics tests in the existing diagnostics test location
- `docs/interfaces/ros_runtime_contracts.md`
- current sprint implementation docs after code lands

Implementation requirements:

- Add `robot_diagnostics_field_evidence_rerun_execution_pack_summary` as a safe alias.
- Prefer canonical execution-pack summary and reject raw execution-pack material when it contains unsafe fields.
- Redact or omit raw ROS topics, `/cmd_vel`, serial/UART details, WAVE ROVER parameters, credentials, local paths, complete artifacts, checksums, traceback, HIL/pass wording, and delivery success claims.
- Preserve `software_proof_docker_field_evidence_rerun_execution_pack_gate`.
- Keep existing diagnostics aliases backward compatible.

Acceptance commands:

```bash
python3 -m py_compile pc-tools/operator_gateway_diagnostics.py
python3 -m unittest tests.test_operator_gateway_diagnostics
rg -n "robot_diagnostics_field_evidence_rerun_execution_pack_summary|field_evidence_rerun_execution_pack|software_proof_docker_field_evidence_rerun_execution_pack_gate|safe_to_control=false|delivery_success=false|primary_actions_enabled=false|not_proven" pc-tools tests docs/interfaces/ros_runtime_contracts.md sprints/2026.05.20_18-19_field-evidence-rerun-execution-pack
git diff --check -- pc-tools tests docs/interfaces/ros_runtime_contracts.md sprints/2026.05.20_18-19_field-evidence-rerun-execution-pack
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

- Add a read-only “现场证据复跑执行包” panel.
- Prefer `robot_diagnostics_field_evidence_rerun_execution_pack_summary`; fall back only to safe compatible summary fields already present in status/diagnostics payloads.
- Show safe `evidence_ref`, execution-pack status, execution steps, material templates, owner handoff, fail/pass thresholds, backfill instructions, evidence boundary, `not_proven`, `safe_to_control=false`, `delivery_success=false`, and `primary_actions_enabled=false`.
- Never send Start Delivery, Confirm Dropoff, Cancel, ACK, cursor, diagnostics fetch, queue scheduling, execution scheduling, or robot command requests from the panel.
- Keep existing Start Delivery, Confirm Dropoff, and Cancel gating unchanged.

Acceptance commands:

```bash
node --check mobile/web/app.js
python3 -m unittest mobile/web/test_mobile_web_entrypoint.py
python3 -m json.tool mobile/web/fixtures/status.json >/dev/null
rg -n "field_evidence_rerun_execution_pack|software_proof_docker_field_evidence_rerun_execution_pack_gate|safe_to_control=false|delivery_success=false|primary_actions_enabled=false|not_proven|现场证据复跑执行包" mobile/web docs/product/mobile_user_flow.md sprints/2026.05.20_18-19_field-evidence-rerun-execution-pack
git diff --check -- mobile/web docs/product/mobile_user_flow.md sprints/2026.05.20_18-19_field-evidence-rerun-execution-pack
```

## Product Closeout Plan

Product closeout runs only after the three Engineer workers return changed files, validation snippets, failures if any, and remaining risk.

Product closeout later owns:

- `OKR.md`
- `docs/process/okr_progress_log.md`
- `sprints/2026.05.20_18-19_field-evidence-rerun-execution-pack/tech-done.md`
- `sprints/2026.05.20_18-19_field-evidence-rerun-execution-pack/side2side_check.md`
- `sprints/2026.05.20_18-19_field-evidence-rerun-execution-pack/final.md`

Closeout duties:

- Confirm all engineering docs under `docs/` were synchronized.
- Confirm code comments added by Engineering are Chinese and satisfy the project comment-density requirement where code was touched.
- Confirm no wording claims real现场复跑、真实 Nav2、真实 route/elevator field pass、HIL、O5 external proof、真实 phone/browser proof、PR #5 resolved, or delivery success.
- Update OKR and progress log conservatively. Do not raise Objective 5 or Objective 1 unless real evidence appears.

Product closeout acceptance commands:

```bash
test -f sprints/2026.05.20_18-19_field-evidence-rerun-execution-pack/tech-done.md
test -f sprints/2026.05.20_18-19_field-evidence-rerun-execution-pack/side2side_check.md
test -f sprints/2026.05.20_18-19_field-evidence-rerun-execution-pack/final.md
rg -n "field_evidence_rerun_execution_pack|software_proof_docker_field_evidence_rerun_execution_pack_gate|safe_to_control=false|delivery_success=false|primary_actions_enabled=false|not_proven|Objective 5|Objective 1|PRRT_kwDOSWB9286CJ3tX|3269642220|PR #6" OKR.md docs/process/okr_progress_log.md sprints/2026.05.20_18-19_field-evidence-rerun-execution-pack
git diff --check -- OKR.md docs/process/okr_progress_log.md docs sprints/2026.05.20_18-19_field-evidence-rerun-execution-pack
```

## Boundaries And Non-Claims

The implementation must not claim:

- real field rerun
- real Nav2
- real route/elevator field pass
- real task record
- real route completion signal
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

Manual reply `3269642220` remains a published software-proof GitHub reply only. PR #6 remains README docs-only with no runtime/hardware/HIL/true phone/browser/O5 external tests.

## Planning Validation Commands

The planning handoff itself must pass:

```bash
test -f sprints/2026.05.20_18-19_field-evidence-rerun-execution-pack/pre_start.md
test -f sprints/2026.05.20_18-19_field-evidence-rerun-execution-pack/prd.md
test -f sprints/2026.05.20_18-19_field-evidence-rerun-execution-pack/tech-plan.md
rg -n "sprint_type: epic|OKR 最低优先级核对|field_evidence_rerun_execution_pack|software_proof_docker_field_evidence_rerun_execution_pack_gate|Objective 5|Objective 1|PRRT_kwDOSWB9286CJ3tX|3269642220|PR #6|safe_to_control=false|delivery_success=false|primary_actions_enabled=false|not_proven" sprints/2026.05.20_18-19_field-evidence-rerun-execution-pack
git diff --check -- sprints/2026.05.20_18-19_field-evidence-rerun-execution-pack
```
