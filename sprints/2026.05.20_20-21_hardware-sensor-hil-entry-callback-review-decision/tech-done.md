# Hardware Sensor HIL-entry Callback Review Decision Tech Done

## Final Implementation Evidence

- sprint_type: epic
- Sprint: `2026.05.20_20-21_hardware-sensor-hil-entry-callback-review-decision`
- Evidence boundary: `software_proof_docker_hardware_sensor_hil_entry_callback_review_decision_gate`
- Preserved states: `source=software_proof`, `hardware_material_pending`, `not_proven`, `safe_to_control=false`, `delivery_success=false`, `primary_actions_enabled=false`

## Task A - Hardware PC Gate

Hardware worker added `hardware_sensor_hil_entry_callback_review_decision` as a PC-only metadata gate.

Changed files:

- `pc-tools/evidence/hardware_sensor_hil_entry_callback_review_decision_gate.py`
- `pc-tools/evidence/test_hardware_sensor_hil_entry_callback_review_decision_gate.py`
- `pc-tools/README.md`
- `docs/product/production_hardware_boundary.md`

Implementation:

- Consumes `hardware_sensor_hil_entry_callback_intake` artifact, summary, or Robot-safe wrapper.
- Emits `trashbot.hardware_sensor_hil_entry_callback_review_decision.v1` and `trashbot.hardware_sensor_hil_entry_callback_review_decision_summary.v1`.
- Maps callback intake accepted, missing, rejected, mismatch, unsupported, unsafe, and weak-contract states into a fail-closed review decision.
- Outputs decision reasons, next required evidence, owner handoff, safe rerun command, sanitized safe copy, and repo-local vendor/source boundary.
- Keeps `docs/vendor/VENDOR_INDEX.md` as source boundary and does not treat Orange Pi / WAVE ROVER vendor files as proof of project 2D LiDAR or ToF procurement.

Vendor sources read by Hardware worker:

- `AGENTS.md`
- `docs/vendor/VENDOR_INDEX.md`
- `docs/vendor/waveshare_wave_rover/ugv_rpi/base_ctrl.py`
- `docs/vendor/waveshare_wave_rover/ugv_rpi/config.yaml`
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/json_cmd.h`
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/uart_ctrl.h`

Hardware conclusion:

- Local vendor material confirms WAVE ROVER UART uses newline-delimited UTF-8 JSON; Raspberry Pi vendor defaults include `/dev/ttyAMA0` at `115200`; command references include `T=1`, `T=13`, `T=130`, `T=131`, `T=142`, and `T=143`.
- This sprint does not verify Orange Pi actual UART device, real 2D LiDAR, real ToF, WAVE ROVER runtime, or HIL.

Validation:

- `PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile pc-tools/evidence/hardware_sensor_hil_entry_callback_review_decision_gate.py`: passed.
- `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest pc-tools/evidence/test_hardware_sensor_hil_entry_callback_review_decision_gate.py`: passed, `Ran 7 tests in 0.009s`, `OK`.
- `python3 pc-tools/evidence/hardware_sensor_hil_entry_callback_review_decision_gate.py --help`: passed.
- Required `rg`: passed.
- Scoped `git diff --check`: passed.

## Task B - Robot Diagnostics Safe Alias

Robot worker added `robot_diagnostics_hardware_sensor_hil_entry_callback_review_decision_summary`.

Changed files:

- `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py`
- `onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`
- `docs/interfaces/ros_runtime_contracts.md`

Implementation:

- Consumes sanitized `hardware_sensor_hil_entry_callback_review_decision` summary/artifact wrappers only.
- Fails closed on missing summary, unsupported schema or boundary, weak safe evidence ref, unsafe copy/raw markers, success/control claims, and action-enabled flags.
- Removes raw callback/review material from `latest_status` and exposes only safe summary aliases.
- Keeps Start Delivery, Confirm Dropoff, Cancel, ACK, cursor, Nav2, HIL, dropoff/cancel completion, delivery result, and primary actions disabled.

Validation:

- `PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`: passed.
- `PYTHONPATH=onboard/src/ros2_trashbot_behavior PYTHONDONTWRITEBYTECODE=1 python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`: passed, `Ran 237 tests in 0.728s`, `OK`.
- Required `rg`: passed.
- Scoped `git diff --check`: passed.

Failure found and fixed by Robot worker:

- First diagnostics unittest run treated `{}` as a valid summary candidate. The worker fixed this by accepting only non-empty sanitized summary candidates, removed an accidental stale status write in older similar branches, and reran the targeted suite.

## Task C - Mobile Read-only Panel

Full-Stack worker added a read-only first-screen mobile panel.

Changed files:

- `mobile/web/app.js`
- `mobile/web/fixtures/status.json`
- `mobile/web/fixtures/robot_diagnostics_hardware_sensor_hil_entry_callback_review_decision_summary.json`
- `mobile/web/test_mobile_web_entrypoint.py`
- `docs/product/mobile_user_flow.md`

Implementation:

- Adds the “传感器 HIL 回调复核决策” panel after callback intake.
- Prefers `robot_diagnostics_hardware_sensor_hil_entry_callback_review_decision_summary` and supports direct safe summary fallback.
- Displays review decision, source callback intake status, accepted/missing/rejected callback materials, decision reasons, owner handoff, next required evidence, safe rerun command, safe evidence ref, boundary, and `not_proven`.
- Adds no fetch, ACK, cursor, robot command, Start Delivery, Confirm Dropoff, or Cancel behavior; existing main-action gating remains unchanged.

Validation:

- `node --check mobile/web/app.js`: passed.
- `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest mobile/web/test_mobile_web_entrypoint.py`: passed, `Ran 179 tests in 1.300s`, `OK`.
- `python3 -m json.tool mobile/web/fixtures/status.json >/dev/null`: passed.
- `python3 -m json.tool mobile/web/fixtures/robot_diagnostics_hardware_sensor_hil_entry_callback_review_decision_summary.json >/dev/null`: passed.
- Required `rg`: passed.
- Scoped `git diff --check`: passed.

## Product Integration Rerun

Product closeout reran the combined fenced integration checks after all workers returned:

```text
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile pc-tools/evidence/hardware_sensor_hil_entry_callback_review_decision_gate.py onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py
passed

PYTHONDONTWRITEBYTECODE=1 python3 -m unittest pc-tools/evidence/test_hardware_sensor_hil_entry_callback_review_decision_gate.py
Ran 7 tests in 0.009s
OK

PYTHONPATH=onboard/src/ros2_trashbot_behavior PYTHONDONTWRITEBYTECODE=1 python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py
Ran 237 tests in 0.728s
OK

node --check mobile/web/app.js
passed

PYTHONDONTWRITEBYTECODE=1 python3 -m unittest mobile/web/test_mobile_web_entrypoint.py
Ran 179 tests in 1.300s
OK

fixture JSON checks
passed

python3 pc-tools/evidence/hardware_sensor_hil_entry_callback_review_decision_gate.py --help
passed

required rg and scoped git diff --check
passed
```

## Remaining Risk

- This is software-proof only. It does not prove real 2D LiDAR, real ToF, procurement, installation, wiring, power, calibration, WAVE ROVER/UART, HIL-entry pass, Nav2/SLAM field pass, route/elevator field pass, real phone/browser proof, O5 external proof, PR #5 `PRRT_kwDOSWB9286CJ3tX` resolution, dropoff/cancel completion, or delivery success.
- Real materials must still be provided by field/hardware owners before Objective 1 can increase materially.
