# Sprint 2026.05.16_02-03 Elevator Route Evidence Reconciliation - Tech Done

sprint_type: epic

## 1. 用户价值和产品北极星

本轮把电梯 assisted delivery 的 phase evidence 与 route task completion signal 放到同一 `evidence_ref` 复账链里，减少现场同学手工比对多个 artifact 的成本，避免把 rehearsal evidence、ACK、diagnostics summary 或 mobile 只读展示误读成真实送达成功。

产品北极星仍是：普通手机用户交付垃圾后，小车可沿固定路线和电梯 assisted delivery 主链路完成可验证、可复盘、可解释的送达流程。本轮只推进复账能力，不宣称真实交付完成。

## 2. OKR 映射和 KR 更新

- Objective 3：从约 73% 保守上调到约 74%。理由是 route completion signal 与电梯 phase evidence 已进入同一 `evidence_ref` 复账 gate，支撑固定路线/任务材料链可复核。
- Objective 2：从约 74% 保守上调到约 75%。理由是电梯 assisted delivery 主链路现在能和 route completion signal 对齐复账，支撑 KR5/KR6/KR7 的证据闭环。
- Objective 4：从约 74% 保守上调到约 75%。理由是手机端新增只读“电梯路线证据复账” panel，能解释复账结果、missing/mismatch 和下一步补证动作。
- Objective 1：保持约 73%。本轮未触碰 WAVE ROVER、UART、Orange Pi、真实串口或 HIL。
- Objective 5：保持约 66%。本轮没有真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue connectivity、worker/migration 或其他外部材料；not real Objective 5 external proof。

## 3. 本轮核心抓手

核心抓手是 `software_proof_docker_elevator_route_evidence_reconciliation_gate`：

- PC CLI 产出 `trashbot.elevator_route_evidence_reconciliation.v1` artifact 与 summary。
- Robot diagnostics metadata-only 消费 artifact/summary，支持 explicit ref 和 `TRASHBOT_ELEVATOR_ROUTE_EVIDENCE_RECONCILIATION` / `_SUMMARY`。
- `mobile/web` 只读展示 phone-safe summary，不改变 Start / Confirm Dropoff / Cancel gating。

## 4. 实际改动

Task A - Autonomy Algorithm Engineer：

- 新增 `pc-tools/evidence/elevator_route_evidence_reconciliation.py`。
- 新增 `pc-tools/evidence/test_elevator_route_evidence_reconciliation.py`。
- 更新 `pc-tools/README.md`、`docs/navigation/fixed_route_workflow.md`、`docs/product/elevator_assisted_delivery.md`。
- 输出 `schema=trashbot.elevator_route_evidence_reconciliation.v1` / summary，固定 `source=software_proof`、`same_evidence_ref_required=true`、`delivery_success=false`、`primary_actions_enabled=false`、`not_proven` 和 `evidence_boundary=software_proof_docker_elevator_route_evidence_reconciliation_gate`。
- 首轮 unsafe copy 自触发后已修复并重跑验证。

Task B - Robot Platform Engineer：

- 更新 `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py`。
- 更新 `onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`。
- 更新 `docs/interfaces/ros_contracts.md`。
- 新增 diagnostics metadata-only `elevator_route_evidence_reconciliation` / summary，支持 explicit ref 和环境变量来源。
- 固定 `delivery_success=false`、`primary_actions_enabled=false`，不触发 collect/dropoff/cancel、ACK、Nav2、HIL 或 delivery success claim。

Task C - User Touchpoint Full-Stack Engineer：

- 更新 `mobile/web/app.js`。
- 更新 `mobile/fixtures/mobile_web_status.fixture.json`。
- 更新 `mobile/test_mobile_web_entrypoint.py`。
- 更新 `docs/product/mobile_user_flow.md`。
- 新增只读“电梯路线证据复账” panel，展示 safe `evidence_ref`、same evidence ref 状态、source states、missing/mismatch、operator next steps、not_proven 和 boundary。
- Start / Confirm Dropoff / Cancel gating 未改变。

Product Manager / OKR Owner：

- 新增本文件、`side2side_check.md`、`final.md`。
- 更新 `OKR.md` 4.1 和第 6 节。
- 更新 `docs/process/okr_progress_log.md` 顶部。

## 5. 验证结果

工程 worker 验证摘要：

- Task A：`py_compile` pass；`pc-tools/evidence/test_elevator_route_evidence_reconciliation.py` 输出 `Ran 8 tests in 0.018s OK`；CLI `--help` pass；required `rg` pass；scoped `git diff --check` pass。
- Task B：`operator_gateway_diagnostics.py` `py_compile` pass；`test_operator_gateway_diagnostics.py` 输出 `Ran 81 tests in 0.070s OK`；required `rg` pass；scoped `git diff --check` pass。
- Task C：`mobile/test_mobile_web_entrypoint.py` 输出 `Ran 45 tests in 0.142s OK`；`py_compile` pass；`node --check mobile/web/app.js` pass；required `rg` pass；scoped `git diff --check` pass。

Product closeout 验收命令：

```bash
rg -n "elevator_route_evidence_reconciliation|software_proof_docker_elevator_route_evidence_reconciliation_gate|Objective 3|Objective 5|not real|不证明|delivery_success=false" sprints/2026.05.16_02-03_elevator-route-evidence-reconciliation OKR.md docs/process/okr_progress_log.md
git diff --check -- sprints/2026.05.16_02-03_elevator-route-evidence-reconciliation OKR.md docs/process/okr_progress_log.md
```

实际执行结果见本轮最终回复；Product closeout 命令在文档更新后通过。

## 6. 优先级、责任 Engineer 与验收口径

- P0 Autonomy：同一 `evidence_ref` 复账 artifact / summary 必须 fail closed，责任人 `autonomy-engineer`。
- P0 Robot：diagnostics 只能 metadata-only 消费，不触发任何真实动作，责任人 `robot-software-engineer`。
- P0 Full-stack：手机端只读解释复账结果，不放行控制，不泄漏 raw artifact、本机路径、serial/UART、WAVE ROVER、token、ROS topic 或 traceback，责任人 `full-stack-software-engineer`。
- P0 Product：OKR 只上调 O2/O3/O4，不上调 O5，并把证据边界写入 sprint closeout、OKR 和进度日志，责任人 `product-okr-owner`。

## 7. 失败定位

已知实现阶段失败定位：Task A 初次 unsafe copy 自触发，已由 Autonomy 修复并重跑验证通过。Product closeout 阶段未发现新的验证失败。

## 8. 剩余风险和证据链缺口

本轮 `software_proof_docker_elevator_route_evidence_reconciliation_gate` 只证明 Docker/local PC CLI、Robot diagnostics metadata-only consumption 和 mobile read-only panel 可复核同一 `evidence_ref` 下的电梯 phase evidence 与 route completion signal。

它不证明真实电梯、真实 Nav2/fixed-route、真实路线采集、WAVE ROVER/UART/HIL、真实手机/browser、真实 dropoff/cancel completion、delivery success 或 Objective 5 external proof。下一步若仍无 O5 外部材料，应优先做 O2/O3 的真实现场/上车复账：真实电梯门状态、目标楼层确认、人工协助记录、Nav2/fixed-route runtime log、task record、completion signal、WAVE ROVER/HIL 与同一 `evidence_ref` 的上车实机材料。
