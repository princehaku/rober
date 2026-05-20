# PR5 Mandatory Sensor Source Alignment Tech Done

## Sprint Declaration

- sprint_type: epic
- Sprint: `2026.05.21_04-05_pr5-mandatory-sensor-source-alignment`
- Target capability: `pr5_mandatory_sensor_source_alignment`
- Evidence boundary: `software_proof_docker_pr5_mandatory_sensor_source_alignment_gate`
- Preserved states: `source=software_proof`, `hardware_material_pending`, `not_proven`, `safe_to_control=false`, `delivery_success=false`, `primary_actions_enabled=false`
- Product closeout time: 2026-05-21 04:21 Asia/Shanghai

## Actual Changes

Hardware Infra Engineer changed:

- `pc-tools/evidence/pr5_mandatory_sensor_source_alignment.py`
- `tests/test_pr5_mandatory_sensor_source_alignment.py`
- `docs/interfaces/pr5_mandatory_sensor_source_alignment.md`
- `docs/product/production_hardware_boundary.md`

Robot Platform Engineer changed:

- `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py`
- `onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`
- `docs/interfaces/ros_runtime_contracts.md`

User Touchpoint Full-Stack Engineer changed:

- `mobile/web/app.js`
- `mobile/web/fixtures/status.json`
- `mobile/web/test_mobile_web_entrypoint.py`
- `docs/product/mobile_user_flow.md`

Autonomy Algorithm Engineer changed:

- `docs/navigation/fixed_route_workflow.md`
- `docs/interfaces/evidence_contracts.md`

Product Manager / OKR Owner changed:

- `OKR.md`
- `docs/process/okr_progress_log.md`
- `sprints/2026.05.21_04-05_pr5-mandatory-sensor-source-alignment/tech-done.md`
- `sprints/2026.05.21_04-05_pr5-mandatory-sensor-source-alignment/side2side_check.md`
- `sprints/2026.05.21_04-05_pr5-mandatory-sensor-source-alignment/final.md`

## Vendor And Source Material Used

Hardware source-boundary work cited local vendor refs only:

- `docs/vendor/VENDOR_INDEX.md`
- `docs/vendor/waveshare_wave_rover/ugv_rpi/README.md`
- `docs/vendor/waveshare_wave_rover/ugv_rpi/base_ctrl.py`
- `docs/vendor/waveshare_wave_rover/ugv_rpi/config.yaml`
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/json_cmd.h`
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/uart_ctrl.h`
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/movtion_module.h`
- Orange Pi Zero 3 manual/schematic were cited only as local vendor refs listed by the index; no pin or voltage conclusions were derived.

## Worker Validation Results

- Hardware: `py_compile` passed; `python3 -m unittest tests.test_pr5_mandatory_sensor_source_alignment` reported `Ran 6 tests ... OK`; CLI `--help` passed; required `rg` passed; diff check passed after intent-to-add; comment density gate reported `20.1%`, test `24.0%`.
- Robot: `py_compile` passed; diagnostics unittest reported `Ran 245 tests in 0.795s OK`; required `rg` and diff check passed. The worker fixed one unsafe scanner false positive where a `delivery_success` false-state token in `not_proven` was misread as success wording.
- Full-Stack: `node --check` passed; `python3 -m unittest mobile/web/test_mobile_web_entrypoint.py` reported `Ran 193 tests ... OK`; fixture JSON check passed; required `rg` and diff check passed.
- Autonomy: required `rg` passed; scoped diff check passed.

## Product Acceptance Result

Product accepted the sprint as a conservative software-proof closeout. The implementation moved the PR #5 mandatory sensor source-alignment contract forward across Hardware, Robot diagnostics, mobile/web, and Autonomy documentation, while preserving the non-proof boundary.

No Objective percentage is raised. Objective 5 remains about 68%; Objective 1 remains about 81%.

## Remaining Risks

- PR #5 `PRRT_kwDOSWB9286CJ3tX` remains unresolved / `is_resolved=false` / `hardware_material_pending`.
- This sprint does not prove real 2D LiDAR / ToF SKU/source/receipt/procurement, installation, wiring, power validation, calibration, HIL-entry, WAVE ROVER/UART/HIL, true Nav2/SLAM/fixed-route pass, near-field safety pass, true phone/browser proof, O5 external proof, dropoff/cancel completion, delivery result, or delivery success.
- Next O1 progress still requires real material evidence or reviewer resolution; next O5 progress still requires real external cloud/mobile proof.
