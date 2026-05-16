# Sprint 2026.05.17_05-06 Route Task Field Retest Acceptance Brief - Pre Start

sprint_type: epic

## 1. 启动背景

本轮创建 fresh sprint folder，目标为 `route_task_field_retest_acceptance_brief`。产品北极星仍是让普通手机用户把垃圾交给低成本 ROS2 小车后，可以通过固定路线和电梯 assisted delivery 获得可验证、可解释、可复盘的送达体验。

当前 `OKR.md` 4.1 快照更新时间为 2026-05-17 04:16 Asia/Shanghai：

- Objective 1：约 77%
- Objective 2：约 87%
- Objective 3：约 87%
- Objective 4：约 98%
- Objective 5：约 66%

Objective 5 数值最低，但本机是 Docker-only，缺真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/migration。继续堆 O5 local metadata depth 不能形成 Objective 5 external proof，本轮不继续消费该 blocker。

最新 `sprints/2026.05.17_04-05_route-task-field-retest-drill-console/final.md` 表明 `route_task_field_retest_drill_console` 已把 material pack、result intake、result reconciliation 的 command labels、safe checklist、missing prompts 和 callback checklist 串成 PC / Robot / mobile 共同消费的 software proof。下一层应把该 summary 转成现场支持可以执行、复核和交接的 acceptance brief / handoff packet。

最近 O1 hardware chain 已完成 readiness review 和 execution pack，但继续本地硬件 wrapper 会重复消费真实硬件、2D LiDAR、ToF、WAVE ROVER、UART 和 HIL-entry 缺失。本轮按 PR #4 和最近 route-task 结果，继续推进 Objective 2 / Objective 3 的现场复测链。

## 2. 近期 PR / 评审证据

- GitHub PR #4 `Add elevator-assisted delivery capability to agents, registry and OKR` 已把电梯 assisted delivery 写入主行为链，但没有运行集成测试；因此现场复测 acceptance brief 必须继续要求真实门状态、目标楼层确认、人工协助记录和同一 `evidence_ref` 的 route/task 材料。
- GitHub PR #5 `Make elevator-assisted delivery mandatory; update agents, OKR and hardware baseline` 要求单目 + 2D LiDAR + ToF safety ring、参数化硬件配置和证据链，暴露硬件材料缺口；本轮不能把 acceptance brief 写成真实硬件或 HIL 完成。
- `route_task_field_retest_drill_console` 已形成 drill console summary，但还缺现场支持的 acceptance criteria、handoff owner、pass/fail worksheet、required evidence packet 和 phone-safe read-only handoff view。

## 3. 本轮目标

新增 `route_task_field_retest_acceptance_brief`，证据边界为 `software_proof_docker_route_task_field_retest_acceptance_brief_gate`。

本轮必须保持：

- `trashbot.route_task_field_retest_acceptance_brief.v1`
- `trashbot.route_task_field_retest_acceptance_brief_summary.v1`
- `not_proven`
- `delivery_success=false`
- `primary_actions_enabled=false`

本轮不读取真实材料目录，不访问 ROS graph、Nav2 runtime、serial/UART、WAVE ROVER、真实电梯、外部云、OSS/CDN、DB/queue 或 4G；不声明 route/elevator field pass、HIL、真实投放、真实 cancel/dropoff completion 或 delivery success。

## 4. 用户价值和产品北极星

用户价值是把“现场复测演练控制台知道下一步要补什么”推进为“现场支持拿到一份可执行 acceptance brief / handoff packet”：同一 `evidence_ref` 下清楚列出现场准入条件、复测执行顺序、材料回填项、pass/fail 判定、回退动作、owner handoff 和不可声明的边界。

产品北极星不变：普通用户不需要 SSH、ROS2、串口或硬件调试知识，也能看懂机器人当前是否可以安全进入下一步；工程侧则必须保留可复盘证据链，并把 Docker-only software proof 与真实 field pass 分开。

## 5. Owner 与并行策略

本轮是 3 owner Epic sprint，文件范围互不重叠，按 AGENTS.md 并行启动强制规则执行：

- Task A Autonomy Algorithm Engineer：新增 dependency-free PC acceptance brief gate，消费 `route_task_field_retest_drill_console` artifact / summary，输出 acceptance brief artifact / summary。
- Task B Robot Platform Engineer：新增 diagnostics metadata-only consumer，fail closed，只展示 acceptance readiness、owner handoff、pass/fail criteria 和 evidence packet status。
- Task C User Touchpoint Full-Stack Engineer：新增 mobile/web 只读“现场复测验收简报” panel，只展示 phone-safe acceptance brief / handoff packet，Start Delivery、Confirm Dropoff、Cancel gating 不变。

Product closeout 后续由 Product Manager / OKR Owner 处理，届时再更新 `tech-done.md`、`side2side_check.md`、`final.md`、`OKR.md` 和 `docs/process/okr_progress_log.md`。

## 6. 风险、阻塞和证据链缺口

- Objective 5 external proof 仍缺：真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/migration。
- Objective 1 / 硬件材料仍缺：真实 2D LiDAR / ToF SKU、source、receipt、procurement、installation、wiring、power、calibration、HIL-entry 和 WAVE ROVER / UART / `T=1001` feedback。
- Objective 2 / Objective 3 仍缺：真实 Nav2/fixed-route runtime log、route completion signal、task record、真实电梯门状态、目标楼层确认、人工协助记录、dropoff/cancel completion、delivery result 和同一 `evidence_ref` 的实机复账。
- Objective 4 仍缺：真实 iPhone/Android browser、production app、真实 PWA prompt/user choice 和真实现场 phone behavior。

## 7. 本轮需要创建或更新的 sprint 文档

Planning 阶段创建：

- `sprints/2026.05.17_05-06_route-task-field-retest-acceptance-brief/pre_start.md`
- `sprints/2026.05.17_05-06_route-task-field-retest-acceptance-brief/prd.md`
- `sprints/2026.05.17_05-06_route-task-field-retest-acceptance-brief/tech-plan.md`

实现完成后必须继续补齐：

- `sprints/2026.05.17_05-06_route-task-field-retest-acceptance-brief/tech-done.md`
- `sprints/2026.05.17_05-06_route-task-field-retest-acceptance-brief/side2side_check.md`
- `sprints/2026.05.17_05-06_route-task-field-retest-acceptance-brief/final.md`
