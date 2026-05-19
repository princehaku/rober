# Sprint 2026.05.19_18-19 Mobile Real Device Acceptance Callback Review Decision - Tech Done

## 1. Sprint 类型

sprint_type: epic

## 2. 实际改动

Full-Stack worker 完成 Objective 4 手机侧只读复核决策链路：

- 修改 `mobile/web/app.js`、`mobile/web/styles.css`、`mobile/web/test_mobile_web_entrypoint.py`。
- 修改 `mobile/fixtures/mobile_web_status.fixture.json`、`mobile/web/fixtures/status.json`。
- 修改 `docs/product/mobile_user_flow.md`。
- 新增 `mobile_real_device_field_trial_acceptance_execution_callback_review_decision` 只读 panel，消费上一轮 callback intake 的 received / missing / rejected 状态，展示 review decision、decision reasons、owner handoff、next_required_evidence 和 rerun guidance。
- 保持 Start Delivery、Confirm Dropoff、Cancel gating 不变，继续 `delivery_success=false`、`primary_actions_enabled=false`、`safe_to_control=false`。
- 增加 safe alias 消费、unsafe 文案过滤、summary normalize、fixture 和 targeted tests。

Robot worker 完成 Robot diagnostics 只读 safe alias：

- 修改 `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py`。
- 修改 `onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`。
- 修改 `docs/interfaces/ros_contracts.md`。
- 新增 `mobile_real_device_field_trial_acceptance_execution_callback_review_decision` / `robot_diagnostics_mobile_real_device_field_trial_acceptance_execution_callback_review_decision_summary` 只读 safe alias。
- 缺字段、schema mismatch、unsafe copy、success/control copy、raw artifact 和控制暗示继续 fail closed。

Product closeout 本轮补齐：

- `tech-done.md`
- `side2side_check.md`
- `final.md`
- `OKR.md`
- `docs/process/okr_progress_log.md`

## 3. 验证结果

Full-Stack worker 已验证：

```text
python3 mobile/web/test_mobile_web_entrypoint.py
Ran 133 tests ... OK

python3 -m py_compile mobile/web/test_mobile_web_entrypoint.py
passed

node --check mobile/web/app.js
passed

required rg
passed

git diff --check -- mobile/web/app.js mobile/web/styles.css mobile/web/test_mobile_web_entrypoint.py mobile/fixtures/mobile_web_status.fixture.json mobile/web/fixtures/status.json docs/product/mobile_user_flow.md
passed
```

Robot worker 已验证：

```text
python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py
passed

PYTHONPATH=onboard/src/ros2_trashbot_behavior python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py
Ran 210 tests in 0.533s OK

required rg
passed

git diff --check -- onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py docs/interfaces/ros_contracts.md
passed
```

Product closeout 验收已通过：

```text
test -f .../tech-done.md && test -f .../side2side_check.md && test -f .../final.md
passed

rg -n "mobile_real_device_field_trial_acceptance_execution_callback_review_decision|Objective 5|Objective 1|Objective 4|PR #5|PRRT_kwDOSWB9286CJ3tX|software_proof|not_proven|delivery_success=false|primary_actions_enabled=false|safe_to_control=false" sprints/... OKR.md docs/process/okr_progress_log.md
matched required closeout terms across sprint docs, OKR.md, and okr_progress_log.md

git diff --check -- sprints/... OKR.md docs/process/okr_progress_log.md
passed
```

## 4. 证据边界

本轮证据边界是 `software_proof_docker_mobile_real_device_field_trial_acceptance_execution_callback_review_decision_gate`。

必须保持：

- `source=software_proof`
- `software_proof`
- `not_proven`
- `delivery_success=false`
- `primary_actions_enabled=false`
- `safe_to_control=false`

本轮不证明真实 iPhone/Android、production app、真实 PWA prompt/user choice、Objective 5 external proof、WAVE ROVER/UART/HIL、真实 route/elevator field pass、Nav2/fixed-route、dropoff/cancel completion 或 delivery success。

## 5. 偏差和失败定位

未收到工程 worker 报告的未修复失败。已知边界偏差不是失败：本轮只有 software-proof callback review decision，没有真实手机材料，因此 OKR 百分比保守不提高。

## 6. 剩余风险

- 仍缺真实手机设备、真实 iPhone/Android device behavior、production app、真实 PWA prompt/user choice 和 true phone/browser acceptance。
- Objective 5 仍缺公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue connectivity、production worker/migration/cutover 或其他 external proof。
- Objective 1 仍缺 WAVE ROVER/UART/HIL、真实 `feedback_T1001.log`、真实 `/odom`、`/imu/data`、`/battery`、operator HIL report。
- PR #5 `PRRT_kwDOSWB9286CJ3tX` 仍 unresolved / `blocked_pending_real_materials`，缺真实 2D LiDAR / ToF SKU/source/receipt/procurement/installation/wiring/power/calibration/HIL-entry。
- Objective 2 / Objective 3 仍缺真实 route/elevator field pass、Nav2/fixed-route、route completion signal、现场 task record、dropoff/cancel completion、cancel completion、delivery result 和 delivery success。
