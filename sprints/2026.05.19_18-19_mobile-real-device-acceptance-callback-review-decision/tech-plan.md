# Sprint 2026.05.19_18-19 Mobile Real Device Acceptance Callback Review Decision - Tech Plan

## 1. 技术目标

新增 fail-closed `mobile_real_device_field_trial_acceptance_execution_callback_review_decision`，消费上一轮 `mobile_real_device_field_trial_acceptance_execution_callback_intake` 的 received / missing / rejected callback evidence，并输出只读 review decision、decision reasons、owner_handoff、next_required_evidence 和 rerun guidance。

本轮 evidence boundary 是 `software_proof_docker_mobile_real_device_field_trial_acceptance_execution_callback_review_decision_gate`。所有实现必须保持 `source=software_proof`、`software_proof`、`not_proven`、`delivery_success=false`、`primary_actions_enabled=false`、`safe_to_control=false`，不得写成真实手机验收通过、真实 route/elevator field pass、HIL、dropoff/cancel completion、delivery success 或 Objective 5 external proof。

## OKR 最低优先级核对

当前 `OKR.md` 4.1 最新快照：

- Objective 5：约 68%，数字最低。
- Objective 1：约 81%，次低。
- Objective 2 / Objective 3 / Objective 4：约 99%。

本 sprint 不直接推进 Objective 5。理由：Objective 5 下一步必须依赖真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue connectivity、production worker/migration/cutover 或真实 external phone/browser proof。当前主机 Docker-only，不能制造这些材料；继续本地 O5 metadata depth 会重复消费已 blocked 的 O5 blocker。

本 sprint 不直接推进 Objective 1。理由：Objective 1 需要真实 WAVE ROVER/UART/HIL、`feedback_T1001.log`、真实 `/odom`、`/imu/data`、`/battery` 和 operator HIL report。PR #5 `PRRT_kwDOSWB9286CJ3tX` 仍 unresolved，缺真实 2D LiDAR / ToF SKU/source/receipt/procurement/installation/wiring/power/calibration/HIL-entry material。当前主机没有真实硬件和真实材料，不能把本轮 O4 review decision 写成 O1 进度或 PR #5 closeout。

本 sprint 不继续 O2/O3 blocker wrapper。理由：仍缺真实 dropoff/cancel completion、Nav2/fixed-route、route/elevator field pass、真实 route completion signal、真实 task record 和 delivery result；这些 blocker 已被多轮 software-proof wrapper 消费。本轮转向 O4 callback review decision，避免重复消费同一 route/elevator real-material blocker。

本 sprint 选择 Objective 4。理由：上一轮 `17-18` 已完成 `mobile_real_device_field_trial_acceptance_execution_callback_intake`，真实手机验收 execution callback 已有 fail-closed intake 入口；下一步最有价值且当前 Docker-only 可推进的是 review decision，把 received / missing / rejected 转成只读复核决策、owner handoff、next_required_evidence 和 rerun guidance。

## 2. PR / Review 证据

- PR #5 thread `PRRT_kwDOSWB9286CJ3tX` 仍 unresolved / blocked_pending_real_materials，缺真实 2D LiDAR / ToF SKU/source/receipt/procurement/installation/wiring/power/calibration/HIL-entry material，本轮不得关闭。
- 最新 `2026.05.19_17-18_mobile-real-device-acceptance-callback-intake` final 明确：手机端和 Robot diagnostics 已能展示 accepted / missing / rejected callback evidence、same safe `evidence_ref`、owner handoff、next_required_evidence 和 rerun_guidance，但不是现场真实手机验收通过。
- 17-18 final 的下一步指向真实 iPhone/Android device behavior、production app、真实 PWA prompt/user choice 回调材料；当前本机无真机，因此本轮只能推进 fail-closed review decision，不提高 OKR 百分比。

## 3. Owner 分工和文件范围

### Owner A：User Touchpoint Full-Stack Engineer

- 角色：`full-stack-software-engineer`
- 主责：mobile/web callback review decision panel、fixture、targeted tests、产品文档。
- 文件范围：
  - `mobile/web/app.js`
  - `mobile/web/styles.css`
  - `mobile/web/test_mobile_web_entrypoint.py`
  - `mobile/fixtures/mobile_web_status.fixture.json`
  - `mobile/web/fixtures/status.json`
  - `docs/product/mobile_user_flow.md`
- 实现要求：
  - 新增 `mobile_real_device_field_trial_acceptance_execution_callback_review_decision` fixture / summary 兼容渲染。
  - Panel 展示 review decision、source callback intake status、accepted / missing / rejected callback evidence、same safe `evidence_ref`、decision reasons、owner_handoff、next_required_evidence 和 rerun_guidance。
  - 缺 summary、schema mismatch、missing safe evidence_ref、unsafe copy、raw artifact、credentials、ROS topic、serial/UART、`/cmd_vel`、control wording 或 success wording 均 fail closed。
  - Start Delivery、Confirm Dropoff、Cancel gating 不变，保持 `safe_to_control=false`、`delivery_success=false`、`primary_actions_enabled=false`。
- 验收命令：
  - `python3 mobile/web/test_mobile_web_entrypoint.py`
  - `python3 -m py_compile mobile/web/test_mobile_web_entrypoint.py`
  - `node --check mobile/web/app.js`
  - `rg -n "mobile_real_device_field_trial_acceptance_execution_callback_review_decision|software_proof_docker_mobile_real_device_field_trial_acceptance_execution_callback_review_decision_gate|source=software_proof|software_proof|not_proven|delivery_success=false|primary_actions_enabled=false|safe_to_control=false" mobile/web/app.js mobile/web/styles.css mobile/web/test_mobile_web_entrypoint.py mobile/fixtures/mobile_web_status.fixture.json mobile/web/fixtures/status.json docs/product/mobile_user_flow.md`
  - `git diff --check -- mobile/web/app.js mobile/web/styles.css mobile/web/test_mobile_web_entrypoint.py mobile/fixtures/mobile_web_status.fixture.json mobile/web/fixtures/status.json docs/product/mobile_user_flow.md`

### Owner B：Robot Platform Engineer

- 角色：`robot-software-engineer`
- 主责：operator gateway diagnostics safe alias、targeted diagnostics unittest、接口文档。
- 文件范围：
  - `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py`
  - `onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`
  - `docs/interfaces/ros_contracts.md`
- 实现要求：
  - 新增 `robot_diagnostics_mobile_real_device_field_trial_acceptance_execution_callback_review_decision_summary` 或等价 safe alias。
  - Alias 只读暴露 callback review decision summary，不触发 ACK、cursor、Start Delivery、Confirm Dropoff、Cancel、diagnostics fetch 或 robot command。
  - 保持 source callback intake status、accepted / missing / rejected 分类、same safe `evidence_ref`、decision reasons、owner_handoff、next_required_evidence 和 rerun_guidance。
  - 缺字段、schema mismatch、unsafe evidence_ref、callback rejected、missing material 或 success/control copy 均 fail closed。
- 验收命令：
  - `python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`
  - `PYTHONPATH=onboard/src/ros2_trashbot_behavior python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`
  - `rg -n "mobile_real_device_field_trial_acceptance_execution_callback_review_decision|robot_diagnostics_mobile_real_device_field_trial_acceptance_execution_callback_review_decision_summary|software_proof_docker_mobile_real_device_field_trial_acceptance_execution_callback_review_decision_gate|source=software_proof|software_proof|not_proven|delivery_success=false|primary_actions_enabled=false|safe_to_control=false" onboard/src/ros2_trashbot_behavior docs/interfaces/ros_contracts.md`
  - `git diff --check -- onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py docs/interfaces/ros_contracts.md`

### Owner C：Product Manager / OKR Owner

- 角色：`product-okr-owner`
- 主责：sprint closeout、OKR、progress log、验收口径回顾。
- 文件范围：
  - `sprints/2026.05.19_18-19_mobile-real-device-acceptance-callback-review-decision/tech-done.md`
  - `sprints/2026.05.19_18-19_mobile-real-device-acceptance-callback-review-decision/side2side_check.md`
  - `sprints/2026.05.19_18-19_mobile-real-device-acceptance-callback-review-decision/final.md`
  - `OKR.md`
  - `docs/process/okr_progress_log.md`
- 实现要求：
  - 汇总 Full-Stack / Robot 验证结果。
  - 保守更新 Objective 4 evidence boundary；没有真实手机材料时不得提高 OKR 百分比。
  - 明确 Objective 5、Objective 1、Objective 4、PR #5、PRRT_kwDOSWB9286CJ3tX、O2/O3 剩余缺口。
  - `final.md` 必须回顾 `OKR 最低优先级核对` 的理由是否仍成立。
- 验收命令：
  - `test -f sprints/2026.05.19_18-19_mobile-real-device-acceptance-callback-review-decision/tech-done.md && test -f sprints/2026.05.19_18-19_mobile-real-device-acceptance-callback-review-decision/side2side_check.md && test -f sprints/2026.05.19_18-19_mobile-real-device-acceptance-callback-review-decision/final.md`
  - `rg -n "mobile_real_device_field_trial_acceptance_execution_callback_review_decision|Objective 5|Objective 1|Objective 4|PR #5|PRRT_kwDOSWB9286CJ3tX|software_proof|not_proven|delivery_success=false|primary_actions_enabled=false|safe_to_control=false" sprints/2026.05.19_18-19_mobile-real-device-acceptance-callback-review-decision OKR.md docs/process/okr_progress_log.md`
  - `git diff --check -- sprints/2026.05.19_18-19_mobile-real-device-acceptance-callback-review-decision OKR.md docs/process/okr_progress_log.md`

## 4. 接口影响

- 新增 phone-safe callback review decision summary，不改变 existing Start Delivery / Confirm Dropoff / Cancel command path。
- 新增 Robot diagnostics alias 时必须保持 read-only metadata surface，不新增控制 endpoint。
- Mobile/web 只消费现有 `/api/status`、`/api/diagnostics`、`phone_readiness`、diagnostics summary 或 fixture 中的 safe summary。
- 所有输出必须过滤 raw JSON、ROS topic、`/cmd_vel`、serial/UART、baudrate、WAVE ROVER parameter、credentials、DB/queue URL、OSS AK/SK、local path、traceback、complete artifact、checksum 和 success/control copy。

## 5. 并行启动规则

本 sprint 是 Epic，涉及 Full-Stack、Robot、Product 三个 owner。实现阶段必须并行启动 2 个 implementation worker，并由 Product 做最终 closeout：

- Full-Stack worker 负责 mobile/web 范围。
- Robot worker 负责 diagnostics 范围。
- Product owner 在工程 worker 返回后负责 closeout 范围。

Full-Stack 与 Robot 文件范围互不重叠；若 summary field naming 有接口耦合，以 `mobile_real_device_field_trial_acceptance_execution_callback_review_decision` 为 canonical feature id，以 `robot_diagnostics_mobile_real_device_field_trial_acceptance_execution_callback_review_decision_summary` 为 Robot summary alias。

## 6. 集成验收围栏

实现阶段完成后只跑以下围栏，不跑 Docker/Humble 或 broad suite：

```bash
python3 mobile/web/test_mobile_web_entrypoint.py
python3 -m py_compile mobile/web/test_mobile_web_entrypoint.py
node --check mobile/web/app.js
python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py
PYTHONPATH=onboard/src/ros2_trashbot_behavior python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py
rg -n "mobile_real_device_field_trial_acceptance_execution_callback_review_decision|software_proof_docker_mobile_real_device_field_trial_acceptance_execution_callback_review_decision_gate|source=software_proof|software_proof|not_proven|delivery_success=false|primary_actions_enabled=false|safe_to_control=false" mobile/web mobile/fixtures onboard/src/ros2_trashbot_behavior docs/product docs/interfaces
git diff --check -- mobile/web/app.js mobile/web/styles.css mobile/web/test_mobile_web_entrypoint.py mobile/fixtures/mobile_web_status.fixture.json mobile/web/fixtures/status.json docs/product/mobile_user_flow.md onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py docs/interfaces/ros_contracts.md
```

Product closeout 额外跑：

```bash
test -f sprints/2026.05.19_18-19_mobile-real-device-acceptance-callback-review-decision/tech-done.md && test -f sprints/2026.05.19_18-19_mobile-real-device-acceptance-callback-review-decision/side2side_check.md && test -f sprints/2026.05.19_18-19_mobile-real-device-acceptance-callback-review-decision/final.md
rg -n "mobile_real_device_field_trial_acceptance_execution_callback_review_decision|Objective 5|Objective 1|Objective 4|PR #5|PRRT_kwDOSWB9286CJ3tX|software_proof|not_proven|delivery_success=false|primary_actions_enabled=false|safe_to_control=false" sprints/2026.05.19_18-19_mobile-real-device-acceptance-callback-review-decision OKR.md docs/process/okr_progress_log.md
git diff --check -- sprints/2026.05.19_18-19_mobile-real-device-acceptance-callback-review-decision OKR.md docs/process/okr_progress_log.md
```

## 7. 本规划文档验收命令

```bash
test -f sprints/2026.05.19_18-19_mobile-real-device-acceptance-callback-review-decision/pre_start.md && test -f sprints/2026.05.19_18-19_mobile-real-device-acceptance-callback-review-decision/prd.md && test -f sprints/2026.05.19_18-19_mobile-real-device-acceptance-callback-review-decision/tech-plan.md
rg -n "sprint_type: epic|mobile_real_device_field_trial_acceptance_execution_callback_review_decision|OKR 最低优先级核对|Objective 5|Objective 1|Objective 4|PR #5|PRRT_kwDOSWB9286CJ3tX|software_proof|not_proven|delivery_success=false|primary_actions_enabled=false|safe_to_control=false" sprints/2026.05.19_18-19_mobile-real-device-acceptance-callback-review-decision
git diff --check -- sprints/2026.05.19_18-19_mobile-real-device-acceptance-callback-review-decision
```

## 8. 剩余风险和不证明事项

- 不证明真实 iPhone / Android、production app、真实 PWA prompt/user choice、真实 phone/browser acceptance。
- 不证明 Objective 5 external proof：公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/cutover。
- 不证明 Objective 1 / PR #5：WAVE ROVER/UART/HIL、真实底盘 feedback、2D LiDAR / ToF SKU/source/receipt/procurement/installation/wiring/power/calibration/HIL-entry；`PRRT_kwDOSWB9286CJ3tX` 仍需真实 material。
- 不证明 Objective 2 / Objective 3：真实 route/elevator field pass、Nav2/fixed-route、route completion signal、task record、dropoff completion、cancel completion、delivery result 或 delivery success。
- 不授予 `safe_to_control=true`，不改变 `primary_actions_enabled=false`。

