# Sprint 2026.05.20_09-10 Mobile Real Device Acceptance Handoff Intake - Tech Done

## 1. sprint_type

sprint_type: epic

## 2. 用户价值和产品北极星

本轮继续服务北极星：普通手机用户不需要理解 ROS2、raw JSON、设备路径或现场证据文件，也能看懂“真实手机现场验收交接回执是否已收到、还缺什么、下一步谁处理”。它不是让手机端开始控制机器人，而是把现场 owner 回执变成 Robot diagnostics 与 mobile/web 都能安全读取的只读状态。

## 3. OKR 映射

- Objective 4：本轮核心推进对象。新增 `mobile_real_device_field_trial_acceptance_execution_handoff_intake` / `robot_diagnostics_mobile_real_device_field_trial_acceptance_execution_handoff_intake_summary`，让手机端只读展示现场验收交接回执、缺口和 rerun guidance。
- Objective 5：保持约 68%。本轮不提供公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、production worker/cutover 或 O5 external proof。
- Objective 1：保持约 81%。本轮不处理 WAVE ROVER/UART/HIL，不提供真实 2D LiDAR / ToF SKU/source/receipt/procurement/installation/wiring/power/calibration/HIL-entry；PR #5 `PRRT_kwDOSWB9286CJ3tX` 仍 unresolved / material pending，reply comment `3269642220` 不等于 resolved。
- Objective 2 / Objective 3 / Objective 4：均保守保持约 99%。本轮不是真实 route/elevator field pass，不是真实 Nav2/fixed-route，不是 dropoff/cancel completion，不是 delivery success。

## 4. KR 拆解或更新

- KR4.5 / KR4.7：补齐真实手机现场验收链路的只读回执入口，帮助现场 owner 明确 `owner_ack_status`、`missing_evidence`、`next_owner`、`rerun_guidance` 和 blocker summary。
- KR4.5 验收边界：手机端只能展示 phone-safe metadata，必须保持 `software_proof`、`not_proven`、`safe_to_control=false`、`delivery_success=false`、`primary_actions_enabled=false`。
- KR4.7 风险边界：这不是真实手机/browser、真实 PWA prompt/userChoice、production app 或 true phone/browser acceptance。

## 5. 本轮核心抓手

核心抓手是 `software_proof_docker_mobile_real_device_field_trial_acceptance_execution_handoff_intake_gate`：从上一轮 callback review handoff 派生现场 owner ack/intake safe summary，并让 mobile/web 以只读 panel 方式消费。Product closeout 只接受 metadata-only / fail-closed 证据，不把工程实现或回执入口写成真实现场验收通过。

## 6. 实际改动

Robot Platform Engineer 已完成：

- `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py`
- `onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`
- `docs/interfaces/ros_contracts.md`

实际结果：

- 新增 `mobile_real_device_field_trial_acceptance_execution_handoff_intake` safe summary。
- 新增 `robot_diagnostics_mobile_real_device_field_trial_acceptance_execution_handoff_intake_summary` diagnostics alias。
- summary 固定 `software_proof`、`not_proven`、`safe_to_control=false`、`delivery_success=false`、`primary_actions_enabled=false`。
- 缺 source handoff、缺 safe `evidence_ref`、schema mismatch、unsafe copy 或成功/控制文案时 fail closed。

User Touchpoint Full-Stack Engineer 已完成：

- `mobile/web/app.js`
- `mobile/web/styles.css`
- `mobile/web/test_mobile_web_entrypoint.py`
- `mobile/fixtures/mobile_web_status.fixture.json`
- `mobile/web/fixtures/status.json`
- `docs/product/mobile_user_flow.md`

实际结果：

- 新增只读“现场验收交接回执” panel。
- safe summary selection 与 fail-closed normalization 覆盖 handoff intake。
- copy/export 仅允许 whitelist metadata。
- Start Delivery、Confirm Dropoff、Cancel 不因 handoff intake metadata 解锁。

Product Owner closeout 已完成：

- `sprints/2026.05.20_09-10_mobile-real-device-acceptance-handoff-intake/tech-done.md`
- `sprints/2026.05.20_09-10_mobile-real-device-acceptance-handoff-intake/side2side_check.md`
- `sprints/2026.05.20_09-10_mobile-real-device-acceptance-handoff-intake/final.md`
- `OKR.md`
- `docs/process/okr_progress_log.md`

## 7. 验证结果

Robot worker 验证：

```text
python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py
pass

PYTHONPATH=onboard/src/ros2_trashbot_behavior python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py
Ran 225 tests in 0.650s
OK

required rg
pass

git diff --check -- onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py docs/interfaces/ros_contracts.md
pass
```

Full-Stack worker 验证：

```text
python3 mobile/web/test_mobile_web_entrypoint.py
Ran 157 tests ... OK

python3 -m py_compile mobile/web/test_mobile_web_entrypoint.py
pass

node --check mobile/web/app.js
pass

required rg
pass

git diff --check -- mobile/web/app.js mobile/web/styles.css mobile/web/test_mobile_web_entrypoint.py mobile/fixtures/mobile_web_status.fixture.json mobile/web/fixtures/status.json docs/product/mobile_user_flow.md
pass
```

Product closeout 验证记录见 `final.md`。

## 8. 失败定位

无未关闭失败。工程 worker 回传验证均通过；Product closeout 验证通过后本轮可收口。

## 9. 剩余风险

- `software_proof_docker_mobile_real_device_field_trial_acceptance_execution_handoff_intake_gate` 只证明 repo-local safe summary、fixture 和静态 mobile/web panel 行为，不证明真实手机/browser。
- 真实 iPhone/Android device behavior、production app、真实 PWA prompt/userChoice、true phone/browser acceptance 仍缺。
- O5 external proof 仍缺：公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、production worker/migration/cutover。
- O1 hardware/HIL 仍缺：WAVE ROVER/UART/HIL、真实 2D LiDAR / ToF materials、真实 feedback / odom / imu / battery 样本。
- PR #5 `PRRT_kwDOSWB9286CJ3tX` 仍 unresolved / material pending；reply comment `3269642220` 不等于 resolved。
- Objective 2 / Objective 3 仍缺真实 route/elevator field pass、Nav2/fixed-route、dropoff/cancel completion 和 delivery success。
