# Sprint 2026.05.16_02-03 Elevator Route Evidence Reconciliation - PRD

sprint_type: epic

## 1. 用户价值

现场同学现在分别有电梯 assisted delivery 的 rehearsal evidence 和 route/task 的 completion signal，但还缺一层复账：它们是否属于同一次运行、是否共享同一 `evidence_ref`、缺什么材料、下一次应该重跑什么。没有这层复账，用户和支持人员仍需要手工对比多个 artifact，容易把 rehearsal evidence、route completion signal 或 ACK 误读成真实送达成功。

本轮要把这些分散材料汇成一个只读、安全、可复核的电梯+路线证据复账结果。它服务 Objective 3 的固定路线可复盘流程，也支撑 Objective 2 的电梯必达闭环和 Objective 4 的手机可解释性。

## 2. OKR 映射

- Objective 3：推进 KR2/KR3/KR5。把 Nav2/fixed-route runtime / route completion signal 和电梯 phase evidence 放进同一 `evidence_ref` 复账链。
- Objective 2：推进 KR5/KR6/KR7。让电梯状态链的 phase evidence、failure/manual takeover 和任务完成信号之间有可解释的复账结果。
- Objective 4：支撑 KR5/KR6/KR7。手机端只读展示复账结果和下一步补证动作，但不开放控制、不宣称成功。
- Objective 5：不推进。没有真实公网 HTTPS/TLS、4G/SIM、OSS/CDN、production DB/queue 或 worker/migration 材料。

## 3. 成功标准

1. 产出 `schema=trashbot.elevator_route_evidence_reconciliation.v1` 的 artifact，固定 `evidence_boundary=software_proof_docker_elevator_route_evidence_reconciliation_gate`。
2. 支持读取 elevator rehearsal evidence artifact / summary 与 route task completion signal artifact / summary。
3. 输出 `reconciliation_verdict`、`same_evidence_ref_status`、`source_states`、`missing_materials`、`mismatch_reasons`、`operator_next_steps`、`phone_safe_summary`、`not_proven`、`delivery_success=false`、`primary_actions_enabled=false`。
4. `evidence_ref` 不一致、材料缺失、unsupported schema、unsafe copy、success/control claim 必须 fail closed。
5. Robot diagnostics 只读消费 summary，不泄漏本地路径、raw artifact、ROS topic、serial/UART、WAVE ROVER、凭证或 traceback。
6. `mobile/web` 只展示 phone-safe summary，不改变 Start / Confirm Dropoff / Cancel gating。

## 4. 非目标

- 不证明真实电梯门状态、真实目标楼层确认、真实人工协助。
- 不证明真实 Nav2/fixed-route、真实路线采集、WAVE ROVER、UART、HIL 或真实底盘运动。
- 不证明真实 dropoff completion、cancel completion、delivery success。
- 不证明真实手机设备/browser、production app、PWA prompt/user choice。
- 不证明 Objective 5 外部云/4G/OSS/CDN/DB/queue。

## 5. 验收命令概览

各 worker 只运行对应围栏命令；失败时必须定位并重跑：

- Autonomy：py_compile、`pc-tools/evidence/test_elevator_route_evidence_reconciliation.py`、CLI `--help`、CLI ready/mismatch drill、required `rg`、scoped diff check。
- Robot：py_compile `operator_gateway_diagnostics.py`、`test_operator_gateway_diagnostics.py`、required `rg`、scoped diff check。
- Full-stack：`mobile/test_mobile_web_entrypoint.py`、py_compile、`node --check mobile/web/app.js`、required `rg`、scoped diff check。
- Product：closeout `rg` 和 scoped diff check，更新 OKR 与 progress log 时保持 evidence boundary。
