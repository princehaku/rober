# Hardware Sensor HIL-entry Callback Review Decision Tech Plan

## OKR 最低优先级核对

1. 当前 `OKR.md` 4.1 完成度最低的是 Objective 5，约 68%。
2. 本 sprint 不针对 Objective 5。
3. 理由：最新 `cloud_auth_failure_status_guard` final 和 `OKR.md` 均要求 O5 下一步必须有真实外部材料；本机只有 Docker，没有公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/cutover 或真实手机/browser external proof。本轮改走次低 Objective 1，并承接 PR #5 unresolved review thread `PRRT_kwDOSWB9286CJ3tX`。

## Task A - Hardware PC Gate

Owner: Hardware Infra Engineer.

Allowed files:

- `pc-tools/evidence/hardware_sensor_hil_entry_callback_review_decision_gate.py`
- `pc-tools/evidence/test_hardware_sensor_hil_entry_callback_review_decision_gate.py`
- `pc-tools/README.md`
- `docs/product/production_hardware_boundary.md`

Scope:

- Consume `hardware_sensor_hil_entry_callback_intake` artifact/summary/wrapper.
- Emit `trashbot.hardware_sensor_hil_entry_callback_review_decision.v1` and summary schema.
- Keep `software_proof_docker_hardware_sensor_hil_entry_callback_review_decision_gate`.
- Fail closed on missing/unsupported input, evidence ref mismatch, unsafe raw copy, weak contract, success claims, and control claims.

Acceptance commands:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile pc-tools/evidence/hardware_sensor_hil_entry_callback_review_decision_gate.py
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest pc-tools/evidence/test_hardware_sensor_hil_entry_callback_review_decision_gate.py
python3 pc-tools/evidence/hardware_sensor_hil_entry_callback_review_decision_gate.py --help
rg -n "hardware_sensor_hil_entry_callback_review_decision|software_proof_docker_hardware_sensor_hil_entry_callback_review_decision_gate|docs/vendor/VENDOR_INDEX.md|hardware_material_pending|not_proven|delivery_success=false|primary_actions_enabled=false" pc-tools/evidence pc-tools/README.md docs/product/production_hardware_boundary.md
git diff --check -- pc-tools/evidence/hardware_sensor_hil_entry_callback_review_decision_gate.py pc-tools/evidence/test_hardware_sensor_hil_entry_callback_review_decision_gate.py pc-tools/README.md docs/product/production_hardware_boundary.md
```

## Task B - Robot Diagnostics Safe Alias

Owner: Robot Platform Engineer.

Allowed files:

- `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py`
- `onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`
- `docs/interfaces/ros_runtime_contracts.md`

Scope:

- Add `robot_diagnostics_hardware_sensor_hil_entry_callback_review_decision_summary`.
- Consume only safe summary/artifact fields from explicit ref, latest status, top-level payload, and nested diagnostics wrappers.
- Preserve no Start / Confirm Dropoff / Cancel / ACK / cursor / Nav2 / HIL / delivery side effects.

Acceptance commands:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py
PYTHONPATH=onboard/src/ros2_trashbot_behavior PYTHONDONTWRITEBYTECODE=1 python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py
rg -n "robot_diagnostics_hardware_sensor_hil_entry_callback_review_decision_summary|hardware_sensor_hil_entry_callback_review_decision|software_proof_docker_hardware_sensor_hil_entry_callback_review_decision_gate|delivery_success=false|primary_actions_enabled=false" onboard/src/ros2_trashbot_behavior docs/interfaces/ros_runtime_contracts.md
git diff --check -- onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py docs/interfaces/ros_runtime_contracts.md
```

## Task C - Mobile Read-only Panel

Owner: User Touchpoint Full-Stack Engineer.

Allowed files:

- `mobile/web/app.js`
- `mobile/web/fixtures/status.json`
- `mobile/web/fixtures/robot_diagnostics_hardware_sensor_hil_entry_callback_review_decision_summary.json`
- `mobile/web/test_mobile_web_entrypoint.py`
- `docs/product/mobile_user_flow.md`

Scope:

- Add a read-only “传感器 HIL 回调复核决策” panel.
- Prefer Robot diagnostics safe alias and support direct safe summary fallback.
- Do not add fetch, ACK, cursor, robot command, Start Delivery, Confirm Dropoff, or Cancel behavior.

Acceptance commands:

```bash
node --check mobile/web/app.js
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest mobile/web/test_mobile_web_entrypoint.py
python3 -m json.tool mobile/web/fixtures/status.json >/dev/null
python3 -m json.tool mobile/web/fixtures/robot_diagnostics_hardware_sensor_hil_entry_callback_review_decision_summary.json >/dev/null
rg -n "hardware_sensor_hil_entry_callback_review_decision|robot_diagnostics_hardware_sensor_hil_entry_callback_review_decision_summary|software_proof_docker_hardware_sensor_hil_entry_callback_review_decision_gate|传感器 HIL 回调复核决策|delivery_success=false|primary_actions_enabled=false" mobile/web docs/product/mobile_user_flow.md
git diff --check -- mobile/web/app.js mobile/web/fixtures/status.json mobile/web/fixtures/robot_diagnostics_hardware_sensor_hil_entry_callback_review_decision_summary.json mobile/web/test_mobile_web_entrypoint.py docs/product/mobile_user_flow.md
```

## Task D - Product Closeout

Owner: Product Manager / OKR Owner.

Allowed files:

- `OKR.md`
- `docs/process/okr_progress_log.md`
- `sprints/2026.05.20_20-21_hardware-sensor-hil-entry-callback-review-decision/tech-done.md`
- `sprints/2026.05.20_20-21_hardware-sensor-hil-entry-callback-review-decision/side2side_check.md`
- `sprints/2026.05.20_20-21_hardware-sensor-hil-entry-callback-review-decision/final.md`

Scope:

- Record actual evidence from Tasks A/B/C.
- Keep Objective 5 at about 68% and Objective 1 conservative unless real hardware materials exist.
- State that PR #5 `PRRT_kwDOSWB9286CJ3tX` remains unresolved until live reviewer resolution.

Acceptance commands:

```bash
rg -n "hardware_sensor_hil_entry_callback_review_decision|software_proof_docker_hardware_sensor_hil_entry_callback_review_decision_gate|Objective 5|Objective 1|PRRT_kwDOSWB9286CJ3tX|not_proven|delivery_success=false|primary_actions_enabled=false" sprints/2026.05.20_20-21_hardware-sensor-hil-entry-callback-review-decision OKR.md docs/process/okr_progress_log.md
git diff --check -- OKR.md docs/process/okr_progress_log.md sprints/2026.05.20_20-21_hardware-sensor-hil-entry-callback-review-decision
```
