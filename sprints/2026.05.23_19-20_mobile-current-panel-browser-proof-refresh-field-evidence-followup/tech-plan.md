# Mobile Current Panel Browser Proof Refresh Field Evidence Followup Tech Plan

Run time: 2026-05-23 19:20 Asia/Shanghai

## Sprint Type

sprint_type: epic

## OKR 最低优先级核对

1. 当前 `OKR.md` 4.1 中完成度最低的是 Objective 5：云中转 + OSS/CDN 数据通路产品化，约 68%。
2. 本 sprint 不直接做 Objective 5 external proof。
3. 原因：Objective 5 需要真实 public HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/cutover、verified terminal result 和 true phone/browser evidence；当前主机没有真实硬件，只有 Docker/local，且最近已经多轮消费真实外部、terminal-result 和硬件材料缺失 blocker。
4. PR #5 `PRRT_kwDOSWB9286CJ3tX` 仍 unresolved / `is_resolved=false` / `hardware_material_pending`，缺真实 2D LiDAR / ToF SKU/source/receipt/procurement/installation/wiring/power/calibration/HIL-entry 材料。本轮不再堆 O5/PR #5 真实材料 blocker wrapper。
5. 本 sprint 转向 Objective 4 fallback：做 current-panel browser proof refresh，让 `phone_browser_acceptance_gate.py` 覆盖最新 `field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_followup_escalation_status` mobile panel，同时保持 `software_proof_docker_mobile_current_panel_browser_proof_refresh_field_evidence_followup_gate`、`not_proven`、`delivery_success=false`、`primary_actions_enabled=false`、`safe_to_control=false` 和 no OKR percentage lift。

## Capability And Evidence Boundary

Latest panel to cover:

`field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_followup_escalation_status`

Browser proof boundary:

`software_proof_docker_mobile_current_panel_browser_proof_refresh_field_evidence_followup_gate`

Required preserved flags:

- `not_proven`
- `delivery_success=false`
- `primary_actions_enabled=false`
- `safe_to_control=false`
- no OKR percentage lift

This is local Chromium-family software proof only. It is not true phone/browser proof, not Objective 5 external proof, not route/elevator field pass, not verified terminal result, not HIL, not PR #5 resolution, and not delivery success.

## Parallel Task Split

Start Task A and Task B in parallel after planning. Task C runs only after A/B return enough evidence.

### Task A Full-Stack Implementation And Validation

Owner: User Touchpoint Full-Stack Engineer.

Goal: refresh the local current-panel/browser proof so `phone_browser_acceptance_gate.py` covers the latest `field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_followup_escalation_status` mobile panel under the new proof boundary.

Allowed file range:

- `pc-tools/evidence/phone_browser_acceptance_gate.py`
- `mobile/web/app.js`
- `mobile/web/test_mobile_web_entrypoint.py`
- `mobile/web/fixtures/robot_diagnostics_field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_followup_escalation_status.json`
- `docs/product/mobile_user_flow.md`
- `sprints/2026.05.23_19-20_mobile-current-panel-browser-proof-refresh-field-evidence-followup/tech-done.md`

Implementation requirements:

- Reuse the existing current-panel/browser proof machinery; do not add a separate proof script unless the existing gate cannot support the boundary.
- Stamp the proof as `software_proof_docker_mobile_current_panel_browser_proof_refresh_field_evidence_followup_gate`.
- Assert that the latest field-evidence follow-up panel is present and still fail-closed.
- Preserve `not_proven`, `delivery_success=false`, `primary_actions_enabled=false`, and `safe_to_control=false`.
- Keep Start Delivery, Confirm Dropoff, and Cancel disabled.
- Do not expose raw JSON, raw artifacts, ROS topics, `/cmd_vel`, serial/UART details, credentials, local filesystem paths, checksums, complete artifacts, GitHub action, material upload, procurement action, review action, handoff action, diagnostics fetch, ACK, cursor, or robot command.

Acceptance commands:

```bash
node --check mobile/web/app.js
python3 -m json.tool mobile/web/fixtures/robot_diagnostics_field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_followup_escalation_status.json >/tmp/field_evidence_followup_browser_proof_fixture.json
python3 -m unittest mobile/web/test_mobile_web_entrypoint.py
python3 pc-tools/evidence/phone_browser_acceptance_gate.py --help
rg -n "field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_followup_escalation_status|software_proof_docker_mobile_current_panel_browser_proof_refresh_field_evidence_followup_gate|not_proven|delivery_success=false|primary_actions_enabled=false|safe_to_control=false|not true phone/browser proof|no OKR percentage lift" pc-tools/evidence/phone_browser_acceptance_gate.py mobile/web/app.js mobile/web/test_mobile_web_entrypoint.py mobile/web/fixtures/robot_diagnostics_field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_followup_escalation_status.json docs/product/mobile_user_flow.md sprints/2026.05.23_19-20_mobile-current-panel-browser-proof-refresh-field-evidence-followup/tech-done.md
git diff --check -- pc-tools/evidence/phone_browser_acceptance_gate.py mobile/web/app.js mobile/web/test_mobile_web_entrypoint.py mobile/web/fixtures/robot_diagnostics_field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_followup_escalation_status.json docs/product/mobile_user_flow.md sprints/2026.05.23_19-20_mobile-current-panel-browser-proof-refresh-field-evidence-followup/tech-done.md
```

### Task B Robot Read-Only Safety Boundary Consultation

Owner: Robot Platform Engineer.

Goal: read the Robot diagnostics summary and mobile panel consumption boundary, then confirm whether the current summary is safe for browser proof refresh without changing Robot code.

Allowed file range:

- Read-only only: `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py`
- Read-only only: `onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`
- Read-only only: `docs/interfaces/ros_runtime_contracts.md`
- May append consultation result only to `sprints/2026.05.23_19-20_mobile-current-panel-browser-proof-refresh-field-evidence-followup/tech-done.md` after Task A creates it, if the main runtime asks for a combined closeout.

Consultation requirements:

- Confirm the summary remains read-only and safe for mobile/browser consumption.
- Confirm no raw ROS topic, `/cmd_vel`, serial/UART path, WAVE ROVER detail, credential, local path, checksum, complete artifact, raw diagnostics, or control/success copy is required for the panel proof.
- Confirm Robot does not need a code change for this proof refresh unless Task A discovers a missing safe field.
- Preserve `not_proven`, `delivery_success=false`, `primary_actions_enabled=false`, and `safe_to_control=false`.

Acceptance commands:

```bash
rg -n "field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_followup_escalation_status|robot_diagnostics_field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_followup_escalation_status_summary|not_proven|delivery_success=false|primary_actions_enabled=false|safe_to_control=false" onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py docs/interfaces/ros_runtime_contracts.md
git diff --check -- onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py docs/interfaces/ros_runtime_contracts.md
```

### Task C Product Closeout After A/B

Owner: Product Manager / OKR Owner.

Goal: after Task A and Task B return evidence, update closeout documents and preserve the OKR truth boundary.

Allowed file range after A/B:

- `sprints/2026.05.23_19-20_mobile-current-panel-browser-proof-refresh-field-evidence-followup/tech-done.md`
- `sprints/2026.05.23_19-20_mobile-current-panel-browser-proof-refresh-field-evidence-followup/side2side_check.md`
- `sprints/2026.05.23_19-20_mobile-current-panel-browser-proof-refresh-field-evidence-followup/final.md`
- `OKR.md`, only if closeout scope explicitly allows it and wording stays no percentage lift.
- `docs/process/okr_progress_log.md`, only if closeout scope explicitly allows it.

Closeout requirements:

- State this is `software_proof_docker_mobile_current_panel_browser_proof_refresh_field_evidence_followup_gate`.
- State `field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_followup_escalation_status` is covered in local current-panel browser proof.
- Preserve `not_proven`, `delivery_success=false`, `primary_actions_enabled=false`, `safe_to_control=false`, and no OKR percentage lift.
- State Objective 5 remains lowest and blocked on real external/terminal-result materials.
- State PR #5 `PRRT_kwDOSWB9286CJ3tX` remains unresolved / `hardware_material_pending` unless live review evidence changes.
- State this is not true phone/browser proof, not Objective 5 external proof, not route/elevator field pass, not HIL, and not delivery success.

Acceptance commands:

```bash
test -f sprints/2026.05.23_19-20_mobile-current-panel-browser-proof-refresh-field-evidence-followup/tech-done.md
test -f sprints/2026.05.23_19-20_mobile-current-panel-browser-proof-refresh-field-evidence-followup/side2side_check.md
test -f sprints/2026.05.23_19-20_mobile-current-panel-browser-proof-refresh-field-evidence-followup/final.md
rg -n "software_proof_docker_mobile_current_panel_browser_proof_refresh_field_evidence_followup_gate|field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_followup_escalation_status|Objective 5|Objective 4|PRRT_kwDOSWB9286CJ3tX|not_proven|delivery_success=false|primary_actions_enabled=false|safe_to_control=false|no OKR percentage lift" sprints/2026.05.23_19-20_mobile-current-panel-browser-proof-refresh-field-evidence-followup
git diff --check -- sprints/2026.05.23_19-20_mobile-current-panel-browser-proof-refresh-field-evidence-followup OKR.md docs/process/okr_progress_log.md
```

## Interface And Safety Boundary

- The browser proof refresh may verify current panel coverage but must not alter command authorization.
- The mobile panel remains read-only support/status metadata.
- Missing fields must fail closed.
- Any browser output is local Docker/software proof only and must not be described as true phone/browser acceptance.
- Hardware-specific claims remain out of scope; this sprint does not inspect or modify WAVE ROVER, ESP32, Orange Pi, UART, voltage, pin, baudrate, firmware, or mechanical dimensions.

## Planning Phase Validation

Run these commands for this planning-only phase:

```bash
test -f sprints/2026.05.23_19-20_mobile-current-panel-browser-proof-refresh-field-evidence-followup/pre_start.md
test -f sprints/2026.05.23_19-20_mobile-current-panel-browser-proof-refresh-field-evidence-followup/prd.md
test -f sprints/2026.05.23_19-20_mobile-current-panel-browser-proof-refresh-field-evidence-followup/tech-plan.md
rg -n "sprint_type: epic|OKR 最低优先级核对|Objective 5|Objective 4|software_proof_docker_mobile_current_panel_browser_proof_refresh_field_evidence_followup_gate|field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_followup_escalation_status|PRRT_kwDOSWB9286CJ3tX|not_proven|delivery_success=false|primary_actions_enabled=false|safe_to_control=false|no OKR percentage lift" sprints/2026.05.23_19-20_mobile-current-panel-browser-proof-refresh-field-evidence-followup
git diff --check -- sprints/2026.05.23_19-20_mobile-current-panel-browser-proof-refresh-field-evidence-followup
```

## Remaining Risks

- This plan cannot prove Objective 5 external readiness.
- This plan cannot resolve PR #5 `PRRT_kwDOSWB9286CJ3tX`.
- This plan cannot prove true iPhone/Android browser behavior, real PWA prompt/userChoice, production app behavior, route/elevator field pass, verified terminal result, dropoff/cancel completion, HIL, or delivery success.
- If Task A finds stale browser cache or panel runtime errors, it should fix only the scoped current-panel proof path and rerun the same fenced checks.
