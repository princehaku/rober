# Sprint 2026.05.14_21-22 Route Task Rehearsal Execution Bundle - Side2Side Check

sprint_type: epic

## 对照结论

本轮 PRD 要求把 route status、software replay、task record 和 crosscheck 从“已有 artifact + diagnostics 可消费”推进为“一次命令可生成 execution bundle，diagnostics 可只读消费 bundle manifest”。工程事实满足该口径：Autonomy 新增 execution bundle CLI 和 manifest，Robot diagnostics 新增 `route_task_rehearsal_execution_bundle` summary，并保守处理 missing/read_error/unsupported schema/crosscheck fail。

## 用户价值核对

- 支持人员现在可以拿到一个可复跑 manifest，而不是分散 status、task record、replay 和 artifact 路径。
- manifest 顶层暴露 artifact ref、crosscheck status、HIL alignment status、diagnostics summary 和 `not_proven`，让 diagnostics consumer 不必猜 nested shape。
- diagnostics 消费 bundle 时仍是 metadata-only，不启用 primary actions，不触发 ACK POST/cursor，也不声称 HIL 或 delivery success。

## OKR 核对

- Objective 2：从任务复盘可消费推进到 execution bundle 可复跑，保守上调到约 80%。
- Objective 3：从固定路线软件对账 artifact 推进到 bundle manifest + diagnostics 消费链，保守上调到约 80%。
- Objective 5：仍最低约 68%，但本轮没有真实外部云/4G/OSS/CDN/DB/queue 材料，不上调。

## 非目标确认

- 未证明真实 Nav2/fixed-route 实跑。
- 未证明真实路线采集、关键帧实景证据或上车复账。
- 未证明 WAVE ROVER、真实串口、HIL、dropoff/cancel completion 或 delivery success。
- 未证明公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue connectivity 或 production worker/migration。

## 验收判断

本 sprint 可作为 `software_proof_docker_route_task_rehearsal_execution_bundle_gate` 收口。下一步若继续 O2/O3，应从 bundle/software proof 转向真实路线、同一 `evidence_ref` 的上车复账或 Nav2/fixed-route 实跑；若要推进最低的 Objective 5，必须先补真实外部云/4G/OSS/CDN/DB/queue 材料。
