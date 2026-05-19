# Sprint 2026.05.19_19-20 Mobile Real Device Acceptance Callback Review Handoff - Tech Plan

## 1. 目标

实现 Objective 4 的 `mobile_real_device_field_trial_acceptance_execution_callback_review_handoff` software-proof rung：把上一轮 callback review decision 转成 Robot diagnostics 与 mobile/web 都能消费的 owner handoff package、rerun guidance、next required evidence 和 blocker summary。

本轮不新增控制能力，不打开 Start Delivery、Confirm Dropoff、Cancel，不修改 O5 cloud external proof，不处理 PR #5 硬件真实材料，不声称 Objective 1 / Objective 5 提升。

## 2. OKR 最低优先级核对

当前 `OKR.md` 4.1 数字最低 Objective 是 Objective 5，约 68%。

本 sprint 不针对 Objective 5 completion。原因：Objective 5 下一步有效提升需要真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue connectivity、production worker/migration/cutover 或其他 external proof。当前 evidence 明确这些材料缺失；继续本地 O5 metadata depth 会重复消费同一 blocker，不能形成完成度提升。

下一低项 Objective 1 约 81%，本 sprint 也不针对 Objective 1 completion。原因：PR #5 `PRRT_kwDOSWB9286CJ3tX` 仍 unresolved / `blocked_pending_real_materials`，真实 2D LiDAR / ToF SKU/source/receipt/procurement/installation/wiring/power/calibration/HIL-entry 仍缺；真实 WAVE ROVER/UART/HIL 也缺失。没有本地 vendor/source 或真实材料前，不能关闭该 thread，也不能提升 Objective 1。

本 sprint 选择 Objective 4。原因：最新 18-19 sprint 已完成 `mobile_real_device_field_trial_acceptance_execution_callback_review_decision`，下一步最可执行、且不弱化证据边界的 functional rung 是 `mobile_real_device_field_trial_acceptance_execution_callback_review_handoff`。它能让现场 owner 从手机和 Robot diagnostics 读取 handoff、rerun guidance、next required evidence，并继续保持 `software_proof`、`not_proven`、`delivery_success=false`、`primary_actions_enabled=false`、`safe_to_control=false`。

## 3. 并行 owner 分工

必须在同一轮实现阶段并行启动 2 个 worker。文件范围互不重叠。

### 3.1 Robot Platform Engineer

允许改动：

- `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py`
- `onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`
- `docs/interfaces/ros_contracts.md`

任务：

- 新增 `mobile_real_device_field_trial_acceptance_execution_callback_review_handoff` / `robot_diagnostics_mobile_real_device_field_trial_acceptance_execution_callback_review_handoff_summary` safe summary。
- 从 source callback review decision summary 派生 handoff status，不读取 raw artifact、cursor、ACK payload、local path、credentials、complete artifact 或 checksum。
- 缺 source review decision、缺 safe `evidence_ref`、schema mismatch、unsafe copy、pass/success/control 文案时 fail closed。
- 输出字段必须包含 owner handoff、next required evidence、rerun guidance、blocker summary、same safe `evidence_ref`、source review decision status、evidence boundary、`software_proof`、`not_proven`、`delivery_success=false`、`primary_actions_enabled=false`、`safe_to_control=false`。

验收命令：

```bash
python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py
PYTHONPATH=onboard/src/ros2_trashbot_behavior python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py
rg -n "mobile_real_device_field_trial_acceptance_execution_callback_review_handoff|robot_diagnostics_mobile_real_device_field_trial_acceptance_execution_callback_review_handoff_summary|software_proof|not_proven|delivery_success=false|primary_actions_enabled=false|safe_to_control=false" onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py docs/interfaces/ros_contracts.md
git diff --check -- onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py docs/interfaces/ros_contracts.md
```

### 3.2 User Touchpoint Full-Stack Engineer

允许改动：

- `mobile/web/app.js`
- `mobile/web/styles.css`
- `mobile/web/test_mobile_web_entrypoint.py`
- `mobile/fixtures/mobile_web_status.fixture.json`
- `mobile/web/fixtures/status.json`
- `docs/product/mobile_user_flow.md`

任务：

- 新增只读 “现场验收回调交接” panel，消费 `robot_diagnostics_mobile_real_device_field_trial_acceptance_execution_callback_review_handoff_summary`。
- 展示 source review status、safe `evidence_ref`、owner handoff、next required evidence、rerun guidance、blocker summary、evidence boundary 和 `not_proven`。
- copy/export 只能输出 whitelisted phone-safe metadata。
- Start Delivery、Confirm Dropoff、Cancel gating 不能因 handoff metadata 改变。
- 缺 summary、缺 fail-closed flags、unsafe copy、success/control wording、raw path、credentials、raw JSON、checksum、complete artifact 时 fail closed。

验收命令：

```bash
python3 mobile/web/test_mobile_web_entrypoint.py
python3 -m py_compile mobile/web/test_mobile_web_entrypoint.py
node --check mobile/web/app.js
rg -n "mobile_real_device_field_trial_acceptance_execution_callback_review_handoff|robot_diagnostics_mobile_real_device_field_trial_acceptance_execution_callback_review_handoff_summary|software_proof|not_proven|delivery_success=false|primary_actions_enabled=false|safe_to_control=false" mobile/web/app.js mobile/web/test_mobile_web_entrypoint.py mobile/fixtures/mobile_web_status.fixture.json mobile/web/fixtures/status.json docs/product/mobile_user_flow.md
git diff --check -- mobile/web/app.js mobile/web/styles.css mobile/web/test_mobile_web_entrypoint.py mobile/fixtures/mobile_web_status.fixture.json mobile/web/fixtures/status.json docs/product/mobile_user_flow.md
```

## 4. 接口影响

新增接口是 metadata-only safe summary，不改变 command API、不改变 ACK 语义、不改变 Start Delivery / Confirm Dropoff / Cancel gating。

推荐 summary 语义：

- schema: `trashbot.mobile_real_device_field_trial_acceptance_execution_callback_review_handoff_summary.v1`
- status: `ready_for_field_owner_handoff_not_proven` 或 `blocked_missing_callback_review_decision_not_proven`
- source: `software_proof`
- evidence_boundary: `software_proof_docker_mobile_real_device_field_trial_acceptance_execution_callback_review_handoff_gate`
- delivery_success: false
- primary_actions_enabled: false
- safe_to_control: false
- not_proven: 包含真实 iPhone/Android、production app、真实 PWA prompt/user choice、true phone/browser acceptance、O5 external proof、WAVE ROVER/UART/HIL、真实 route/elevator field pass、Nav2/fixed-route、dropoff/cancel completion、delivery success。

## 5. 风险边界

- 不新增 raw artifact 或 complete artifact 透传。
- 不暴露 ROS topic、`/cmd_vel`、serial/UART、baudrate、WAVE ROVER 参数、credentials、DB/queue URL、OSS AK/SK、local path、checksum。
- 不使用 pass、success、field_pass、hil_pass、delivery completed 等真实通过文案，除非明确在 `not_proven` 中否定。
- 不修改 `OKR.md` 或 `docs/process/okr_progress_log.md`，closeout 阶段再按真实结果处理。
- 不把 Product planning 文件当工程交付；必须由 Robot Platform Engineer 和 User Touchpoint Full-Stack Engineer 实现并验证。

## 6. 本规划阶段验收命令

Product Owner 创建规划文件后必须运行：

```bash
test -f sprints/2026.05.19_19-20_mobile-real-device-acceptance-callback-review-handoff/pre_start.md && test -f sprints/2026.05.19_19-20_mobile-real-device-acceptance-callback-review-handoff/prd.md && test -f sprints/2026.05.19_19-20_mobile-real-device-acceptance-callback-review-handoff/tech-plan.md
rg -n "sprint_type: epic|OKR 最低优先级核对|Objective 5|Objective 1|Objective 4|PR #5|PRRT_kwDOSWB9286CJ3tX|mobile_real_device_field_trial_acceptance_execution_callback_review_handoff|software_proof|not_proven|delivery_success=false|primary_actions_enabled=false|safe_to_control=false" sprints/2026.05.19_19-20_mobile-real-device-acceptance-callback-review-handoff
git diff --check -- sprints/2026.05.19_19-20_mobile-real-device-acceptance-callback-review-handoff
```

## 7. 实现阶段输出要求

每个 worker 必须返回：

1. 实际改动文件列表。
2. 验证命令输出结果。
3. 失败定位，如有。
4. 剩余风险。

Product closeout 必须核对：

- `tech-done.md` 记录工程实际改动和验证结果。
- `side2side_check.md` 记录验收对照。
- `final.md` 回顾 `## OKR 最低优先级核对` 是否仍成立。
- 如无真实手机 / external / hardware / field materials，OKR 百分比保守不提高。
