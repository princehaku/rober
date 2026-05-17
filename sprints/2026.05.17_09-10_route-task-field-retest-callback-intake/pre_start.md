# Sprint 2026.05.17_09-10 Route Task Field Retest Callback Intake - Pre Start

sprint_type: epic

## 1. 启动背景

本轮 fresh Epic sprint 目标为 `route_task_field_retest_callback_intake`。产品北极星仍是让普通手机用户把垃圾交给低成本 ROS2 小车后，可以通过固定路线和电梯 assisted delivery 获得可验证、可解释、可复盘的送达体验；工程侧必须把 Docker-only software proof 与真实 field pass、HIL、真实手机/browser 和 Objective 5 external proof 分开。

当前 `OKR.md` 4.1 快照更新时间为 2026-05-17 08:59 Asia/Shanghai：

- Objective 1：约 77%
- Objective 2：约 89%
- Objective 3：约 89%
- Objective 4：约 99%
- Objective 5：约 68%

Objective 5 当前数值最低，但 `OKR.md` 第 6 节明确：只有拿到真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue connectivity、production worker/migration/cutover 或真实手机/browser 证据时，才应继续提升 O5 completion。当前主机只有 Docker，继续堆 O5 local wrapper 不能形成真实外部证据，也不应继续上调 Objective 5。

最新 sprint `sprints/2026.05.17_08-09_cloud-worker-cutover-drain-gate/final.md` 已完成 `software_proof_docker_cloud_worker_cutover_drain_gate`，证明 Docker-only 的 pending command drain、cursor before/after、terminal ACK summary、idempotent rerun、partial-drain fail-closed 和 Robot metadata-only diagnostics fence；final 明确这不是 real external proof，下一步应拿真实外部材料，否则切回 PR #4 route/elevator field materials 或 PR #5 2D LiDAR / ToF materials。

GitHub PR #5 仍有 3 个未解决 review threads：

- P1：`docs/product/production_hardware_boundary.md` 默认硬件集未列 2D LiDAR / ToF，却又把 `monocular + 2D LiDAR + ToF` 作为 mandatory sensor baseline。
- P2：`OKR.md` lowest-objective claim 曾与表格数值漂移，会误导 sprint routing。
- P2：mandatory sensor assumptions 缺 `docs/vendor/` source，硬件假设不可追溯。

近期硬件 HIL-entry readiness / execution pack 已连续消费 PR #5 相关 blocker；继续只包一层硬件 blocker 会违反同一根因 blocker 重复消费红线。本轮不再做 O1/O4 硬件材料 wrapper。

PR #4 已把 elevator-assisted delivery 写成 required capability；PR #5 继续要求 2D LiDAR / ToF material evidence。最近 O2/O3 sprint `sprints/2026.05.17_06-07_route-task-field-retest-evidence-dispatch/final.md` 已把现场证据包派发给 owner/file/backfill/callback checklist，但仍缺一个“回执/回填入口”来接收现场人员回传的 sanitized callback metadata。

## 2. 本轮目标

新增 `route_task_field_retest_callback_intake` planning 和 implementation 入口，把上一轮 evidence dispatch 的 owner/file/backfill/callback checklist 转成 PC / Robot / mobile 三端可消费的 metadata-only callback intake。

本轮必须保持：

- `software_proof_docker_route_task_field_retest_callback_intake_gate`
- `trashbot.route_task_field_retest_callback_intake.v1`
- `trashbot.route_task_field_retest_callback_intake_summary.v1`
- `not_proven`
- `delivery_success=false`
- `primary_actions_enabled=false`

本轮只接收现场人员回传的 sanitized callback JSON：推荐文件名是否收到、`evidence_ref` 是否一致、缺项、下一次回填动作。它生成 artifact / summary，作为真实材料回填入口；它不证明真实 route/elevator field pass、HIL、真实手机/browser、真实 Nav2/fixed-route、真实投放、dropoff/cancel completion、delivery success 或 Objective 5 external proof。

## 3. 用户价值和产品北极星

用户价值：现场支持人员不再停在“已派发材料清单”，而是可以把实际回传状态用 sanitized JSON 回填到同一 `evidence_ref` 下，让 PC、Robot diagnostics 和手机只读页面都知道推荐文件名是否收到、哪些材料缺失、下一步该补哪项。

产品北极星：普通手机用户最终只需要理解机器人能否继续任务、哪里需要人工介入；工程侧必须保证 route/elevator 关键行为有同一 `evidence_ref` 可回放证据链，且不会把本地 callback intake 误写成真实送达。

## 4. OKR 映射

- Objective 2：把电梯 assisted delivery 的 door_state、target_floor_confirmation、human_assistance_note、dropoff_or_cancel_completion、delivery_result 从“派发清单”推进为可回执、可缺项、可下一步回填的 callback intake。
- Objective 3：把 Nav2/fixed-route runtime log、route completion signal、task record 的同一 `evidence_ref` 回填入口固化，降低真实固定路线复测时文件名收到但证据号错配、缺项未登记或回填动作不明确的风险。
- Objective 4：mobile/web 只读展示“现场回执入口”状态，帮助现场人员理解缺项和下一步动作，但不改变 Start Delivery、Confirm Dropoff、Cancel gating。
- Objective 5：保持约 68%。本轮不是 Objective 5 external proof，没有真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue 或 worker/migration/cutover。
- Objective 1：本轮不推进真实硬件 HIL-entry；PR #5 所需 2D LiDAR / ToF / vendor/source / 参数化硬件材料仍等待真实材料。

## 5. Owner 与并行策略

本轮是 4 task Epic sprint，A/B/C 文件范围互不重叠，按 AGENTS.md 并行启动强制规则执行；Task D 等 A/B/C worker 证据返回后执行收口。

- Task A Autonomy Algorithm Engineer：新增 PC callback intake CLI / test / docs，消费 evidence dispatch artifact / summary 与 sanitized callback JSON，输出 callback intake artifact / summary。
- Task B Robot Platform Engineer：新增 diagnostics metadata-only consumer，同步 `docs/interfaces/ros_contracts.md`。
- Task C User Touchpoint Full-Stack Engineer：新增 mobile/web 只读“现场回执入口” panel、fixture/test，同步 `docs/product/mobile_user_flow.md`。
- Task D Product Manager / OKR Owner：收口时更新 `tech-done.md`、`side2side_check.md`、`final.md`、`OKR.md` 和 `docs/process/okr_progress_log.md`。

## 6. 风险、阻塞和证据链缺口

- Objective 5 external proof 仍缺：真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue connectivity、production worker/migration/cutover。
- Objective 1 / PR #5 硬件材料仍缺：真实 2D LiDAR / ToF SKU、vendor/source、receipt、procurement、installation、wiring、power、calibration、HIL-entry、WAVE ROVER / UART / `T=1001` feedback。
- Objective 2 / Objective 3 仍缺真实现场材料：Nav2/fixed-route runtime log、route completion signal、task record、door_state、target_floor_confirmation、human_assistance_note、dropoff_or_cancel_completion、delivery_result 和同一 `evidence_ref` 的上车实机复账。
- Objective 4 仍缺：真实 iPhone/Android device behavior、production app、真实 PWA prompt/user choice 和真实现场 phone behavior。

## 7. 本轮需要创建或更新的 sprint 文档

Planning 阶段创建：

- `sprints/2026.05.17_09-10_route-task-field-retest-callback-intake/pre_start.md`
- `sprints/2026.05.17_09-10_route-task-field-retest-callback-intake/prd.md`
- `sprints/2026.05.17_09-10_route-task-field-retest-callback-intake/tech-plan.md`

实现完成后必须继续补齐：

- `sprints/2026.05.17_09-10_route-task-field-retest-callback-intake/tech-done.md`
- `sprints/2026.05.17_09-10_route-task-field-retest-callback-intake/side2side_check.md`
- `sprints/2026.05.17_09-10_route-task-field-retest-callback-intake/final.md`
