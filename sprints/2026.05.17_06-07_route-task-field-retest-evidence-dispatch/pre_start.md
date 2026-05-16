# Sprint 2026.05.17_06-07 Route Task Field Retest Evidence Dispatch - Pre Start

sprint_type: epic

## 1. 启动背景

本轮 fresh sprint 目标为 `route_task_field_retest_evidence_dispatch`。产品北极星仍是让普通手机用户把垃圾交给低成本 ROS2 小车后，可以通过固定路线和电梯 assisted delivery 获得可验证、可解释、可复盘的送达体验；工程侧必须把 Docker-only software proof 与真实 field pass、HIL、真实手机/browser 和 Objective 5 external proof 分开。

当前 `OKR.md` 4.1 快照更新时间为 2026-05-17 05:17 Asia/Shanghai：

- Objective 1：约 77%
- Objective 2：约 88%
- Objective 3：约 88%
- Objective 4：约 99%
- Objective 5：约 66%

Objective 5 当前数值最低，但本机只有 Docker，没有真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、production worker/migration。继续叠加 O5 local metadata wrapper 不应提升 Objective 5，本轮不继续消费该 blocker。

最新 sprint `sprints/2026.05.17_05-06_route-task-field-retest-acceptance-brief/final.md` 已完成 `software_proof_docker_route_task_field_retest_acceptance_brief_gate`，把现场复测准入、执行 checklist、pass/fail criteria、required evidence packet、owner handoff 和 rerun notes 固化为 acceptance brief。但 final 明确剩余风险仍是真实现场材料缺口：Nav2/fixed-route runtime log、route completion signal、task record、door_state、target_floor_confirmation、human_assistance_note、dropoff_or_cancel_completion、delivery_result，并要求保持同一 `evidence_ref`。

近期 PR #4 已把 elevator-assisted delivery 变成必须能力；PR #5 要求硬件 baseline、2D LiDAR / ToF、vendor/source 和参数化约束。最近 O1 hardware HIL-entry execution pack 已收口为缺真实材料，继续本地硬件 wrapper 会重复消费 blocker。因此本轮选择最低可行动作 Objective 2 / Objective 3，把 acceptance brief 推进为 evidence packet dispatch。

## 2. 本轮目标

新增 `route_task_field_retest_evidence_dispatch` planning 和 implementation 入口，证据边界固定为 `software_proof_docker_route_task_field_retest_evidence_dispatch_gate`。

本轮必须保持：

- `trashbot.route_task_field_retest_evidence_dispatch.v1`
- `trashbot.route_task_field_retest_evidence_dispatch_summary.v1`
- `not_proven`
- `delivery_success=false`
- `primary_actions_enabled=false`

本轮边界是 Docker-only local software proof。它只分派现场复测材料 owner、文件名、同一 `evidence_ref`、回填顺序、callback checklist 和 fail-closed rerun notes；不证明真实 field pass、HIL、真实手机/browser、真实 Nav2/fixed-route、真实投放、dropoff/cancel completion、delivery success 或 Objective 5 external proof。

## 3. 用户价值和产品北极星

用户价值：现场支持不再只拿到 acceptance brief 的材料清单，而是得到一份 evidence packet dispatch：谁负责哪份现场材料、应该用什么文件名、必须绑定哪个 safe `evidence_ref`、按什么顺序回填、callback 时检查什么、失败后如何 fail closed 重新派发。

产品北极星：普通手机用户最终只需要理解机器人能否继续任务、哪里需要人工介入；工程侧必须保证每个 route/elevator 关键行为都有同一 `evidence_ref` 可回放证据链，且不会把本地软件分派包误写成真实送达。

## 4. OKR 映射

- Objective 2：把电梯 assisted delivery 的现场复测材料从 acceptance brief 推进为 owner/file/sequence dispatch，直接服务 door_state、target_floor_confirmation、human_assistance_note、dropoff_or_cancel_completion、delivery_result 的真实回填。
- Objective 3：把 Nav2/fixed-route runtime log、route completion signal、task record 的现场材料分派和同一 `evidence_ref` 约束固化，降低真实固定路线复测时漏采、错配或乱序回填风险。
- Objective 4：mobile/web 只读展示“现场证据包派发”，帮助现场人员理解下一步材料责任和回调清单，但不改变 Start/Confirm/Cancel gating。
- Objective 5：保持约 66%。本轮不是 Objective 5 external proof，没有真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue 或 worker/migration。
- Objective 1：本轮不推进真实硬件 HIL-entry；PR #5 所需 2D LiDAR / ToF / vendor/source / 参数化硬件材料仍等待真实材料。

## 5. Owner 与并行策略

本轮是 4 task Epic sprint，A/B/C 文件范围互不重叠，按 AGENTS.md 并行启动强制规则执行：

- Task A Autonomy Algorithm Engineer：新增 PC evidence dispatch gate 和 focused unittest，消费 acceptance brief artifact / summary，输出 dispatch artifact / summary。
- Task B Robot Platform Engineer：新增 diagnostics metadata-only consumer 和 focused diagnostics unittest，同步 `docs/interfaces/ros_contracts.md`。
- Task C User Touchpoint Full-Stack Engineer：新增 mobile/web 只读“现场证据包派发” panel、fixture/test，同步 `docs/product/mobile_user_flow.md`。
- Task D Product Manager / OKR Owner：收口时更新 `tech-done.md`、`side2side_check.md`、`final.md`、`OKR.md` 和 `docs/process/okr_progress_log.md`。

## 6. 风险、阻塞和证据链缺口

- Objective 5 external proof 仍缺：真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、production worker/migration。
- Objective 1 / PR #5 硬件材料仍缺：真实 2D LiDAR / ToF SKU、vendor/source、receipt、procurement、installation、wiring、power、calibration、HIL-entry、WAVE ROVER / UART / `T=1001` feedback。
- Objective 2 / Objective 3 仍缺真实现场材料：Nav2/fixed-route runtime log、route completion signal、task record、door_state、target_floor_confirmation、human_assistance_note、dropoff_or_cancel_completion、delivery_result 和同一 `evidence_ref` 的上车实机复账。
- Objective 4 仍缺：真实 iPhone/Android device behavior、production app、真实 PWA prompt/user choice 和真实现场 phone behavior。

## 7. 本轮需要创建或更新的 sprint 文档

Planning 阶段创建：

- `sprints/2026.05.17_06-07_route-task-field-retest-evidence-dispatch/pre_start.md`
- `sprints/2026.05.17_06-07_route-task-field-retest-evidence-dispatch/prd.md`
- `sprints/2026.05.17_06-07_route-task-field-retest-evidence-dispatch/tech-plan.md`

实现完成后必须继续补齐：

- `sprints/2026.05.17_06-07_route-task-field-retest-evidence-dispatch/tech-done.md`
- `sprints/2026.05.17_06-07_route-task-field-retest-evidence-dispatch/side2side_check.md`
- `sprints/2026.05.17_06-07_route-task-field-retest-evidence-dispatch/final.md`
