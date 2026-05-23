# PR #5 Mandatory Sensor Material Owner Response Intake - Tech Plan

Capability: `pr5_mandatory_sensor_material_owner_response_intake`

Evidence boundary: `software_proof_docker_pr5_mandatory_sensor_material_owner_response_intake_gate`

This plan is ready for parallel implementation by three owners. It does not implement product code during planning.

## OKR 最低优先级核对

- 当前 `OKR.md` 4.1 节里完成度最低的 Objective：Objective 5，约 68%。
- 本 sprint 是否针对该最低 Objective：否。
- 不针对 Objective 5 的理由：`OKR.md` line 207 area requires at least one real external or terminal material before more O5 completion work: public HTTPS/TLS, 4G/SIM, OSS/CDN live traffic, production DB/queue, worker/cutover, true phone/browser, or verified terminal delivery/dropoff/cancel result. The current host is Docker-only and has none of these materials. Recent work already covered O5 terminal-result owner-response review-decision metadata and O4 current-panel browser proof refresh, both without OKR lift, so more local O5 metadata would repeat the same blocker.
- 本 sprint 针对的下一低项 Objective：Objective 1，约 81%。
- Objective 1 evidence: live PR #5 review threads show `PRRT_kwDOSWB9286CJ3tQ` resolved, `PRRT_kwDOSWB9286CJ3tU` resolved, and `PRRT_kwDOSWB9286CJ3tX` unresolved / `is_resolved=false` / `hardware_material_pending`. The unresolved thread is on `docs/product/production_hardware_boundary.md` and asks for vendor-source evidence for mandatory sensor assumptions.
- Objective 1 boundary: this sprint advances only `pr5_mandatory_sensor_material_owner_response_intake` software proof. It must not claim PR thread resolved, LiDAR/ToF installed, HIL, WAVE ROVER/UART proof, route/elevator field pass, true phone/browser, Objective 5 external proof, OKR percentage lift, or delivery success.

## Shared Evidence Rules

All owners must preserve:

- `software_proof`
- `hardware_material_pending`
- `not_proven`
- `delivery_success=false`
- `primary_actions_enabled=false`
- `safe_to_control=false`
- `PRRT_kwDOSWB9286CJ3tX` unresolved / `is_resolved=false` unless live reviewer state changes
- `docs/vendor/VENDOR_INDEX.md` as the local hardware source-boundary entrypoint

Allowed owner-response intake decisions:

- `accepted`
- `missing`
- `rejected`
- `unsafe`
- `blocked`

Disallowed claims:

- PR #5 `PRRT_kwDOSWB9286CJ3tX` resolved
- 2D LiDAR / ToF SKU/source/receipt/procurement proven
- 2D LiDAR / ToF installed, wired, powered, calibrated, or HIL-proven
- WAVE ROVER/UART/HIL proof
- `/odom`, `/imu/data`, `/battery` real robot proof
- route/elevator field pass
- Nav2/fixed-route runtime pass
- true phone/browser proof
- public HTTPS/TLS, 4G/SIM, OSS/CDN live traffic, production DB/queue, or worker/cutover
- verified terminal delivery/dropoff/cancel result
- delivery success or primary action enablement

## Parallel Owner Plan

Start these three implementation workers in parallel. Their file ranges are intentionally disjoint except for shared read-only references.

### Owner A: Hardware Infra Engineer

Responsibility: PC gate plus hardware/vendor documentation.

Allowed file range:

- Create: `pc-tools/evidence/pr5_mandatory_sensor_material_owner_response_intake.py`
- Create: `pc-tools/evidence/test_pr5_mandatory_sensor_material_owner_response_intake.py`
- Modify: `pc-tools/README.md`
- Modify: `docs/product/production_hardware_boundary.md`
- Create or modify: `docs/interfaces/pr5_mandatory_sensor_material_owner_response_intake.md`

Read-only references:

- `AGENTS.md`
- `OKR.md`
- `docs/vendor/VENDOR_INDEX.md`
- `docs/product/production_hardware_boundary.md`
- `sprints/2026.05.23_04-05_pr5-mandatory-sensor-material-followup-escalation-status/tech-done.md`
- Existing `pc-tools/evidence/pr5_mandatory_sensor_material_followup_escalation_status.py`

Implementation requirements:

1. Read `docs/vendor/VENDOR_INDEX.md` before writing hardware-related logic or docs.
2. Consume a previous `pr5_mandatory_sensor_material_followup_escalation_status` safe summary.
3. Consume a sanitized owner response packet containing safe references only: owner id/role, response status, same safe `evidence_ref`, material refs, missing refs, rejected refs, reviewer next step, and safe notes.
4. Fail closed if the owner response includes raw artifact bodies, credentials, signed URLs, ROS topics, `/cmd_vel`, serial/UART paths, baudrate values, WAVE ROVER parameters, checksums, local filesystem paths, HIL/pass copy, installed-sensor claims, delivery-success claims, or PR-resolution claims.
5. Emit `accepted`, `missing`, `rejected`, `unsafe`, or `blocked`.
6. Emit safe summary fields for Robot/mobile consumption and preserve `software_proof`, `hardware_material_pending`, `not_proven`, `delivery_success=false`, `primary_actions_enabled=false`, and `safe_to_control=false`.
7. Document that local vendor files support Orange Pi Zero 3 and WAVE ROVER UART JSON source attribution only, not 2D LiDAR / ToF real-material proof.

Acceptance commands:

```bash
python3 -m py_compile pc-tools/evidence/pr5_mandatory_sensor_material_owner_response_intake.py
python3 -m unittest pc-tools/evidence/test_pr5_mandatory_sensor_material_owner_response_intake.py
python3 pc-tools/evidence/pr5_mandatory_sensor_material_owner_response_intake.py --help
rg -n "pr5_mandatory_sensor_material_owner_response_intake|software_proof_docker_pr5_mandatory_sensor_material_owner_response_intake_gate|hardware_material_pending|not_proven|delivery_success=false|primary_actions_enabled=false|safe_to_control=false|accepted|missing|rejected|unsafe|blocked|PRRT_kwDOSWB9286CJ3tX|docs/vendor/VENDOR_INDEX.md" pc-tools/evidence/pr5_mandatory_sensor_material_owner_response_intake.py pc-tools/evidence/test_pr5_mandatory_sensor_material_owner_response_intake.py pc-tools/README.md docs/product/production_hardware_boundary.md docs/interfaces/pr5_mandatory_sensor_material_owner_response_intake.md
git diff --check -- pc-tools/evidence/pr5_mandatory_sensor_material_owner_response_intake.py pc-tools/evidence/test_pr5_mandatory_sensor_material_owner_response_intake.py pc-tools/README.md docs/product/production_hardware_boundary.md docs/interfaces/pr5_mandatory_sensor_material_owner_response_intake.md
```

### Owner B: Robot Platform Engineer

Responsibility: diagnostics safe alias plus interface documentation.

Allowed file range:

- Modify: `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py`
- Modify: `onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`
- Modify: `docs/interfaces/ros_runtime_contracts.md`
- Modify: `docs/interfaces/pr5_mandatory_sensor_material_owner_response_intake.md`

Read-only references:

- `AGENTS.md`
- `OKR.md`
- Hardware owner output from Owner A after available
- Existing diagnostics patterns for `robot_diagnostics_pr5_mandatory_sensor_material_followup_escalation_status_summary`

Implementation requirements:

1. Add Robot diagnostics support for `pr5_mandatory_sensor_material_owner_response_intake` safe summaries.
2. Expose safe alias `robot_diagnostics_pr5_mandatory_sensor_material_owner_response_intake_summary`.
3. Consume only safe summary fields from the PC gate output; do not read raw owner response bodies.
4. Include decision, source follow-up status, safe `evidence_ref`, accepted/missing/rejected/unsafe refs, next required evidence, owner/reviewer next step, evidence boundary, and conservative flags.
5. Preserve `safe_to_control=false`, `delivery_success=false`, and `primary_actions_enabled=false`.
6. Keep technical comments in Chinese and focused on why raw owner material must stay outside Robot diagnostics.

Acceptance commands:

```bash
python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py
python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py
rg -n "pr5_mandatory_sensor_material_owner_response_intake|robot_diagnostics_pr5_mandatory_sensor_material_owner_response_intake_summary|software_proof_docker_pr5_mandatory_sensor_material_owner_response_intake_gate|hardware_material_pending|not_proven|delivery_success=false|primary_actions_enabled=false|safe_to_control=false|accepted|missing|rejected|unsafe|blocked|PRRT_kwDOSWB9286CJ3tX" onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py docs/interfaces/ros_runtime_contracts.md docs/interfaces/pr5_mandatory_sensor_material_owner_response_intake.md
git diff --check -- onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py docs/interfaces/ros_runtime_contracts.md docs/interfaces/pr5_mandatory_sensor_material_owner_response_intake.md
```

### Owner C: User Touchpoint Full-Stack Engineer

Responsibility: mobile/web read-only panel plus product-flow documentation.

Allowed file range:

- Modify: `mobile/web/app.js`
- Create: `mobile/web/fixtures/robot_diagnostics_pr5_mandatory_sensor_material_owner_response_intake.json`
- Modify: `mobile/web/test_mobile_web_entrypoint.py`
- Modify: `docs/product/mobile_user_flow.md`

Read-only references:

- `AGENTS.md`
- `OKR.md`
- `docs/product/mobile_user_flow.md`
- Robot safe alias contract from Owner B after available
- Existing mobile panels for PR #5 follow-up escalation and material owner-response flows

Implementation requirements:

1. Add a read-only panel for `pr5_mandatory_sensor_material_owner_response_intake`.
2. Prefer `robot_diagnostics_pr5_mandatory_sensor_material_owner_response_intake_summary`; allow only compatible safe-summary fallbacks.
3. Show decision, source follow-up status, safe `evidence_ref`, accepted/missing/rejected/unsafe reasons, next required evidence, owner/reviewer next step, evidence boundary, and conservative flags.
4. Never add copy/export/raw-material controls for this panel.
5. Never trigger ACK, cursor, diagnostics fetch, Start Delivery, Confirm Dropoff, Cancel, review routes, material routes, or robot command requests.
6. Keep Start Delivery, Confirm Dropoff, and Cancel controlled only by existing action gates and preserve disabled state when `primary_actions_enabled=false`.
7. Filter raw JSON, ROS topics, `/cmd_vel`, serial/UART paths, credentials, local paths, complete artifacts, checksums, WAVE ROVER parameters, Objective 5 external proof claims, real phone/browser claims, HIL/pass wording, and delivery-success claims.

Acceptance commands:

```bash
python3 -m json.tool mobile/web/fixtures/robot_diagnostics_pr5_mandatory_sensor_material_owner_response_intake.json >/tmp/pr5_mandatory_sensor_material_owner_response_intake_fixture.json
python3 -m unittest mobile.web.test_mobile_web_entrypoint
rg -n "pr5_mandatory_sensor_material_owner_response_intake|robot_diagnostics_pr5_mandatory_sensor_material_owner_response_intake_summary|software_proof_docker_pr5_mandatory_sensor_material_owner_response_intake_gate|hardware_material_pending|not_proven|delivery_success=false|primary_actions_enabled=false|safe_to_control=false|accepted|missing|rejected|unsafe|blocked|PRRT_kwDOSWB9286CJ3tX" mobile/web/app.js mobile/web/fixtures/robot_diagnostics_pr5_mandatory_sensor_material_owner_response_intake.json mobile/web/test_mobile_web_entrypoint.py docs/product/mobile_user_flow.md
git diff --check -- mobile/web/app.js mobile/web/fixtures/robot_diagnostics_pr5_mandatory_sensor_material_owner_response_intake.json mobile/web/test_mobile_web_entrypoint.py docs/product/mobile_user_flow.md
```

## Product Closeout Plan

Product closeout is not part of the three parallel implementation owners. Run it after the three owner outputs are available.

Allowed file range:

- Create: `sprints/2026.05.23_16-17_pr5-mandatory-sensor-material-owner-response-intake/tech-done.md`
- Create: `sprints/2026.05.23_16-17_pr5-mandatory-sensor-material-owner-response-intake/side2side_check.md`
- Create: `sprints/2026.05.23_16-17_pr5-mandatory-sensor-material-owner-response-intake/final.md`
- Modify: `OKR.md`
- Modify: `docs/process/okr_progress_log.md`

Closeout requirements:

1. Re-check live PR #5 thread state before final wording.
2. Summarize actual files changed and each owner validation result.
3. Keep acceptance as `software_proof_docker_pr5_mandatory_sensor_material_owner_response_intake_gate`.
4. Keep Objective 5 around 68% unless real O5 materials appear.
5. Keep Objective 1 around 81% unless real PR #5/hardware/HIL material or reviewer resolution appears.
6. Preserve no real route/elevator/phone/HIL/O5/delivery claims.
7. Record whether docs under `docs/` were synchronized and whether code comments added by engineers are Chinese and sufficient for touched implementation files.

Product validation commands:

```bash
rg -n "software_proof_docker_pr5_mandatory_sensor_material_owner_response_intake_gate|Objective 5|Objective 1|PRRT_kwDOSWB9286CJ3tX|hardware_material_pending|not_proven|delivery_success=false|primary_actions_enabled=false|safe_to_control=false|no OKR percentage lift" sprints/2026.05.23_16-17_pr5-mandatory-sensor-material-owner-response-intake OKR.md docs/process/okr_progress_log.md
git diff --check -- sprints/2026.05.23_16-17_pr5-mandatory-sensor-material-owner-response-intake OKR.md docs/process/okr_progress_log.md
```

## Integration Acceptance

The sprint can proceed to implementation when:

- the three parallel owners have disjoint file ranges;
- each owner has an explicit acceptance command set;
- the shared evidence boundary is named consistently;
- the O5 skip rationale is explicit;
- the O1 PR #5 unresolved thread is explicit;
- `docs/vendor/VENDOR_INDEX.md` remains the hardware-source entrypoint;
- no planning doc asks any worker to claim hardware proof, HIL, PR resolution, O5 external proof, true phone/browser proof, or delivery success.

## Planning Validation Commands

Run after creating the first three planning docs:

```bash
test -f sprints/2026.05.23_16-17_pr5-mandatory-sensor-material-owner-response-intake/pre_start.md && test -f sprints/2026.05.23_16-17_pr5-mandatory-sensor-material-owner-response-intake/prd.md && test -f sprints/2026.05.23_16-17_pr5-mandatory-sensor-material-owner-response-intake/tech-plan.md
rg -n "sprint_type: epic|OKR 最低优先级核对|Objective 5|Objective 1|PRRT_kwDOSWB9286CJ3tX|pr5_mandatory_sensor_material_owner_response_intake|software_proof_docker_pr5_mandatory_sensor_material_owner_response_intake_gate|hardware_material_pending|not_proven|delivery_success=false|primary_actions_enabled=false|safe_to_control=false|docs/vendor/VENDOR_INDEX.md" sprints/2026.05.23_16-17_pr5-mandatory-sensor-material-owner-response-intake
git diff --check -- sprints/2026.05.23_16-17_pr5-mandatory-sensor-material-owner-response-intake
```
