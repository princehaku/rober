# Sprint 2026.05.17_14-15 Route Task Result Acceptance Packet - Tech Done

sprint_type: epic

## Task A - Autonomy PC Gate

自主能力目标和本轮抓手：新增 PC gate `route_task_field_retest_result_acceptance_packet`，把上一轮 `route_task_field_retest_result_reconciliation` 的 safe lineage、八类 required result materials、缺口、owner handoff、rerun commands 和 pass/fail criteria 汇总成 acceptance packet artifact / summary。边界保持 `software_proof_docker_route_task_field_retest_result_acceptance_packet_gate`、`not_proven`、`delivery_success=false`、`primary_actions_enabled=false`。

改动文件和接口影响：

- `pc-tools/evidence/route_task_field_retest_result_acceptance_packet.py`：新增 artifact schema `trashbot.route_task_field_retest_result_acceptance_packet.v1` 和 summary schema `trashbot.route_task_field_retest_result_acceptance_packet_summary.v1`。
- `pc-tools/evidence/test_route_task_field_retest_result_acceptance_packet.py`：新增 focused unittest，覆盖 ready、nested summary、blocked reconciliation、missing/bad JSON、unsupported schema、evidence_ref mismatch、弱类型 same-ref、unsafe copy、success/control claim。
- `pc-tools/README.md`：补 PC gate 用法、schema、边界和 fail-closed 说明。
- `docs/navigation/fixed_route_workflow.md`：补固定路线 result acceptance packet 工作流。
- 接口影响：新增 PC-only JSON artifact / summary，不新增 ROS topic/service/action，不读取 raw handoff artifact，不改变 Robot/mobile 控制语义。

实现内容：gate 只消费 `route_task_field_retest_result_reconciliation` artifact / summary / wrapper / nested JSON 的白名单字段，汇总八类 result material status、safe lineage、missing/mismatch、owner handoff、rerun commands、pass/fail criteria 和 safe copy。缺输入、bad JSON、unsupported schema/boundary、safe `evidence_ref` 不一致、`same_evidence_ref_required` 非严格 true、reconciliation 未 ready、缺材料、unsafe copy、success/control claim 均 fail closed。

测试、dry-run 或上车验证结果：

- `python3 -m py_compile pc-tools/evidence/route_task_field_retest_result_acceptance_packet.py`：通过，无输出。
- `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest pc-tools/evidence/test_route_task_field_retest_result_acceptance_packet.py`：通过，`Ran 5 tests in 0.052s`，`OK`。第一轮失败定位为输出自身的 hardware boundary 文案含 forbidden copy 关键词，被最终安全扫描正确拦截；已改成抽象 `hardware_transport` / `hardware_feedback` 表述并重跑通过。
- `python3 pc-tools/evidence/route_task_field_retest_result_acceptance_packet.py --help`：通过，显示 `--reconciliation-json`、`--evidence-ref`、`--output`、`--summary-output`、`--once-json`。
- `rg -n "route_task_field_retest_result_acceptance_packet|route_task_field_retest_result_reconciliation|software_proof_docker_route_task_field_retest_result_acceptance_packet_gate|not_proven|delivery_success=false|primary_actions_enabled=false|pass/fail criteria|rerun commands" pc-tools/evidence pc-tools/README.md docs/navigation/fixed_route_workflow.md sprints/2026.05.17_14-15_route-task-result-acceptance-packet`：通过，命中新增 gate、README、navigation workflow 和本 sprint 留档。
- `git diff --check -- pc-tools/evidence/route_task_field_retest_result_acceptance_packet.py pc-tools/evidence/test_route_task_field_retest_result_acceptance_packet.py pc-tools/README.md docs/navigation/fixed_route_workflow.md sprints/2026.05.17_14-15_route-task-result-acceptance-packet/tech-done.md`：通过，无输出。

数据、样本或调试输出变化：新增 acceptance packet artifact / summary 输出，八类材料仍是 metadata-only；未新增真实 Nav2/fixed-route、serial/UART、WAVE ROVER、云、4G、OSS/CDN、DB/queue 或真实手机/browser 输出。

剩余风险和下一步能力建设建议：当前仍是 Docker/local software proof；pass/fail criteria 只是下一次现场复测判断口径，不证明真实 field pass、真实 route/elevator、dropoff/cancel completion、delivery success、HIL 或真实手机/browser。下一步应由 Robot / Full-stack 只读消费该 summary，并由 Product closeout 在 Task A/B/C 全部证据返回后更新最终 OKR 口径。

## Task B - Robot Platform Engineer

### 实际改动

- `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py`：新增 `route_task_field_retest_result_acceptance_packet` / summary 只读 diagnostics consumer，支持 explicit ref、env、top-level status 和 nested diagnostics summary 输入；输出 packet status、safe `evidence_ref`、missing material summary、owner handoff、rerun command summary、pass/fail criteria summary、safe copy、`not_proven`、`delivery_success=false`、`primary_actions_enabled=false`。
- `onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`：新增 acceptance packet diagnostics 正向和 fail-closed 单测，覆盖 file/env/nested/missing/unsupported/missing required fields/unsafe copy 和控制隔离。
- `docs/interfaces/ros_contracts.md`：补充 Robot diagnostics acceptance packet contract，明确 `software_proof_docker_route_task_field_retest_result_acceptance_packet_gate`、白名单字段和 fail-closed 边界。

### 验证结果

- `python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py`：通过，无输出。
- `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`：通过，`Ran 146 tests in 0.219s`，`OK`。第一轮失败定位为 nested diagnostics source 直接携带 artifact schema + 白名单 summary 字段时被误判 `missing_summary`；已收窄修复为只在 packet schema 且存在白名单 summary 字段时接受该形态，并重跑通过。
- `rg -n "route_task_field_retest_result_acceptance_packet|route_task_field_retest_result_reconciliation|software_proof_docker_route_task_field_retest_result_acceptance_packet_gate|not_proven|delivery_success=false|primary_actions_enabled=false|pass/fail criteria|rerun commands" onboard/src/ros2_trashbot_behavior docs/interfaces sprints/2026.05.17_14-15_route-task-result-acceptance-packet`：通过，命中 Robot diagnostics、单测、接口文档和 sprint 留档。
- `git diff --check -- onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py docs/interfaces/ros_contracts.md sprints/2026.05.17_14-15_route-task-result-acceptance-packet/tech-done.md`：通过，无输出。

### 剩余风险

- 本 Task B 只提供 Robot diagnostics metadata-only 消费，不证明真实 route/elevator field pass、Nav2 runtime、dropoff/cancel completion、delivery result、HIL、真实手机/browser 或 Objective 5 external proof。
- 不改变 `task_orchestrator`、action result、Start/Dropoff/Cancel、ACK、cursor 或 Nav2 控制语义。

## Task C - User Touchpoint Full-Stack Engineer

### 实际改动

- `mobile/web/app.js`：新增只读“路线任务结果验收包” panel，消费 `route_task_field_retest_result_acceptance_packet` / summary / Robot diagnostics compatible summary，展示 packet status、safe lineage、八类 result materials summary、missing items、owner handoff、rerun commands、pass/fail criteria、safe copy、`not_proven`、`delivery_success=false` 和 `primary_actions_enabled=false`。
- `mobile/web/fixtures/status.json`：补 acceptance packet fixture，使手机入口能展示最新 software-proof summary。
- `mobile/web/test_mobile_web_entrypoint.py`：新增 focused assertion，确认 panel、copy/export 白名单和控制 gating 边界。
- `docs/product/mobile_user_flow.md`：补 phone-safe acceptance packet 说明，明确该 panel 只解释下一次现场复测材料和验收口径，不代表真实送达或现场通过。

### 验证结果

- `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest mobile.web.test_mobile_web_entrypoint`：通过，`Ran 42 tests`，`OK`。
- `node --check mobile/web/app.js`：通过，无输出。
- `rg -n "route_task_field_retest_result_acceptance_packet|route_task_field_retest_result_reconciliation|software_proof_docker_route_task_field_retest_result_acceptance_packet_gate|not_proven|delivery_success=false|primary_actions_enabled=false|pass/fail criteria|rerun commands" mobile/web docs/product sprints/2026.05.17_14-15_route-task-result-acceptance-packet`：通过，命中 mobile panel、fixture、测试、产品文档和 sprint 留档。
- `git diff --check -- mobile/web/app.js mobile/web/fixtures/status.json mobile/web/test_mobile_web_entrypoint.py docs/product/mobile_user_flow.md sprints/2026.05.17_14-15_route-task-result-acceptance-packet/tech-done.md`：通过，无输出。

### 剩余风险

- 本 Task C 只提供 local mobile/web 只读解释层，不证明真实手机/browser、production app、真实 PWA prompt/user choice、真实 route/elevator field pass、真实 Nav2/fixed-route、dropoff/cancel completion、delivery result、HIL 或 Objective 5 external proof。
- Start Delivery、Confirm Dropoff、Cancel gating 未改变，panel 不发送 robot command，不读取 raw artifact。

## Task D - Product Closeout

### 用户价值和产品北极星

北极星仍是普通手机用户能把垃圾交给小车，并在跨楼层或固定路线场景中获得可解释、可恢复、可复盘的送达体验。本轮 acceptance packet 的用户价值是把工程复账翻译成现场/支持/手机都能执行的验收包：缺哪八类 result materials、谁负责、如何重跑、什么算 pass/fail，以及为什么当前仍是 `not_proven`。

### OKR 映射和 KR 更新

- Objective 2：O2 KR5 / KR6 / KR7 获得保守进展；PR #4 route/elevator result materials 现在可从 result reconciliation 进入 acceptance packet，门状态、目标楼层确认、人工协助记录、dropoff/cancel completion 和 delivery result 的现场验收口径更清晰。
- Objective 3：O3 KR2 / KR3 / KR4 获得保守进展；Nav2/fixed-route runtime log、route completion signal、task record 等材料被纳入 packet、rerun commands 和 pass/fail criteria。
- Objective 5：不更新；本轮没有真实 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue connectivity、production worker/migration/cutover 或真实手机/browser 证据。

### Product 收口改动

- `OKR.md`：将最新 sprint 更新为 `2026.05.17_14-15_route-task-result-acceptance-packet`，Objective 2 / Objective 3 各从约 94% 保守上调到约 95%，Objective 1 / 4 / 5 保持不变，并把 `route_task_field_retest_result_acceptance_packet` 加入 stop-rule 边界。
- `docs/process/okr_progress_log.md`：新增本轮 14-15 进度日志，记录 A/B/C 验证结果、失败修复和证据边界。
- `side2side_check.md`：补阶段验收对照。
- `final.md`：补 sprint final，回顾 OKR 最低优先级核对、O5 stop rule、PR #4 / PR #5 边界和剩余风险。

### Product 验收结果

- Task A / B / C 的 focused verification 均已返回通过，并均保留 `software_proof_docker_route_task_field_retest_result_acceptance_packet_gate`、`not_proven`、`delivery_success=false`、`primary_actions_enabled=false`。
- 本轮 closeout 不修改工程代码、测试代码、mobile 实现代码、Robot/Autonomy 文件或硬件配置。

### 剩余风险

- 本轮只证明 Docker/local software-proof acceptance packet chain，不是真实 route/elevator field pass、真实 Nav2/fixed-route、真实 dropoff/cancel completion、delivery result、HIL、真实手机/browser、Objective 5 external proof 或 PR #5 真实硬件材料。
- 下一步若要继续提高 O2/O3，需要真实现场材料回填：Nav2/fixed-route runtime log、route completion signal、task record、door state、target floor confirmation、human assistance note、dropoff/cancel completion 和 delivery result，并保持同一 `evidence_ref`。
