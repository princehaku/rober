# Sprint 2026.05.19_17-18 Mobile Real Device Acceptance Callback Intake - Tech Done

## 1. Sprint 类型

sprint_type: epic

本轮完成 `mobile_real_device_field_trial_acceptance_execution_callback_intake` 的软件入口收口：Full-Stack 和 Robot workers 已把上一轮真实手机 acceptance execution pack 的后续回调材料入口接到 mobile/web 与 Robot diagnostics safe alias。Product closeout 只更新本 sprint 收口、`OKR.md` 和 `docs/process/okr_progress_log.md`。

## 2. 实际改动

Full-Stack worker 已修改：

- `mobile/web/app.js`
- `mobile/web/styles.css`
- `mobile/web/test_mobile_web_entrypoint.py`
- `mobile/fixtures/mobile_web_status.fixture.json`
- `mobile/web/fixtures/status.json`
- `docs/product/mobile_user_flow.md`

实现结果：

- mobile/web 在 execution pack panel 后新增只读“现场真实手机验收执行回调入口”panel。
- 展示 callback intake status、accepted/missing/rejected callback evidence、same safe `evidence_ref`、owner handoff、next required evidence 和 rerun guidance。
- Start Delivery、Confirm Dropoff、Cancel gating 保持不变。
- 首轮 fixture safety test 拒绝 “field pass” 文案后，Full-Stack worker 改为 phone-safe “现场材料缺口”并重跑通过。

Robot worker 已修改：

- `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py`
- `onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`
- `docs/interfaces/ros_contracts.md`

实现结果：

- 新增 `mobile_real_device_field_trial_acceptance_execution_callback_intake` / summary schema。
- 新增 canonical diagnostics alias `robot_diagnostics_mobile_real_device_field_trial_acceptance_execution_callback_intake_summary`。
- Alias 保持 read-only，只暴露 accepted/missing/rejected callback evidence、same safe `evidence_ref`、owner handoff、next required evidence 和 rerun guidance。
- 首轮发现 raw `latest_status["mobile_real_device_field_trial_acceptance_execution_callback_intake"]` 未被 diagnostics-only 清理，Robot worker 已增加 pop cleanup 并重跑通过。

Product closeout 已修改：

- `sprints/2026.05.19_17-18_mobile-real-device-acceptance-callback-intake/tech-done.md`
- `sprints/2026.05.19_17-18_mobile-real-device-acceptance-callback-intake/side2side_check.md`
- `sprints/2026.05.19_17-18_mobile-real-device-acceptance-callback-intake/final.md`
- `OKR.md`
- `docs/process/okr_progress_log.md`

## 3. 验证结果

Full-Stack worker 报告：

```text
python3 mobile/web/test_mobile_web_entrypoint.py
Ran 131 tests ... OK

python3 -m py_compile mobile/web/test_mobile_web_entrypoint.py
exit 0

node --check mobile/web/app.js
exit 0

required rg passed
scoped git diff --check passed
```

Robot worker 报告：

```text
python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py
exit 0

PYTHONPATH=onboard/src/ros2_trashbot_behavior python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py
Ran 209 tests ... OK

required rg passed
scoped git diff --check passed
```

Product closeout 本地围栏：

```text
test -f tech-done.md && test -f side2side_check.md && test -f final.md
passed

rg -n "mobile_real_device_field_trial_acceptance_execution_callback_intake|Objective 5|Objective 1|Objective 4|PR #5|PRRT_kwDOSWB9286CJ3tX|software_proof|not_proven|delivery_success=false|primary_actions_enabled=false|safe_to_control=false" ...
passed

git diff --check -- sprints/2026.05.19_17-18_mobile-real-device-acceptance-callback-intake OKR.md docs/process/okr_progress_log.md
passed
```

## 4. 证据边界

本轮证据边界是 `software_proof_docker_mobile_real_device_field_trial_acceptance_execution_callback_intake_gate`。必须保持：

- `source=software_proof`
- `not_proven`
- `delivery_success=false`
- `primary_actions_enabled=false`
- `safe_to_control=false`

本轮不证明：真实 iPhone/Android、production app、真实 PWA prompt/user choice、true phone/browser acceptance、Objective 5 external proof、PR #5 hardware material / thread `PRRT_kwDOSWB9286CJ3tX`、WAVE ROVER/UART/HIL、PR #4 route/elevator field pass、Nav2/fixed-route、dropoff/cancel completion 或 delivery success。

## 5. 剩余风险

- Objective 5 仍约 68%，仍缺真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue connectivity、production worker/migration/cutover 或真实 external phone/browser proof。
- Objective 1 仍约 81%，仍缺真实 WAVE ROVER/UART/HIL、底盘 feedback、operator HIL report，以及 PR #5 2D LiDAR / ToF SKU/source/receipt/procurement/installation/wiring/power/calibration/HIL-entry material。
- Objective 4 仍约 99%，本轮只增加真实手机执行回调入口，不是现场真实手机验收通过。
- Objective 2 / Objective 3 仍约 99%，仍缺真实 route/elevator field pass、Nav2/fixed-route、route completion signal、task record、dropoff/cancel completion 和 delivery result。
