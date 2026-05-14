# Sprint 2026.05.15_00-01 Route Task Field Run Readiness - Side2Side Check

sprint_type: epic

## 用户价值对照

预期：把 PC route debug console、operator review、execution bundle、diagnostics 和 mobile read-only summary 串成下一次真实路线-任务联跑前的可执行 handoff。

结果：已由 Task A/B/C 形成 `software_proof_docker_route_task_field_run_readiness_gate` 链路：

- Autonomy 产出 dependency-light readiness artifact / CLI，列出同一 `evidence_ref`、缺失材料、可运行命令、`not_proven` 和 `delivery_success=false`。
- Robot diagnostics 只读消费 readiness summary，保持 metadata-only，不触发控制动作。
- Mobile 只读展示 readiness availability / next evidence，不读取 raw artifact，不改变 Start/Confirm/Cancel gating。

## OKR 对照

- Objective 2：支持任务闭环 KR5 的复盘材料准备；本轮把下一次真实 route-task field run 需要的材料清单和同一 `evidence_ref` 复账要求做成软件证据。可保守上调到约 83%。
- Objective 3：支持固定路线可验证流程；本轮把 PC route debug、operator review、execution bundle 汇总为 field-run readiness handoff。可保守上调到约 83%。
- Objective 5：未获得真实外部云/4G/OSS/CDN/DB/queue proof，不提升，保持约 68%。
- Objective 1：未获得真实 WAVE ROVER、串口/UART、HIL 或底盘 feedback，不提升，保持约 75%。
- Objective 4：手机端只是新增只读 consumption surface，主完成度不提升，保持约 95%。

## 验收口径对照

- `schema=trashbot.route_task_field_run_readiness.v1`：满足。
- `evidence_boundary=software_proof_docker_route_task_field_run_readiness_gate`：满足。
- 同一 `evidence_ref` handoff：满足，且 `same_evidence_ref_required=true`。
- `not_proven` 包含真实 Nav2/fixed-route、真实路线采集、WAVE ROVER、真实串口/UART、HIL、dropoff/cancel completion、delivery success、Objective 5 external proof：满足。
- diagnostics metadata-only：满足。
- mobile read-only，不读 raw artifact，不改变 Start/Confirm/Cancel gating：满足。

## 未证明边界

本轮明确 not_proven：

- 真实 Nav2/fixed-route。
- 真实路线采集。
- WAVE ROVER。
- 真实串口/UART。
- HIL。
- 同一 `evidence_ref` 上车复账。
- dropoff/cancel completion。
- delivery success。
- Objective 5 external proof，包括公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue connectivity、production worker/migration。

## Product 结论

本轮符合 Product closeout 口径：它不是成功送达证明，而是下一次真实路线-任务 field run 的材料准备和跨端 handoff 软件证据。Objective 2 / Objective 3 的 82% -> 83% 是保守进展；最低 Objective 5 仍需要真实外部材料，不能由本轮 Docker/local readiness gate 替代。
