# Sprint 2026.05.16_02-03 Elevator Route Evidence Reconciliation - Side2Side Check

sprint_type: epic

## 1. 对照范围

本轮对照 `prd.md` 和 `tech-plan.md` 的 Product 验收口径，核对工程 worker 已完成的 Task A/B/C 是否满足用户价值、OKR 映射、证据边界和只读控制约束。

## 2. 需求逐项核对

| 需求 | 对照结果 | 证据 |
| --- | --- | --- |
| 产出 `trashbot.elevator_route_evidence_reconciliation.v1` artifact / summary | 通过 | Task A 新增 CLI 与测试，验证 `Ran 8 tests in 0.018s OK`，schema 和 boundary 已在 PC README 与产品/导航文档中同步。 |
| 检查 same `evidence_ref`、phase evidence、route completion signal、missing/mismatch | 通过 | Task A 输出 `same_evidence_ref_status`、source states、materials status、operator next steps 和 phone-safe summary。 |
| Robot diagnostics 只读 metadata-only consumption | 通过 | Task B 支持 explicit ref 与 `TRASHBOT_ELEVATOR_ROUTE_EVIDENCE_RECONCILIATION` / `_SUMMARY`；验证 `Ran 81 tests in 0.070s OK`。 |
| `mobile/web` 只读“电梯路线证据复账” panel | 通过 | Task C 新增 panel，验证 `Ran 45 tests in 0.142s OK` 与 `node --check mobile/web/app.js` pass。 |
| 不改变 Start / Confirm Dropoff / Cancel gating | 通过 | Task C 明确只读展示，Product 复核文档中保持 `primary_actions_enabled=false`。 |
| 保持证据边界，不声明真实完成 | 通过 | Closeout、OKR 和 progress log 均写明 `software_proof_docker_elevator_route_evidence_reconciliation_gate` 不证明真实电梯、真实 Nav2/fixed-route、HIL、真实手机/browser、dropoff/cancel completion、delivery success 或 O5 external proof。 |

## 3. OKR 对照

- Objective 3：本轮主目标达成。route completion signal 与电梯 phase evidence 进入同一 `evidence_ref` 复账 gate，完成度从约 73% 保守上调到约 74%。
- Objective 2：支撑目标达成。电梯 assisted delivery 主链路可与 route completion signal 复账，完成度从约 74% 保守上调到约 75%。
- Objective 4：支撑目标达成。手机端可解释复账结果和补证动作，完成度从约 74% 保守上调到约 75%。
- Objective 1：无硬件/HIL 新证据，保持约 73%。
- Objective 5：无真实外部云/4G/OSS/CDN/DB/queue 证据，保持约 66%；not real Objective 5 external proof。

## 4. 边界核对

本轮只证明 Docker/local PC CLI、Robot diagnostics metadata-only consumption 和 mobile read-only panel。它不证明：

- 真实电梯、真实门状态、真实目标楼层确认、真实人工协助。
- 真实 Nav2/fixed-route、真实路线采集、关键帧实景证据。
- WAVE ROVER、真实串口/UART、HIL 或真实底盘运动。
- 真实 dropoff/cancel completion、delivery success。
- 真实手机/browser、production app、PWA prompt/user choice。
- Objective 5 external proof、公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue 或 worker/migration。

## 5. 结论

本轮可以收口为 `software_proof_docker_elevator_route_evidence_reconciliation_gate`。它是 O2/O3/O4 的软件复账进展，不是 O1 硬件证据，也不是 O5 外部云证据。下一步应把同一 `evidence_ref` 带到真实现场/上车材料采集，而不是继续堆本地 O5 metadata。
