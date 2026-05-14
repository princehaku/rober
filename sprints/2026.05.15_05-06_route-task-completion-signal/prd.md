# Sprint 2026.05.15_05-06 Route Task Completion Signal - PRD

sprint_type: epic

## 1. 用户价值和产品北极星

产品北极星：让不会 ROS2、串口或命令行的普通手机用户，把垃圾交给低成本小车后，能看到一次送垃圾任务是否真的走到了可解释的完成/未完成状态，并在失败时知道下一步要补什么证据或如何人工处理。

本轮用户价值不是证明真实送达，而是把 Docker/local route/task chain 从“材料复账 verdict”推进为“completion signal”：同一 `evidence_ref` 下能回答任务有没有足够材料证明完成、哪里缺 dropoff/cancel completion、固定路线或 task record 是否中断，以及失败/恢复原因是什么。这样下一次现场或上车执行时，Engineer 和操作员不再靠散落 artifact 猜测任务结果。

## 2. OKR 映射

- Objective 2：推进 KR4 和 KR5。completion signal 必须汇总 task record state transitions、dropoff/cancel completion flags、failure/recovery reason，并输出明确 action/result 口径；没有真实材料时必须保留 `delivery_success=false`。
- Objective 3：推进 KR2、KR3 和 KR5。completion signal 必须消费 fixed-route status/replay 与 route/task evidence，给 PC/diagnostics/mobile 一致的固定路线完成状态视图。
- Objective 4：仅做只读触点增量。mobile/web 展示 completion verdict，但不改变 Start/Confirm/Cancel gating，不证明真实 iPhone/Android 或 production app。
- Objective 5：本轮不推进。没有真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue 或 worker/migration 材料。

## 3. KR 拆解或更新

本轮不直接修改 `OKR.md`。实现完成并通过验收后，closeout 才能根据证据保守更新 Objective 2 / Objective 3。

建议本轮 KR 证据拆解：

- O2.KR4：completion verdict 至少区分 `completed_not_proven`、`blocked_missing_completion_materials`、`blocked_mismatch_evidence_ref`、`failed_with_recovery_reason` 这类可执行状态。
- O2.KR5：completion artifact 必须包含起止/目标摘要、状态转换摘要、dropoff/cancel completion flags、failure/recovery reason、same `evidence_ref` 检查和 operator next steps。
- O3.KR2/KR3：CLI 必须支持 Docker/local fixed-route status/replay 与 task record 输入；无硬件、无 Nav2 时仍可验证读取、汇总和 fail-closed 输出。
- O3.KR5：diagnostics 与 mobile 只能消费 summary，不读取 raw artifact、本机路径、ROS topic、串口或硬件细节。

## 4. 本轮核心抓手

核心抓手：`software_proof_docker_route_task_completion_signal_gate`。

它不是再包一层 metadata wrapper。验收标准是产生一份可被三端复用的 completion signal：

- Autonomy 生成 `schema=trashbot.route_task_completion_signal.v1` artifact。
- Robot diagnostics 只读消费 explicit ref 或环境变量指向的 artifact，并导出 metadata-only summary。
- Full-stack mobile/web 展示只读 completion panel，继续 fail closed。

## 5. 需要做什么

1. Autonomy：新增 PC/evidence completion-signal CLI，读取上一轮 reconciliation 或同类 route/task 材料、fixed-route status/replay、task record、dropoff/cancel completion flags、failure/recovery reason，输出 phone-safe completion artifact。
2. Robot：在 diagnostics 层增加 metadata-only consumption。它只能暴露 `route_task_completion_signal` / summary，不能触发 collect/dropoff/cancel、ACK POST、cursor/persistence、terminal ACK、Nav2、WAVE ROVER、HIL 或 delivery claim。
3. Full-stack：在 `mobile/web` 增加只读“路线任务完成信号”panel，展示 completion verdict、safe `evidence_ref`、dropoff/cancel completion status、failure/recovery reason、operator next steps、`delivery_success=false` 和 `not_proven`。
4. 三条线都必须同步更新对应 `docs/` 文档，并把代码技术注释保持中文且超过 20% 的规范作为 review 条件。

## 6. 优先级和验收口径

优先级：

1. P0：completion signal schema、evidence boundary、same `evidence_ref`、`delivery_success=false`、`not_proven` 边界不可漂移。
2. P0：CLI、diagnostics、mobile 三端字段名兼容，缺材料时必须 blocked/not_proven。
3. P1：operator next steps 必须能指导下一次真实 Nav2/fixed-route、dropoff/cancel 或现场复账材料采集。
4. P1：验证围栏只跑目标 unittest、`py_compile`、`node --check` 和 scoped `git diff --check`，不做大范围回归。

验收口径：

- 通过 Autonomy CLI 样例输出和 targeted unittest。
- 通过 Robot diagnostics targeted unittest，确认 metadata-only 字段不会触发动作或 ACK。
- 通过 mobile/web targeted unittest 和 JS syntax check，确认 panel 只读、缺 summary blocked/not_proven、按钮 gating 不变。
- 通过 required `rg`，能看到 `software_proof_docker_route_task_completion_signal_gate`、`delivery_success=false`、`not_proven`、`primary_actions_enabled=false`、`dropoff_completion`、`cancel_completion`、`same_evidence_ref_required`。
- closeout 前不得更新 `OKR.md` 完成度；只有实现和验证证据通过后才由 Product Owner 收口。

## 7. 对应责任 Engineer

- Autonomy Algorithm Engineer：`autonomy-engineer`，负责 PC/evidence completion-signal CLI、测试和 `docs/navigation/`。
- Robot Platform Engineer：`robot-software-engineer`，负责 diagnostics metadata-only consumption、测试和 `docs/interfaces/`。
- User Touchpoint Full-Stack Engineer：`full-stack-software-engineer`，负责 mobile/web 只读 panel、测试和 `docs/product/`。

Hardware Infra Engineer 本轮不介入；本轮不改硬件、不引入真实串口或 WAVE ROVER 参数。

## 8. 风险、阻塞和需要补齐的证据链

风险：

- Docker/local completion signal 容易被误读为真实送达完成；因此所有输出必须固定保留 `delivery_success=false` 和完整 `not_proven`。
- dropoff/cancel completion flags 若来自缺失或模拟材料，只能写为 missing/not_proven，不能推导为 completed。
- mobile/web 面板若展示过多 raw 信息，会违反 phone-safe 和普通用户入口原则。
- Robot diagnostics 若把 summary 当 command envelope，会破坏安全边界。

仍需补齐的真实证据链：

- 真实 Nav2/fixed-route 运行。
- 真实路线采集与关键帧实景证据。
- 同一 `evidence_ref` 的上车实机复账。
- 真实 dropoff completion、cancel completion、failure recovery。
- WAVE ROVER、真实串口/UART、`T=1001` feedback、HIL。
- 真实手机设备/browser、production app、PWA prompt/user choice。
- Objective 5 external proof：公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/migration。

## 9. 需要创建或更新的 sprint 文档

本 planning 阶段只创建：

- `sprints/2026.05.15_05-06_route-task-completion-signal/pre_start.md`
- `sprints/2026.05.15_05-06_route-task-completion-signal/prd.md`
- `sprints/2026.05.15_05-06_route-task-completion-signal/tech-plan.md`

实现阶段完成后必须继续补齐：

- `sprints/2026.05.15_05-06_route-task-completion-signal/tech-done.md`
- `sprints/2026.05.15_05-06_route-task-completion-signal/side2side_check.md`
- `sprints/2026.05.15_05-06_route-task-completion-signal/final.md`

