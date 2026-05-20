# Field Evidence Rerun Execution Pack Tech Done

## Worker 1 - Autonomy Algorithm Engineer

- 自主能力目标和抓手：新增 `field_evidence_rerun_execution_pack` PC-only gate，消费 `field_evidence_rerun_queue` artifact/summary，把 queue candidate 转成 field owner 可执行的 metadata-only execution pack。
- 改动文件和接口影响：
  - `pc-tools/evidence/field_evidence_rerun_execution_pack.py`
  - `tests/test_field_evidence_rerun_execution_pack.py`
  - `pc-tools/README.md`
  - `docs/interfaces/evidence_contracts.md`
  - `sprints/2026.05.20_18-19_field-evidence-rerun-execution-pack/tech-done.md`
- 实现内容：新增 schema `trashbot.field_evidence_rerun_execution_pack.v1`、summary schema `trashbot.field_evidence_rerun_execution_pack_summary.v1`、Robot safe alias `robot_diagnostics_field_evidence_rerun_execution_pack_summary`，边界固定为 `software_proof_docker_field_evidence_rerun_execution_pack_gate`。输出 `execution_steps`、`material_templates`、`owner_handoff`、`fail_thresholds`、`pass_thresholds`、`backfill_instructions` 和 `safe_copy`，并强制保留 `source=software_proof`、`not_proven`、`safe_to_control=false`、`delivery_success=false`、`primary_actions_enabled=false`。
- 数据、样本或调试输出变化：单测 fixture 覆盖 ready queue、missing/unsupported queue、non-ready backfill、same evidence_ref mismatch、unsafe raw copy/success claim、wrapper/nested artifact。未新增真实现场材料、Nav2 log、硬件/HIL、O5 external proof 或真实 phone/browser evidence。
- 验证结果：
  - `python3 -m py_compile pc-tools/evidence/field_evidence_rerun_execution_pack.py` passed。
  - `python3 -m unittest tests.test_field_evidence_rerun_execution_pack` passed：`Ran 5 tests in 0.146s OK`。
  - `python3 pc-tools/evidence/field_evidence_rerun_execution_pack.py --help` passed，显示 `--queue-json`、`--evidence-ref`、`--output`、`--summary-output`、`--once-json`。
  - `rg -n "field_evidence_rerun_execution_pack|software_proof_docker_field_evidence_rerun_execution_pack_gate|safe_to_control=false|delivery_success=false|primary_actions_enabled=false|not_proven" ...` passed。
  - `git diff --check -- pc-tools/evidence/field_evidence_rerun_execution_pack.py tests/test_field_evidence_rerun_execution_pack.py pc-tools/README.md docs/interfaces/evidence_contracts.md sprints/2026.05.20_18-19_field-evidence-rerun-execution-pack` passed。
- 失败定位：第一次单测发现最终 success/control 扫描误伤内部说明里的 `field pass` / `HIL pass` 文案，已改为不触发成功断言的边界说明并重新通过单测。
- 剩余风险：本 worker 只完成 PC gate 和 canonical artifact；Robot diagnostics alias 与 mobile/web read-only panel 仍由其他 workers 收口。本产物仍是 `software_proof` / `not_proven`，不证明真实现场复跑、真实 Nav2、真实 route/elevator field pass、HIL、O5 external proof、delivery success、PR #5 resolved 或真实 phone/browser evidence。

## Worker 2 - Robot Platform Engineer

- Run time: 2026-05-20 18:18:37 CST
- Scope: Robot diagnostics safe alias for `field_evidence_rerun_execution_pack`.
- Plan command path variance:
  - The tech plan's historical `pc-tools/operator_gateway_diagnostics.py` path does not exist in the current repo.
  - Current diagnostics implementation and focused test paths are `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py` and `onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`.
- Actual changes:
  - `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py`: added `field_evidence_rerun_execution_pack` constants, fail-closed default summary, source contract, safe alias summarizer, diagnostics payload input/ref/env wiring, raw latest-status stripping, and `robot_diagnostics_field_evidence_rerun_execution_pack_summary` payload alias.
  - `onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`: added focused coverage for canonical summary consumption, nested summary lookup, missing summary, unsupported schema/boundary, `safe_evidence_ref` mismatch, unsafe enabled/raw payload blocking, latest-status raw stripping, and sensitive text exclusion.
  - `docs/interfaces/ros_runtime_contracts.md`: documented the new Robot-visible safe alias, allowed fields, preserved fail-closed flags, and non-claims.
- Implementation notes:
  - The alias accepts only `trashbot.field_evidence_rerun_execution_pack_summary.v1` or a direct artifact that contains that sanitized nested summary.
  - Raw execution-pack artifacts without sanitized summary remain `missing_summary`.
  - The safe output preserves `source=software_proof`, `not_proven`, `safe_to_control=false`, `delivery_success=false`, `primary_actions_enabled=false`, and `software_proof_docker_field_evidence_rerun_execution_pack_gate`.
  - It omits raw artifact bodies, ROS topic names, `/cmd_vel`, serial/UART/WAVE ROVER details, credentials, local paths, checksums, tracebacks, HIL/pass wording, ACK/cursor/control claims, and delivery success claims.
- Validation:
  - `test -f pc-tools/operator_gateway_diagnostics.py`: failed as expected; historical plan path is absent, so the current onboard path was used.
  - `python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`: passed.
  - `PYTHONPATH=onboard/src/ros2_trashbot_behavior python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`: first run failed because the generic unsafe-key helper treated `execution_pack_status` / `backfill_instructions` as unsafe due the `ack` substring in `pack` / `backfill`; fixed with an execution-pack-specific unsafe-field helper, then reran and passed: `Ran 234 tests in 0.736s`, `OK`.
  - `rg -n "robot_diagnostics_field_evidence_rerun_execution_pack_summary|field_evidence_rerun_execution_pack|software_proof_docker_field_evidence_rerun_execution_pack_gate|safe_to_control=false|delivery_success=false|primary_actions_enabled=false|not_proven" onboard/src/ros2_trashbot_behavior docs/interfaces/ros_runtime_contracts.md sprints/2026.05.20_18-19_field-evidence-rerun-execution-pack`: passed; matched diagnostics implementation, focused tests, runtime contract doc, sprint plan, and tech-done evidence.
  - `git diff --check -- onboard/src/ros2_trashbot_behavior docs/interfaces/ros_runtime_contracts.md sprints/2026.05.20_18-19_field-evidence-rerun-execution-pack`: passed.
- Remaining risk:
  - This is Robot diagnostics software proof only. It does not prove real field rerun, real Nav2/fixed-route runtime, real route/elevator field pass, real task record, real phone/browser validation, WAVE ROVER/UART/HIL, dropoff/cancel completion, Objective 5 external proof, or delivery success.
- Collaboration:
  - Autonomy owns the canonical PC gate/artifact semantics.
  - Full-Stack owns mobile read-only rendering.
  - Product should do final conservative OKR/progress closeout after all workers return.

## Worker 3 - User Touchpoint Full-Stack Engineer

- 用户触点目标和抓手：在 `mobile/web` 增加只读“现场证据复跑执行包”panel，让现场 owner 和支持同学能在手机入口看到 execution steps、material templates、owner handoff、fail/pass thresholds 和 backfill instructions。
- 改动文件和接口影响：
  - `mobile/web/app.js`
  - `mobile/web/fixtures/status.json`
  - `mobile/web/test_mobile_web_entrypoint.py`
  - `docs/product/mobile_user_flow.md`
- 实现内容：优先消费 `robot_diagnostics_field_evidence_rerun_execution_pack_summary`，并兼容 safe summary / nested summary；展示 `software_proof_docker_field_evidence_rerun_execution_pack_gate`、`not_proven`、`safe_to_control=false`、`delivery_success=false`、`primary_actions_enabled=false`。Start Delivery / Confirm Dropoff / Cancel gating 保持不变。
- 验证结果：
  - `node --check mobile/web/app.js` passed。
  - `python3 -m unittest mobile/web/test_mobile_web_entrypoint.py` passed：`Ran 175 tests OK`。
  - `python3 -m json.tool mobile/web/fixtures/status.json >/dev/null` passed。
  - required `rg` and scoped `git diff --check` passed。
- 剩余风险：本 worker 只完成 phone-safe local fixture / static UI software proof；不证明真实 phone/browser、真实 PWA prompt/userChoice、production app、真实 field rerun、真实 Nav2/fixed-route、dropoff/cancel completion、delivery result、WAVE ROVER/UART/HIL、O5 external proof 或 PR #5 resolved。

## Product Closeout - OKR Owner

- Run time: 2026-05-20 18:22 CST
- 用户价值和产品北极星：本轮把现场复跑队列转成可执行 package，让 field owner 下次真实复跑时知道必须采集哪些材料、用哪个 same safe `evidence_ref`、什么情况下 fail/pass、如何 backfill。北极星仍是 phone-first trash delivery robot，但本轮只推进证据采集可执行性，不推进真实送达。
- OKR 映射：
  - Objective 5 仍约 68%，本轮不是 O5 external proof。
  - Objective 1 仍约 81%，本轮不是 WAVE ROVER/UART/HIL，也不解决 PR #5 `PRRT_kwDOSWB9286CJ3tX`。
  - Objective 2 / Objective 3 / Objective 4 仍约 99%，本轮只补 O2/O3/O4 现场材料复跑 execution-pack software proof。
- KR 拆解和本轮核心抓手：PC gate 产出 canonical execution pack；Robot diagnostics 产出 safe alias；mobile/web 只读展示 execution pack；Product closeout 只做证据边界、OKR、progress log 和 sprint final。
- 需要做什么和责任 Engineer：
  - Autonomy Algorithm Engineer：PC gate、artifact/schema、focused tests、evidence contract。
  - Robot Platform Engineer：Robot diagnostics safe alias、focused diagnostics tests、runtime contract。
  - User Touchpoint Full-Stack Engineer：mobile/web read-only panel、fixture/test、mobile user flow。
  - Product Manager / OKR Owner：本 closeout、side2side、final、OKR 和 progress log。
- docs 同步确认：Engineering workers 已同步 `docs/interfaces/evidence_contracts.md`、`docs/interfaces/ros_runtime_contracts.md`、`docs/product/mobile_user_flow.md`；Product closeout 同步 `docs/process/okr_progress_log.md`。
- 证据边界：`software_proof_docker_field_evidence_rerun_execution_pack_gate`；保留 `source=software_proof`、`not_proven`、`safe_to_control=false`、`delivery_success=false`、`primary_actions_enabled=false`。
- 明确非证明：不是真实 field rerun、真实 Nav2/fixed-route、真实 task record、route completion signal、真实电梯门/楼层/人工协助、dropoff/cancel completion、delivery result、真实 phone/browser、WAVE ROVER/UART/HIL、O5 external proof、PR #5 thread resolved 或 delivery success。
- PR/review 证据：PR #5 thread `PRRT_kwDOSWB9286CJ3tX` 仍 unresolved / material pending，comment `3269642220` 只是 published reply，不是 hardware proof；PR #6 是 README docs-only。
- Product closeout validation summary：见 `side2side_check.md` 和 `final.md`；集成围栏复跑通过。
- 剩余风险：下一步仍需要现场 owner 回填同一 safe `evidence_ref` 的真实 task record、真实 Nav2/fixed-route runtime log、route completion signal、真实电梯门/楼层/人工协助、dropoff/cancel completion、delivery result 和真实 phone/browser evidence；O1/O5 仍需真实硬件或外部云材料后才能提高完成度。
