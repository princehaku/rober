# PR5 Mandatory Sensor Source Alignment Tech Plan

## Sprint Declaration

- sprint_type: epic
- Sprint: `2026.05.21_04-05_pr5-mandatory-sensor-source-alignment`
- Target capability: `pr5_mandatory_sensor_source_alignment`
- Evidence boundary: `software_proof_docker_pr5_mandatory_sensor_source_alignment_gate`
- Required preserved states: `source=software_proof`, `hardware_material_pending`, `not_proven`, `safe_to_control=false`, `delivery_success=false`, `primary_actions_enabled=false`
- Planning status: ready for four parallel Engineer workers after Product planning.

## OKR 最低优先级核对

1. Current lowest Objective in `OKR.md` 4.1: Objective 5 is about 68%, below Objective 1 at about 81% and Objectives 2/3/4 at about 99%.
2. This sprint is not targeting Objective 5 directly.
3. Reason: Objective 5 currently needs real external proof unavailable on this Docker-only host: real public HTTPS/TLS, 4G/SIM, OSS/CDN live traffic, production DB/queue, production worker/cutover, or true phone/browser external proof. Recent O5 local guards already covered multiple metadata/fail-closed states, so another local O5 wrapper would repeat the same blocker.
4. Next lowest Objective 1 is the lowest actionable Objective because PR #5 `PRRT_kwDOSWB9286CJ3tX` remains unresolved / `is_resolved=false` / material pending and the live review asks for mandatory sensor assumptions to cite local vendor source.
5. This sprint targets Objective 1 source-alignment readiness only. It must not claim HIL, real sensor procurement, installation, calibration, WAVE ROVER/UART proof, reviewer resolution, or OKR percentage movement.
6. Latest O2/O3/O4 sprint already closed a field evidence handoff and warned not to add another wrapper around the same missing real field proof. Therefore this sprint pivots to PR #5 mandatory sensor source alignment instead of continuing that chain.
7. PR #6 has no review threads and is docs-only; it is not runtime, hardware, HIL, true phone/browser, or O5 external proof.

## Evidence Inputs

- `AGENTS.md` hardware source rule: hardware work must read `docs/vendor/VENDOR_INDEX.md` and referenced local vendor files.
- `OKR.md` 4.1 current snapshot and section 6 priority guidance.
- `/Users/m4/.codex/automations/skill-progression-map/memory.md` stop rules for repeated O5/O1/route-elevator blockers.
- Latest sprint files: `sprints/2026.05.21_03-04_field-evidence-rerun-execution-callback-review-handoff/final.md` and `tech-done.md`.
- `docs/process/okr_progress_log.md` 2026-05-21 and 2026-05-20 evidence history.
- GitHub evidence supplied by main session: PR #5 unresolved thread `PRRT_kwDOSWB9286CJ3tX` asks for mandatory sensor assumptions to cite local vendor source; PR #6 has no review threads and is docs-only.

## Interface Boundary

- New proof family: `pr5_mandatory_sensor_source_alignment`.
- Output schemas to plan for implementation:
  - `trashbot.pr5_mandatory_sensor_source_alignment.v1`
  - `trashbot.pr5_mandatory_sensor_source_alignment_summary.v1`
  - `robot_diagnostics_pr5_mandatory_sensor_source_alignment_summary`
- Required source entrypoint: `docs/vendor/VENDOR_INDEX.md`.
- Required false states: `hardware_material_pending`, `not_proven`, `safe_to_control=false`, `delivery_success=false`, `primary_actions_enabled=false`.
- Required thread state: `PRRT_kwDOSWB9286CJ3tX` remains material pending until reviewer resolves it.

## Worker 1: Hardware Infra Engineer

Responsibility: canonical source-alignment PC gate and product hardware boundary.

文件范围:

- `pc-tools/evidence/pr5_mandatory_sensor_source_alignment.py`
- `tests/test_pr5_mandatory_sensor_source_alignment.py`
- `docs/interfaces/pr5_mandatory_sensor_source_alignment.md`
- `docs/product/production_hardware_boundary.md`
- current sprint implementation docs after code lands

Implementation requirements:

- Read `docs/vendor/VENDOR_INDEX.md` plus the local vendor refs it points to before writing code or docs.
- Verify that mandatory sensor assumptions separate current default hardware, target sensing baseline, and missing real materials.
- Cite local source refs for Orange Pi / WAVE ROVER / UART JSON / camera/vendor app source-boundary context.
- Mark 2D LiDAR / ToF as `hardware_material_pending` until real SKU/source/receipt/procurement/mounting/wiring/power/calibration/HIL-entry evidence exists.
- Generate artifact and summary under `software_proof_docker_pr5_mandatory_sensor_source_alignment_gate`.
- Fail closed on missing vendor index, missing source-boundary wording, unsafe success/control wording, raw absolute local paths, raw serial paths, credentials, HIL/field pass claims, PR #5 resolved claims, or delivery success.
- Keep code comments in Chinese and maintain the repo comment-quality rule for new code.

验收命令:

```bash
python3 -m py_compile pc-tools/evidence/pr5_mandatory_sensor_source_alignment.py
python3 -m unittest tests.test_pr5_mandatory_sensor_source_alignment
python3 pc-tools/evidence/pr5_mandatory_sensor_source_alignment.py --help
rg -n "pr5_mandatory_sensor_source_alignment|software_proof_docker_pr5_mandatory_sensor_source_alignment_gate|PRRT_kwDOSWB9286CJ3tX|docs/vendor/VENDOR_INDEX.md|hardware_material_pending|not_proven|delivery_success=false|primary_actions_enabled=false" pc-tools/evidence tests docs/interfaces/pr5_mandatory_sensor_source_alignment.md docs/product/production_hardware_boundary.md sprints/2026.05.21_04-05_pr5-mandatory-sensor-source-alignment
git diff --check -- pc-tools/evidence/pr5_mandatory_sensor_source_alignment.py tests/test_pr5_mandatory_sensor_source_alignment.py docs/interfaces/pr5_mandatory_sensor_source_alignment.md docs/product/production_hardware_boundary.md sprints/2026.05.21_04-05_pr5-mandatory-sensor-source-alignment
```

## Worker 2: Robot Platform Engineer

Responsibility: diagnostics safe alias.

文件范围:

- `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py`
- `onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`
- `docs/interfaces/ros_runtime_contracts.md`
- current sprint implementation docs after code lands

Implementation requirements:

- Add `robot_diagnostics_pr5_mandatory_sensor_source_alignment_summary`.
- Consume only sanitized summary data from the Hardware gate; reject unsupported schema, missing false states, unsafe success/control claims, raw source material, raw local paths, serial/UART details, credentials, ROS topic/control details, HIL/pass wording, and delivery success wording.
- Expose only thread id, source boundary, missing materials, next required evidence, owner handoff, evidence boundary, and false states.
- Preserve existing diagnostics aliases and compatibility.

验收命令:

```bash
python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py
PYTHONPATH=onboard/src/ros2_trashbot_behavior python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py
rg -n "robot_diagnostics_pr5_mandatory_sensor_source_alignment_summary|pr5_mandatory_sensor_source_alignment|software_proof_docker_pr5_mandatory_sensor_source_alignment_gate|PRRT_kwDOSWB9286CJ3tX|hardware_material_pending|not_proven|delivery_success=false|primary_actions_enabled=false" onboard/src/ros2_trashbot_behavior docs/interfaces/ros_runtime_contracts.md sprints/2026.05.21_04-05_pr5-mandatory-sensor-source-alignment
git diff --check -- onboard/src/ros2_trashbot_behavior docs/interfaces/ros_runtime_contracts.md sprints/2026.05.21_04-05_pr5-mandatory-sensor-source-alignment
```

## Worker 3: User Touchpoint Full-Stack Engineer

Responsibility: mobile/web read-only panel and phone-safe copy.

文件范围:

- `mobile/web/app.js`
- `mobile/web/fixtures/status.json`
- `mobile/web/test_mobile_web_entrypoint.py`
- `docs/product/mobile_user_flow.md`
- current sprint implementation docs after code lands

Implementation requirements:

- Add a read-only "PR #5 传感器来源对齐" panel.
- Prefer `robot_diagnostics_pr5_mandatory_sensor_source_alignment_summary`; fall back only to safe compatible summary fields already present in status/diagnostics payloads.
- Show PR #5 thread id, source-boundary refs, missing 2D LiDAR / ToF materials, next required evidence, owner handoff, evidence boundary, `hardware_material_pending`, `not_proven`, `safe_to_control=false`, `delivery_success=false`, and `primary_actions_enabled=false`.
- Never send Start Delivery, Confirm Dropoff, Cancel, ACK, cursor, diagnostics fetch, queue scheduling, callback submission, review submission, handoff submission, procurement action, GitHub action, or robot command request from the panel.
- Keep existing Start Delivery, Confirm Dropoff, and Cancel gating unchanged and fail-closed.

验收命令:

```bash
node --check mobile/web/app.js
python3 -m unittest mobile/web/test_mobile_web_entrypoint.py
python3 -m json.tool mobile/web/fixtures/status.json >/dev/null
rg -n "pr5_mandatory_sensor_source_alignment|software_proof_docker_pr5_mandatory_sensor_source_alignment_gate|PRRT_kwDOSWB9286CJ3tX|hardware_material_pending|not_proven|safe_to_control=false|delivery_success=false|primary_actions_enabled=false|PR #5 传感器来源对齐" mobile/web docs/product/mobile_user_flow.md sprints/2026.05.21_04-05_pr5-mandatory-sensor-source-alignment
git diff --check -- mobile/web docs/product/mobile_user_flow.md sprints/2026.05.21_04-05_pr5-mandatory-sensor-source-alignment
```

## Worker 4: Autonomy Algorithm Engineer

Responsibility: Nav2/fixed-route sensing-assumption boundary.

文件范围:

- `docs/navigation/fixed_route_workflow.md`
- `docs/interfaces/evidence_contracts.md`
- current sprint implementation docs after code lands

Implementation requirements:

- Document that route/fixed-route/Nav2 wording may reference the target sensing baseline only as a product assumption until real 2D LiDAR / ToF material and field evidence exist.
- Preserve the distinction between source alignment, route/elevator field materials, true Nav2/SLAM field pass, near-field safety pass, and delivery success.
- Reference `pr5_mandatory_sensor_source_alignment` as an upstream source-boundary summary, not as field proof.
- Avoid changing route runtime code in this sprint unless the implementation worker finds a hard docs/code contradiction; if that happens, Product must be notified before scope expands.

验收命令:

```bash
rg -n "pr5_mandatory_sensor_source_alignment|PRRT_kwDOSWB9286CJ3tX|2D LiDAR|ToF|hardware_material_pending|not_proven|Nav2|fixed-route|delivery_success=false" docs/navigation/fixed_route_workflow.md docs/interfaces/evidence_contracts.md sprints/2026.05.21_04-05_pr5-mandatory-sensor-source-alignment
git diff --check -- docs/navigation/fixed_route_workflow.md docs/interfaces/evidence_contracts.md sprints/2026.05.21_04-05_pr5-mandatory-sensor-source-alignment
```

## Product Closeout Plan

Product closeout owns after implementation:

- `OKR.md`
- `docs/process/okr_progress_log.md`
- `sprints/2026.05.21_04-05_pr5-mandatory-sensor-source-alignment/tech-done.md`
- `sprints/2026.05.21_04-05_pr5-mandatory-sensor-source-alignment/side2side_check.md`
- `sprints/2026.05.21_04-05_pr5-mandatory-sensor-source-alignment/final.md`

Closeout requirements:

- Confirm every implementation worker synchronized the relevant docs under `docs/`.
- Confirm no wording claims real 2D LiDAR / ToF procurement, installation, wiring, power validation, calibration, HIL entry, WAVE ROVER/UART/HIL, true Nav2/SLAM field pass, near-field safety pass, PR #5 thread resolved, O5 external proof, true phone/browser proof, dropoff/cancel completion, delivery result, or delivery success.
- Update `OKR.md` and progress log conservatively. Do not raise Objective 5 or Objective 1 unless real external/hardware/reviewer-resolution evidence appears.
- Stage only intended files, then run staged/scoped diff checks before commit and push.

Product acceptance commands after implementation:

```bash
test -f sprints/2026.05.21_04-05_pr5-mandatory-sensor-source-alignment/tech-done.md
test -f sprints/2026.05.21_04-05_pr5-mandatory-sensor-source-alignment/side2side_check.md
test -f sprints/2026.05.21_04-05_pr5-mandatory-sensor-source-alignment/final.md
rg -n "pr5_mandatory_sensor_source_alignment|software_proof_docker_pr5_mandatory_sensor_source_alignment_gate|Objective 5|Objective 1|PRRT_kwDOSWB9286CJ3tX|Docker-only|hardware_material_pending|not_proven|delivery_success=false|primary_actions_enabled=false" OKR.md docs/process/okr_progress_log.md sprints/2026.05.21_04-05_pr5-mandatory-sensor-source-alignment
git diff --check -- OKR.md docs/process/okr_progress_log.md docs sprints/2026.05.21_04-05_pr5-mandatory-sensor-source-alignment
```

## Planning-only 验收命令

The Product planning step must run:

```bash
test -f sprints/2026.05.21_04-05_pr5-mandatory-sensor-source-alignment/pre_start.md && test -f sprints/2026.05.21_04-05_pr5-mandatory-sensor-source-alignment/prd.md && test -f sprints/2026.05.21_04-05_pr5-mandatory-sensor-source-alignment/tech-plan.md
rg -n "sprint_type: epic|OKR 最低优先级核对|Objective 5|PRRT_kwDOSWB9286CJ3tX|Docker-only|验收命令|文件范围" sprints/2026.05.21_04-05_pr5-mandatory-sensor-source-alignment
git diff --check -- sprints/2026.05.21_04-05_pr5-mandatory-sensor-source-alignment
```

## Boundaries And Non-claims

This sprint must not claim real 2D LiDAR / ToF procurement, install, wiring, power validation, calibration, HIL entry, WAVE ROVER/UART/HIL, Nav2/SLAM field pass, near-field safety pass, real route/elevator field pass, real phone/browser validation, real PWA prompt/userChoice, O5 external proof, public HTTPS/TLS proof, 4G/SIM proof, OSS/CDN live traffic proof, production DB/queue or worker/cutover proof, PR #5 `PRRT_kwDOSWB9286CJ3tX` resolved, dropoff completion, cancel completion, delivery result, or delivery success.
