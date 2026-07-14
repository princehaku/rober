# O3 Runtime Wait AMCL CLI Closeout PRD

## 用户价值和产品北极星

产品北极星不变：普通手机用户把垃圾交给机器人后，机器人能沿固定路线稳定送达。当前最接近这条主链路的有效抓手不是 O5 support-only，也不是继续产出 graph fallback summary，而是把真实板 no-motion runtime wait 和 AMCL/TF gate 收口到可判断 path generation 的状态。本 sprint 的价值是为 current same-run path generation success、Nav2 route execution success 和后续 delivery evidence 补齐前置门槛。

## OKR 映射和方向判断

- O5 当前约 `85%`，是数字最低 Objective；但缺口是公网 HTTPS/TLS、4G/SIM、production DB/queue、worker/cutover、OSS/CDN live traffic、真实手机/browser 等 external evidence。没有新 external evidence 时继续 O5 support-only 不计 OKR 增量。
- O1、O6、O7 当前约 `93%`。O1 的主要缺口仍包括 current same-run path generation success 与 Nav2 route execution success；本轮 O3 no-motion runtime/path gate 是当前环境下最接近 O1 缺口的可执行前置链路。
- 方向判断：`调整执行优先级`，不直接做 O5；`继续` O3/O1 strict no-motion runtime wait / AMCL CLI fallback closeout；`暂停` O5 support-only；`不调整` 百分比；`不归档` KR。

## 问题定义

截至 `23-49` final，true-board graph fallback 已证明进入 `ros2 node list`，但 live artifact 仍停在：

- `partial_runtime_in_progress`
- `last_phase=managed_runtime_started`
- `current_command.command=ros2 node list`
- `recent_commands[*].error.type=TimeoutExpired`
- `path_generation_attempted=false`
- `path_generated=false`

缺口是：

1. final `managed_runtime_wait_result` 尚未写出，graph wait 最终 root cause 仍未完成 closeout。
2. AMCL CLI fallback 虽已实现并通过单测，但没有 live closeout artifact。
3. gate 未 ready 前不能进入 planner-only path attempt，因此必须继续保持 `path_generation_attempted=false`。

本 sprint 要解决的问题是：如何让 true-board graph wait 自然收口，并把 AMCL CLI fallback 的现场 inventory 消费掉，避免继续用 partial/fallback-readback 冒充 path readiness。

## 范围内

- O3/O1 no-motion localization/runtime/path readiness
- true-board managed runtime wait final closeout
- `ros2 node list` fallback 的最终结果归因
- AMCL CLI fallback live closeout
- `/tf`、`/tf_static`、`/amcl` 只读 inventory
- gate ready 后的 planner-only `ComputePathToPose` attempt
- 后续 `tech-done.md`、`side2side_check.md`、`final.md` 证据记录

## 范围外

- O5 production / external evidence 实现
- O6/O7 archive/readback/UI
- 手机/Web/API
- NavigateToPose
- 真实 route execution
- delivery/operator acceptance
- HIL pass
- 发布 `/cmd_vel`
- `/api/base/manual`
- WAVE ROVER UART
- 任何真实底盘运动

## KR 拆解、更新或历史归档

本轮不提前归档 KR，不提前调整百分比。只有出现以下事实之一，后续 closeout 才能讨论 OKR 增量：

- current same-run `path_generated=true`
- Nav2 route execution success
- current live HIL acceptance
- delivery/operator acceptance
- 真实 production external evidence

若本轮只拿到 final `managed_runtime_wait_result` 或 AMCL CLI fallback closeout，最多计为 O3/O1 supporting diagnostic delta；不得归档 O1 current path / route / HIL KR。

已完成 KR 历史记录位置：本轮无新增完成 KR，历史区不更新。证据来源仅记录在本 sprint 的 `tech-done.md`、`side2side_check.md`、`final.md` 以及 live artifact 中。

## 本轮核心抓手

1. 把 `partial_runtime_in_progress` 转成自然结束的 final runtime wait closeout。
2. 明确 `ros2 node list` fallback 的最终状态，不再只记录 current command。
3. 让 AMCL CLI fallback 在 true-board artifact 中产出 closeout。
4. 保持 no-motion 和 fail-closed；gate 未 ready 时继续 `path_generation_attempted=false`、`path_generated=false`。

## 成功标准

计划阶段成功标准：

- 三份初始文档完整存在：`pre_start.md`、`prd.md`、`tech-plan.md`
- `tech-plan.md` 包含 `## OKR 最低优先级核对`
- owner、文件范围、接口边界、no-motion 强约束、验收命令和 acceptance criteria 明确

implementation 阶段成功标准：

- final `managed_runtime_wait_result` 出现在 true-board artifact 中
- AMCL CLI fallback closeout 出现在 true-board artifact 中，或给出比 `23-49` 更窄的 blocked reason
- 所有 safety/control/HIL/delivery 字段保持 false
- gate 未 ready 时 `path_generation_attempted=false`、`path_generated=false`
- gate ready 时才允许 planner-only `ComputePathToPose` attempt，且必须记录 attempt/generated 结果

## 不加分边界

以下结果不能算 OKR 新进展：

- 继续重复 O5 support-only packet/readback
- 只证明 `managed_runtime_started=true`
- 只证明 `ros2 node list` fallback 已执行
- 只留下 `partial_runtime_in_progress`
- 只有 `path_generation_requested=true`
- 没有 AMCL CLI fallback live closeout
- 没有 final `managed_runtime_wait_result`
- 任意突破 no-motion 边界的“成功”

## 优先级和验收口径

P0 验收：

- `managed_runtime_wait_result` 必须最终落盘；若失败，失败原因必须比 `TimeoutExpired` current command 更可执行。
- AMCL CLI fallback 必须被现场消费；如果没跑到，必须说明挡在 managed wait 哪一层。
- `safe_to_control=false` 必须保留。

P1 验收：

- 若 gate ready，允许 planner-only `ComputePathToPose` attempt。
- 若 path attempt 未发生，`path_generation_attempted=false` 必须有明确 gate blocked reason。
- 若 path attempt 发生，`path_generated=false` 或 `path_generated=true` 都必须有 planner-only artifact 支撑。

## 风险、阻塞和需要补齐的证据链

- true-board graph wait 可能仍卡在 `ros2 node list`，导致 AMCL CLI fallback 无法进入现场 closeout。
- AMCL CLI fallback 可能暴露 `/tf`、`/tf_static` 或 `/amcl` inventory 缺失，仍不足以支持 path attempt。
- 即使 planner-only path attempt 成功，也不等于 NavigateToPose、route execution、delivery success 或 HIL。
- 后续仍需补齐 same-run path artifact、route execution result、delivery/operator acceptance、current live HIL 或 production external evidence。
