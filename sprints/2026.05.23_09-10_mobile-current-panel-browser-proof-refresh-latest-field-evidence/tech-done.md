# Tech Done

## Sprint Type

sprint_type: epic

## Task A Full-Stack Current Panel Browser Proof Refresh Latest Field Evidence

Owner: `full-stack-software-engineer`

Scope: implemented `mobile_current_panel_browser_proof_refresh_latest_field_evidence` in the existing local Chromium-family browser proof path. This keeps the boundary as `software_proof_docker_mobile_current_panel_browser_proof_refresh_latest_field_evidence_gate`, read-only, fail-closed, and `not true phone/browser`.

User journey change:

- The local browser proof now explicitly checks the latest current panel `field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_intake`.
- The phone entry continues to show support-readable safe metadata while Start Delivery, Confirm Dropoff, and Cancel remain disabled.
- The user-facing boundary remains `delivery_success=false`, `primary_actions_enabled=false`, and `safe_to_control=false`; this is not delivery success, not true phone/browser, and not route/elevator/HIL proof.

Files changed by Task A:

- `pc-tools/evidence/phone_browser_acceptance_gate.py`
- `mobile/web/test_mobile_web_entrypoint.py`
- `mobile/test_mobile_web_entrypoint.py`
- `docs/product/mobile_user_flow.md`
- `sprints/2026.05.23_09-10_mobile-current-panel-browser-proof-refresh-latest-field-evidence/evidence/mobile_current_panel_browser_proof_refresh_latest_field_evidence_390x844.json`
- `sprints/2026.05.23_09-10_mobile-current-panel-browser-proof-refresh-latest-field-evidence/evidence/mobile_current_panel_browser_proof_refresh_latest_field_evidence_390x844.png`
- `sprints/2026.05.23_09-10_mobile-current-panel-browser-proof-refresh-latest-field-evidence/evidence/mobile_current_panel_browser_proof_refresh_latest_field_evidence_768x900.json`
- `sprints/2026.05.23_09-10_mobile-current-panel-browser-proof-refresh-latest-field-evidence/evidence/mobile_current_panel_browser_proof_refresh_latest_field_evidence_768x900.png`
- `sprints/2026.05.23_09-10_mobile-current-panel-browser-proof-refresh-latest-field-evidence/evidence/mobile_current_panel_browser_proof_refresh_latest_field_evidence_summary.json`
- `sprints/2026.05.23_09-10_mobile-current-panel-browser-proof-refresh-latest-field-evidence/tech-done.md`

Interface impact:

- No ROS2, cloud, hardware, Robot command, launch, or API contract changes.
- `phone_browser_acceptance_gate.py` current-panel expectations now include the latest reviewer ACK intake panel title, boundary, and flags:
  - `fieldEvidenceRerunExecutionResultAcceptanceHandoffIntakeOwnerResponseReviewerAckIntakeTitle`
  - `fieldEvidenceRerunExecutionResultAcceptanceHandoffIntakeOwnerResponseReviewerAckIntakeBoundary`
  - `fieldEvidenceRerunExecutionResultAcceptanceHandoffIntakeOwnerResponseReviewerAckIntakeFlags`
- The latest panel boundary checked by the gate is `software_proof_docker_field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_intake_gate`.

Verification evidence:

```text
PYTHONDONTWRITEBYTECODE=1 python3 pc-tools/evidence/phone_browser_acceptance_gate.py --output-dir sprints/2026.05.23_09-10_mobile-current-panel-browser-proof-refresh-latest-field-evidence/evidence --fresh-profile --require-console-zero --capability mobile_current_panel_browser_proof_refresh_latest_field_evidence --evidence-boundary software_proof_docker_mobile_current_panel_browser_proof_refresh_latest_field_evidence_gate
viewport=390x844 passed=true current_panels_status=passed current_boundaries_status=passed primary_actions_disabled=true phone_safe_status=passed fresh_browser_markers_status=passed service_worker_dynamic_no_store_status=passed console_zero_status=passed console_error_count=0
viewport=768x900 passed=true current_panels_status=passed current_boundaries_status=passed primary_actions_disabled=true phone_safe_status=passed fresh_browser_markers_status=passed service_worker_dynamic_no_store_status=passed console_zero_status=passed console_error_count=0
summary=sprints/2026.05.23_09-10_mobile-current-panel-browser-proof-refresh-latest-field-evidence/evidence/mobile_current_panel_browser_proof_refresh_latest_field_evidence_summary.json ok=true capability=mobile_current_panel_browser_proof_refresh_latest_field_evidence evidence_boundary=software_proof_docker_mobile_current_panel_browser_proof_refresh_latest_field_evidence_gate fresh_profile=true require_console_zero=true
```

```text
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest mobile.web.test_mobile_web_entrypoint
Ran 292 tests in 2.545s
OK

PYTHONDONTWRITEBYTECODE=1 python3 -m unittest mobile.test_mobile_web_entrypoint
Ran 54 tests in 0.735s
OK
```

Fresh browser evidence artifacts:

- `mobile_current_panel_browser_proof_refresh_latest_field_evidence_390x844.json`
- `mobile_current_panel_browser_proof_refresh_latest_field_evidence_390x844.png`
- `mobile_current_panel_browser_proof_refresh_latest_field_evidence_768x900.json`
- `mobile_current_panel_browser_proof_refresh_latest_field_evidence_768x900.png`
- `mobile_current_panel_browser_proof_refresh_latest_field_evidence_summary.json`

Failure定位:

- No gate, unittest, console-zero, current-panel, current-boundary, phone-safe, or diff-check failure was observed in Task A after the implementation.

Remaining risk:

- This is local Chromium-family software proof only and `not true phone/browser`.
- It does not prove real iPhone/Android behavior, production app, real PWA prompt/user choice, public HTTPS/TLS, 4G/SIM, OSS/CDN live traffic, production DB/queue, route/elevator field pass, dropoff/cancel completion, HIL, WAVE ROVER/UART, PR #5 resolution, or delivery success.
- Product closeout still needs to decide OKR wording separately; Task A did not create `side2side_check.md` or `final.md`.

## Task B Robot Read-Only Consultation

Owner: `robot-software-engineer`

Scope: read-only consultation for `mobile_current_panel_browser_proof_refresh_latest_field_evidence`; no product code, test code, Robot runtime code, mobile fixture, or docs changes were made.

Allowed write performed:

- `sprints/2026.05.23_09-10_mobile-current-panel-browser-proof-refresh-latest-field-evidence/tech-done.md`

Read-only evidence checked:

- `mobile/web/app.js`
- `mobile/web/fixtures/robot_diagnostics_field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_intake.json`
- `mobile/web/test_mobile_web_entrypoint.py`
- `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py`
- `onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`

Consultation result:

- Phone-safe consumption is aligned. The current panel for `field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_intake` first consumes Robot diagnostics safe summary aliases such as `robot_diagnostics_field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_intake_summary`, then sanitized fallback summary shapes.
- The panel does not require raw ROS topics, `/cmd_vel`, raw control payloads, hardware parameters, WAVE ROVER/UART details, credentials, secret values, local filesystem paths, tracebacks, checksums, or complete artifacts. Web-side sanitizer text and Robot-side unsafe-field rejection both explicitly block those classes.
- The Robot safe summary semantics stay fail-closed: `delivery_success=false`, `primary_actions_enabled=false`, and `safe_to_control=false`. Mobile fixture top-level action affordances also keep `can_collect=false`, `can_confirm_dropoff=false`, and `can_cancel=false`.
- Evidence boundary remains `software_proof_docker_mobile_current_panel_browser_proof_refresh_latest_field_evidence_gate`. This is `not true phone/browser`, not HIL, not route/elevator field pass, not delivery success, and not a real phone-device proof.

## Verification

Command:

```bash
rg -n "field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_intake|delivery_success=false|primary_actions_enabled=false|safe_to_control=false|software_proof_docker_mobile_current_panel_browser_proof_refresh_latest_field_evidence_gate|not true phone/browser" sprints/2026.05.23_09-10_mobile-current-panel-browser-proof-refresh-latest-field-evidence mobile/web mobile/fixtures mobile/web/fixtures onboard/src/ros2_trashbot_behavior
```

Result: PASS, exit code 0. Output was large (4510 matched lines on final rerun). Representative hits:

```text
sprints/2026.05.23_09-10_mobile-current-panel-browser-proof-refresh-latest-field-evidence/tech-done.md:27:- Phone-safe consumption is aligned. The current panel for `field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_intake` first consumes Robot diagnostics safe summary aliases such as `robot_diagnostics_field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_intake_summary`, then sanitized fallback summary shapes.
sprints/2026.05.23_09-10_mobile-current-panel-browser-proof-refresh-latest-field-evidence/tech-done.md:29:- The Robot safe summary semantics stay fail-closed: `delivery_success=false`, `primary_actions_enabled=false`, and `safe_to_control=false`. Mobile fixture top-level action affordances also keep `can_collect=false`, `can_confirm_dropoff=false`, and `can_cancel=false`.
sprints/2026.05.23_09-10_mobile-current-panel-browser-proof-refresh-latest-field-evidence/tech-done.md:30:- Evidence boundary remains `software_proof_docker_mobile_current_panel_browser_proof_refresh_latest_field_evidence_gate`. This is `not true phone/browser`, not HIL, not route/elevator field pass, not delivery success, and not a real phone-device proof.
mobile/web/fixtures/robot_diagnostics_field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_intake.json:31:    "safe_phone_copy": "现场证据复跑执行结果验收交接回执 owner response reviewer ACK intake: ack_status=reviewer_acknowledged_not_proven, source=software_proof, software_proof, not_proven, safe_to_control=false, delivery_success=false, primary_actions_enabled=false.",
onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py:85291:        robot_diagnostics_field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_intake_summary=(
```

Command:

```bash
git diff --check -- sprints/2026.05.23_09-10_mobile-current-panel-browser-proof-refresh-latest-field-evidence
```

Result: PASS, exit code 0, no output.

## Failure定位

- None so far. This task is read-only consultation plus sprint evidence write; no runtime code path was changed.

## Remaining Risk

- No real phone/browser run was performed by this Robot consultation task.
- No HIL, true route/elevator field pass, `/cmd_vel`, UART, WAVE ROVER, or delivery runtime evidence was generated.
- Product closeout still needs to keep this boundary as software proof only unless separate real-device or field materials are attached.

## Coordination

- Product: needed for closeout and no-OKR-lift wording under the software-proof-only boundary.
- Full-Stack: needed only if browser proof or mobile panel behavior changes after this consultation.
- Hardware: not needed for this read-only consultation because no hardware parameters or WAVE ROVER/UART behavior were changed.
- Autonomy: not needed unless future real route/elevator field evidence is supplied.

## Task C Product Closeout

Owner: `product-okr-owner`

Scope: closeout accepted Task A and Task B as a bounded Epic sprint result for `mobile_current_panel_browser_proof_refresh_latest_field_evidence`.

User value and product north star:

- User value: the phone-facing current-panel proof now catches whether the latest field-evidence reviewer ACK intake panel is present, bounded, phone-safe, and fail-closed before anyone treats the mobile surface as current.
- Product north star: keep the user touchpoint honest. The phone surface may explain blocked field evidence and next steps, but it must not imply the robot is safe to control, delivered, or externally proven without real phone, field, cloud, or hardware material.

OKR mapping:

- Objective 4 is the main beneficiary because this sprint refreshes `mobile/web` current-panel browser coverage.
- Objective 5 remains the lowest numeric Objective at about 68%, but this sprint has no true external evidence and therefore does not raise O5.
- Objective 1 remains about 81% because PR #5 `PRRT_kwDOSWB9286CJ3tX` remains unresolved / `is_resolved=false` / `hardware_material_pending`, while `PRRT_kwDOSWB9286CJ3tQ` and `PRRT_kwDOSWB9286CJ3tU` are resolved but do not close X.
- Objective 2 / Objective 3 / Objective 4 remain about 99% because there is no true route/elevator field pass, Nav2/fixed-route runtime pass, true phone/browser run, or production app evidence.

Integrated evidence accepted:

- Task A browser proof PASS for `390x844` and `768x900`.
- Summary evidence reports `current_panels_status=passed`, `current_boundaries_status=passed`, `console_zero_status=passed`, and `console_error_count=0`.
- Task A unittests PASS: `mobile.web` reported `Ran 292 tests ... OK`; `mobile` wrapper reported `Ran 54 tests ... OK`.
- Task B consultation accepted the latest panel consumption as phone-safe: no raw ROS topics, `/cmd_vel`, raw control payloads, hardware parameters, WAVE ROVER/UART details, secrets, paths, tracebacks, checksums, or complete artifacts are required by the panel.
- Task B confirmed `delivery_success=false`, `primary_actions_enabled=false`, and `safe_to_control=false` remain aligned with the Robot safe-summary semantics.

Exact proof boundary:

- Capability: `mobile_current_panel_browser_proof_refresh_latest_field_evidence`.
- Boundary: `software_proof_docker_mobile_current_panel_browser_proof_refresh_latest_field_evidence_gate`.
- Latest covered panel: `field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_intake`.
- This is local Chromium-family browser proof only and `not true phone/browser`.

Not claimed:

- No true phone/browser.
- No public HTTPS/TLS.
- No 4G/SIM.
- No OSS/CDN live traffic.
- No production DB/queue.
- No worker/cutover.
- No HIL.
- No WAVE ROVER/UART.
- No route/elevator field pass.
- No verified terminal result.
- No dropoff/cancel completion.
- No delivery result.
- No delivery success.
- No PR #5 resolution.
- No OKR percentage lift.

Files changed by Task C:

- `OKR.md`
- `docs/process/okr_progress_log.md`
- `sprints/2026.05.23_09-10_mobile-current-panel-browser-proof-refresh-latest-field-evidence/tech-done.md`
- `sprints/2026.05.23_09-10_mobile-current-panel-browser-proof-refresh-latest-field-evidence/side2side_check.md`
- `sprints/2026.05.23_09-10_mobile-current-panel-browser-proof-refresh-latest-field-evidence/final.md`

Remaining risk:

- The next useful OKR lift still requires real material: Objective 5 external proof, Objective 1 hardware/HIL/material proof, true phone/browser evidence, or route/elevator field evidence.
- This sprint only reduces current-panel browser-proof drift; it does not complete a user delivery loop.
