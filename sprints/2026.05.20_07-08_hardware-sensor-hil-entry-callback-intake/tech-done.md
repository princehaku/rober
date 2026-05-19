# Sprint 2026.05.20_07-08 Hardware Sensor HIL-entry Callback Intake - Tech Done

sprint_type: epic

## 1. 实际改动

本轮由三位 implementation worker 完成，并由 Product closeout 做集成验收与 OKR 同步。

- Hardware Infra Engineer 新增 `pc-tools/evidence/hardware_sensor_hil_entry_callback_intake_gate.py` 与 focused unittest，更新 `pc-tools/README.md`、`docs/product/production_hardware_boundary.md`。
- Robot Platform Engineer 在 `operator_gateway_diagnostics.py` 新增 `hardware_sensor_hil_entry_callback_intake` / summary safe alias，补充 diagnostics tests 和 `docs/interfaces/ros_contracts.md`。
- User Touchpoint Full-Stack Engineer 在 `mobile/web` 新增只读“传感器 HIL 回调入口”panel、fixture、entrypoint test 和 `docs/product/mobile_user_flow.md`。
- Product Manager / OKR Owner 更新 `OKR.md`、`docs/process/okr_progress_log.md`、本 sprint closeout 文档，并保持 Objective 5 约 68%、Objective 1 约 81%。

## 2. 验证结果

Product closeout 运行集成验收围栏：

```bash
python3 -m py_compile pc-tools/evidence/hardware_sensor_hil_entry_callback_intake_gate.py onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py
python3 -m unittest pc-tools/evidence/test_hardware_sensor_hil_entry_callback_intake_gate.py
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest mobile.web.test_mobile_web_entrypoint
node --check mobile/web/app.js
rg -n "hardware_sensor_hil_entry_callback_intake|software_proof_docker_hardware_sensor_hil_entry_callback_intake_gate|Objective 5|Objective 1|PRRT_kwDOSWB9286CJ3tX|hardware_material_pending|not_proven|delivery_success=false|primary_actions_enabled=false|真实 2D LiDAR|真实手机|O5 external proof" OKR.md docs/process/okr_progress_log.md sprints/2026.05.20_07-08_hardware-sensor-hil-entry-callback-intake pc-tools/evidence pc-tools/README.md docs/product docs/interfaces onboard/src/ros2_trashbot_behavior mobile/web
git diff --check -- OKR.md docs/process/okr_progress_log.md sprints/2026.05.20_07-08_hardware-sensor-hil-entry-callback-intake pc-tools/evidence/hardware_sensor_hil_entry_callback_intake_gate.py pc-tools/evidence/test_hardware_sensor_hil_entry_callback_intake_gate.py pc-tools/README.md docs/product/production_hardware_boundary.md onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py docs/interfaces/ros_contracts.md mobile/web/app.js mobile/web/styles.css mobile/web/fixtures/status.json mobile/web/test_mobile_web_entrypoint.py docs/product/mobile_user_flow.md
git diff --cached --check
```

验收摘要：

- Hardware callback intake unittest：7 tests OK。
- Robot diagnostics unittest：223 tests OK。
- mobile/web entrypoint unittest：153 tests OK。
- `py_compile`、`node --check`、required `rg`、scoped `git diff --check`、`git diff --cached --check` 均通过。

## 3. 偏差与修正

`pre_start.md`、`prd.md`、`tech-plan.md` 最初按 planning-only 记录。本轮 closeout 已补充 implementation/closeout 状态，避免 sprint 文档继续误写为“只做 planning”。

未运行 Docker colcon 或大构建，符合本轮验收命令边界。

## 4. 剩余风险

本轮证据边界是 `software_proof_docker_hardware_sensor_hil_entry_callback_intake_gate`。它不证明真实 2D LiDAR / ToF，不证明真实采购、安装、接线、供电、标定或 HIL-entry，不证明 WAVE ROVER/UART/HIL，不证明 PR #5 `PRRT_kwDOSWB9286CJ3tX` resolved，不证明 Objective 5 external proof，不证明真实 phone/browser，不证明 route/elevator field pass，也不证明 delivery success。

下一步若要提升 Objective 1，必须回填真实 2D LiDAR / ToF SKU/source/receipt/procurement/installation/wiring/power/calibration/HIL-entry，或在真实 WAVE ROVER 环境采集同一 safe `evidence_ref` 的 HIL packet 与 operator report。
