# Sprint 2026.05.19_12-13 Task Terminal Field Material Intake - Tech Done

## sprint_type: epic

Run time: 2026-05-19 12:25 Asia/Shanghai。

## 1. 本轮目标

本轮完成 `task_terminal_field_material_intake` 的 software-proof 主链路收口：Robot diagnostics 暴露 safe summary，mobile/web 展示只读“现场材料回填入口”，Autonomy 只读确认 route/elevator/Nav2 字段语义不冲突，Product 只记录可回填性，不提高真实 field pass、HIL、O5 external proof 或 delivery success。

证据边界固定为：

- `software_proof`
- `not_proven`
- `delivery_success=false`
- `primary_actions_enabled=false`
- `safe_to_control=false`

## 2. 实际改动文件

Robot worker 改动：

- `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py`
- `onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`
- `docs/interfaces/operator_gateway_diagnostics.md`

Full-Stack worker 改动：

- `mobile/web/app.js`
- `mobile/web/styles.css`
- `mobile/web/test_mobile_web_entrypoint.py`
- `mobile/fixtures/mobile_web_status.fixture.json`
- `mobile/web/fixtures/status.json`
- `docs/product/mobile_user_flow.md`

Product closeout 改动：

- `sprints/2026.05.19_12-13_task-terminal-field-material-intake/tech-done.md`
- `sprints/2026.05.19_12-13_task-terminal-field-material-intake/side2side_check.md`
- `sprints/2026.05.19_12-13_task-terminal-field-material-intake/final.md`
- `OKR.md`
- `docs/process/okr_progress_log.md`

Autonomy worker 只读咨询，未修改文件。

## 3. Robot 结果

Robot worker 新增 `robot_diagnostics_task_terminal_field_material_intake_summary` safe alias。该 alias 只消费 sanitized terminal field material intake summary，输出 safe `evidence_ref`、accepted safe refs、missing materials、next required evidence、phone-safe copy 和 evidence boundary。

Robot 侧固定保持：

- `source=software_proof`
- `status=not_proven` 或 blocked / missing-material 状态
- `delivery_success=false`
- `primary_actions_enabled=false`
- `safe_to_control=false`

Robot 不从 raw artifacts、local paths、checksums、credentials、ACK、cursor、completion wording、field-pass wording、HIL wording 或 O5 external proof wording 推导成功，也不触发 ACK、commands、Nav2、route execution、HIL、terminal ACK、cursor advance 或 robot command。

Robot worker 验证：

```text
python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py
pass

python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py
Ran 206 tests in 0.512s
OK

rg required keywords
pass

git diff --check -- onboard/src/ros2_trashbot_behavior docs/interfaces sprints/2026.05.19_12-13_task-terminal-field-material-intake
pass
```

Robot 剩余风险：该 alias 只是 diagnostics software proof，不证明真实现场材料、真实 route/elevator field pass、真实 Nav2/fixed-route、真实手机/browser、WAVE ROVER/UART/HIL 或 O5 external proof。

## 4. Full-Stack 结果

Full-Stack worker 在 `mobile/web` 新增只读“现场材料回填入口”panel，优先消费 `robot_diagnostics_task_terminal_field_material_intake_summary`。panel 展示 intake status、safe `evidence_ref`、accepted safe refs、missing materials、next required evidence、phone-safe copy 和 evidence boundary。

Full-Stack 侧固定保持：

- `software_proof`
- `not_proven`
- `delivery_success=false`
- `primary_actions_enabled=false`
- `safe_to_control=false`

缺 summary 或命中不安全文案时 fail closed。panel 不从 raw artifacts、ACK、cursor、old material status 或 completion summary 推导成功；Start Delivery、Confirm Dropoff、Cancel gating 不变。

Full-Stack worker 验证：

```text
python3 mobile/web/test_mobile_web_entrypoint.py
Ran 122 tests in 0.863s
OK

python3 -m py_compile mobile/web/test_mobile_web_entrypoint.py
pass

node --check mobile/web/app.js
pass

rg required keywords
pass

git diff --check -- mobile/web mobile/fixtures docs/product/mobile_user_flow.md sprints/2026.05.19_12-13_task-terminal-field-material-intake
pass
```

Full-Stack 额外 Browser QA 曾尝试，但本地 PWA/service-worker 缓存让 in-app browser 停在旧 offline shell，截图命令超时；本轮不把 Browser QA 计为通过证据。

Full-Stack 剩余风险：未做真实 ROS2/Robot、真实手机浏览器或真实现场材料联调；本轮仅证明 mobile/web 对 Robot safe summary 的 software-proof 只读展示。

## 5. Autonomy 只读咨询结果

Autonomy 只读检查了 `AGENTS.md`、`OKR.md`、本 sprint `tech-plan.md` / `prd.md`、`docs/navigation/fixed_route_workflow.md`、`docs/interfaces/task_record.md`、`docs/interfaces/operator_gateway_diagnostics.md` 和 elevator material backfill intake 文档；未修改文件，未运行实现/验收命令。

咨询结论：

- `task_terminal_field_material_intake` 与 Objective 3 不冲突，前提是 Robot diagnostics 和 mobile/web 只把 route/elevator/Nav2 字段作为 missing materials / next required evidence 展示。
- 新 summary 不应使用 `route_passed`、`fixed_route_passed`、`nav2_passed`、`field_pass` 或任何 completion claim；不建议新增 `route_elevator_field_pass` pass 类字段。
- `accepted_safe_refs` 只能表示安全引用已接收，不能表示真实材料通过。
- 后续真实回填至少需要同一 safe `evidence_ref` 下的真实 Nav2/fixed-route runtime log、route completion signal、真实 field task record、真实电梯门状态、真实目标楼层确认、真实人工协助记录、真实 dropoff/cancel terminal material 和 delivery result safe refs。

## 6. Product OKR 判断

- Objective 5：保持约 68%，不提高。本轮没有真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、production worker/migration/cutover 或真实手机/browser external proof。
- Objective 1：保持约 81%，不提高。本轮没有真实 WAVE ROVER/UART/HIL、`feedback_T1001.log`、真实 `/odom`、`/imu/data`、`/battery`、operator HIL report，也没有 PR #5 2D LiDAR / ToF SKU/source/receipt/procurement/installation/wiring/power/calibration/HIL-entry。
- Objective 2：保持约 99%，只记录 dropoff/cancel terminal field material intake 的 software-proof 可回填性；不证明真实 dropoff completion、真实 cancel completion、delivery result 或 delivery_success。
- Objective 3：保持约 99%，只记录 route/elevator/Nav2 evidence fields 可作为 missing / next-required evidence 进入同一 safe `evidence_ref` 回填入口；不证明真实 Nav2/fixed-route、route completion signal、现场 task record 或 route/elevator field pass。
- Objective 4：保持约 99%，只记录 mobile/web 可只读展示 Robot safe summary 的可见性；不证明真实 iPhone/Android device behavior、production app/browser、真实 PWA prompt/user choice 或真实手机/browser external proof。

## 7. 剩余风险

- 未证明真实 dropoff completion 或真实 cancel completion。
- 未证明 `delivery_success=true`，当前必须保持 `delivery_success=false`。
- 未证明真实电梯、真实 Nav2/fixed-route、真实 route completion signal、真实门状态、真实楼层确认或人工协助现场记录。
- 未证明真实手机、真实 iPhone/Android device behavior、production app/browser external proof 或真实 PWA prompt/user choice。
- 未证明 WAVE ROVER/UART/HIL、真实串口日志、`feedback_T1001`、真实 `/odom`、`/imu/data`、`/battery` 或 operator HIL report。
- 未证明 PR #5 真实材料，包括 2D LiDAR / ToF SKU/source/receipt/procurement/installation/wiring/power/calibration/HIL-entry。
- 未证明 Objective 5 external proof，包括公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、production worker/migration/cutover。
