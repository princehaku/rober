# Sprint 2026.05.16_20-21 Route Task Field Retest Execution Pack - Side2Side Check

sprint_type: epic

## 1. 对照范围

本次 side-by-side 对照 `prd.md`、`tech-plan.md`、三条 worker 返回结果与 Task D closeout 要求。验收对象不是用户真实现场送达，而是 `route_task_field_retest_execution_pack` 这条 Docker/local software proof 链路是否把下一次现场复测材料说清楚，并且是否严格保留 `software_proof_docker_route_task_field_retest_execution_pack_gate`、`not_proven`、`delivery_success=false`、`primary_actions_enabled=false`。

## 2. 用户价值和产品北极星

用户价值已推进：现场同学现在能看到下一次 field retest 需要的材料、重跑命令、operator handoff 和 checklist；手机端也能只读解释当前为什么仍未证明送达。

产品北极星保持一致：`rober` 仍以普通手机用户可理解、现场可复测、证据可复盘的低成本 ROS2 自主垃圾投递机器人为目标。本轮不把 execution pack 当作真实 delivery success。

## 3. PRD 验收对照

| PRD / Tech Plan 要求 | 对照结果 |
| --- | --- |
| PC gate 输出 `trashbot.route_task_field_retest_execution_pack.v1` 和 summary | 满足。Task A 已实现并通过 py_compile、10 个 unittest、CLI help、rg 与 scoped diff check。 |
| Required materials 覆盖真实 Nav2/fixed-route runtime log、route completion signal、task record、operator note、mobile/diagnostics safe summary | 满足。Execution pack 将这些材料作为下一次现场复测必需项；elevator source 还追加 door state、target floor confirmation、human assistance note。 |
| Robot diagnostics 只读消费，fail closed | 满足。Task B 支持多个 safe source，缺失、unsupported、unsafe、missing ref、same-ref mismatch、success wording、primary action enabled 均 fail closed；不触发 collect/dropoff/cancel/ACK/cursor/Nav2/HIL/delivery success。 |
| Mobile/web 只读 panel，copy/export whitelist-only，primary actions 不变 | 满足。Task C 展示现场复测执行包，Start / Confirm Dropoff / Cancel gating 未改。 |
| Closeout 明确 Objective 5 blocked 与 PR #5 两轮 blocker 红线 | 满足。`tech-done.md`、`final.md`、`OKR.md` 和 progress log 均记录。 |

## 4. OKR 映射对照

- Objective 2：通过 execution pack 把下一次 task record、route completion signal、operator handoff、field retest checklist 和 elevator 材料要求串到同一 `evidence_ref`，可保守上调到约 81%。
- Objective 3：通过 rerun commands 和 required field materials 把 Nav2/fixed-route 现场复测材料变成可执行链路，可保守上调到约 81%。
- Objective 4：通过 mobile/web 只读 panel 提升普通用户和现场支持的解释能力，可保守上调到约 90%。
- Objective 1：不涉及真实硬件，不上调。
- Objective 5：仍缺真实外部材料，不上调。

## 5. 证据边界

本轮只证明当前 repo 内 PC gate、Robot diagnostics metadata-only consumer、mobile/web read-only panel 和文档同步的 software proof。它不证明真实 Nav2/fixed-route、真实 route/elevator field pass、真实电梯门状态、真实楼层确认、真实人工协助、真实 dropoff/cancel completion、delivery result、真实手机/browser、production app、WAVE ROVER、UART、HIL 或 Objective 5 external proof。

## 6. 未完成事项

下一次要补的真实证据仍是：真实 Nav2/fixed-route runtime log、route completion signal、task record、真实电梯门状态、真实楼层确认、人工协助记录、dropoff/cancel completion、delivery result、WAVE ROVER/UART/HIL、真实手机/browser、Objective 5 external proof。
