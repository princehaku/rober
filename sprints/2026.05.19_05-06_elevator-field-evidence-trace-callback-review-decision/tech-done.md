# Sprint 2026.05.19_05-06 Elevator Field Evidence Trace Callback Review Decision - Tech Done

## sprint_type: epic

Closeout time: 2026-05-19 05:23 Asia/Shanghai.

## 用户价值和产品北极星

用户价值：现场 owner 后续补 route/elevator field materials 时，现在不仅能先做 callback intake，还能把 intake 结果转成明确 review decision：继续补材料、重新回执，或进入 owner handoff。手机端只读展示这个决策，避免把聊天口径或散落材料误写成真实现场通过。

产品北极星不变：普通手机用户交给小车的送垃圾任务必须可解释、可恢复、可复盘。本轮证据边界仍是 Docker/local `software_proof`，保持 `not_proven`、`delivery_success=false`、`primary_actions_enabled=false`。

## OKR 映射

- Objective 2：主目标。把 PR #4 elevator assisted delivery 的 callback intake 推进到 review decision，支撑现场材料复核和 owner handoff。
- Objective 3：共同目标。继续把真实 Nav2/fixed-route runtime log、route completion signal、field task record、dropoff/cancel completion、delivery result 作为 hard requirements。
- Objective 4：支撑目标。mobile/web 只读展示 review decision、decision reasons、missing/rejected materials、next required evidence 和 owner handoff，不改变 Start Delivery、Confirm Dropoff、Cancel gating。
- Objective 1：不推进。没有真实 WAVE ROVER/UART/HIL 或 PR #5 真实 2D LiDAR / ToF 材料。
- Objective 5：不推进。没有真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/cutover 或 external proof。

## 实际改动

### Autonomy Algorithm Engineer

- `pc-tools/evidence/elevator_field_evidence_trace_callback_review_decision.py`
- `tests/test_elevator_field_evidence_trace_callback_review_decision.py`
- `docs/interfaces/elevator_field_evidence_trace_callback_review_decision.md`

新增 PC-only review-decision gate，读取上一轮 `elevator_field_evidence_trace_callback_intake` artifact/summary/wrapper JSON，输出 `trashbot.elevator_field_evidence_trace_callback_review_decision.v1` artifact 与 `trashbot.elevator_field_evidence_trace_callback_review_decision_summary.v1` summary。决策覆盖 missing intake、unsupported input、same-ref mismatch、unsafe copy/success claim、callback rerun、material backfill、owner handoff ready。

### Robot Platform Engineer

- `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py`
- `onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`
- `docs/interfaces/operator_gateway_diagnostics.md`

新增 `robot_diagnostics_elevator_field_evidence_trace_callback_review_decision_summary` safe alias，只读消费 review-decision summary。缺失、unsupported schema/boundary、source/status 不匹配、unsafe copy/key、success/control claim、`delivery_success=true`、`primary_actions_enabled=true` 均 fail closed。

### User Touchpoint Full-Stack Engineer

- `mobile/web/app.js`
- `mobile/web/styles.css`
- `mobile/web/test_mobile_web_entrypoint.py`
- `mobile/web/fixtures/status.json`
- `mobile/fixtures/mobile_web_status.fixture.json`
- `docs/product/mobile_user_flow.md`

新增 mobile/web 只读 “电梯现场证据回调复核决策” panel，优先消费 Robot diagnostics alias，兼容同名 summary/artifact fixture；展示 `review_decision`、`decision_reasons`、missing/rejected materials、`next_required_evidence`、owner handoff 和 evidence boundary。Start Delivery、Confirm Dropoff、Cancel gating 不变。

### Product Manager / OKR Owner

- `sprints/2026.05.19_05-06_elevator-field-evidence-trace-callback-review-decision/tech-done.md`
- `sprints/2026.05.19_05-06_elevator-field-evidence-trace-callback-review-decision/side2side_check.md`
- `sprints/2026.05.19_05-06_elevator-field-evidence-trace-callback-review-decision/final.md`
- `OKR.md`
- `docs/process/okr_progress_log.md`

完成 sprint closeout、OKR 4.1 快照、当前最高优先级和风险边界同步。

## 验证结果

主会话复跑围栏结果：

- `python3 -m py_compile pc-tools/evidence/elevator_field_evidence_trace_callback_review_decision.py onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py mobile/web/test_mobile_web_entrypoint.py`：通过。
- `python3 -m unittest tests/test_elevator_field_evidence_trace_callback_review_decision.py`：`Ran 7 tests in 0.043s OK`。
- `python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`：`Ran 196 tests in 0.475s OK`。
- `python3 mobile/web/test_mobile_web_entrypoint.py`：`Ran 108 tests in 0.688s OK`。
- `node --check mobile/web/app.js`：通过。
- 三组 required `rg` 命中 PC、Robot、mobile 和 sprint contract literal。
- `git diff --check -- ...` scoped 到本轮改动文件和 sprint 文件：通过。

Worker 报告的失败均已定位并修复：

- Autonomy 首轮将 `delivery_success=true` 归为 unsupported；已改为 unsafe/success copy fail-closed。
- Robot 首轮 unsupported fixture 使用 intake summary schema；已改为 review-decision summary 回指错误 source schema。
- Full-Stack 请求的围栏命令无失败；补充 browser smoke 发现既有 dynamic panel listener 顺序问题，已在允许范围内补齐相关 panel ensure 调用。

## 剩余风险和证据缺口

- 本轮不证明真实电梯、真实 Nav2/fixed-route runtime、真实 route completion signal、真实 field task record、真实 dropoff/cancel completion、真实 delivery result、真实送达、真实 phone/browser、WAVE ROVER/UART/HIL、PR #5 真实 2D LiDAR / ToF 材料或 O5 external proof。
- `ready_for_elevator_field_owner_handoff_not_proven` 只能表示 owner handoff 的 metadata review ready，不是真实 field pass。
- `delivery_success=false` 和 `primary_actions_enabled=false` 必须继续保持。
