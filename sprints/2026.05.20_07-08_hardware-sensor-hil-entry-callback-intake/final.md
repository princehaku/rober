# Sprint 2026.05.20_07-08 Hardware Sensor HIL-entry Callback Intake - Final

sprint_type: epic

## 1. 收口结论

本轮完成 `hardware_sensor_hil_entry_callback_intake` software-proof 闭环：PC gate 生成 fail-closed artifact / summary，Robot diagnostics 只消费 sanitized safe alias，mobile/web 展示只读“传感器 HIL 回调入口”panel。Product closeout 已同步 OKR 快照和进度日志，并将本轮证据边界固定为 `software_proof_docker_hardware_sensor_hil_entry_callback_intake_gate`。

本轮不提高 OKR 百分比：Objective 5 保持约 68%，Objective 1 保持约 81%。

## 2. OKR 进度回顾

- Objective 5：仍缺真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/cutover 和真实手机/browser，因此保持约 68%。
- Objective 1：本轮只新增真实材料执行后的 callback intake software proof；仍缺真实 2D LiDAR / ToF SKU/source/receipt/procurement/installation/wiring/power/calibration/HIL-entry、真实 WAVE ROVER/UART/HIL 和 PR #5 `PRRT_kwDOSWB9286CJ3tX` closure，因此保持约 81%。
- Objective 4：mobile/web 只读可见性改善，但没有真实 phone/browser acceptance，因此保持约 99%。

## 3. 验收证据

Product closeout 运行并通过本轮要求的集成围栏：

- `py_compile` 覆盖 callback intake gate 和 Robot diagnostics module。
- `python3 -m unittest pc-tools/evidence/test_hardware_sensor_hil_entry_callback_intake_gate.py`：7 tests OK。
- `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`：223 tests OK。
- `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest mobile.web.test_mobile_web_entrypoint`：153 tests OK。
- `node --check mobile/web/app.js`：通过。
- required `rg`：覆盖 sprint / OKR / progress log / PC gate / Robot / mobile / docs 的关键 proof-boundary 和 not-proven 词。
- scoped `git diff --check` 与 `git diff --cached --check`：通过。

未运行 Docker colcon 或大构建，符合本轮明确验收边界。

## 4. 风险与阻塞

剩余 blocker 未关闭：

- 真实 2D LiDAR / ToF SKU/source/receipt/procurement/installation/wiring/power/calibration/HIL-entry 仍缺。
- 真实 WAVE ROVER/UART/HIL、`feedback_T1001.log`、`/odom`、`/imu/data`、`/battery`、operator HIL report 仍缺。
- PR #5 `PRRT_kwDOSWB9286CJ3tX` 仍不得写成 resolved。
- O5 external proof、真实 phone/browser、route/elevator field pass 和 delivery success 仍缺。

## 5. 下一步

下一轮若继续 Objective 1，必须让现场 owner 通过本轮 callback intake 回填真实 sensor/HIL-entry materials；如果真实硬件材料仍不可得，应转向 Objective 5 的真实 external proof 或 Objective 4 的真实手机/browser 现场验收材料，避免继续消费同一 blocker。
