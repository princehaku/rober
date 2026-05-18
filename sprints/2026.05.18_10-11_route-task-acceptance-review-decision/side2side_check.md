# Sprint 2026.05.18_10-11 Route Task Acceptance Review Decision - Side By Side Check

## 1. 验收结论

本轮验收通过，但只通过 `software_proof_docker_route_task_field_retest_acceptance_review_decision_gate`。它证明 PC / Robot / mobile 三端对 `route_task_field_retest_acceptance_review_decision` 的 safe summary、Robot alias、手机只读 panel 与 fail-closed flags 对齐，不证明真实路线、电梯、硬件、手机设备或云外部链路。

## 2. 用户价值对照

- 用户价值：现场复跑前，operator 不再只拿到 acceptance brief 清单，而是拿到下一步复核决策：可准备受控现场复跑、需要材料回填、需要 owner handoff，或因 schema / `evidence_ref` / unsafe claim 失败而重跑。
- 产品北极星：继续服务“普通手机用户完成低成本送垃圾闭环”，但本轮只降低现场材料回填前的解释偏差，不把软件 gate 写成已送达。
- OKR 映射：Objective 2、Objective 3、Objective 4 的 route/elevator field-material 链路继续变得可复核；Objective 1 和 Objective 5 不推进。

## 3. 证据链对照

| 项目 | 结果 | 边界 |
| --- | --- | --- |
| Autonomy PC gate | `route_task_field_retest_acceptance_review_decision` unittest `Ran 5 tests OK` | PC software proof，不读取真实 Nav2/fixed-route runtime 或现场材料目录 |
| Robot diagnostics | `robot_diagnostics_route_task_field_retest_acceptance_review_decision_summary` alias，diagnostics unittest `Ran 178 tests OK` | 只读 sanitized summary，不触发 task_orchestrator、ACK、Start、Confirm、Cancel 或 primary actions |
| mobile/web | 只读 panel，mobile unittest `Ran 74 tests OK`，`node --check` pass | 真实手机/browser/device 未验收，不证明 production app 或 PWA prompt/user choice |
| 组合验收 | required `rg` pass，scoped `git diff --check` pass | 仅覆盖本轮 touched scope 和 closeout docs |

## 4. Side-by-Side 判断

- `not_proven` 必须保留：通过。
- `delivery_success=false` 必须保留：通过。
- `primary_actions_enabled=false` 必须保留：通过。
- PR #4 route/elevator 真实材料仍缺：通过，未写成现场通过。
- PR #5 hardware baseline / 2D LiDAR / ToF 真实材料仍缺：通过，未写成硬件已闭环。
- Objective 5 external proof 仍缺：通过，未把本地 software proof 写成公网、4G、OSS/CDN、DB/queue 或 production worker proof。

## 5. 未完成事项

下一步需要真实材料，而不是继续堆本地 metadata：真实 route/elevator field pass、真实 Nav2/fixed-route runtime log、route completion signal、task record、门状态、目标楼层确认、人工协助记录、dropoff/cancel completion、delivery result、真实手机/browser/device、WAVE ROVER/UART/HIL，或 Objective 5 external proof。
