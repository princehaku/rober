# PR #5 Mandatory Sensor Material Owner Response Review Decision - Tech Plan

Capability: `pr5_mandatory_sensor_material_owner_response_review_decision`

Evidence boundary: `software_proof_docker_pr5_mandatory_sensor_material_owner_response_review_decision_gate`

This plan is ready for implementation by four owners. The first three owners should run in parallel because their write scopes are disjoint except for documented contract references. Product closeout runs after engineering evidence is available.

## OKR 最低优先级核对

- 当前 `OKR.md` 4.1 节里完成度最低的 Objective：Objective 5，约 68%。
- 本 sprint 是否针对该最低 Objective：否。
- 不针对 Objective 5 的理由：本机没有真实硬件、只有 Docker，也没有 public HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/cutover、真实手机/browser 或 verified terminal result material。继续做 O5 本地 metadata depth 不会形成真实外部证据，也不会带来 OKR 百分比提升。
- 本 sprint 针对的下一低且有 live PR evidence 的 Objective：Objective 1，约 81%。
- Objective 1 evidence：PR #5 live review thread `PRRT_kwDOSWB9286CJ3tX` 仍 unresolved / `is_resolved=false` / `is_outdated=false` / `resolved_by=null`，path `docs/product/production_hardware_boundary.md`，问题是 mandatory sensor assumptions 需要 `docs/vendor/` source attribution 和真实 2D LiDAR / ToF material。
- 本 sprint 目标边界：`software_proof_docker_pr5_mandatory_sensor_material_owner_response_review_decision_gate`。它只把 safe owner response intake metadata 转成 review-decision 状态，不证明真实硬件、真实 LiDAR/ToF、HIL、PR #5 resolution、delivery success 或 O5 external proof。

## Repeated Blocker Scan

Latest two finals reviewed before planning:

- `sprints/2026.05.23_16-17_pr5-mandatory-sensor-material-owner-response-intake/final.md`: intake rung landed as `software_proof_docker_pr5_mandatory_sensor_material_owner_response_intake_gate`; `PRRT_kwDOSWB9286CJ3tX` remains unresolved and `hardware_material_pending`.
- `sprints/2026.05.23_15-16_mobile-current-panel-browser-proof-refresh-terminal-result-owner-response/final.md`: mobile current-panel proof refresh landed; real O5 external proof, true phone/browser, HIL, and PR #5 material remain missing.

Decision: this sprint is not third-round consumption of the same blocker. It is the required next rung after intake: `pr5_mandatory_sensor_material_owner_response_review_decision`. If implementation cannot consume an existing safe intake summary, it must emit `blocked_missing_owner_response_intake_not_proven` rather than broadening claims.

## Shared Evidence Rules

All owners must preserve:

- `software_proof`
- `hardware_material_pending`
- `not_proven`
- `delivery_success=false`
- `primary_actions_enabled=false`
- `safe_to_control=false`
- `PRRT_kwDOSWB9286CJ3tX` unresolved unless live reviewer state changes in a later closeout
- `docs/vendor/VENDOR_INDEX.md` as the local hardware source-boundary entrypoint

Allowed review-decision states:

- `accepted_for_reviewer_closeout_not_proven`
- `needs_more_material_not_proven`
- `rejected_unsafe_material_not_proven`
- `blocked_missing_owner_response_intake_not_proven`
- `blocked_evidence_ref_mismatch_not_proven`

Disallowed claims:

- PR #5 `PRRT_kwDOSWB9286CJ3tX` resolved
- real 2D LiDAR / ToF source, SKU, receipt, procurement, installation, wiring, power, calibration, or HIL proof
- WAVE ROVER/UART/HIL proof
- `/odom`, `/imu/data`, `/battery` real robot proof
- route/elevator field pass
- Nav2/fixed-route runtime pass
- true phone/browser proof
- public HTTPS/TLS, 4G/SIM, OSS/CDN live traffic, production DB/queue, worker/cutover
- verified terminal delivery/dropoff/cancel result
- delivery success or primary action enablement

## Parallel Owner Plan

### Owner A: Hardware Infra Engineer - PC Gate

Responsibility: implement the fail-closed PC review-decision gate and hardware/source-boundary docs.

Allowed file range:

- Create: `pc-tools/evidence/pr5_mandatory_sensor_material_owner_response_review_decision.py`
- Create: `pc-tools/evidence/test_pr5_mandatory_sensor_material_owner_response_review_decision.py`
- Modify: `pc-tools/README.md`
- Modify: `docs/product/production_hardware_boundary.md`
- Create or modify: `docs/interfaces/pr5_mandatory_sensor_material_owner_response_review_decision.md`

Read-only references:

- `AGENTS.md`
- `OKR.md`
- `docs/vendor/VENDOR_INDEX.md`
- `docs/product/production_hardware_boundary.md`
- `docs/interfaces/pr5_mandatory_sensor_material_owner_response_intake.md`
- `pc-tools/evidence/pr5_mandatory_sensor_material_owner_response_intake.py`
- `sprints/2026.05.23_16-17_pr5-mandatory-sensor-material-owner-response-intake/final.md`

Implementation requirements:

1. Read `docs/vendor/VENDOR_INDEX.md` before writing hardware-related logic or docs.
2. Consume only sanitized `pr5_mandatory_sensor_material_owner_response_intake` artifact or summary fields.
3. Require the same safe `evidence_ref` across follow-up, owner-response intake, and review-decision output.
4. Emit one of the allowed review-decision states.
5. Fail closed if intake is missing, unsupported, unsafe, raw, credential-like, local-path-like, serial/UART-detail-like, ROS-topic-like, HIL/pass-like, PR-resolution-like, O5 external-proof-like, or delivery-success-like.
6. Preserve `software_proof`, `hardware_material_pending`, `not_proven`, `delivery_success=false`, `primary_actions_enabled=false`, and `safe_to_control=false`.
7. Document that `docs/vendor/VENDOR_INDEX.md` supports source attribution for existing Orange Pi / WAVE ROVER / UART JSON references only; it does not prove real 2D LiDAR / ToF material.

Acceptance commands:

```bash
python3 -m py_compile pc-tools/evidence/pr5_mandatory_sensor_material_owner_response_review_decision.py
python3 -m unittest pc-tools/evidence/test_pr5_mandatory_sensor_material_owner_response_review_decision.py
python3 pc-tools/evidence/pr5_mandatory_sensor_material_owner_response_review_decision.py --help
rg -n "pr5_mandatory_sensor_material_owner_response_review_decision|software_proof_docker_pr5_mandatory_sensor_material_owner_response_review_decision_gate|accepted_for_reviewer_closeout_not_proven|needs_more_material_not_proven|rejected_unsafe_material_not_proven|blocked_missing_owner_response_intake_not_proven|blocked_evidence_ref_mismatch_not_proven|hardware_material_pending|not_proven|delivery_success=false|primary_actions_enabled=false|safe_to_control=false|PRRT_kwDOSWB9286CJ3tX|docs/vendor/VENDOR_INDEX.md" pc-tools/evidence/pr5_mandatory_sensor_material_owner_response_review_decision.py pc-tools/evidence/test_pr5_mandatory_sensor_material_owner_response_review_decision.py pc-tools/README.md docs/product/production_hardware_boundary.md docs/interfaces/pr5_mandatory_sensor_material_owner_response_review_decision.md
git diff --check -- pc-tools/evidence/pr5_mandatory_sensor_material_owner_response_review_decision.py pc-tools/evidence/test_pr5_mandatory_sensor_material_owner_response_review_decision.py pc-tools/README.md docs/product/production_hardware_boundary.md docs/interfaces/pr5_mandatory_sensor_material_owner_response_review_decision.md
```

### Owner B: Robot Platform Engineer - Diagnostics Safe Alias

Responsibility: expose the review-decision safe alias through Robot diagnostics without raw material access.

Allowed file range:

- Modify: `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py`
- Modify: `onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`
- Modify: `docs/interfaces/ros_runtime_contracts.md`
- Modify: `docs/interfaces/pr5_mandatory_sensor_material_owner_response_review_decision.md`

Read-only references:

- `AGENTS.md`
- `OKR.md`
- Hardware owner output after available
- Existing diagnostics patterns for `robot_diagnostics_pr5_mandatory_sensor_material_owner_response_intake_summary`

Implementation requirements:

1. Add Robot diagnostics support for `pr5_mandatory_sensor_material_owner_response_review_decision` safe summaries.
2. Expose `robot_diagnostics_pr5_mandatory_sensor_material_owner_response_review_decision_summary`.
3. Consume only the PC gate safe summary fields; do not read raw owner-response bodies or real material payloads.
4. Include review decision, source intake status, safe `evidence_ref`, missing/rejected/unsafe material summaries, reviewer next step, next required evidence, evidence boundary, and conservative flags.
5. Preserve `safe_to_control=false`, `delivery_success=false`, and `primary_actions_enabled=false`.
6. Keep any new technical code comments in Chinese and focused on why raw PR/hardware material cannot enter Robot diagnostics.

Acceptance commands:

```bash
python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py
python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py
rg -n "pr5_mandatory_sensor_material_owner_response_review_decision|robot_diagnostics_pr5_mandatory_sensor_material_owner_response_review_decision_summary|software_proof_docker_pr5_mandatory_sensor_material_owner_response_review_decision_gate|accepted_for_reviewer_closeout_not_proven|needs_more_material_not_proven|rejected_unsafe_material_not_proven|blocked_missing_owner_response_intake_not_proven|blocked_evidence_ref_mismatch_not_proven|hardware_material_pending|not_proven|delivery_success=false|primary_actions_enabled=false|safe_to_control=false|PRRT_kwDOSWB9286CJ3tX" onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py docs/interfaces/ros_runtime_contracts.md docs/interfaces/pr5_mandatory_sensor_material_owner_response_review_decision.md
git diff --check -- onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py docs/interfaces/ros_runtime_contracts.md docs/interfaces/pr5_mandatory_sensor_material_owner_response_review_decision.md
```

### Owner C: User Touchpoint Full-Stack Engineer - Mobile Read-Only Panel

Responsibility: show the Robot safe alias in `mobile/web` as read-only review-decision status.

Allowed file range:

- Modify: `mobile/web/app.js`
- Create: `mobile/web/fixtures/robot_diagnostics_pr5_mandatory_sensor_material_owner_response_review_decision.json`
- Modify: `mobile/web/test_mobile_web_entrypoint.py`
- Modify: `docs/product/mobile_user_flow.md`

Read-only references:

- `AGENTS.md`
- `OKR.md`
- `docs/product/mobile_user_flow.md`
- Robot safe alias contract from Owner B after available
- Existing mobile panels for PR #5 material owner-response intake and review-decision-style flows

Implementation requirements:

1. Add a read-only panel for `pr5_mandatory_sensor_material_owner_response_review_decision`.
2. Prefer `robot_diagnostics_pr5_mandatory_sensor_material_owner_response_review_decision_summary`; allow only compatible safe-summary fallbacks.
3. Show decision, source intake status, safe `evidence_ref`, missing/rejected/unsafe material summaries, reviewer next step, next required evidence, evidence boundary, and conservative flags.
4. Do not add copy/export/raw-material controls.
5. Do not trigger ACK, cursor, diagnostics fetch, Start Delivery, Confirm Dropoff, Cancel, review routes, material routes, or robot command requests.
6. Keep Start Delivery, Confirm Dropoff, and Cancel disabled when `primary_actions_enabled=false`.
7. Filter raw JSON, ROS topics, `/cmd_vel`, serial/UART paths, credentials, local paths, complete artifacts, checksums, WAVE ROVER parameters, Objective 5 external proof claims, real phone/browser claims, HIL/pass wording, PR-resolution claims, and delivery-success claims.

Acceptance commands:

```bash
python3 -m json.tool mobile/web/fixtures/robot_diagnostics_pr5_mandatory_sensor_material_owner_response_review_decision.json >/tmp/pr5_mandatory_sensor_material_owner_response_review_decision_fixture.json
python3 -m unittest mobile.web.test_mobile_web_entrypoint
rg -n "pr5_mandatory_sensor_material_owner_response_review_decision|robot_diagnostics_pr5_mandatory_sensor_material_owner_response_review_decision_summary|software_proof_docker_pr5_mandatory_sensor_material_owner_response_review_decision_gate|accepted_for_reviewer_closeout_not_proven|needs_more_material_not_proven|rejected_unsafe_material_not_proven|blocked_missing_owner_response_intake_not_proven|blocked_evidence_ref_mismatch_not_proven|hardware_material_pending|not_proven|delivery_success=false|primary_actions_enabled=false|safe_to_control=false|PRRT_kwDOSWB9286CJ3tX" mobile/web/app.js mobile/web/fixtures/robot_diagnostics_pr5_mandatory_sensor_material_owner_response_review_decision.json mobile/web/test_mobile_web_entrypoint.py docs/product/mobile_user_flow.md
git diff --check -- mobile/web/app.js mobile/web/fixtures/robot_diagnostics_pr5_mandatory_sensor_material_owner_response_review_decision.json mobile/web/test_mobile_web_entrypoint.py docs/product/mobile_user_flow.md
```

### Owner D: Product Manager / OKR Owner - Closeout

Responsibility: run product acceptance after engineering workers return and update sprint closeout chain only after evidence exists.

Allowed file range:

- Create: `sprints/2026.05.23_17-18_pr5-mandatory-sensor-material-owner-response-review-decision/tech-done.md`
- Create: `sprints/2026.05.23_17-18_pr5-mandatory-sensor-material-owner-response-review-decision/side2side_check.md`
- Create: `sprints/2026.05.23_17-18_pr5-mandatory-sensor-material-owner-response-review-decision/final.md`
- Modify: `OKR.md`
- Modify: `docs/process/okr_progress_log.md`

Closeout requirements:

1. Re-check PR #5 thread `PRRT_kwDOSWB9286CJ3tX` before final wording.
2. Summarize actual files changed and each owner validation result.
3. Keep acceptance as `software_proof_docker_pr5_mandatory_sensor_material_owner_response_review_decision_gate`.
4. Keep Objective 5 around 68% unless real O5 materials appear.
5. Keep Objective 1 around 81% unless real PR #5/hardware/HIL material or reviewer resolution appears.
6. Preserve no real route/elevator/phone/HIL/O5/delivery claims.
7. Record whether docs under `docs/` were synchronized and whether touched implementation code comments are Chinese and sufficient for the changed logic.

Product validation commands:

```bash
rg -n "software_proof_docker_pr5_mandatory_sensor_material_owner_response_review_decision_gate|Objective 5|Objective 1|PRRT_kwDOSWB9286CJ3tX|hardware_material_pending|not_proven|delivery_success=false|primary_actions_enabled=false|safe_to_control=false|no OKR percentage lift" sprints/2026.05.23_17-18_pr5-mandatory-sensor-material-owner-response-review-decision OKR.md docs/process/okr_progress_log.md
git diff --check -- sprints/2026.05.23_17-18_pr5-mandatory-sensor-material-owner-response-review-decision OKR.md docs/process/okr_progress_log.md
```

## Integration Acceptance

The sprint can proceed to implementation when:

- the first three engineering owners have disjoint file ranges;
- each owner has explicit acceptance commands;
- Product closeout is separated from engineering implementation;
- the O5 skip rationale is explicit;
- the Objective 1 PR #5 unresolved thread is explicit;
- `docs/vendor/VENDOR_INDEX.md` remains the hardware-source entrypoint;
- no plan asks any worker to claim hardware proof, HIL, PR resolution, O5 external proof, true phone/browser proof, or delivery success.

## Planning Validation Commands

Run after creating the first three planning docs:

```bash
test -f sprints/2026.05.23_17-18_pr5-mandatory-sensor-material-owner-response-review-decision/pre_start.md && test -f sprints/2026.05.23_17-18_pr5-mandatory-sensor-material-owner-response-review-decision/prd.md && test -f sprints/2026.05.23_17-18_pr5-mandatory-sensor-material-owner-response-review-decision/tech-plan.md
rg -n "sprint_type: epic|OKR 最低优先级核对|Objective 5|Objective 1|PRRT_kwDOSWB9286CJ3tX|pr5_mandatory_sensor_material_owner_response_review_decision|software_proof_docker_pr5_mandatory_sensor_material_owner_response_review_decision_gate|hardware_material_pending|not_proven|delivery_success=false|primary_actions_enabled=false|safe_to_control=false|docs/vendor/VENDOR_INDEX.md" sprints/2026.05.23_17-18_pr5-mandatory-sensor-material-owner-response-review-decision
git diff --check -- sprints/2026.05.23_17-18_pr5-mandatory-sensor-material-owner-response-review-decision
```
