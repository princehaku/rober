# Field Evidence Rerun Acceptance Review Handoff Tech Done

Run time: 2026-05-22 23:18 Asia/Shanghai

## Sprint Type

sprint_type: epic

Capability: `field_evidence_rerun_execution_result_acceptance_review_handoff`

Evidence boundary: `software_proof_docker_field_evidence_rerun_execution_result_acceptance_review_handoff_gate`

## 用户价值和产品北极星

本轮把上一轮 `ready_for_field_rerun_result_acceptance_review_handoff` 转成可交给 field owner / support / reviewer 的验收交接包。用户价值是让现场材料缺口、同一 safe `evidence_ref`、下一步责任和禁止声明范围在 PC、Robot diagnostics、mobile/web 三端一致可见，而不是让普通手机用户误以为任务已经真实送达或可以继续控制。

产品北极星保持为低成本、手机可用、证据可复盘的 ROS2 垃圾投递机器人。本轮只推进证据交接 readiness，不替代真实 route/elevator field pass、真实手机/browser、delivery success、Objective 5 external proof、Objective 1 HIL 或 PR #5 reviewer resolution。

## OKR 映射与 KR 拆解

- Objective 2：现场复跑执行结果验收交接包列出真实 task record、真实电梯门状态、目标楼层确认、人工协助记录、dropoff/cancel completion 或 delivery result 作为后续必需材料；本轮不证明真实送达。
- Objective 3：交接包把真实 Nav2/fixed-route runtime log 和 route completion signal 纳入 checklist；本轮不证明真实路线或固定路线运行通过。
- Objective 4：mobile/web 增加只读“现场证据复跑执行结果验收交接”panel，保持 Start Delivery / Confirm Dropoff / Cancel disabled；本轮不证明真实手机设备验收。
- Objective 5：仍是最低约 68%，但无真实 public HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/cutover、真实手机/browser 或 verified terminal result material；no OKR percentage lift。
- Objective 1：仍约 81%，无真实 WAVE ROVER/UART/HIL、2D LiDAR/ToF material、operator HIL report 或 PR #5 `PRRT_kwDOSWB9286CJ3tX` reviewer resolution；no OKR percentage lift。

## 实际改动

Task A Autonomy Algorithm Engineer:

- 新增 `pc-tools/evidence/field_evidence_rerun_execution_result_acceptance_review_handoff.py`
- 新增 `pc-tools/evidence/test_field_evidence_rerun_execution_result_acceptance_review_handoff.py`
- 更新 `pc-tools/README.md`
- 更新 `docs/interfaces/evidence_contracts.md`
- 新 schema：`trashbot.field_evidence_rerun_execution_result_acceptance_review_handoff.v1`
- 新 schema：`trashbot.field_evidence_rerun_execution_result_acceptance_review_handoff_summary.v1`
- 首轮 forbidden proof scanner 误把 `not_proven` 内的 snake_case `real_hil_pass` 当自由文本 claim，已收窄为 free-copy phrase scanner。

Task B Robot Platform Engineer:

- 更新 `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py`
- 更新 `onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`
- 更新 `docs/interfaces/ros_runtime_contracts.md`
- 新增 safe alias `robot_diagnostics_field_evidence_rerun_execution_result_acceptance_review_handoff_summary`
- 补齐 `build_diagnostics_payload`、`latest_status`、env/ref wiring 与 fail-closed summary。

Task C User Touchpoint Full-Stack Engineer:

- 更新 `mobile/web/app.js`
- 新增 `mobile/web/fixtures/robot_diagnostics_field_evidence_rerun_execution_result_acceptance_review_handoff.json`
- 更新 `mobile/web/test_mobile_web_entrypoint.py`
- 更新 `docs/product/mobile_user_flow.md`
- 新增只读“现场证据复跑执行结果验收交接”panel，优先消费 Robot safe alias，并保持 Start Delivery / Confirm Dropoff / Cancel disabled。

Task D Product Manager / OKR Owner:

- 新增本文件 `tech-done.md`
- 新增 `side2side_check.md`
- 新增 `final.md`
- 更新 `OKR.md`
- 更新 `docs/process/okr_progress_log.md`

## 验证结果

Task A reported:

```text
python3 -m py_compile pc-tools/evidence/field_evidence_rerun_execution_result_acceptance_review_handoff.py
python3 -m unittest pc-tools/evidence/test_field_evidence_rerun_execution_result_acceptance_review_handoff.py
Ran 5 tests in 0.175s OK
python3 pc-tools/evidence/field_evidence_rerun_execution_result_acceptance_review_handoff.py --help
required rg passed
scoped git diff --check passed
```

Task B reported:

```text
python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py
python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py
Ran 294 tests in 2.309s OK
required rg passed
scoped git diff --check passed
```

Task C reported:

```text
node --check mobile/web/app.js
python3 -m json.tool mobile/web/fixtures/robot_diagnostics_field_evidence_rerun_execution_result_acceptance_review_handoff.json
python3 -m unittest mobile/web/test_mobile_web_entrypoint.py
Ran 274 tests ... OK
required rg passed
scoped git diff --check passed
```

Product closeout validation:

```text
test -f tech-done.md && test -f side2side_check.md && test -f final.md
required rg for Objective 1/2/3/4/5, PRRT_kwDOSWB9286CJ3tX, not_proven, delivery_success=false, primary_actions_enabled=false, safe_to_control=false
scoped git diff --check
```

## 偏差与修复

- Task A 首轮 scanner 误判 safe snake_case 字段，已收窄到自由文案 overclaim 扫描；最终 5 个 focused tests 通过。
- Task B 无剩余失败。
- Task C 无剩余失败。
- Product closeout 没有改动产品代码、测试、mobile/Robot/PC implementation docs 之外的文件；只改本轮允许的 sprint closeout、`OKR.md` 和 `docs/process/okr_progress_log.md`。

## 剩余风险

- 本轮仍只是 `software_proof_docker_field_evidence_rerun_execution_result_acceptance_review_handoff_gate`，必须保留 `source=software_proof`、`not_proven`、`delivery_success=false`、`primary_actions_enabled=false`、`safe_to_control=false`。
- PR #5 `PRRT_kwDOSWB9286CJ3tX` 仍 unresolved / `is_resolved=false` / `hardware_material_pending`；`PRRT_kwDOSWB9286CJ3tQ` 和 `PRRT_kwDOSWB9286CJ3tU` resolved 不等于硬件材料 thread resolved。
- 仍缺真实 task record、真实 Nav2/fixed-route runtime log、route completion signal、真实电梯门状态、目标楼层确认、人工协助记录、dropoff/cancel completion、delivery result、真实手机/browser evidence。
- 仍缺 Objective 5 external proof：真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/cutover、真实手机/browser 或 verified terminal result。
- 仍缺 Objective 1 materials：真实 WAVE ROVER/UART/HIL、2D LiDAR/ToF SKU/source/receipt/procurement/installation/wiring/power/calibration/HIL-entry、operator HIL report 和 reviewer resolution。
