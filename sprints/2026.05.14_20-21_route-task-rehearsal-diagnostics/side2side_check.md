# Sprint 2026.05.14_20-21 Route Task Rehearsal Diagnostics - Side2Side Check

sprint_type: epic

## 验收结论

通过。P0 验收项满足：route/task rehearsal artifact 已从 PC 工具落盘推进到 diagnostics/support 面可消费；summary 保持 phone-safe / metadata-only，只声明 `software_proof_docker_route_task_rehearsal_diagnostics_gate`。

## 对照验收

| PRD 验收项 | 结果 | 证据 |
| --- | --- | --- |
| artifact summary 包含 schema、evidence boundary、`evidence_ref`、crosscheck status、HIL alignment status、`not_proven`、下一步提示 | 通过 | Task A 新增 `diagnostics_summary`，schema 为 `trashbot.route_task_rehearsal_diagnostics_summary`，边界为 `software_proof_docker_route_task_rehearsal_diagnostics_gate`。 |
| diagnostics 只读消费 artifact，不触发 collect/dropoff/cancel、ACK、cursor、HIL、delivery success | 通过 | Task B `summarize_route_task_rehearsal_artifact()` 与 `build_diagnostics_payload(..., route_task_rehearsal_artifact_ref=...)` 只输出 `route_task_rehearsal` metadata summary；测试覆盖 valid artifact、missing/sensitive path、crosscheck fail。 |
| summary 过滤本地路径、串口、bearer/Authorization、OSS AK/SK、DB/queue URL、traceback 等敏感信息 | 通过 | Task B 中间 copy/redaction 问题已修复并重跑 `test_operator_gateway_diagnostics` 45 tests OK。 |
| 文档同步 `pc-tools/README.md`、`docs/navigation/fixed_route_workflow.md`、`docs/interfaces/ros_contracts.md` | 通过 | Task A/B 均已同步对应文档，Task C 已在 `OKR.md` 和 `docs/process/okr_progress_log.md` 收口。 |

## OKR 对照

- Objective 2：从约 78% 谨慎上调到约 79%。理由是任务复盘 artifact 已可被 diagnostics/support 面消费，后续支持人员能沿同一 `evidence_ref` 查 status、crosscheck、HIL alignment 和 `not_proven`。
- Objective 3：从约 78% 谨慎上调到约 79%。理由是 fixed-route software rehearsal 的证据链从可保存推进到可诊断，且文档和围栏测试同步。
- Objective 5：保持约 68%。本轮没有真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue connectivity 或 worker/migration 材料。
- Objective 1 和 Objective 4：保持不变。本轮不触碰硬件/HIL，也不新增真实手机设备或 production app 验收。

## 边界复核

本轮不是真实 Nav2/fixed-route、真实路线采集、WAVE ROVER、真实串口、HIL、同一 `evidence_ref` 上车复账、dropoff/cancel completion、delivery success、O5 external proof、公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic 或 production DB/queue。
