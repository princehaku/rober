# Sprint 2026.05.18_22-23 Mobile Real Device Acceptance Review Handoff - Tech Plan

## 1. 技术目标

实现 `mobile_real_device_field_trial_acceptance_review_handoff*` 的下一轮 team 执行计划：Full-stack 主责手机端 UI / fixture / unittest / product flow，Robot 主责 diagnostics metadata-only safe alias，Product 主责 closeout / OKR / progress log。该 handoff packet 消费上一轮 review decision 输出，把 owner handoff、next required evidence、rerun command summary、safe copy 和证据边界安全展示给现场执行者。

本轮计划只创建前置文档；执行阶段不得预先写 `tech-done.md`、`side2side_check.md` 或 `final.md`。

## 2. OKR 最低优先级核对

1. 当前 `OKR.md` 4.1 完成度最低是 Objective 5，约 68%。
2. 本 sprint 不针对 Objective 5。原因：O5 的下一次有效提升需要真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue connectivity、production worker/migration/cutover 或真实手机/browser external proof；当前主机只有 Docker，无法提供这些真实外部材料。继续新增本地 O5 metadata 会违反 O5 stop rule。
3. 本 sprint 不针对 Objective 1。原因：Objective 1 约 81%，但当前没有真实 WAVE ROVER/UART/HIL、`feedback_T1001.log`、`/odom`、`/imu/data`、`/battery`、operator HIL report，也没有 PR #5 2D LiDAR / ToF SKU/source/receipt/procurement/installation/wiring/power/calibration/HIL-entry 真实材料。本轮不应继续包装同一硬件 blocker。
4. 本 sprint 不继续 PR #4 route/elevator wrapper。原因：PR #4 已合并且电梯 assisted delivery 是主链，但 18-19 和 19-20 已连续消费同一真实 route/elevator field-material blocker，20-21 已明确停止第三次本地 wrapper。
5. 本 sprint 推进 Objective 4。原因：最新 21-22 sprint 已完成 `mobile_real_device_field_trial_acceptance_review_decision*` fail-closed review decision，下一阶最可执行的软件工作是把该决策包装成 owner / 现场执行者可用的 `mobile_real_device_field_trial_acceptance_review_handoff*`，同时继续保持真实手机验收 `not_proven`。

## 3. 文件范围

### Full-stack 允许改动

- `mobile/web/app.js`
- `mobile/fixtures/mobile_web_status.fixture.json`
- `mobile/web/test_mobile_web_entrypoint.py`
- `docs/product/mobile_user_flow.md`

### Robot 允许改动

- `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py`
- `onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`
- `docs/interfaces/ros_contracts.md`

### Product 允许改动

- `sprints/2026.05.18_22-23_mobile-real-device-acceptance-review-handoff/tech-done.md`
- `sprints/2026.05.18_22-23_mobile-real-device-acceptance-review-handoff/side2side_check.md`
- `sprints/2026.05.18_22-23_mobile-real-device-acceptance-review-handoff/final.md`
- `OKR.md`
- `docs/process/okr_progress_log.md`

### 本规划已改动

- `sprints/2026.05.18_22-23_mobile-real-device-acceptance-review-handoff/pre_start.md`
- `sprints/2026.05.18_22-23_mobile-real-device-acceptance-review-handoff/prd.md`
- `sprints/2026.05.18_22-23_mobile-real-device-acceptance-review-handoff/tech-plan.md`

## 4. 并行 owner 分工

### User Touchpoint Full-Stack Engineer

主责 UI / fixture / test / product flow。

任务：

1. 新增 `mobile_real_device_field_trial_acceptance_review_handoff` 和 `mobile_real_device_field_trial_acceptance_review_handoff_summary` 消费逻辑。
2. 手机端展示只允许白名单字段：handoff status、safe `evidence_ref`、owner handoff、next required evidence、accepted/missing/rejected material summaries、rerun commands summary、safe copy、evidence boundary、`not_proven`、`safe_to_control=false`、`delivery_success=false`、`primary_actions_enabled=false`。
3. 缺 summary 或缺 safe copy 时 fail closed。
4. 不改变 Start Delivery、Confirm Dropoff、Cancel gating。

### Robot Platform Engineer

主责 diagnostics metadata-only safe alias。

任务：

1. 在 diagnostics 中透出 `robot_diagnostics_mobile_real_device_field_trial_acceptance_review_handoff_summary` 或等价 safe alias。
2. 只允许 metadata-only summary，不透出 raw artifacts、local paths、checksums、tracebacks、credentials、ROS topics、`/cmd_vel`、serial/UART details、DB/queue URLs 或 OSS AK/SK。
3. 保持 `safe_to_control=false`、`delivery_success=false`、`primary_actions_enabled=false`。
4. 不新增 ROS2 motion command、不改 task_orchestrator 状态机、不开放控制动作。

### Product Manager / OKR Owner

主责 closeout / OKR / progress log。

任务：

1. 汇总 worker 证据，更新 `tech-done.md`、`side2side_check.md`、`final.md`。
2. 保守更新 `OKR.md` 和 `docs/process/okr_progress_log.md`。
3. 明确本轮是 software proof / handoff packet，不证明真实手机、真实云、HIL、route/elevator field pass 或 delivery success。

## 5. 接口影响

- 新增或消费 schema：`trashbot.mobile_real_device_field_trial_acceptance_review_handoff.v1`。
- 新增或消费 summary：`trashbot.mobile_real_device_field_trial_acceptance_review_handoff_summary.v1`。
- 新增 evidence boundary：`software_proof_docker_mobile_real_device_field_trial_acceptance_review_handoff_gate`。
- 兼容输入：上一轮 `mobile_real_device_field_trial_acceptance_review_decision*`、`mobile_real_device_field_trial_acceptance_session*` 的 safe summary / safe copy。
- 控制面影响：无。Start Delivery、Confirm Dropoff、Cancel 继续由既有 `command_safety` 和 legacy gates 控制，不因 handoff summary 放开。

## 6. 证据边界

必须保持：

- `source=software_proof`
- `not_proven`
- `safe_to_control=false`
- `delivery_success=false`
- `primary_actions_enabled=false`

不得证明：

- 真实 iPhone/Android device behavior。
- production app。
- 真实 PWA prompt/user choice。
- delivery success。
- dropoff/cancel completion。
- Objective 5 external proof。
- 真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/cutover。
- WAVE ROVER、UART、HIL、`feedback_T1001.log`、`/odom`、`/imu/data`、`/battery`。
- PR #4 route/elevator field pass。
- PR #5 2D LiDAR / ToF SKU/source/receipt/procurement/installation/wiring/power/calibration/HIL-entry 材料。

## 7. 验收命令

Full-stack worker 必须运行：

```bash
node --check mobile/web/app.js
python3 -m unittest mobile.web.test_mobile_web_entrypoint
rg -n "mobile_real_device_field_trial_acceptance_review_handoff|safe_to_control=false|delivery_success=false|primary_actions_enabled=false|not_proven" mobile/web mobile/fixtures docs/product/mobile_user_flow.md
git diff --check -- mobile/web/app.js mobile/fixtures/mobile_web_status.fixture.json mobile/web/test_mobile_web_entrypoint.py docs/product/mobile_user_flow.md
```

Robot worker 必须运行：

```bash
PYTHONPATH=onboard/src/ros2_trashbot_behavior python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py
rg -n "mobile_real_device_field_trial_acceptance_review_handoff|robot_diagnostics_mobile_real_device_field_trial_acceptance_review_handoff_summary|safe_to_control=false|delivery_success=false|primary_actions_enabled=false|not_proven" onboard/src/ros2_trashbot_behavior docs/interfaces/ros_contracts.md
git diff --check -- onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py docs/interfaces/ros_contracts.md
```

Product closeout 必须运行：

```bash
test -f sprints/2026.05.18_22-23_mobile-real-device-acceptance-review-handoff/tech-done.md && test -f sprints/2026.05.18_22-23_mobile-real-device-acceptance-review-handoff/side2side_check.md && test -f sprints/2026.05.18_22-23_mobile-real-device-acceptance-review-handoff/final.md
rg -n "sprint_type: epic|mobile_real_device_field_trial_acceptance_review_handoff|Objective 5|Objective 1|PR #4|PR #5|safe_to_control=false|delivery_success=false|primary_actions_enabled=false|not_proven" sprints/2026.05.18_22-23_mobile-real-device-acceptance-review-handoff OKR.md docs/process/okr_progress_log.md
git diff --check -- sprints/2026.05.18_22-23_mobile-real-device-acceptance-review-handoff OKR.md docs/process/okr_progress_log.md
```

本轮规划文档验收命令：

```bash
test -f sprints/2026.05.18_22-23_mobile-real-device-acceptance-review-handoff/pre_start.md && test -f sprints/2026.05.18_22-23_mobile-real-device-acceptance-review-handoff/prd.md && test -f sprints/2026.05.18_22-23_mobile-real-device-acceptance-review-handoff/tech-plan.md
rg -n "sprint_type: epic|mobile_real_device_field_trial_acceptance_review_handoff|Objective 5|Objective 1|PR #4|PR #5|OKR 最低优先级核对|safe_to_control=false|delivery_success=false|primary_actions_enabled=false|not_proven|验收命令|文件范围" sprints/2026.05.18_22-23_mobile-real-device-acceptance-review-handoff
git diff --check -- sprints/2026.05.18_22-23_mobile-real-device-acceptance-review-handoff
```

## 8. 风险和剩余证据

- 真实手机证据仍需 owner 提供：iPhone/Android device behavior、production app、真实 PWA prompt/user choice、现场截图或录屏、用户选择日志。
- O5 仍需外部材料：公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/cutover。
- O1 仍需真实硬件材料：WAVE ROVER/UART/HIL、真实反馈、operator HIL report。
- PR #4 仍需真实 route/elevator field materials。
- PR #5 仍需真实 2D LiDAR / ToF source/procurement/install/calibration/HIL-entry 材料。
- 如果 worker 发现需要改共享接口或扩大文件范围，必须先回到 Product 更新计划，不得顺手越界。
