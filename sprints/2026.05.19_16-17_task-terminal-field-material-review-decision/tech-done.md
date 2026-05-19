# Sprint 2026.05.19_16-17 Task Terminal Field Material Review Decision - Tech Done

## sprint_type: epic

Closeout time: 2026-05-19 16:19 Asia/Shanghai.

## 1. 实际改动

### Autonomy worker

- Changed `pc-tools/evidence/task_terminal_field_material_review_decision.py`.
- Changed `tests/test_task_terminal_field_material_review_decision.py`.
- Changed `pc-tools/README.md`.
- Added read-only PC evidence gate mapping `task_terminal_field_material_intake` returned/missing materials into `accepted_materials`, `missing_materials`, `rejected_materials`, `blocked_materials`, `owner_handoff`, `next_required_evidence`, and `rerun_guidance`.
- Fixed first-round bug: present empty `missing_materials: []` is now interpreted as no material gap, not as an absent field.

### Robot worker

- Changed `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py`.
- Changed `onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`.
- Changed `docs/interfaces/operator_gateway_diagnostics.md`.
- Added `robot_diagnostics_task_terminal_field_material_review_decision_summary`.
- Kept missing, unsupported, unsafe, success, and control inputs fail-closed with `software_proof`, `not_proven`, `delivery_success=false`, `primary_actions_enabled=false`, and `safe_to_control=false`.

### Full-Stack worker

- Changed `mobile/web/app.js`.
- Changed `mobile/web/styles.css`.
- Changed `mobile/web/test_mobile_web_entrypoint.py`.
- Changed `mobile/fixtures/mobile_web_status.fixture.json`.
- Changed `mobile/web/fixtures/status.json`.
- Changed `docs/product/mobile_user_flow.md`.
- Added read-only mobile/web “现场材料复核决策” panel.
- The panel only consumes `robot_diagnostics_task_terminal_field_material_review_decision_summary`; Start Delivery, Confirm Dropoff, and Cancel gating are unchanged.

### Product closeout

- Created this `tech-done.md`.
- Created `side2side_check.md`.
- Created `final.md`.
- Updated `OKR.md` 4.1 latest sprint narrative.
- Updated `docs/process/okr_progress_log.md`.

## 2. 验证结果

### Autonomy worker

```text
python3 -m py_compile pc-tools/evidence/task_terminal_field_material_review_decision.py
passed

python3 -m unittest tests.test_task_terminal_field_material_review_decision
Ran 5 tests ... OK

python3 pc-tools/evidence/task_terminal_field_material_review_decision.py --help
passed

required rg
passed

git diff --check -- pc-tools/evidence tests pc-tools/README.md sprints/2026.05.19_16-17_task-terminal-field-material-review-decision
passed
```

### Robot worker

```text
python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py
passed

python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py
Ran 208 tests in 0.509s OK

required rg
passed

git diff --check -- onboard/src/ros2_trashbot_behavior docs/interfaces
passed
```

### Full-Stack worker

```text
python3 mobile/web/test_mobile_web_entrypoint.py
Ran 129 tests ... OK

python3 -m py_compile mobile/web/test_mobile_web_entrypoint.py
passed

node --check mobile/web/app.js
passed

required rg
passed

git diff --check -- mobile/web mobile/fixtures docs/product/mobile_user_flow.md
passed
```

### Product closeout fence

Product closeout runs the required file existence, required `rg`, and scoped `git diff --check` after these documents and OKR/progress log are updated. The command output is recorded in the final response.

## 3. 偏差与失败定位

- Autonomy first round bug: empty `missing_materials: []` was initially treated as absent. Root cause was conflating field presence with list emptiness. The worker corrected it so present empty means no material gap.
- No remaining implementation failure was reported by the three workers after rerun.
- Product closeout did not run broad ROS2/Humble, browser, or hardware validation because this closeout scope is limited to sprint, OKR, and progress log documents, while worker validation already covered the changed product surfaces.

## 4. 证据边界

This sprint is `software_proof_docker_task_terminal_field_material_review_decision_gate`.

It is not real Objective 5 external proof, not Objective 1 HIL, not PR #4 route/elevator field pass, not PR #5 hardware material, not real phone/browser proof, not real Nav2/fixed-route proof, not dropoff/cancel completion, not delivery success, and not a grant of control authority.

The required boundary stays explicit:

- `software_proof`
- `not_proven`
- `delivery_success=false`
- `primary_actions_enabled=false`
- `safe_to_control=false`

## 5. 剩余风险

- Objective 5 remains about 68% because there is still no real HTTPS/TLS public ingress, 4G/SIM, OSS/CDN live traffic, production DB/queue connectivity, worker/cutover, or real external phone/browser evidence.
- Objective 1 remains about 81% because there is still no WAVE ROVER/UART/HIL, real `feedback_T1001.log`, real `/odom`, `/imu/data`, `/battery`, operator HIL report, or PR #5 real 2D LiDAR / ToF SKU/source/receipt/procurement/installation/wiring/power/calibration/HIL-entry material.
- Objective 2/3/4 remain about 99% because this sprint only improves review decision hygiene and owner handoff; real task record, real dropoff/cancel terminal material, real route/elevator field material, real Nav2/fixed-route runtime log, real route completion signal, real elevator door/floor/human-assistance record, and real phone/browser behavior are still missing.
