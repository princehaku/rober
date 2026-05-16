# Sprint 2026.05.16_22-23 Route Task Field Retest Result Intake - Final

sprint_type: epic

## 1. 收口结论

本轮完成 `software_proof_docker_route_task_field_retest_result_intake_gate` 并进入可提交状态。A/B/C worker 已完成 PC gate、Robot diagnostics consumer、mobile/web 只读 panel 和相关文档；Product closeout 已完成 `tech-done.md`、`side2side_check.md`、本文件、`OKR.md`、`docs/process/okr_progress_log.md`。

本轮是 Docker-only software proof。统一结果仍为：

- `not_proven`
- `delivery_success=false`
- `primary_actions_enabled=false`
- 不证明真实 field pass、真实 Nav2/fixed-route、真实电梯、真实 dropoff/cancel completion、真实 delivery result、真实手机/browser、WAVE ROVER/UART/HIL 或 Objective 5 external proof。

## 2. 用户价值和产品北极星

用户价值：现场复测结果有了可回填、可对账、可 fail-closed 的入口。现场同学可以按同一 `evidence_ref` 回填八类结果材料；支持同学和手机用户只能看到安全摘要、缺失项和下一步动作，不会把材料入口误读成真实送达成功。

产品北极星：继续把 `rober` 做成普通手机用户能理解、现场支持能复测、证据链能复盘的低成本 ROS2 自主垃圾投递机器人。本轮推进的是 Objective 2 / Objective 3 的现场结果 intake readiness，不是 O5 本地 metadata depth，也不是 PR #5 硬件 blocker 第三轮消费。

## 3. OKR 映射和进度

- Objective 1 保持约 75%。本轮没有真实 WAVE ROVER、UART、HIL、`T=1001` feedback、`/odom`、`/imu/data`、`/battery` 或真实 2D LiDAR / ToF 材料。
- Objective 2 从约 82% 保守上调到约 83%。result intake 把 task record、door_state、target_floor_confirmation、human_assistance_note、dropoff/cancel completion、delivery_result 变成可检查回填入口；不是 field pass。
- Objective 3 从约 82% 保守上调到约 83%。result intake 把真实 Nav2/fixed-route runtime log、route completion signal、task record 和 rerun summary 变成可对账入口；不是真实 Nav2/fixed-route 实跑。
- Objective 4 从约 91% 保守上调到约 92%。mobile/web 能 phone-safe 展示 result intake 状态和缺口，copy/export fail closed，主操作授权不变；不是真实手机/browser 或 production app proof。
- Objective 5 保持约 66%。本机 Docker-only，仍缺真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue connectivity、production worker/migration。

## 4. PR 和 blocker 处理

- PR #4 已把 elevator-assisted delivery 写成主线必须能力。本轮将 door_state、target_floor_confirmation、human_assistance_note 纳入 result intake，但不宣称真实电梯闭环完成。
- PR #5 已把单目 + 2D LiDAR + ToF 安全环、参数化传感器配置和证据链写成硬件/产品基线。`17-18_hardware-baseline-source-alignment` 与 `18-19_hardware-sensor-hil-entry-config-precheck` 已连续两轮消费该硬件/source/config blocker；本轮按 `AGENTS.md` 红线切换到 O2/O3 field retest result intake，没有第三次消费同一 blocker。
- O5 stop rule 仍成立：Objective 5 数值最低，但没有真实外部云/4G/OSS/CDN/DB/queue/worker 证据时，不继续堆本地 O5 metadata wrapper。

## 5. 实际交付

Task A Autonomy：

- 新增 `pc-tools/evidence/route_task_field_retest_result_intake.py`
- 新增 `pc-tools/evidence/test_route_task_field_retest_result_intake.py`
- 更新 `pc-tools/README.md`
- 更新 `docs/navigation/fixed_route_workflow.md`
- 验证：py_compile pass；unittest `Ran 8 tests in 0.036s OK`；CLI `--help` pass；required rg pass；scoped diff check pass。
- 失败定位：首轮修复 `required_result_materials` 误判和普通绝对路径脱敏问题。

Task B Robot：

- 更新 `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py`
- 更新 `onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`
- 更新 `docs/interfaces/ros_contracts.md`
- 验证：py_compile pass；diagnostics unittest `Ran 116 tests in 0.143s OK`；required rg pass；scoped diff check pass。

Task C Full-stack：

- 更新 `mobile/web/app.js`
- 更新 `mobile/web/styles.css`
- 更新 `mobile/web/test_mobile_web_entrypoint.py`
- 更新 `mobile/web/fixtures/status.json`
- 更新 `docs/product/mobile_user_flow.md`
- 验证：mobile unittest `Ran 18 tests in 0.033s OK`；`node --check` pass；required rg pass；scoped diff check pass；fixture-backed DOM check pass。
- 失败定位：截图捕获超时，未计为 browser proof；允许范围内修复既有 `nextEvidence` fallback guard。

Task D Product closeout：

- 新增 `tech-done.md`
- 新增 `side2side_check.md`
- 新增 `final.md`
- 更新 `OKR.md`
- 更新 `docs/process/okr_progress_log.md`
- 验证：required rg pass；closeout scoped `git diff --check` pass。

## 6. 剩余风险和下一步证据链

仍需补齐真实现场材料：

- 真实 Nav2/fixed-route runtime log
- route completion signal
- task record
- door_state
- target_floor_confirmation
- human_assistance_note
- dropoff_or_cancel_completion
- delivery_result

仍需补齐真实系统证据：

- WAVE ROVER/UART/HIL、`T=1001` feedback、真实 `/odom`、`/imu/data`、`/battery`
- 真实电梯、真实路线采集、真实 fixed-route/Nav2 实跑
- 真实 iPhone/Android browser、production app、真实 PWA prompt/user choice
- Objective 5 external proof：公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue connectivity、production worker/migration

下一轮建议：如果仍没有 O5 外部材料，继续围绕同一 `evidence_ref` 推进真实现场材料回填或 field result reconciliation；不要把本轮 intake readiness 当作 field pass。
