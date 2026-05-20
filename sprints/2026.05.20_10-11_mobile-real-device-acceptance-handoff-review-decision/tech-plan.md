# Sprint 2026.05.20_10-11 Mobile Real Device Acceptance Handoff Review Decision - Tech Plan

## 1. 目标

实现 Objective 4 的 `mobile_real_device_field_trial_acceptance_execution_handoff_review_decision` software-proof rung：把上一轮 `mobile_real_device_field_trial_acceptance_execution_handoff_intake` 后的现场验收交接回执，复核成 `accepted`、`missing`、`rejected`、`blocked` 四类材料判定，并让 PC / Robot diagnostics 与 mobile/web 后续都能消费同一 fail-closed 状态。

本轮不新增控制能力，不打开 Start Delivery、Confirm Dropoff、Cancel，不修改 O5 cloud external proof，不处理 PR #5 硬件真实材料，不声称 Objective 1 / Objective 5 提升，不声称真实手机/browser 通过。

## 2. OKR 最低优先级核对

当前 `OKR.md` 4.1 数字最低 Objective 是 Objective 5，约 68%。

本 sprint 不针对 Objective 5 completion。原因：当前有效提升需要真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue connectivity、production worker/migration/cutover 或真实手机/browser。当前主机只有 Docker；继续本地 O5 metadata depth 会重复消费同一 blocker，不能形成完成度提升。

下一低项 Objective 1 约 81%，本 sprint 也不针对 Objective 1 completion。原因：GitHub PR #5 thread `PRRT_kwDOSWB9286CJ3tX` 仍 unresolved；Q/U 已 resolved，但 X 仍等待真实 2D LiDAR / ToF SKU/source/receipt/procurement/install/wiring/power/calibration/HIL-entry。真实 WAVE ROVER/UART/HIL 也缺失。没有真实材料或 reviewer resolve 前，不能关闭该 thread，也不能提升 Objective 1。

Objective 2 / Objective 3 / Objective 4 约 99%，真实 route/elevator field materials、真实 dropoff/cancel completion 和真实手机/browser acceptance 仍缺。本 sprint 选择 Objective 4 的原因不是提高百分比，而是上一轮 `mobile_real_device_field_trial_acceptance_execution_handoff_intake` 已完成，下一步最可执行、且不弱化证据边界的 functional rung 是 `mobile_real_device_field_trial_acceptance_execution_handoff_review_decision`。它能让现场 owner 从手机和 Robot diagnostics 读取 accepted / missing / rejected / blocked、next owner、rerun guidance，并继续保持 `software_proof`、`not_proven`、`safe_to_control=false`、`delivery_success=false`、`primary_actions_enabled=false`。

## 3. 并行 owner 分工

实现阶段必须在同一轮并行启动 2 个工程 worker；文件范围互不重叠。Product Owner 在工程返回后负责 closeout 文档和 OKR 边界核对。

### 3.1 Robot Platform Engineer

允许改动：

- `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py`
- `onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`
- `docs/interfaces/ros_contracts.md`

任务：

- 新增 `mobile_real_device_field_trial_acceptance_execution_handoff_review_decision` / `robot_diagnostics_mobile_real_device_field_trial_acceptance_execution_handoff_review_decision_summary` safe summary。
- 从 source handoff intake summary 派生 review decision，不读取 raw artifact、cursor、ACK payload、local path、credentials、complete artifact 或 checksum。
- decision 只允许 `accepted`、`missing`、`rejected`、`blocked`；缺 source intake、缺 safe `evidence_ref`、schema mismatch、unsafe copy、pass/success/control 文案时 fail closed 到 `blocked` 或 `rejected`。
- 输出字段必须包含 source handoff intake status、review decision、accepted material summary、missing material summary、rejected material summary、blocked reason、next owner、rerun guidance、same safe `evidence_ref`、evidence boundary、`software_proof`、`not_proven`、`safe_to_control=false`、`delivery_success=false`、`primary_actions_enabled=false`。

验收命令：

```bash
python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py
PYTHONPATH=onboard/src/ros2_trashbot_behavior python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py
rg -n "mobile_real_device_field_trial_acceptance_execution_handoff_review_decision|robot_diagnostics_mobile_real_device_field_trial_acceptance_execution_handoff_review_decision_summary|accepted|missing|rejected|blocked|software_proof|not_proven|safe_to_control=false|delivery_success=false|primary_actions_enabled=false" onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py docs/interfaces/ros_contracts.md
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

- 新增只读 “现场验收交接复核决策” panel，消费 `robot_diagnostics_mobile_real_device_field_trial_acceptance_execution_handoff_review_decision_summary`。
- 展示 source handoff intake status、safe `evidence_ref`、review decision、accepted / missing / rejected / blocked summaries、next owner、rerun guidance、evidence boundary 和 `not_proven`。
- copy/export 只能输出 whitelisted phone-safe metadata。
- Start Delivery、Confirm Dropoff、Cancel gating 不能因 handoff review decision metadata 改变。
- 缺 summary、缺 fail-closed flags、unsafe copy、success/control wording、raw path、credentials、raw JSON、checksum、complete artifact 时 fail closed。

验收命令：

```bash
python3 mobile/web/test_mobile_web_entrypoint.py
python3 -m py_compile mobile/web/test_mobile_web_entrypoint.py
node --check mobile/web/app.js
rg -n "mobile_real_device_field_trial_acceptance_execution_handoff_review_decision|robot_diagnostics_mobile_real_device_field_trial_acceptance_execution_handoff_review_decision_summary|accepted|missing|rejected|blocked|software_proof|not_proven|safe_to_control=false|delivery_success=false|primary_actions_enabled=false" mobile/web/app.js mobile/web/test_mobile_web_entrypoint.py mobile/fixtures/mobile_web_status.fixture.json mobile/web/fixtures/status.json docs/product/mobile_user_flow.md
git diff --check -- mobile/web/app.js mobile/web/styles.css mobile/web/test_mobile_web_entrypoint.py mobile/fixtures/mobile_web_status.fixture.json mobile/web/fixtures/status.json docs/product/mobile_user_flow.md
```

### 3.3 Product Owner

允许改动：

- `sprints/2026.05.20_10-11_mobile-real-device-acceptance-handoff-review-decision/tech-done.md`
- `sprints/2026.05.20_10-11_mobile-real-device-acceptance-handoff-review-decision/side2side_check.md`
- `sprints/2026.05.20_10-11_mobile-real-device-acceptance-handoff-review-decision/final.md`
- `OKR.md`
- `docs/process/okr_progress_log.md`

任务：

- 汇总 Robot 与 Full-Stack worker 的实际改动、验证输出、失败定位和剩余风险。
- 回顾 `## OKR 最低优先级核对` 是否仍成立。
- 若没有真实手机 / external / hardware / field materials，OKR 百分比保守不提高。
- 明确 PR #5 `PRRT_kwDOSWB9286CJ3tX` 仍 unresolved，除非 reviewer 或真实材料实际改变。

Product closeout 验收命令：

```bash
test -f sprints/2026.05.20_10-11_mobile-real-device-acceptance-handoff-review-decision/tech-done.md && test -f sprints/2026.05.20_10-11_mobile-real-device-acceptance-handoff-review-decision/side2side_check.md && test -f sprints/2026.05.20_10-11_mobile-real-device-acceptance-handoff-review-decision/final.md
rg -n "mobile_real_device_field_trial_acceptance_execution_handoff_review_decision|Objective 5|Objective 1|Objective 4|PRRT_kwDOSWB9286CJ3tX|software_proof_docker_mobile_real_device_field_trial_acceptance_execution_handoff_review_decision_gate|software_proof|not_proven|safe_to_control=false|delivery_success=false|primary_actions_enabled=false" sprints/2026.05.20_10-11_mobile-real-device-acceptance-handoff-review-decision OKR.md docs/process/okr_progress_log.md
git diff --check -- sprints/2026.05.20_10-11_mobile-real-device-acceptance-handoff-review-decision OKR.md docs/process/okr_progress_log.md
```

## 4. 接口影响

新增接口是 metadata-only safe summary，不改变 command API、不改变 ACK 语义、不改变 Start Delivery / Confirm Dropoff / Cancel gating。

推荐 summary 语义：

- schema: `trashbot.mobile_real_device_field_trial_acceptance_execution_handoff_review_decision_summary.v1`
- status: `accepted_not_proven`、`missing_required_materials_not_proven`、`rejected_unsafe_or_invalid_materials_not_proven` 或 `blocked_waiting_real_environment_materials_not_proven`
- decision: `accepted`、`missing`、`rejected` 或 `blocked`
- source: `software_proof`
- evidence_boundary: `software_proof_docker_mobile_real_device_field_trial_acceptance_execution_handoff_review_decision_gate`
- safe_to_control: false
- delivery_success: false
- primary_actions_enabled: false
- not_proven: 包含真实 iPhone/Android、production app、真实 PWA prompt/userChoice、true phone/browser acceptance、O5 external proof、WAVE ROVER/UART/HIL、真实 2D LiDAR / ToF 材料、真实 route/elevator field pass、Nav2/fixed-route、dropoff/cancel completion、delivery success。

## 5. 风险边界

- 不新增 raw artifact 或 complete artifact 透传。
- 不暴露 ROS topic、`/cmd_vel`、serial/UART、baudrate、WAVE ROVER 参数、credentials、DB/queue URL、OSS AK/SK、local path、checksum。
- 不使用 pass、success、field_pass、hil_pass、delivery completed 等真实通过文案，除非明确在 `not_proven` 中否定。
- 不修改控制入口、ACK/cursor 请求、Start Delivery、Confirm Dropoff 或 Cancel gating。
- 不把 Product planning 文件当工程交付；必须由 Robot Platform Engineer 和 User Touchpoint Full-Stack Engineer 实现并验证。

## 6. 本规划阶段验收命令

Product Owner 创建规划文件后必须运行：

```bash
test -f sprints/2026.05.20_10-11_mobile-real-device-acceptance-handoff-review-decision/pre_start.md && test -f sprints/2026.05.20_10-11_mobile-real-device-acceptance-handoff-review-decision/prd.md && test -f sprints/2026.05.20_10-11_mobile-real-device-acceptance-handoff-review-decision/tech-plan.md
rg -n "sprint_type: epic|OKR 最低优先级核对|Objective 5|Objective 1|Objective 4|PRRT_kwDOSWB9286CJ3tX|mobile_real_device_field_trial_acceptance_execution_handoff_review_decision|software_proof_docker_mobile_real_device_field_trial_acceptance_execution_handoff_review_decision_gate|safe_to_control=false|delivery_success=false|primary_actions_enabled=false" sprints/2026.05.20_10-11_mobile-real-device-acceptance-handoff-review-decision
git diff --check -- sprints/2026.05.20_10-11_mobile-real-device-acceptance-handoff-review-decision
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
