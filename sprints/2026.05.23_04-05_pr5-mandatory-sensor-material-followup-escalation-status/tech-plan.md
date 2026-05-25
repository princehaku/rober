# PR #5 Mandatory Sensor Material Follow-Up Escalation Status Tech Plan

Run time: 2026-05-23 04:05 Asia/Shanghai

> For implementation workers: use subagent-driven development. This sprint has 3 parallel Engineer owners with disjoint file scopes, plus Product closeout after implementation. The main session must not write product code, tests, hardware config, or runtime implementation.

## Goal

Build `pr5_mandatory_sensor_material_followup_escalation_status`, the material follow-up escalation status after `pr5_mandatory_sensor_source_alignment`.

The implementation must produce only `software_proof_docker_pr5_mandatory_sensor_material_followup_escalation_status_gate` evidence and must keep `source=software_proof`, `software_proof`, `hardware_material_pending`, `not_proven`, `safe_to_control=false`, `delivery_success=false`, and `primary_actions_enabled=false`.

## Architecture

- Hardware owns the PC-only follow-up escalation status gate that consumes `pr5_mandatory_sensor_source_alignment` safe output plus a safe material follow-up packet and emits sanitized owner/reviewer material status.
- Robot owns the operator gateway diagnostics alias that exposes only safe PR #5 material follow-up metadata and fails closed.
- Full-Stack owns the `mobile/web` read-only panel that shows PR #5 material follow-up status without enabling primary actions.
- Product owns post-implementation closeout only after the three Engineer streams return evidence.

## OKR 最低优先级核对

- 当前 `OKR.md` 4.1 节完成度最低的 Objective：Objective 5，约 68%。
- 本 sprint 是否针对该最低 Objective：否。本 sprint 不直接针对 Objective 5，也不提升 Objective 5。
- 不针对 Objective 5 的理由：当前本机只有 Docker/local，没有真实 public HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/cutover、真实 phone/browser 或 verified terminal result materials；最近两轮 `2026.05.23_03-04` 与 `2026.05.23_02-03` 已连续扩展 field-evidence acceptance/handoff metadata 且均 no OKR percentage lift，继续本地 O5 metadata 会重复消费同一外部真实材料 blocker。
- 本 sprint 针对的 Objective：Objective 1。Live PR #5 evidence 显示 `PRRT_kwDOSWB9286CJ3tQ` resolved，`PRRT_kwDOSWB9286CJ3tU` resolved，`PRRT_kwDOSWB9286CJ3tX` 仍 `is_resolved=false` / `hardware_material_pending`；该 unresolved thread 的主题是 mandatory 2D LiDAR/ToF sensor assumptions 缺 `docs/vendor/` source / real hardware materials。
- 本 sprint 的 Objective 1 边界：只推进 `pr5_mandatory_sensor_material_followup_escalation_status` software-proof follow-up 状态，不 claim thread resolved、HIL、LiDAR/ToF installed、route/elevator field pass、delivery_success 或 OKR percentage lift。
- `final.md` 收口时必须复核：如果没有真实 O5 external proof、真实 O1 hardware/HIL material、PR #5 reviewer resolution、真实 route/elevator pass、真实 phone/browser 或 verified terminal result，`OKR.md` 不得提高百分比。

## Shared Contract

All owners must preserve these fields and wording:

- `pr5_mandatory_sensor_material_followup_escalation_status`
- `software_proof_docker_pr5_mandatory_sensor_material_followup_escalation_status_gate`
- Previous capability: `pr5_mandatory_sensor_source_alignment`
- Previous boundary: `software_proof_docker_pr5_mandatory_sensor_source_alignment_gate`
- `source=software_proof`
- `software_proof`
- `hardware_material_pending`
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
- `ready_for_reviewer_followup_not_proven`

Required owner/reviewer follow-up checklist:

- 2D LiDAR SKU/source/receipt/procurement material
- ToF SKU/source/receipt/procurement material
- mounting/installation material
- wiring and power-budget material
- calibration plan or calibration result
- HIL-entry material
- operator HIL report
- PR #5 reviewer follow-up or reviewer resolution evidence

Forbidden claims:

- real HIL
- WAVE ROVER/UART proof
- LiDAR/ToF installed
- real route/elevator field pass
- real Nav2/fixed-route runtime pass
- real phone/browser proof
- Objective 5 external proof
- verified terminal result
- dropoff/cancel completion
- `delivery_success=true`
- PR #5 reviewer resolution unless live thread state proves it

Forbidden exposure:

- raw ROS topics, `/cmd_vel`, serial/UART paths, baudrate values, WAVE ROVER parameters
- credentials, bearer tokens, Authorization headers, OSS AK/SK, DB/queue URLs
- raw artifacts, complete artifacts, local paths, checksums, tracebacks
- success phrasing, control-enable copy, or hidden primary-action enablement

## Parallel Owner Plan

### Task A: Hardware PC Gate + Tests + Boundary Docs

Role id: `rober-hardware-engineer`

Files:

- Create: `pc-tools/evidence/pr5_mandatory_sensor_material_followup_escalation_status.py`
- Create: `pc-tools/evidence/test_pr5_mandatory_sensor_material_followup_escalation_status.py`
- Modify: `pc-tools/README.md`
- Modify: `docs/interfaces/pr5_mandatory_sensor_source_alignment.md`
- Optionally modify if needed for boundary refs only: `docs/product/production_hardware_boundary.md`

Interface impact:

- Adds a PC-only evidence artifact and summary contract. It must not alter ROS2 runtime APIs, cloud APIs, mobile command endpoints, hardware parameters, launch defaults, vendor files, or existing source-alignment outputs.

Source requirement:

- Before implementing, re-read `docs/vendor/VENDOR_INDEX.md` and keep the source boundary explicit. Local vendor files can support Orange Pi / WAVE ROVER / UART source context only; they do not prove a project 2D LiDAR / ToF SKU/source/receipt, purchase, installation, wiring, power, calibration, HIL entry, PR #5 resolution, O5 external proof, or delivery success.

Responsibilities:

1. Implement a CLI gate that accepts the previous `pr5_mandatory_sensor_source_alignment` artifact, summary, or Robot diagnostics safe alias plus a safe material follow-up packet.
2. Require the previous safe output to include `pr5_mandatory_sensor_source_alignment`, the same safe `evidence_ref`, and the boundary `software_proof_docker_pr5_mandatory_sensor_source_alignment_gate`.
3. Emit status `pending`, `overdue`, `escalated`, `blocked`, or `ready_for_reviewer_followup_not_proven` only when the prior source alignment is safe, the follow-up packet is safe, same-`evidence_ref` matches, and no unsafe copy, success claim, control-enable state, credentials, raw artifact exposure, external-proof claim, HIL claim, installed-sensor claim, or PR #5 resolution claim appears.
4. Fail closed to `blocked` with structured reasons for missing source alignment, missing required material, evidence-ref mismatch, unsafe copy, or forbidden proof/control claims.
5. Emit only safe summary fields for Robot/mobile and keep `source=software_proof`, `software_proof`, `hardware_material_pending`, `not_proven`, `safe_to_control=false`, `delivery_success=false`, and `primary_actions_enabled=false`.
6. Add targeted tests for pending, overdue, escalated, ready-for-reviewer-followup-not-proven, blocked missing source alignment, evidence-ref mismatch, and unsafe/success/HIL/installed-sensor claim rejection.

Risk boundary:

- This gate can package safe follow-up status only. It must not read or validate raw field logs as true proof, must not claim LiDAR/ToF installation, and must not unblock controls.

Acceptance commands:

```bash
python3 -m py_compile pc-tools/evidence/pr5_mandatory_sensor_material_followup_escalation_status.py
python3 -m unittest pc-tools/evidence/test_pr5_mandatory_sensor_material_followup_escalation_status.py
python3 pc-tools/evidence/pr5_mandatory_sensor_material_followup_escalation_status.py --help
rg -n "pr5_mandatory_sensor_material_followup_escalation_status|software_proof_docker_pr5_mandatory_sensor_material_followup_escalation_status_gate|source=software_proof|hardware_material_pending|not_proven|delivery_success=false|primary_actions_enabled=false|safe_to_control=false|pending|overdue|escalated|blocked|ready_for_reviewer_followup_not_proven|PRRT_kwDOSWB9286CJ3tX" pc-tools/evidence/pr5_mandatory_sensor_material_followup_escalation_status.py pc-tools/evidence/test_pr5_mandatory_sensor_material_followup_escalation_status.py pc-tools/README.md docs/interfaces/pr5_mandatory_sensor_source_alignment.md docs/product/production_hardware_boundary.md
git diff --check -- pc-tools/evidence/pr5_mandatory_sensor_material_followup_escalation_status.py pc-tools/evidence/test_pr5_mandatory_sensor_material_followup_escalation_status.py pc-tools/README.md docs/interfaces/pr5_mandatory_sensor_source_alignment.md docs/product/production_hardware_boundary.md
```

### Task B: Robot Diagnostics Safe Alias + Tests + Diagnostics Docs

Role id: `robot-software-engineer`

Files:

- Modify: `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py`
- Modify: `onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`
- Modify: `docs/interfaces/ros_runtime_contracts.md`

Interface impact:

- Adds a diagnostics safe alias for existing operator-gateway summary surfaces. It must not add robot commands, change task_orchestrator semantics, expose ROS topics, change launch defaults, or change primary action authorization.

Responsibilities:

1. Add Robot diagnostics support for `pr5_mandatory_sensor_material_followup_escalation_status` safe summary.
2. Expose a safe alias such as `robot_diagnostics_pr5_mandatory_sensor_material_followup_escalation_status_summary`.
3. Preserve fail-closed defaults when the summary is missing, malformed, unsupported, unsafe, or contains success/control/external-proof/HIL/installed-sensor/PR-resolution wording.
4. Expose only follow-up status, source alignment status, safe `evidence_ref`, pending/overdue/escalated/blocked reasons, missing required material refs, owner/reviewer next step, evidence boundary, `software_proof`, `hardware_material_pending`, `not_proven`, `source=software_proof`, `safe_to_control=false`, `delivery_success=false`, and `primary_actions_enabled=false`.
5. Do not expose raw manifest contents, local paths, checksums, tracebacks, ROS topics, `/cmd_vel`, serial/UART details, WAVE ROVER details, credentials, DB/queue URLs, or complete artifacts.
6. Add targeted diagnostics tests without broad unrelated regression sweeps.

Risk boundary:

- Diagnostics must remain read-only support metadata. Follow-up statuses are not real sensor material proof and must not enable Start/Confirm/Cancel.

Acceptance commands:

```bash
python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py
python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py
rg -n "pr5_mandatory_sensor_material_followup_escalation_status|software_proof_docker_pr5_mandatory_sensor_material_followup_escalation_status_gate|source=software_proof|hardware_material_pending|not_proven|delivery_success=false|primary_actions_enabled=false|safe_to_control=false|pending|overdue|escalated|blocked|ready_for_reviewer_followup_not_proven|PRRT_kwDOSWB9286CJ3tX" onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py docs/interfaces/ros_runtime_contracts.md
git diff --check -- onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py docs/interfaces/ros_runtime_contracts.md
```

### Task C: Full-Stack Mobile/Web Read-Only Panel + Fixture + Tests + Mobile Docs

Role id: `full-stack-software-engineer`

Files:

- Modify: `mobile/web/app.js`
- Create: `mobile/web/fixtures/robot_diagnostics_pr5_mandatory_sensor_material_followup_escalation_status.json`
- Modify: `mobile/web/test_mobile_web_entrypoint.py`
- Modify: `docs/product/mobile_user_flow.md`

Interface impact:

- Adds one read-only mobile panel that consumes existing status/diagnostics summaries. It must not add fetch routes, command routes, ACK/cursor routes, material upload routes, review routes, handoff routes, follow-up routes, or hidden action enablement.

Responsibilities:

1. Add a read-only “PR #5 强制传感器材料跟进升级状态” panel for `pr5_mandatory_sensor_material_followup_escalation_status`.
2. Consume `robot_diagnostics_pr5_mandatory_sensor_material_followup_escalation_status_summary` first, then compatible safe summaries from existing status/diagnostics shapes.
3. Show only follow-up status, source alignment status, safe `evidence_ref`, missing required material refs, pending/overdue/escalated/blocked reasons, owner/reviewer next step, evidence boundary, `source=software_proof`, `software_proof`, `hardware_material_pending`, `not_proven`, `safe_to_control=false`, `delivery_success=false`, and `primary_actions_enabled=false`.
4. Keep Start Delivery, Confirm Dropoff, and Cancel disabled under the fixture.
5. Do not fetch raw artifacts, raw diagnostics, ACK/cursor routes, material routes, callback routes, review routes, handoff routes, follow-up routes, Start/Confirm/Cancel endpoints, or robot command endpoints from this panel.
6. Add a fixture and targeted mobile test for render, fail-closed controls, redaction boundaries, and no success/control copy.

Risk boundary:

- The panel is support-facing read-only status. It must not turn a material follow-up escalation into true phone/browser proof, sensor installed proof, field pass, delivery success, verified terminal result, or control permission.

Acceptance commands:

```bash
node --check mobile/web/app.js
python3 -m json.tool mobile/web/fixtures/robot_diagnostics_pr5_mandatory_sensor_material_followup_escalation_status.json >/tmp/pr5_mandatory_sensor_material_followup_escalation_status_fixture.json
python3 -m unittest mobile/web/test_mobile_web_entrypoint.py
rg -n "pr5_mandatory_sensor_material_followup_escalation_status|software_proof_docker_pr5_mandatory_sensor_material_followup_escalation_status_gate|source=software_proof|hardware_material_pending|not_proven|delivery_success=false|primary_actions_enabled=false|safe_to_control=false|pending|overdue|escalated|blocked|ready_for_reviewer_followup_not_proven|PRRT_kwDOSWB9286CJ3tX" mobile/web/app.js mobile/web/fixtures/robot_diagnostics_pr5_mandatory_sensor_material_followup_escalation_status.json mobile/web/test_mobile_web_entrypoint.py docs/product/mobile_user_flow.md
git diff --check -- mobile/web/app.js mobile/web/fixtures/robot_diagnostics_pr5_mandatory_sensor_material_followup_escalation_status.json mobile/web/test_mobile_web_entrypoint.py docs/product/mobile_user_flow.md
```

### Task D: Product Closeout After A/B/C

Role id: `product-okr-owner`

Files:

- Create or modify: `sprints/2026.05.23_04-05_pr5-mandatory-sensor-material-followup-escalation-status/tech-done.md`
- Create or modify: `sprints/2026.05.23_04-05_pr5-mandatory-sensor-material-followup-escalation-status/side2side_check.md`
- Create or modify: `sprints/2026.05.23_04-05_pr5-mandatory-sensor-material-followup-escalation-status/final.md`
- Modify: `OKR.md`
- Modify: `docs/process/okr_progress_log.md`

Interface impact:

- Product closeout updates sprint evidence and OKR/progress narrative only. It must not modify product code, tests, hardware configuration, mobile runtime, PC gates, or Robot diagnostics implementation.

Responsibilities:

1. Integrate the three Engineer reports and record actual changed files, validation results, deviations, and remaining risks.
2. Confirm A/B/C docs updates landed under `docs/interfaces/` and `docs/product/`.
3. Keep `OKR.md` conservative: Objective 5 remains around 68% unless real O5 external evidence appears; Objective 1 remains around 81% unless real PR #5/hardware/HIL material appears; Objectives 2/3/4 remain unchanged unless real field/mobile/delivery evidence appears.
4. Write final closeout so this sprint is accepted only as `software_proof_docker_pr5_mandatory_sensor_material_followup_escalation_status_gate`.
5. Explicitly state that PR #5 `PRRT_kwDOSWB9286CJ3tX` remains unresolved unless a live reviewer resolution is present.
6. Preserve `delivery_success=false`, `primary_actions_enabled=false`, `safe_to_control=false`, `not_proven`, and no real route/elevator/phone/HIL/O5 claims.

Risk boundary:

- Product closeout may document readiness and no-lift status only. It must not raise OKR completion or imply real field acceptance unless real materials are present.

Acceptance commands:

```bash
test -f sprints/2026.05.23_04-05_pr5-mandatory-sensor-material-followup-escalation-status/tech-done.md && test -f sprints/2026.05.23_04-05_pr5-mandatory-sensor-material-followup-escalation-status/side2side_check.md && test -f sprints/2026.05.23_04-05_pr5-mandatory-sensor-material-followup-escalation-status/final.md
rg -n "software_proof_docker_pr5_mandatory_sensor_material_followup_escalation_status_gate|Objective 5|Objective 1|Objective 2|Objective 3|Objective 4|PRRT_kwDOSWB9286CJ3tX|delivery_success=false|primary_actions_enabled=false|safe_to_control=false|not_proven" sprints/2026.05.23_04-05_pr5-mandatory-sensor-material-followup-escalation-status OKR.md docs/process/okr_progress_log.md
git diff --check -- sprints/2026.05.23_04-05_pr5-mandatory-sensor-material-followup-escalation-status OKR.md docs/process/okr_progress_log.md
```

## Dispatch Requirements

Implementation must start 3 parallel Engineer workers in one dispatch set:

- Hardware Infra Engineer for PC evidence material follow-up escalation status gate files.
- Robot Platform Engineer for diagnostics/runtime contract files.
- User Touchpoint Full-Stack Engineer for `mobile/web` files.

Product closeout starts only after the three Engineer workers return. If any owner fails validation, send the failure back to the same owner before closeout.

## Planning Validation Commands

The Product Owner planning task must run:

```bash
test -f sprints/2026.05.23_04-05_pr5-mandatory-sensor-material-followup-escalation-status/pre_start.md && test -f sprints/2026.05.23_04-05_pr5-mandatory-sensor-material-followup-escalation-status/prd.md && test -f sprints/2026.05.23_04-05_pr5-mandatory-sensor-material-followup-escalation-status/tech-plan.md
rg -n "sprint_type: epic|OKR 最低优先级核对|pr5_mandatory_sensor_material_followup_escalation_status|PRRT_kwDOSWB9286CJ3tX|Objective 5|Objective 1|software_proof_docker_pr5_mandatory_sensor_material_followup_escalation_status_gate|delivery_success=false|primary_actions_enabled=false|safe_to_control=false|not_proven" sprints/2026.05.23_04-05_pr5-mandatory-sensor-material-followup-escalation-status
git diff --check -- sprints/2026.05.23_04-05_pr5-mandatory-sensor-material-followup-escalation-status
```
