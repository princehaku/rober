# Sprint 2026.05.17_10-11 Route Task Field Retest Callback Review Decision - Pre Start

sprint_type: epic

## 1. 启动背景

本轮 fresh Epic sprint 目标为 `route_task_field_retest_callback_review_decision`。产品北极星仍是让普通手机用户把垃圾交给低成本 ROS2 小车后，可以通过固定路线和电梯 assisted delivery 获得可验证、可解释、可复盘的送达体验；工程侧必须把 Docker-only software proof 与真实 field pass、HIL、真实手机/browser 和 Objective 5 external proof 分开。

当前 `OKR.md` 4.1 快照更新时间为 2026-05-17 09:23 Asia/Shanghai：

- Objective 1：约 77%
- Objective 2：约 90%
- Objective 3：约 90%
- Objective 4：约 99%
- Objective 5：约 68%

Objective 5 当前数值最低，但 `OKR.md` 第 6 节明确：只有拿到至少一种真实外部材料时才应继续推进 O5 completion，包括真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue connectivity、production worker/migration/cutover 或真实手机/browser 证据。当前主机只有 Docker，最近 `sprints/2026.05.17_07-08_cloud-worker-migration-rehearsal/final.md` 与 `sprints/2026.05.17_08-09_cloud-worker-cutover-drain-gate/final.md` 已把 O5 worker/migration/cutover 的 local software proof 推到约 68%；继续堆 O5 local metadata wrapper 不能形成真实 external proof。

最新 sprint `sprints/2026.05.17_09-10_route-task-field-retest-callback-intake/final.md` 已完成 `route_task_field_retest_callback_intake`：把 PR #4 route/elevator field materials 从 evidence dispatch 推进到 sanitized callback 可回填，并通过 PC gate、Robot diagnostics 和 mobile/web 同步展示 received/missing/same-evidence-ref/next-backfill 状态。该 final 明确仍缺真实现场材料，证据边界为：

- `software_proof_docker_route_task_field_retest_callback_intake_gate`
- `not_proven`
- `delivery_success=false`
- `primary_actions_enabled=false`

GitHub PR #4 已把 elevator-assisted delivery 写进 agents / registry / OKR，但 PR 描述明确没有 runtime integration tests，留下 route/elevator field material 后续链路。GitHub PR #5 review 暴露三个硬件/source 与 OKR 口径风险：P1 `docs/product/production_hardware_boundary.md` 默认硬件集合与 `monocular + 2D LiDAR + ToF` mandatory baseline 矛盾；P2 新硬件传感器假设缺 `docs/vendor/` source；P2 低完成度叙述与表格不一致。这些硬件/source blocker 已被多轮硬件材料 ladder 消费，当前仍无真实材料，本轮不继续包装同一硬件 blocker。

## 2. 本轮目标

新增 `route_task_field_retest_callback_review_decision` planning 和 implementation 入口，把上一轮 callback intake 的 received/missing/same-evidence-ref/next-backfill 状态审阅成明确 decision：

- `ready_for_result_intake`
- `needs_material_backfill`
- `evidence_ref_mismatch_rerun`
- `unsupported_callback_schema`
- `blocked_unsafe_callback`
- `blocked_success_claim`

本轮必须保持：

- `software_proof_docker_route_task_field_retest_callback_review_decision_gate`
- `trashbot.route_task_field_retest_callback_review_decision.v1`
- `trashbot.route_task_field_retest_callback_review_decision_summary.v1`
- `not_proven`
- `delivery_success=false`
- `primary_actions_enabled=false`

本轮只读上一轮 callback intake artifact / summary / wrapper / nested JSON，生成 metadata-only decision artifact / summary，并向 PC / Robot diagnostics / mobile(web) 暴露只读 decision summary。它不读取真实现场材料目录，不访问 ROS graph、Nav2 runtime、serial/UART、WAVE ROVER、真实电梯、真实手机/browser、外部云、OSS/CDN、DB/queue 或 4G。

## 3. 用户价值和产品北极星

用户价值：现场支持人员不再只看到 callback intake 的“收到/缺失”状态，而是能看到下一步明确决策：可以进入 result intake、需要补材料、证据号错配需重跑、schema 不支持或存在越界成功/控制声明。PC、Robot diagnostics 和手机只读页面使用同一份 decision summary，减少现场复测后“材料回来了但不知道能否进入结果入口”的歧义。

产品北极星：普通手机用户最终只需要理解机器人能否继续任务、哪里需要人工介入；工程侧必须保证 route/elevator 关键行为围绕同一 `evidence_ref` 可回放、可复核、可审阅，且不会把本地 callback review decision 误写成真实送达。

## 4. OKR 映射

- Objective 2：把电梯 assisted delivery 现场回执从 intake 状态推进到 decision，明确 door_state、target_floor_confirmation、human_assistance_note、dropoff_or_cancel_completion、delivery_result 是否足以进入结果入口或需要补齐。
- Objective 3：把 Nav2/fixed-route runtime log、route completion signal、task record 的 same-`evidence_ref` 回执审阅成可执行 next step，降低真实固定路线复测材料错配后被误采信的风险。
- Objective 4：mobile/web 只读展示“现场回执复核决策”状态，帮助现场人员理解下一步动作，但不改变 Start Delivery、Confirm Dropoff、Cancel gating。
- Objective 5：保持约 68%。本轮不是 Objective 5 external proof，没有真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue 或 worker/migration/cutover。
- Objective 1：本轮不推进真实硬件 HIL-entry；PR #5 所需 2D LiDAR / ToF / vendor/source / 参数化硬件材料仍等待真实材料。

## 5. Owner 与并行策略

本轮是 4 task Epic sprint，A/B/C 文件范围互不重叠，按 AGENTS.md 并行启动强制规则执行；Task D 等 A/B/C worker 证据返回后执行收口。

- Task A Autonomy Algorithm Engineer：新增 PC callback review decision CLI / test / docs，消费 callback intake artifact / summary，输出 review decision artifact / summary。
- Task B Robot Platform Engineer：新增 diagnostics metadata-only decision consumer，同步 `docs/interfaces/ros_contracts.md`。
- Task C User Touchpoint Full-Stack Engineer：新增 mobile/web 只读“现场回执复核决策” panel、fixture/test，同步 `docs/product/mobile_user_flow.md`。
- Task D Product Manager / OKR Owner：收口时更新 `tech-done.md`、`side2side_check.md`、`final.md`、`OKR.md` 和 `docs/process/okr_progress_log.md`。

## 6. 风险、阻塞和证据链缺口

- Objective 5 external proof 仍缺：真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue connectivity、production worker/migration/cutover。
- Objective 1 / PR #5 硬件材料仍缺：真实 2D LiDAR / ToF SKU、vendor/source、receipt、procurement、installation、wiring、power、calibration、HIL-entry、WAVE ROVER / UART / `T=1001` feedback。
- Objective 2 / Objective 3 仍缺真实现场材料：Nav2/fixed-route runtime log、route completion signal、task record、door_state、target_floor_confirmation、human_assistance_note、dropoff_or_cancel_completion、delivery_result 和同一 `evidence_ref` 的上车实机复账。
- Objective 4 仍缺：真实 iPhone/Android device behavior、production app、真实 PWA prompt/user choice 和真实现场 phone behavior。

## 7. 本轮需要创建或更新的 sprint 文档

Planning 阶段创建：

- `sprints/2026.05.17_10-11_route-task-field-retest-callback-review-decision/pre_start.md`
- `sprints/2026.05.17_10-11_route-task-field-retest-callback-review-decision/prd.md`
- `sprints/2026.05.17_10-11_route-task-field-retest-callback-review-decision/tech-plan.md`

实现完成后必须继续补齐：

- `sprints/2026.05.17_10-11_route-task-field-retest-callback-review-decision/tech-done.md`
- `sprints/2026.05.17_10-11_route-task-field-retest-callback-review-decision/side2side_check.md`
- `sprints/2026.05.17_10-11_route-task-field-retest-callback-review-decision/final.md`
