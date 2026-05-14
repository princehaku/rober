# Sprint 2026.05.15_07-08 Route Task Field Run Evidence Kit - Tech Done

sprint_type: epic

## 1. 实际改动

本轮按 Task A/B/C/D 完成 `software_proof_docker_route_task_field_run_evidence_kit_gate` 软件证明闭环。Product closeout 仅更新本 sprint 收口、`OKR.md` 和 `docs/process/okr_progress_log.md`，未改工程代码。

Task A - Autonomy Algorithm Engineer：

- 新增 `pc-tools/evidence/route_task_field_run_evidence_kit.py` 与 `pc-tools/evidence/test_route_task_field_run_evidence_kit.py`。
- 更新 `pc-tools/README.md` 与 `docs/navigation/fixed_route_workflow.md`。
- Evidence kit schema 为 `trashbot.route_task_field_run_evidence_kit.v1`，boundary 为 `software_proof_docker_route_task_field_run_evidence_kit_gate`。
- 输出 material directory manifest、capture templates、commands to run/rerun、same `evidence_ref` verdict、missing materials、operator handoff、robot diagnostics summary、mobile readonly summary、`not_proven`、`primary_actions_enabled=false`、`delivery_success=false`。

Task B - Robot Platform Engineer：

- 更新 `operator_gateway_diagnostics.py`、`test_operator_gateway_diagnostics.py` 与 `docs/interfaces/ros_contracts.md`。
- Diagnostics metadata-only 消费 `route_task_field_run_evidence_kit` / summary，支持 explicit ref 与 `TRASHBOT_ROUTE_TASK_FIELD_RUN_EVIDENCE_KIT` / `_SUMMARY`。
- 校验 schema/boundary，保持 fail-closed，不触发 collect/dropoff/cancel、ACK、Nav2、HIL、dropoff/cancel completion 或 delivery success。

Task C - User Touchpoint Full-Stack Engineer：

- 更新 `mobile/web`、fixture、mobile entrypoint test 与 `docs/product/mobile_user_flow.md`。
- 新增只读“路线现场证据包” panel，展示 kit verdict、safe `evidence_ref`、material manifest、capture templates、commands、missing materials、operator handoff、`not_proven`、`delivery_success=false`、`primary_actions_enabled=false` 和 boundary。
- 不改变 Start/Confirm/Cancel gating，不读取 raw artifact、本机路径、token、serial/UART、`/cmd_vel`、checksum 或 traceback。

Task D - Product Manager / OKR Owner：

- 创建本文件、`side2side_check.md`、`final.md`。
- 更新 `OKR.md` 4.1 快照与当前最高优先级。
- 更新 `docs/process/okr_progress_log.md` 追加本轮记录。

## 2. 验证结果

工程 worker 已报告的验证结果：

- Task A：`python3 -m py_compile pc-tools/evidence/route_task_field_run_evidence_kit.py pc-tools/evidence/test_route_task_field_run_evidence_kit.py` pass；`python3 pc-tools/evidence/test_route_task_field_run_evidence_kit.py` -> `Ran 6 tests ... OK`；CLI `--help` pass；required `rg` pass；scoped diff check pass。
- Task B：`python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py` pass；`python3 onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py` -> `Ran 69 tests in 0.051s OK`；required `rg` pass；scoped diff check pass。
- Task C：`python3 mobile/test_mobile_web_entrypoint.py` -> `38 tests OK`；`python3 -m py_compile mobile/test_mobile_web_entrypoint.py` pass；`node --check mobile/web/app.js` pass；required `rg` pass；scoped diff check pass。

Task D closeout 验收命令由 Product closeout 运行并记录在最终回复中：

```bash
test -f sprints/2026.05.15_07-08_route-task-field-run-evidence-kit/tech-done.md
test -f sprints/2026.05.15_07-08_route-task-field-run-evidence-kit/side2side_check.md
test -f sprints/2026.05.15_07-08_route-task-field-run-evidence-kit/final.md
rg -n "software_proof_docker_route_task_field_run_evidence_kit_gate|Objective 2|Objective 3|Objective 5" OKR.md docs/process/okr_progress_log.md sprints/2026.05.15_07-08_route-task-field-run-evidence-kit
git diff --check -- OKR.md docs/process/okr_progress_log.md sprints/2026.05.15_07-08_route-task-field-run-evidence-kit
```

## 3. 偏差与边界

- 本轮没有真实 Nav2/fixed-route 运行、真实路线采集、WAVE ROVER、串口/UART、HIL、同一 `evidence_ref` 上车实机复账、真实 dropoff/cancel completion 或真实 delivery success。
- 本轮没有真实手机/browser、production app、真实 PWA prompt/user choice，也没有 Objective 5 的公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue 或 worker/migration 外部证明。
- Objective 2 与 Objective 3 只因现场证据包软件准备层更完整，从约 66% 保守上调到约 67%。Objective 5 保持约 66%，Objective 1/4 保持不变。

## 4. 剩余风险

- Evidence kit 仍是现场执行前的材料组织与回填清单，不是现场执行结果。
- 下一步若要继续提升 O2/O3，必须拿到真实 Nav2/fixed-route、真实路线采集、同一 `evidence_ref` 的上车实机复账、真实 dropoff/cancel completion、真实 cancel completion 或 delivery success。
- 下一步若要提升 Objective 5，必须拿到真实外部材料，不能继续用本地 metadata 替代。
