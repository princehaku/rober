# Sprint 2026.05.15_04-05 Route Task Field Run Reconciliation - Side2Side Check

sprint_type: epic

## 1. 对照验收结论

本轮 PRD 要求把 route/task field-run execution pack 推进为现场材料复账能力：同一 `evidence_ref` 下消费 execution pack 与 intake/review 材料，输出可读 verdict、materials status、operator next steps、phone-safe summary 和 `not_proven` 边界。A/B/C worker 结果满足该验收口径，Task D 已将 OKR 和 sprint closeout 同步为 software proof。

## 2. 用户价值对照

用户价值已落到“现场材料是否能复账”这一层：现场人员不再只拿到执行包，还能得到 `reconciliation_verdict`，判断 pack 与 intake/review 是否同属一个 `evidence_ref`、材料是否缺失或不一致、下一步需要补采还是重跑。

该价值仍是工程侧复账能力，不是普通用户侧真实送达闭环。手机端只读 panel 的作用是让用户触点和支持人员看懂材料状态；它不授权 Start/Confirm/Cancel，也不证明 delivery success。

## 3. OKR 映射对照

- Objective 2：复账 verdict 推进 KR5“每次任务产出可复盘记录”，因为 task record、robot-side task evidence、dropoff/cancel completion 等材料状态被汇总为可读判定；保守从约 63% 上调到约 64%。
- Objective 3：复账 artifact 推进 KR2/KR3/KR5，route status、Nav2/fixed-route runtime log、field-run intake/review 和 materials status 能按同一 `evidence_ref` 进入固定路线现场复核；保守从约 63% 上调到约 64%。
- Objective 5：没有真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue connectivity 或 worker/migration；保持约 66%，不因本轮上调。
- Objective 1 / Objective 4：本轮未提供真实硬件证据或真实手机设备验收；均保持约 73%。

## 4. 验收口径对照

通过项：

- Artifact schema 命中 `trashbot.route_task_field_run_reconciliation.v1`。
- Evidence boundary 命中 `software_proof_docker_route_task_field_run_reconciliation_gate`。
- Diagnostics summary 命中 `trashbot.route_task_field_run_reconciliation_summary.v1`。
- `same_evidence_ref_required=true`、`reconciliation_verdict`、`materials_status`、`operator_next_steps`、`phone_safe_summary`、`not_proven`、`delivery_success=false`、`primary_actions_enabled=false` 均进入证据链。
- Worker 验证覆盖 Task A ready/blocked paths、Task B metadata-only isolation、Task C mobile read-only/fail-closed panel。
- Product closeout `rg` 和 scoped `git diff --check` 均通过。

未通过项不是本 sprint 范围：

- 真实 Nav2/fixed-route 实跑未发生。
- 真实路线采集未发生。
- 同一 `evidence_ref` 上车实机复账未发生。
- WAVE ROVER、真实串口/UART、HIL 未发生。
- dropoff/cancel completion 和 delivery success 未发生。
- Objective 5 external proof 未发生。

## 5. 证据边界

本轮验收只确认 Docker/local artifact、diagnostics summary 和 mobile read-only panel 的软件复账能力。所有 closeout 文案均保留 `not_proven`、`delivery_success=false` 和 `primary_actions_enabled=false`，避免把 reconciliation verdict 误写成真实送达、真实固定路线或 HIL。
