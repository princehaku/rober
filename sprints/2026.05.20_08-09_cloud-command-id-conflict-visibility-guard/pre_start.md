# Sprint 2026.05.20_08-09 Cloud Command ID Conflict Visibility Guard - Pre Start

## 1. 迭代声明

- sprint_type: epic
- 主题：`cloud_command_id_conflict_visibility_guard`
- 计划目录：`sprints/2026.05.20_08-09_cloud-command-id-conflict-visibility-guard/`
- 本轮状态：planning only。本轮只创建 `pre_start.md`、`prd.md`、`tech-plan.md`，不实现代码。
- 目标证据边界：`software_proof_docker_cloud_command_id_conflict_visibility_guard`

## 2. 背景证据

- `OKR.md` 4.1 显示 Objective 5 约 68%，是当前完成度最低 Objective。
- Objective 5 仍缺真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/cutover 和真实手机/browser。当前本机没有真实硬件，只有 Docker/local software proof 条件，不能把外部 blocker 包装成进展。
- 最近 sprint `2026.05.20_06-07_cloud-command-idempotency-visibility-guard/final.md` 已完成 duplicate command cached ACK 可见化：同一 `command.id` 重复提交时不重复执行，并在 Robot/operator/mobile 显示 duplicate/deduped 状态。
- 下一层 O5 command/status/ack 风险是：同一 `command.id` 携带不同 `type` 或 `payload` 时，不能被当成普通 duplicate cached ACK，必须 fail closed 成 `command_id_conflict`。
- 最近 sprint `2026.05.20_07-08_hardware-sensor-hil-entry-callback-intake/final.md` 说明 Objective 1 真实 2D LiDAR / ToF 与 WAVE ROVER/HIL 材料仍缺，不应再消费同一硬件 blocker。
- PR #5 live review evidence：`PRRT_kwDOSWB9286CJ3tX` 仍 unresolved / material pending；PR #4 无 unresolved threads。

## 3. 用户价值和产品北极星

用户价值：

- 普通手机用户或云端重试链路出现同一 `command.id` 但内容不一致时，机器人不会把冲突命令误判成幂等 duplicate 并继续执行或复用 cached ACK。
- 手机端能看到明确中文状态：云端命令 ID 冲突，机器人已拒绝执行，主操作保持关闭。
- 支持人员能从 diagnostics 看到 safe command id、冲突字段摘要、fail-closed 状态和证据边界，判断这是控制面安全拦截，不是送达成功。

产品北极星：

- 云中转控制面必须让 command/status/ack 在弱网、重试、乱序和错误重放下可解释、可恢复、默认安全。
- 手机用户不需要理解 ROS2、ACK、payload hash 或幂等键，也不能因为冲突命令看到可点击主操作。

## 4. 本轮核心抓手

本轮计划锁定 Objective 5 控制面软件行为增量：

1. Robot bridge 对 duplicate id + mismatched `type` / `payload` fail closed。
2. Operator/diagnostics 输出 phone-safe `command_id_conflict` 状态。
3. mobile/web 只读展示冲突状态，并保持 `primary_actions_enabled=false`。
4. 产品文档和后续 closeout 必须使用 `software_proof_docker_cloud_command_id_conflict_visibility_guard`，不得声明真实外部云、真实手机/browser、HIL 或 delivery success。

## 5. Owner 和责任边界

- `robot-software-engineer`：主责 Robot bridge、operator gateway、diagnostics safe summary 和 focused tests。
- `full-stack-software-engineer`：主责 mobile/web 只读冲突状态展示、fixture、前端测试和手机产品文档。
- `product-okr-owner`：主责 sprint closeout、OKR/progress log 保守同步和证据边界验收。

## 6. 风险、阻塞和证据链

- 风险：把 `command.id` 相同但内容不同的命令当作普通 duplicate，会让错误指令复用旧 ACK 或遮盖真实冲突。
- 风险：手机端 copy 若只显示 ACK，用户可能误以为任务成功；必须显示 `command_id_conflict` 和“不是送达成功”。
- 阻塞：真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/cutover、真实手机/browser、WAVE ROVER/HIL 和真实送达均不可用。
- 必须补齐的证据链：Robot conflict guard tests、operator diagnostics safe summary、mobile fixture/test、docs/product 同步、sprint `tech-done.md` / `side2side_check.md` / `final.md` 和 scoped `git diff --check`。

## 7. 需要创建或更新的 sprint 文档

本轮 planning 任务创建：

- `pre_start.md`
- `prd.md`
- `tech-plan.md`

后续 implementation / closeout 必须继续创建或更新：

- `tech-done.md`
- `side2side_check.md`
- `final.md`
