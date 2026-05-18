# Sprint 2026.05.18_11-12 Route Task Acceptance Execution Pack - PRD

## 1. 用户价值和产品北极星

用户价值：现场 owner 不需要理解多轮 acceptance brief、review decision、Robot diagnostics 和 mobile/web safe alias 的历史上下文，也能按同一份执行包完成复跑准备、证据采集、失败回填和交接。

产品北极星：PR #4 的 elevator-assisted delivery 主链可以被真实现场材料逐步验收，而不是停留在 Docker-local metadata；每一步都清楚说明当前仍是 `not_proven`，不误导用户认为 delivery success 已经发生。

## 2. OKR 映射

- Objective 2：电梯 assisted delivery 主链需要现场执行包，才能把门状态、楼层确认、人工协助记录、dropoff/cancel completion 和 delivery result 变成可执行采集项。
- Objective 3：Nav2/fixed-route 验收需要 runtime log、route completion signal、task record 和同一 `evidence_ref` 复账；本轮把这些要求写入 rerun commands 和 checklist。
- Objective 4：手机用户体验需要只读展示现场执行包，不开放 Start Delivery、Confirm Dropoff、Cancel 或任何 primary action。
- Objective 5：不推进。缺真实 HTTPS/TLS、公网、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/cutover 和真实手机/browser external proof。
- Objective 1：不推进。缺真实 WAVE ROVER、UART、HIL packet、`/dev/ttyUSB*`、`feedback_T1001.log`、`/odom`、`/imu/data`、`/battery` 和 operator HIL report。

## 3. KR 拆解

KR-A Autonomy：新增 `route_task_field_retest_acceptance_execution_pack` PC gate，消费 `route_task_field_retest_acceptance_review_decision` artifact/summary/wrapper，输出 owner checklist、rerun commands、safe evidence bundle、material requirements、review-decision source 和 fail-closed flags。

KR-B Robot：diagnostics 支持 execution-pack artifact/summary/nested wrapper/file/env source，输出 `route_task_field_retest_acceptance_execution_pack`、`route_task_field_retest_acceptance_execution_pack_summary` 和 `robot_diagnostics_route_task_field_retest_acceptance_execution_pack_summary` safe alias。

KR-C Full-stack：mobile/web 新增只读 execution-pack panel，展示 safe `evidence_ref`、owner checklist、rerun commands、safe evidence bundle、required route/elevator materials、handoff owner、boundary flags、`not_proven`、`delivery_success=false`、`primary_actions_enabled=false`。

## 4. 本轮核心抓手

本轮不是再写一个 review decision，而是把 review decision 变成现场可执行材料：

- owner checklist：现场复跑前必须确认的材料和责任人。
- rerun commands：PC/Robot/mobile 三端最小复核命令。
- safe evidence bundle：用于交给现场 owner 的白名单材料包。
- fail-closed decision：unsupported schema、missing/weak `evidence_ref`、unsafe copy、success/control wording、`delivery_success=true` 或 `primary_actions_enabled=true` 必须阻断。

## 5. 需要做什么

1. Autonomy 新增 PC execution-pack gate 和 focused unittest。
2. Robot 新增 diagnostics execution-pack safe summary 和 focused unittest。
3. Full-stack 新增 mobile/web 只读 execution-pack panel、fixture 和 focused unittest。
4. Product closeout 时只做证据核对、sprint 留档和 OKR 保守收口；若只有 software proof，不大幅提升 OKR。

## 6. 优先级和验收口径

P0：所有产物必须消费上一轮 acceptance review decision，并输出 `software_proof_docker_route_task_field_retest_acceptance_execution_pack_gate`。

P0：所有端保持 `not_proven`、`delivery_success=false`、`primary_actions_enabled=false`。任何 success/control wording 都必须 fail closed。

P1：执行包必须包含 owner checklist、rerun commands、safe evidence bundle、required route/elevator materials、handoff owner 和 next required evidence。

P1：mobile/web 只读展示，不得启用 Start Delivery、Confirm Dropoff、Cancel 或任何 primary action。

P2：PR #5 hardware boundary / 2D LiDAR / ToF 材料缺口只能作为风险列出，不得写成已解决或本轮验收完成。

## 7. 对应责任 Engineer

- Autonomy Algorithm Engineer：PC evidence gate 与 execution-pack schema。
- Robot Platform Engineer：Robot diagnostics safe summary consumer。
- User Touchpoint Full-Stack Engineer：mobile/web execution-pack panel 与 fixture/test。
- Product Manager / OKR Owner：OKR 映射、验收边界、sprint 留档和最终阶段验收。

## 8. 风险、阻塞和证据链缺口

- Objective 5 仍缺真实 external proof；本轮不能提高 O5 production proof。
- Objective 1 仍缺真实硬件和 HIL packet；本轮不能提高真实 HIL proof。
- Objective 2/3/4 仍缺真实 route/elevator field pass、真实 Nav2/fixed-route、真实 route completion signal、真实 task record、真实门状态、真实楼层确认、人工协助记录、真实 dropoff/cancel completion 和 delivery result。
- PR #5 仍缺真实 2D LiDAR / ToF SKU/source/receipt/procurement/installation/wiring/power/calibration/HIL-entry 材料。

## 9. 需要创建或更新的 sprint 文档

本轮已创建规划文档：

- `sprints/2026.05.18_11-12_route-task-acceptance-execution-pack/pre_start.md`
- `sprints/2026.05.18_11-12_route-task-acceptance-execution-pack/prd.md`
- `sprints/2026.05.18_11-12_route-task-acceptance-execution-pack/tech-plan.md`

后续实现与验收必须继续补齐：

- `sprints/2026.05.18_11-12_route-task-acceptance-execution-pack/tech-done.md`
- `sprints/2026.05.18_11-12_route-task-acceptance-execution-pack/side2side_check.md`
- `sprints/2026.05.18_11-12_route-task-acceptance-execution-pack/final.md`
