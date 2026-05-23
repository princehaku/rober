# Mobile Current Panel Browser Proof Refresh Owner Response Bridge Tech Plan

Run time: 2026-05-24 04:03 Asia/Shanghai

## Sprint Type

sprint_type: epic

## OKR 最低优先级核对

1. 当前 `OKR.md` 4.1 中完成度最低的是 Objective 5：云中转 + OSS/CDN 数据通路产品化，约 68%。
2. 本 sprint 不直接针对 Objective 5。
3. 具体原因：Objective 5 当前需要真实 public HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue connectivity、production worker/migration/cutover、verified terminal result 或 true phone/browser evidence；当前主机只有 Docker/local proof，无法提供这些真实材料。
4. Objective 1 也不能作为本轮真实进度，因为 PR #5 `PRRT_kwDOSWB9286CJ3tX` 仍 `is_resolved=false` / `hardware_material_pending`，缺真实 2D LiDAR/ToF SKU/source/receipt、安装、接线、电源、标定、HIL-entry、WAVE ROVER powered bench、UART 和 HIL logs。
5. 最新 sprint final 明确要求 `Do not repeat another local-only metadata wrapper as OKR progress`。因此本轮不再新建 O5 / PR #5 / route material metadata wrapper，而转向 Objective 4 fallback：刷新 `phone_browser_acceptance_gate.py` current-panel browser proof，让它覆盖 `field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_owner_response_intake_bridge` mobile panel。
6. 本 sprint 的证据边界必须是 `software_proof_docker_mobile_current_panel_browser_proof_refresh_owner_response_bridge_gate`，并保持 `not_proven`、`delivery_success=false`、`primary_actions_enabled=false`、`safe_to_control=false`、no OKR percentage lift 和 not true phone/browser proof。

## Capability And Evidence Boundary

Capability to cover:

`field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_owner_response_intake_bridge`

Evidence boundary:

`software_proof_docker_mobile_current_panel_browser_proof_refresh_owner_response_bridge_gate`

Required preserved flags:

- `not_proven`
- `delivery_success=false`
- `primary_actions_enabled=false`
- `safe_to_control=false`
- no OKR percentage lift
- not true phone/browser proof

This is local Chromium-family software proof only. It is not true phone/browser proof, not Objective 5 external proof, not public HTTPS/TLS, not 4G/SIM, not OSS/CDN live traffic, not production DB/queue, not worker/cutover, not route/elevator field pass, not verified terminal result, not HIL, not WAVE ROVER/UART proof, not PR #5 resolution, and not delivery success.

## Parallel Owner Plan

Start Task A and Task B in parallel after this planning phase. Task C runs only after A/B evidence is available.

### Task A Full-Stack Implementation And Validation

Owner: User Touchpoint Full-Stack Engineer.

Goal: refresh current-panel/browser proof so `pc-tools/evidence/phone_browser_acceptance_gate.py` covers the latest owner-response bridge mobile panel under the new proof boundary.

Allowed file range:

- `pc-tools/evidence/phone_browser_acceptance_gate.py`
- `mobile/web/app.js`
- `mobile/web/test_mobile_web_entrypoint.py`
- `mobile/web/fixtures/robot_diagnostics_field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_owner_response_intake_bridge.json`
- `docs/product/mobile_user_flow.md`
- `sprints/2026.05.24_04-05_mobile-current-panel-browser-proof-refresh-owner-response-bridge/tech-done.md`
- `sprints/2026.05.24_04-05_mobile-current-panel-browser-proof-refresh-owner-response-bridge/evidence/`

Implementation requirements:

- Reuse existing `phone_browser_acceptance_gate.py` current-panel/browser proof machinery; do not invent a separate proof script unless the existing gate cannot represent the capability.
- Stamp proof output with `software_proof_docker_mobile_current_panel_browser_proof_refresh_owner_response_bridge_gate`.
- Assert the owner-response bridge panel is present in the current-panel set and remains fail-closed.
- Preserve `not_proven`, `delivery_success=false`, `primary_actions_enabled=false`, and `safe_to_control=false`.
- Keep Start Delivery, Confirm Dropoff, and Cancel disabled.
- Surface only safe owner/support/reviewer route, same safe `evidence_ref`, source bridge state, PR #5 `PRRT_kwDOSWB9286CJ3tX` unresolved / `hardware_material_pending`, next real owner materials, and backend safe copy.
- Do not expose raw JSON, raw artifacts, ROS topics, `/cmd_vel`, serial/UART paths, WAVE ROVER details, credentials, local paths, checksums, complete artifacts, raw diagnostics, ACK/cursor routes, review routes, owner-response routes, material routes, GitHub mutation, procurement action, replay/resubmit controls, or robot commands.
- Keep technical code comments in Chinese and maintain the repository comment-quality expectation for touched code.

Acceptance commands:

```bash
node --check mobile/web/app.js
python3 -m json.tool mobile/web/fixtures/robot_diagnostics_field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_owner_response_intake_bridge.json >/tmp/owner_response_bridge_browser_proof_fixture.json
python3 -m unittest mobile/web/test_mobile_web_entrypoint.py
python3 pc-tools/evidence/phone_browser_acceptance_gate.py --help
PYTHONDONTWRITEBYTECODE=1 python3 pc-tools/evidence/phone_browser_acceptance_gate.py --output-dir sprints/2026.05.24_04-05_mobile-current-panel-browser-proof-refresh-owner-response-bridge/evidence --fresh-profile --require-console-zero --capability mobile_current_panel_browser_proof_refresh_owner_response_bridge --evidence-boundary software_proof_docker_mobile_current_panel_browser_proof_refresh_owner_response_bridge_gate
rg -n "field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_owner_response_intake_bridge|software_proof_docker_mobile_current_panel_browser_proof_refresh_owner_response_bridge_gate|PRRT_kwDOSWB9286CJ3tX|not_proven|delivery_success=false|primary_actions_enabled=false|safe_to_control=false|not true phone/browser proof|no OKR percentage lift" pc-tools/evidence/phone_browser_acceptance_gate.py mobile/web/app.js mobile/web/test_mobile_web_entrypoint.py mobile/web/fixtures/robot_diagnostics_field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_owner_response_intake_bridge.json docs/product/mobile_user_flow.md sprints/2026.05.24_04-05_mobile-current-panel-browser-proof-refresh-owner-response-bridge/tech-done.md
git diff --check -- pc-tools/evidence/phone_browser_acceptance_gate.py mobile/web/app.js mobile/web/test_mobile_web_entrypoint.py mobile/web/fixtures/robot_diagnostics_field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_owner_response_intake_bridge.json docs/product/mobile_user_flow.md sprints/2026.05.24_04-05_mobile-current-panel-browser-proof-refresh-owner-response-bridge
```

### Task B Robot Read-Only Safety Consultation

Owner: Robot Platform Engineer.

Goal: confirm the Robot diagnostics/source bridge summary remains phone-safe for browser proof refresh without requiring Robot code changes unless Task A discovers a missing safe field.

Allowed file range:

- Read-only: `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py`
- Read-only: `onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`
- Read-only: `docs/interfaces/operator_gateway_diagnostics.md`
- Read-only: `docs/interfaces/field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_intake.md`
- May append consultation result only to `sprints/2026.05.24_04-05_mobile-current-panel-browser-proof-refresh-owner-response-bridge/tech-done.md` after Task A creates it and only if the main runtime asks for combined closeout.

Consultation requirements:

- Confirm the summary is read-only, metadata-only, and safe for mobile/browser consumption.
- Confirm no raw ROS topic, `/cmd_vel`, serial/UART path, WAVE ROVER detail, credential, local path, checksum, complete artifact, raw diagnostics, GitHub mutation, material upload, or control/success field is required for the panel proof.
- Confirm Robot does not need code changes for this proof refresh unless Task A finds a missing safe field.
- Preserve `not_proven`, `delivery_success=false`, `primary_actions_enabled=false`, and `safe_to_control=false`.

Acceptance commands:

```bash
rg -n "field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_owner_response_intake_bridge|robot_diagnostics_field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_intake_summary|source_bridge|PRRT_kwDOSWB9286CJ3tX|not_proven|delivery_success=false|primary_actions_enabled=false|safe_to_control=false" onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py docs/interfaces/operator_gateway_diagnostics.md docs/interfaces/field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_intake.md
git diff --check -- onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py docs/interfaces/operator_gateway_diagnostics.md docs/interfaces/field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_intake.md
```

### Task C Product Closeout After A/B

Owner: Product Manager / OKR Owner.

Goal: after Task A and Task B return evidence, close the sprint without overstating local browser proof.

Allowed file range after A/B:

- `sprints/2026.05.24_04-05_mobile-current-panel-browser-proof-refresh-owner-response-bridge/tech-done.md`
- `sprints/2026.05.24_04-05_mobile-current-panel-browser-proof-refresh-owner-response-bridge/side2side_check.md`
- `sprints/2026.05.24_04-05_mobile-current-panel-browser-proof-refresh-owner-response-bridge/final.md`
- `OKR.md`, only if closeout scope explicitly allows it and wording stays no percentage lift.
- `docs/process/okr_progress_log.md`, only if closeout scope explicitly allows it.

Closeout requirements:

- State this is `software_proof_docker_mobile_current_panel_browser_proof_refresh_owner_response_bridge_gate`.
- State `field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_owner_response_intake_bridge` is covered in local current-panel browser proof.
- Preserve `not_proven`, `delivery_success=false`, `primary_actions_enabled=false`, `safe_to_control=false`, and no OKR percentage lift.
- State Objective 5 remains lowest and blocked on real external / terminal-result materials.
- State Objective 4 gets only local browser proof refresh, not true phone/browser proof.
- State PR #5 `PRRT_kwDOSWB9286CJ3tX` remains unresolved / `hardware_material_pending` unless live review evidence changes.
- State this is not public HTTPS/TLS, not 4G/SIM, not OSS/CDN live traffic, not production DB/queue, not worker/cutover, not route/elevator field pass, not HIL, not WAVE ROVER/UART proof, and not delivery success.

Acceptance commands:

```bash
test -f sprints/2026.05.24_04-05_mobile-current-panel-browser-proof-refresh-owner-response-bridge/tech-done.md
test -f sprints/2026.05.24_04-05_mobile-current-panel-browser-proof-refresh-owner-response-bridge/side2side_check.md
test -f sprints/2026.05.24_04-05_mobile-current-panel-browser-proof-refresh-owner-response-bridge/final.md
rg -n "software_proof_docker_mobile_current_panel_browser_proof_refresh_owner_response_bridge_gate|field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_owner_response_intake_bridge|Objective 5|Objective 4|PRRT_kwDOSWB9286CJ3tX|not_proven|delivery_success=false|primary_actions_enabled=false|safe_to_control=false|no OKR percentage lift|not true phone/browser proof" sprints/2026.05.24_04-05_mobile-current-panel-browser-proof-refresh-owner-response-bridge OKR.md docs/process/okr_progress_log.md
git diff --check -- sprints/2026.05.24_04-05_mobile-current-panel-browser-proof-refresh-owner-response-bridge OKR.md docs/process/okr_progress_log.md
```

## Interface And Safety Boundary

- The proof refresh verifies current-panel rendering only.
- Mobile panel remains read-only support/status metadata.
- Missing or unsafe fields must fail closed.
- Start Delivery, Confirm Dropoff, and Cancel remain disabled.
- The implementation must not change cloud command authorization, Robot control contracts, ROS2 topics, hardware settings, or route/elevator execution.
- Hardware-specific details are out of scope; this sprint does not inspect or modify WAVE ROVER, ESP32, Orange Pi, UART, voltage, pin, baudrate, firmware, or mechanical dimensions.

## Planning Phase Validation

Run these commands for this planning-only phase:

```bash
test -f sprints/2026.05.24_04-05_mobile-current-panel-browser-proof-refresh-owner-response-bridge/pre_start.md
test -f sprints/2026.05.24_04-05_mobile-current-panel-browser-proof-refresh-owner-response-bridge/prd.md
test -f sprints/2026.05.24_04-05_mobile-current-panel-browser-proof-refresh-owner-response-bridge/tech-plan.md
rg -n "sprint_type: epic|OKR 最低优先级核对|Objective 5|Objective 4|software_proof_docker_mobile_current_panel_browser_proof_refresh_owner_response_bridge_gate|field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_owner_response_intake_bridge|PRRT_kwDOSWB9286CJ3tX|not_proven|delivery_success=false|primary_actions_enabled=false|safe_to_control=false|no OKR percentage lift" sprints/2026.05.24_04-05_mobile-current-panel-browser-proof-refresh-owner-response-bridge
git diff --check -- sprints/2026.05.24_04-05_mobile-current-panel-browser-proof-refresh-owner-response-bridge
```

## Remaining Risks

- This plan cannot prove Objective 5 external readiness.
- This plan cannot resolve PR #5 `PRRT_kwDOSWB9286CJ3tX`.
- This plan cannot prove true iPhone/Android browser behavior, real PWA prompt/userChoice, production app behavior, route/elevator field pass, verified terminal result, dropoff/cancel completion, HIL, WAVE ROVER/UART, 2D LiDAR/ToF installation, or delivery success.
- If Task A finds stale browser cache or panel runtime errors, it should fix only the scoped current-panel proof path and rerun the same fenced checks.
- If Task B finds a missing safe Robot field, implementation must stop widening mobile assumptions and instead request a scoped Robot-safe metadata fix.
