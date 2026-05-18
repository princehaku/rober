# Sprint 2026.05.18_10-11 Route Task Acceptance Review Decision - PRD

## 1. 用户价值

普通用户不关心 acceptance brief 是哪一个 JSON artifact；他们需要的是现场复跑前的明确结论：现在能不能进入受控现场复测，如果不能，是缺门状态、楼层确认、人工协助记录、Nav2/fixed-route runtime log、task record、dropoff/cancel completion，还是 evidence_ref / unsafe copy / 成功文案越界导致必须回填。

本轮把上一轮 acceptance brief 从“材料清单”推进成“验收前决策”，让 PC operator、Robot diagnostics 和手机端看到同一个下一步，而不是各自解释现场材料。

## 2. OKR 映射

- Objective 2：电梯 assisted delivery 主链需要真实现场材料；本轮提供进入/阻断受控现场复跑的 review decision contract。
- Objective 3：固定路线/Nav2 现场材料需要同一 `evidence_ref` 的 runtime log、completion signal、task record；本轮把这些缺口变成可回填决策。
- Objective 4：手机端只读展示下一步和缺口，不暴露 raw JSON、ROS topic 或控制动作。
- Objective 5：不推进。没有真实公网/4G/OSS/CDN/DB/queue/production worker 外部证据。
- Objective 1：不推进。没有真实 WAVE ROVER/UART/HIL packet，且最近本地 HIL 包装已重复消费 blocker。

## 3. KR

KR-A Autonomy：新增 `route_task_field_retest_acceptance_review_decision` PC gate，消费 `route_task_field_retest_acceptance_brief` artifact/summary/wrapper，输出 review decision、material backfill status、owner handoff、rerun commands、next required evidence 和 safe copy。

KR-B Robot：diagnostics 输出 `route_task_field_retest_acceptance_review_decision` / `_summary` / `robot_diagnostics_route_task_field_retest_acceptance_review_decision_summary` safe alias，并在 unsupported schema/boundary、unsafe copy、success/control claim、`delivery_success=true`、`primary_actions_enabled=true`、weak/missing `evidence_ref` 时 fail closed。

KR-C Full-stack：mobile/web 新增只读 panel，展示 review decision、safe evidence ref、material status、owner handoff、next required evidence、rerun commands 和 boundary flags；Start Delivery、Confirm Dropoff、Cancel 不被打开。

## 4. 验收口径

- 软件证明边界：`software_proof_docker_route_task_field_retest_acceptance_review_decision_gate`。
- 允许的 ready 状态只表示可进入受控现场复跑准备，不表示现场通过或 delivery success。
- 必须保留 `not_proven`、`delivery_success=false`、`primary_actions_enabled=false`。
- 不新增 broad 测试；只跑各 owner 的 py_compile、focused unittest、node syntax、required `rg` 和 touched-file scoped diff check。

## 5. 不做事项

- 不访问真实电梯、真实手机、真实 WAVE ROVER、真实串口、ROS graph、Nav2 runtime、外部云、OSS/CDN、DB/queue 或 4G。
- 不把 PR #5 2D LiDAR / ToF 缺口写成已解决。
- 不把 acceptance review decision 写成真实现场验收通过。
