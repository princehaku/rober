# Field Evidence Rerun Handoff Intake Tech Done

## Sprint Status

- sprint_type: epic
- Sprint: `2026.05.20_16-17_field-evidence-rerun-handoff-intake`
- Product closeout time: 2026-05-20 16:25 CST
- Evidence boundary: `software_proof_docker_field_evidence_rerun_handoff_intake_gate`
- Conservative flags: `software_proof`, `not_proven`, `safe_to_control=false`, `delivery_success=false`, `primary_actions_enabled=false`

## 用户价值和产品北极星

本轮面向现场 owner 和支持同学补齐“复跑交接回执”入口：当上一轮 `field_evidence_rerun_callback_review_handoff` 已把缺口交给 owner 后，系统能接收 owner-safe handoff intake packet，并让 PC gate、Robot diagnostics 和 mobile/web 看到同一 safe `evidence_ref` 的回执状态。

产品北极星不变：普通手机用户最终应能把垃圾交给小车并得到可解释、可复盘、可恢复的送达结果。本轮只推进现场证据链的软件闭环，不把任何 metadata-only 回执写成真实 route/elevator field pass、真实 phone/browser、HIL、delivery success、dropoff/cancel completion、O5 external proof 或 PR #5 resolved。

## OKR 映射

| Objective | Product 判断 |
| --- | --- |
| Objective 1：硬件协议可信底盘 | 保持约 81%。本轮不触碰 WAVE ROVER/UART/HIL、hardware bridge、真实 2D LiDAR / ToF materials 或 PR #5 `PRRT_kwDOSWB9286CJ3tX` resolved 状态；manual reply `3269642220` 仍不是硬件 proof。 |
| Objective 2：可送垃圾任务 + 电梯 assisted delivery 必达闭环 | 保守保持约 99%。本轮只把 route/elevator 现场复跑交接回执做成 `software_proof` intake gate，不证明真实电梯、真实 dropoff/cancel completion、delivery result 或 delivery_success。 |
| Objective 3：可验证导航与固定路线 | 保守保持约 99%。本轮没有真实 Nav2/fixed-route runtime log、route completion signal、现场 task record 或上车复账。 |
| Objective 4：手机用户体验与低成本量产边界 | 保守保持约 99%。mobile/web 新 panel 是只读、安全摘要展示，不是真实 iPhone/Android device behavior、production app、真实 PWA prompt/userChoice 或 true phone/browser acceptance。 |
| Objective 5：云中转 + OSS/CDN 数据通路产品化 | 保持约 68%。本轮不改 cloud commands/status/ack，也没有公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/cutover 或 external proof。 |

## KR 拆解或更新

- KR2/O2 和 KR4/O3：将真实 route/elevator field rerun 所需的同一 safe `evidence_ref`、owner-safe packet、next required evidence 和 blocker 状态继续结构化，但状态仍是 `not_proven`。
- KR4/O4：手机端可读性前进一小步，用户/支持能看到“现场证据复跑交接回执”状态，但主操作 gating 不变。
- KR/O5：无进度更新；本轮不是云外部材料或生产链路证明。
- KR/O1：无进度更新；本轮不是硬件协议、真实串口或 HIL 证明。

## 本轮核心抓手

核心抓手是 owner-safe handoff intake：把上一轮 callback review handoff 后的现场回执，从 PC artifact 到 Robot diagnostics safe alias 再到 mobile/web 只读 panel 串起来，并用 fail-closed 字段防止误读为可控制或已送达。

## 实际改动

### Autonomy Task 1

- `pc-tools/evidence/field_evidence_rerun_handoff_intake.py`
- `tests/test_field_evidence_rerun_handoff_intake.py`
- `pc-tools/README.md`
- `docs/interfaces/evidence_contracts.md`

实现 `trashbot.field_evidence_rerun_handoff_intake.v1` / summary，消费上一轮 callback review handoff artifact/summary/wrapper 与 owner-safe handoff intake packet；在 missing、unsupported、`evidence_ref` mismatch、unsafe fields 时 fail closed。

### Robot Task 2

- `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py`
- `onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`
- `docs/interfaces/ros_runtime_contracts.md`

新增 `robot_diagnostics_field_evidence_rerun_handoff_intake_summary` 和 `summarize_field_evidence_rerun_handoff_intake`，只暴露 metadata-only safe summary。首轮发现 `raw_artifact_consumed=false` 字段名会暴露 forbidden field，Robot worker 移除后复验通过。

### Full-Stack Task 3

- `mobile/web/app.js`
- `mobile/web/fixtures/status.json`
- `mobile/fixtures/mobile_web_status.fixture.json`
- `mobile/web/test_mobile_web_entrypoint.py`
- `docs/product/mobile_user_flow.md`

新增只读“现场证据复跑交接回执”panel，优先消费 Robot safe alias，兼容 fallback summary；Start Delivery、Confirm Dropoff、Cancel gating 不变。

### Product Task 4

- `sprints/2026.05.20_16-17_field-evidence-rerun-handoff-intake/tech-done.md`
- `sprints/2026.05.20_16-17_field-evidence-rerun-handoff-intake/side2side_check.md`
- `sprints/2026.05.20_16-17_field-evidence-rerun-handoff-intake/final.md`
- `OKR.md`
- `docs/process/okr_progress_log.md`

完成 sprint closeout、OKR 保守更新和 progress log 追加。

## 验证结果

### Engineer worker 验证

- Autonomy: `python3 -m py_compile pc-tools/evidence/field_evidence_rerun_handoff_intake.py tests/test_field_evidence_rerun_handoff_intake.py` pass。
- Autonomy: `python3 -m unittest tests.test_field_evidence_rerun_handoff_intake` -> `Ran 5 tests in 0.059s OK`。
- Autonomy: CLI `--help` pass；required `rg` pass；scoped diff check pass。
- Robot: `py_compile` pass。
- Robot: `PYTHONPATH=onboard/src/ros2_trashbot_behavior python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py` -> `Ran 232 tests ... OK`。
- Robot: required `rg` pass；scoped diff check pass。
- Full-Stack: `node --check mobile/web/app.js` pass。
- Full-Stack: `python3 -m unittest mobile/web/test_mobile_web_entrypoint.py` -> `Ran 171 tests in 1.229s OK`。
- Full-Stack: fixture JSON check pass；required `rg` pass；scoped diff check pass。

### 主节点集成复跑

- `python3 -m py_compile pc-tools/evidence/field_evidence_rerun_handoff_intake.py tests/test_field_evidence_rerun_handoff_intake.py onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py` pass。
- `python3 -m unittest tests.test_field_evidence_rerun_handoff_intake` -> `Ran 5 tests in 0.063s OK`。
- `PYTHONPATH=onboard/src/ros2_trashbot_behavior python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py` -> `Ran 232 tests in 0.786s OK`。
- `node --check mobile/web/app.js` pass。
- `python3 -m unittest mobile/web/test_mobile_web_entrypoint.py` -> `Ran 171 tests in 1.220s OK`。
- `python3 -m json.tool mobile/web/fixtures/status.json >/dev/null && python3 -m json.tool mobile/fixtures/mobile_web_status.fixture.json >/dev/null` pass。
- `python3 pc-tools/evidence/field_evidence_rerun_handoff_intake.py --help` pass。
- Required `rg` over touched implementation/docs pass。
- `git diff --check` pass。

## 偏差和失败定位

- Robot worker 首轮失败：safe alias 暴露 `raw_artifact_consumed=false`，字段名触发 forbidden-field boundary。定位为字段命名泄漏 raw artifact 概念；移除该字段后 diagnostics unittest、required `rg` 和 scoped diff check 通过。
- 未发现 Product closeout 范围内的新增实现失败。

## 优先级和验收口径

P0 验收口径：三个 Engineer worker 的 scoped tests、required `rg`、scoped diff check 与主节点集成复跑均通过；所有文档和 OKR 文案保留 `software_proof`、`not_proven`、`safe_to_control=false`、`delivery_success=false`、`primary_actions_enabled=false`。

P1 验收口径：mobile/web 新 panel 只读，不新增 control route、ACK/cursor、fetch raw artifact、copy/export 或主操作解锁；Robot diagnostics 只暴露 safe alias。

## 对应责任 Engineer

- Autonomy Algorithm Engineer：PC evidence gate、schema、CLI 和 evidence docs。
- Robot Platform Engineer：diagnostics safe alias、sanitization 和 ROS runtime docs。
- User Touchpoint Full-Stack Engineer：mobile/web 只读 panel、fixture/test 和 mobile product docs。
- Product Manager / OKR Owner：sprint closeout、OKR/progress log 和保守验收口径。

## 剩余风险和证据链缺口

- 仍缺真实 route/elevator field pass、真实 task record、真实 Nav2/fixed-route runtime log、route completion signal、真实电梯门状态、真实楼层确认、真实人工协助记录、真实 dropoff/cancel completion、真实 cancel completion、delivery result 和 delivery success。
- 仍缺真实 iPhone/Android device behavior、production app、真实 PWA prompt/userChoice、true phone/browser acceptance。
- 仍缺 Objective 5 的公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/cutover 和 external proof。
- 仍缺 Objective 1 的 WAVE ROVER/UART/HIL、真实 `feedback_T1001.log`、`/odom`、`/imu/data`、`/battery`、operator HIL report、真实 2D LiDAR / ToF SKU/source/receipt/procurement/installation/wiring/power/calibration/HIL-entry。
- PR #5 `PRRT_kwDOSWB9286CJ3tX` 仍按 unresolved / `is_resolved=false` / material pending 处理；comment id `3269642220` 不是硬件 proof。
