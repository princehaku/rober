# Sprint 2026.05.18_01-02 Route Task Result Review Intake - PRD

sprint_type: epic

## 1. 用户价值

本轮用户不是终端手机用户本人，而是 route/elevator 现场支持、评审人员和后续集成 verifier。他们需要把上一轮 result callback review handoff 真正摄取成 result review intake：明确本次材料是否可以进入 result review、是否保持同一 safe `evidence_ref`、缺哪些真实现场材料、哪些 owner 需要补齐、哪些情况必须 rerun。

用户收益：

- 不把 `handoff`、ACK、summary、completion signal 或 diagnostics panel 当成真实送达成功。
- 能看到 result review intake 对 PR #4 route/elevator material chain 的下一步要求。
- 能在 PC、Robot diagnostics、mobile/web 三个触点看到同一 metadata-only 结论。
- 能保持 `not_proven`、`delivery_success=false`、`primary_actions_enabled=false`，避免误启用主操作。

## 2. 产品北极星

北极星仍是：把 `rober` 做成面向普通手机用户的低成本 ROS2 自主垃圾投递机器人，能可验证地完成送垃圾任务并把失败原因讲清楚。

本轮不追求新 UI 视觉、不新增真实控制能力、不做真实 route/elevator pass 声明。它只把 PR #4 route/elevator result chain 的“可复核入口”补上，让未来真实现场材料可以按同一 `evidence_ref` 被摄取、复核和追责。

## 3. OKR 映射

- Objective 2：可送垃圾任务 + 电梯 assisted delivery 必达闭环。本轮推进 result review intake，让电梯/路线 result materials 可以进入复核入口，但不证明真实送达、真实电梯、真实 dropoff/cancel completion。
- Objective 3：可验证导航与固定路线能力。本轮要求 Nav2/fixed-route runtime log、route completion signal、task record 与同一 `evidence_ref` 的 result review intake 对齐，但不证明真实路线采集或实跑。
- Objective 4：手机用户体验与低成本量产边界。本轮只增加只读 phone-safe panel，帮助普通用户或支持人员理解“仍未证明”和下一步材料，不改变主操作授权。
- Objective 5：不作为本轮目标。Objective 5 约 68%，但需要真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、production worker/cutover 或真实手机/browser external proof，本 Docker-only 主机不能推进。
- Objective 1：不作为本轮目标。Objective 1 约 81%，但真实 WAVE ROVER HIL packet blocker 已被最近三轮消费，本轮不重复包装同一硬件缺口。

## 4. KR 拆解

### KR-A Autonomy Intake Gate

产出 `route_task_field_retest_result_review_intake` PC gate：

- 输入上一轮 `route_task_field_retest_result_callback_review_handoff` artifact / summary。
- 校验 safe `evidence_ref`、source schema、handoff status、review-ready package、rerun package、owner follow-up 和 next required evidence。
- 输出 `trashbot.route_task_field_retest_result_review_intake.v1` 与 summary。
- evidence boundary 固定为 `software_proof_docker_route_task_field_retest_result_review_intake_gate`。
- 缺字段、unsafe `evidence_ref`、success copy、boundary mismatch、真实材料缺失或 schema mismatch 都必须 fail closed。

### KR-B Robot Diagnostics Consumer

Robot diagnostics 只读消费 Autonomy summary：

- 暴露 metadata-only safe summary。
- 保持 `not_proven`、`delivery_success=false`、`primary_actions_enabled=false`。
- 不暴露 raw artifacts、local absolute paths、checksums、ROS raw topic、`/cmd_vel`、serial/UART、WAVE ROVER 参数、credentials。
- 缺 summary 时显示 blocked/not_proven，不编造状态。

### KR-C Mobile Read-Only Panel

mobile/web 增加只读 “路线/电梯结果复核入口” panel：

- 消费 `route_task_field_retest_result_review_intake` 或 summary。
- 展示 review intake status、safe `evidence_ref`、missing materials、owner follow-up、rerun package、next required evidence、evidence boundary、not_proven。
- 不改变 Start Delivery、Confirm Dropoff、Cancel gating。
- 不 fetch raw artifacts，不发送 robot command。

### KR-D Product Closeout

实现完成后 Product 做阶段收口：

- 更新 `OKR.md` 4.1，只能描述 software proof / metadata-only 进展。
- 更新 `docs/process/okr_progress_log.md`。
- 更新本 sprint `tech-done.md`、`side2side_check.md`、`final.md`。
- 明确没有真实 route/elevator field pass、真实 Nav2/fixed-route、真实手机/browser、HIL、Objective 5 external proof。

## 5. 本轮核心抓手

把 result callback review handoff 变成 result review intake gate。抓手不是再做一个泛化 checklist，而是让“进入 result review 前是否可收件”成为 PC/Robot/mobile 三面一致的 contract。

## 6. 优先级

P0：

- Autonomy PC gate 和 focused unittest。
- evidence boundary、safe `evidence_ref`、`not_proven`、`delivery_success=false`、`primary_actions_enabled=false` 的 fail-closed contract。
- Robot diagnostics metadata-only consumer。
- mobile/web read-only panel，不改变主操作授权。

P1：

- 文档同步：`docs/interfaces/evidence_contracts.md`、`docs/interfaces/ros_contracts.md`、`docs/product/mobile_user_flow.md`。
- Product closeout 更新 `OKR.md` 与 progress log。

P2：

- 后续真实现场材料回填：真实电梯门状态、真实楼层确认、人工协助记录、Nav2/fixed-route runtime log、route completion signal、task record、dropoff/cancel completion、delivery result。

## 7. 验收口径

必须满足：

- 新 gate 能在本地 Docker/PC-only software proof 语义下生成 intake artifact / summary。
- 三面 summary 均包含 `software_proof_docker_route_task_field_retest_result_review_intake_gate`。
- 三面均保留 `not_proven`、`delivery_success=false`、`primary_actions_enabled=false`。
- 缺失、mismatch、unsafe copy、success claim、raw artifact 泄漏必须 fail closed。
- mobile/web 只能展示只读 panel，不改变 Start / Confirm Dropoff / Cancel 授权。
- 文档必须同步更新。
- 验证只跑 focused unittest、`py_compile`、`node --check`、targeted `rg`、scoped `git diff --check`，不做大范围无关回归。

不得满足为完成：

- 不得把 intake summary 写成 route/elevator field pass。
- 不得把 diagnostics/mobile panel 写成真实手机/browser proof。
- 不得把 ACK、completion signal 或 handoff status 写成 delivery success。
- 不得声称 HIL、真实 WAVE ROVER、真实 Nav2/fixed-route、Objective 5 external proof。

## 8. 风险、阻塞和证据链缺口

- Objective 5 真实外部证据仍缺：公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、production worker/cutover、真实手机/browser external proof。
- Objective 1 真实硬件证据仍缺：WAVE ROVER、UART、真实串口日志、`feedback_T1001.log`、`/odom`、`/imu/data`、`/battery`、operator HIL report。
- PR #5 硬件材料仍缺：真实 2D LiDAR / ToF SKU/source/receipt/install/wiring/power/calibration/HIL-entry。
- PR #4 route/elevator field materials 仍缺：真实门状态、真实楼层确认、人工协助记录、Nav2/fixed-route runtime log、route completion signal、task record、dropoff/cancel completion、delivery result。
- 本轮只能降低 result review intake 的证据链混乱风险，不能提升真实现场完成度。

## 9. 需要创建或更新的 sprint 文档

本任务创建：

- `sprints/2026.05.18_01-02_route-task-result-review-intake/pre_start.md`
- `sprints/2026.05.18_01-02_route-task-result-review-intake/prd.md`
- `sprints/2026.05.18_01-02_route-task-result-review-intake/tech-plan.md`

实现和 closeout 阶段必须继续更新：

- `sprints/2026.05.18_01-02_route-task-result-review-intake/tech-done.md`
- `sprints/2026.05.18_01-02_route-task-result-review-intake/side2side_check.md`
- `sprints/2026.05.18_01-02_route-task-result-review-intake/final.md`
