# Sprint 2026.05.19_04-05 Elevator Field Evidence Trace Callback Intake - Tech Done

## sprint_type: epic

Closeout time: 2026-05-19 04:22 Asia/Shanghai.

## 用户价值和产品北极星

用户价值：现场 owner 后续补真实 route/elevator field materials 时，可以先通过 `elevator_field_evidence_trace_callback_intake` 判断 callback packet、`elevator_action_feedback_trace`、Robot diagnostics/mobile summary 与 required materials 是否在同一 safe `evidence_ref` 下对齐，而不是把散落材料或聊天结论人工拼接成验收。

产品北极星不变：普通手机用户交给小车的送垃圾任务必须可解释、可恢复、可复盘。本轮只推进现场材料回填入口的可判定性，证据边界是 Docker/local `software_proof`，保持 `not_proven`、`delivery_success=false`、`primary_actions_enabled=false`。

## OKR 映射

- Objective 2：主目标。把 PR #4 elevator assisted delivery 的现场回填材料入口接到同一 safe `evidence_ref` 判定链，支撑 KR5/KR6/KR7 的可复盘材料闭环。
- Objective 3：共同目标。把真实 Nav2/fixed-route runtime log、route completion signal、field task record、dropoff/cancel completion、delivery result 列入 required materials，避免 trace 被误写成 route pass。
- Objective 4：支撑目标。mobile/web 只读展示 callback intake summary、missing materials 和 owner handoff，不改变 Start Delivery、Confirm Dropoff、Cancel gating。
- Objective 5 仍约 68%，本轮没有真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、production worker/migration/cutover 或真实手机/browser external proof。
- Objective 1 仍约 81%，本轮没有真实 WAVE ROVER/UART/HIL，也没有 PR #5 真实 2D LiDAR / ToF SKU/source/receipt/procurement/installation/wiring/power/calibration/HIL-entry。

## KR 拆解或更新

- Objective 2 KR5：新增 callback intake gate 与 diagnostics/mobile summary，能把未来现场材料纳入同一 `evidence_ref` 下复盘。
- Objective 2 KR6/KR7：将真实电梯门状态、目标楼层确认、人工协助记录、dropoff/cancel completion、delivery result 作为必须回填材料，不把缺失材料隐藏为成功。
- Objective 3 KR3/KR4/KR5：将真实 Nav2/fixed-route runtime log、route completion signal 和现场 task record 作为 required materials；本轮不证明真实路线运行。
- Objective 4 KR6/KR7：手机端新增只读 panel，只展示 phone-safe 摘要，不暴露 raw ROS topic、串口、本机路径、凭证或控制授权。

## 本轮核心抓手

`elevator_field_evidence_trace_callback_intake` software-proof chain：

- PC evidence gate 输出 `trashbot.elevator_field_evidence_trace_callback_intake.v1` artifact 与 `trashbot.elevator_field_evidence_trace_callback_intake_summary.v1` sanitized summary。
- Robot diagnostics 新增 `robot_diagnostics_elevator_field_evidence_trace_callback_intake_summary` safe alias。
- mobile/web 增加只读 callback intake panel 和 fixtures，展示 intake status、missing required materials、owner handoff 和 evidence boundary。

## 实际改动

### Autonomy Algorithm Engineer

- `pc-tools/evidence/elevator_field_evidence_trace_callback_intake.py`
- `tests/test_elevator_field_evidence_trace_callback_intake.py`
- `docs/interfaces/elevator_field_evidence_trace_callback_intake.md`

实现 PC-only evidence gate、safe callback packet/trace/diagnostics/required materials 读取、same safe `evidence_ref` 判定、unsafe copy fail-closed、summary 输出和接口文档。

### Robot Platform Engineer

- `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py`
- `onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`
- `docs/interfaces/operator_gateway_diagnostics.md`

实现 diagnostics safe alias `robot_diagnostics_elevator_field_evidence_trace_callback_intake_summary`，只读消费 summary，缺失/unsupported/unsafe/success/control fields fail closed。

### User Touchpoint Full-Stack Engineer

- `mobile/web/app.js`
- `mobile/web/styles.css`
- `mobile/web/test_mobile_web_entrypoint.py`
- `mobile/web/fixtures/status.json`
- `mobile/fixtures/mobile_web_status.fixture.json`
- `docs/product/mobile_user_flow.md`

实现 mobile/web 只读 panel 和 fixture，展示 `elevator_field_evidence_trace_callback_intake` status、missing materials、owner handoff，不改变 Start Delivery、Confirm Dropoff、Cancel gating。

### Product Manager / OKR Owner

- `sprints/2026.05.19_04-05_elevator-field-evidence-trace-callback-intake/tech-done.md`
- `sprints/2026.05.19_04-05_elevator-field-evidence-trace-callback-intake/side2side_check.md`
- `sprints/2026.05.19_04-05_elevator-field-evidence-trace-callback-intake/final.md`
- `OKR.md`
- `docs/process/okr_progress_log.md`

完成 sprint closeout、OKR 4.1 快照、当前最高优先级和风险边界同步。

## 验证结果

Worker 已完成并报告：

- Autonomy：`py_compile` 通过；`python3 -m unittest tests/test_elevator_field_evidence_trace_callback_intake.py` 输出 `Ran 6 tests in 0.105s OK`；required `rg` 通过；scoped `git diff --check` 通过。
- Robot：`py_compile` 通过；`python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py` 输出 `Ran 195 tests in 0.464s OK`；required `rg` 通过；scoped `git diff --check` 通过。
- Full-Stack：`python3 mobile/web/test_mobile_web_entrypoint.py` 输出 `Ran 106 tests OK`；`py_compile` 通过；`node --check mobile/web/app.js` 通过；required `rg` 通过；scoped `git diff --check` 通过。

Product closeout 复跑结果见 `final.md`。本文件记录的是实现事实与验收边界，不把软件围栏通过写成实机通过。

## 失败定位与修复

- Autonomy 首轮 success regex 过宽，把 `real_route_elevator_field_pass` 的 `not_proven` literal 误判成 success claim；已收窄 regex 并重跑通过。
- Robot 首轮 unsafe key fragment `ack` 过宽，误匹配 `callback`；已改为特定 ACK fields 并重跑通过。
- Full-Stack 本轮未报告阻塞性失败。

## 剩余风险和证据缺口

- `not_proven`：真实电梯、真实 Nav2/fixed-route runtime、真实 route completion signal、真实 field task record、真实 dropoff/cancel completion、真实 delivery result、真实送达、真实 phone/browser、WAVE ROVER/UART/HIL、PR #5 真实 2D LiDAR / ToF 材料、O5 external proof。
- `delivery_success=false` 和 `primary_actions_enabled=false` 必须继续保持；callback packet intake ready 只表示可以进入后续 review decision，不等于真实 field pass。
- 真实现场材料仍需由现场 owner 回填：真实门状态、目标楼层确认、人工协助记录、Nav2/fixed-route runtime log、route completion signal、field task record、dropoff/cancel completion 或 delivery result。
