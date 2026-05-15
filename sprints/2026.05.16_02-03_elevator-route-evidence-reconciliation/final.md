# Sprint 2026.05.16_02-03 Elevator Route Evidence Reconciliation - Final

sprint_type: epic

## 1. 收口结论

本轮完成 `software_proof_docker_elevator_route_evidence_reconciliation_gate`。Autonomy、Robot、Full-stack 三个 worker 分别完成 PC evidence reconciliation CLI、Robot diagnostics metadata-only consumption 和 `mobile/web` 只读“电梯路线证据复账” panel；Product 完成本 sprint closeout、`OKR.md` 和 `docs/process/okr_progress_log.md` 更新。

该 sprint 把电梯 phase evidence 与 route task completion signal 放到同一 `evidence_ref` 复账链，解决上一轮“主链路已有 rehearsal evidence anchor，但尚未和路线完成信号同 run 复账”的缺口。

## 2. OKR 进度更新

- Objective 3：约 73% -> 约 74%。route completion signal 与电梯 phase evidence 已进入同一 `evidence_ref` 复账 gate。
- Objective 2：约 74% -> 约 75%。电梯 assisted delivery 主链路现在能和 route completion signal 复账。
- Objective 4：约 74% -> 约 75%。手机端可以解释复账结果、missing/mismatch、operator next steps 和 boundary。
- Objective 1：保持约 73%。没有真实 WAVE ROVER/UART/HIL 或硬件协议新证据。
- Objective 5：保持约 66%。没有真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue connectivity、worker/migration 或其他外部材料；not real Objective 5 external proof。

## 3. 实际改动文件

工程 worker 改动摘要：

- `pc-tools/evidence/elevator_route_evidence_reconciliation.py`
- `pc-tools/evidence/test_elevator_route_evidence_reconciliation.py`
- `pc-tools/README.md`
- `docs/navigation/fixed_route_workflow.md`
- `docs/product/elevator_assisted_delivery.md`
- `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py`
- `onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`
- `docs/interfaces/ros_contracts.md`
- `mobile/web/app.js`
- `mobile/fixtures/mobile_web_status.fixture.json`
- `mobile/test_mobile_web_entrypoint.py`
- `docs/product/mobile_user_flow.md`

Product closeout 改动：

- `sprints/2026.05.16_02-03_elevator-route-evidence-reconciliation/tech-done.md`
- `sprints/2026.05.16_02-03_elevator-route-evidence-reconciliation/side2side_check.md`
- `sprints/2026.05.16_02-03_elevator-route-evidence-reconciliation/final.md`
- `OKR.md`
- `docs/process/okr_progress_log.md`

## 4. 验证结果

Worker 验证摘要：

- Task A Autonomy：`py_compile` pass；`Ran 8 tests in 0.018s OK`；CLI `--help` pass；required `rg` pass；scoped diff check pass。
- Task B Robot：`py_compile` pass；`Ran 81 tests in 0.070s OK`；required `rg` pass；scoped diff check pass。
- Task C Full-stack：`Ran 45 tests in 0.142s OK`；`py_compile` pass；`node --check mobile/web/app.js` pass；required `rg` pass；scoped diff check pass。

Product closeout 验收：

- `rg -n "elevator_route_evidence_reconciliation|software_proof_docker_elevator_route_evidence_reconciliation_gate|Objective 3|Objective 5|not real|不证明|delivery_success=false" sprints/2026.05.16_02-03_elevator-route-evidence-reconciliation OKR.md docs/process/okr_progress_log.md`：通过，关键证据边界、Objective 3 / Objective 5、`not real`、`不证明`、`delivery_success=false` 均可检索。
- `git diff --check -- sprints/2026.05.16_02-03_elevator-route-evidence-reconciliation OKR.md docs/process/okr_progress_log.md`：通过，无 whitespace error。

## 5. 证据边界

本轮 `software_proof_docker_elevator_route_evidence_reconciliation_gate` 只证明 Docker/local PC CLI、Robot diagnostics metadata-only consumption 和 mobile read-only panel。它不证明真实电梯、真实 Nav2/fixed-route、WAVE ROVER/UART/HIL、真实手机/browser、真实 dropoff/cancel completion、delivery success 或 Objective 5 external proof。

`delivery_success=false`、`primary_actions_enabled=false` 和 `not_proven` 是本轮必须保留的产品边界；reconciliation verdict、diagnostics summary、mobile panel 或 ACK 都不能写成真实完成。

## 6. 下一步

当前数值最低仍是 Objective 5（约 66%），但没有真实外部材料时不继续堆本地 O5 metadata。下一步最高可行动作是把同一 `evidence_ref` 带到真实现场/上车复账：真实电梯门状态、目标楼层确认、人工协助记录、Nav2/fixed-route runtime log、task record、completion signal、WAVE ROVER/HIL、失败恢复、真实 dropoff completion、真实 cancel completion 或 delivery success。

## 7. 剩余风险

- 仍缺真实电梯、真实门状态、真实楼层确认、真实人工协助记录。
- 仍缺真实 Nav2/fixed-route 实跑、真实路线采集、关键帧实景证据。
- 仍缺 WAVE ROVER、真实串口/UART、HIL 和同一 `evidence_ref` 的上车实机复账。
- 仍缺真实手机/browser、production app、PWA prompt/user choice。
- 仍缺 Objective 5 external proof、公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue 和 worker/migration。
