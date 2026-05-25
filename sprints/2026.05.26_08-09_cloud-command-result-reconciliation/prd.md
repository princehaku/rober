# Cloud Command Result Reconciliation PRD

## 1. 用户价值和产品北极星

普通用户从手机发出“开始送垃圾 / 确认投放 / 取消”后，不能只看到一个“已入队”回执就结束。用户需要知道命令现在处于哪个安全状态：还在队列里、机器人已领取/处理中、已经有终态 ACK、结果材料仍缺失，还是云端查询失败。

产品北极星：手机是唯一普通用户入口，云端中转把命令与状态解释成普通中文，所有状态都 fail closed，永远不把 queued、processing、ACK terminal 或本地软件证明写成真实送达成功。

## 2. OKR 映射

- Objective 5：云中转 + OSS/CDN 数据通路产品化。
- 当前最低项：Objective 5 约 72%。
- 本轮预期贡献：从“phone -> cloud command enqueue”推进到“phone-safe command lifecycle query / reconciliation”。是否提升 OKR 百分比由后续 `tech-done.md`、`side2side_check.md`、`final.md` 按验证结果决定。
- 不宣称：公网 HTTPS/TLS、真实 4G/SIM、OSS/CDN live traffic、production DB/queue、HIL、真实手机/browser、Nav2/fixed-route 或 delivery success。

## 3. KR 拆解或更新

本轮不直接修改 `OKR.md`，但实现完成后应在 closeout 更新 Objective 5 证据链：

- KR1：`trashbot.remote.v1` command/status/ack 契约补齐手机安全查询入口，支持按 command id 对账 queued / processing / terminal / missing 状态。
- KR6：云链路 graceful degradation 增加 result reconciliation 失败边界，例如 store unavailable、command missing、ACK pending、terminal result pending。
- Objective 4 关联：手机端必须把状态解释成人能看懂的中文，并保持主操作 fail closed。

## 4. 本轮核心抓手

能力名：`cloud_command_result_reconciliation`

用户故事：

- 作为普通手机用户，我发起送垃圾任务后，能看到“命令已入队，等待机器人处理”。
- 当机器人领取或 ACK 后，我能看到“命令已接收/处理中，尚无真实 delivery/dropoff/cancel result”。
- 当云端已有 terminal ACK 但缺 verified terminal result 时，我能看到“命令已终态，但仍未证明送达/投放/取消完成”。
- 当查询不到命令或 store 不可用时，我能看到“暂时无法确认，请等待或联系支持”，而不是绿色成功。

## 5. 需要做什么

Robot Software Engineer 需要做：

- 在 cloud relay 增加 phone-safe command lifecycle 查询能力。
- 复用既有 command store、ACK/status 语义，不绕开 robot outbound polling。
- 明确输出 schema、capability、evidence boundary、command id、ack/result/pending 状态、next required evidence 和 false-state flags。
- 写单元测试覆盖 queued、processing、terminal result pending、missing、store unavailable、敏感字段脱敏。
- 同步更新云中转产品文档。

User Touchpoint Full-Stack Engineer 需要做：

- `mobile/web` 用同源 API 查询刚入队命令的 lifecycle summary。
- receipt 面板升级为可展示 pending / processing / terminal-result-pending / missing-or-unavailable 的状态区。
- 继续禁用 Start Delivery / Confirm Dropoff / Cancel，除非现有安全 gate 明确允许；本轮不得新增 control grant。
- 写 fixture 和测试，证明 UI 不暴露 raw `/robots/*`、ROS topic、`/cmd_vel`、serial/UART/WAVE ROVER、token、DB/queue URL、raw state path 或完整 artifact。
- 同步更新手机用户流程文档。

## 6. 优先级和验收口径

P0 验收：

- 用户能基于上一轮 receipt 的 `command_id` 查询 phone-safe command lifecycle summary。
- 查询结果必须覆盖 queued、processing、terminal-result-pending、missing-or-expired、store-unavailable 五类状态或等价状态。
- 所有状态都必须保留 `delivery_success=false`、`safe_to_control=false`、`primary_actions_enabled=false`，除非后续真实 verified delivery/dropoff/cancel result contract 明确提供成功证据。
- terminal ACK 不得被 UI 或 API 文案写成 delivery/dropoff/cancel success。
- 错误输出和 fixture 不包含敏感字段或底层机器人控制字段。
- 相关 `docs/product/` 文档同步更新。

P1 验收：

- command lifecycle summary 包含 `next_required_evidence`，能告诉支持同学下一步需要真实 robot ACK、verified terminal result、production DB/queue 或外部云证据中的哪一类。
- mobile/web 支持刷新或重新查询，但不得自动重放、自动 resubmit 或请求 raw diagnostics。

## 7. 对应责任 Engineer

- Robot Software Engineer：主责 backend contract、store 查询、HTTP route、单元测试和 cloud docs。
- User Touchpoint Full-Stack Engineer：主责 mobile/web 查询与展示、fixture、UI 测试和 mobile docs。
- Product Manager / OKR Owner：后续只做验收口径核对、OKR 进度判断和 sprint closeout。

## 8. 风险、阻塞和证据链

- 风险：本轮如果没有真实 production DB/queue，只能证明本地 store / SQLite / file-backed contract，不证明多实例一致性。
- 风险：ACK terminal 可能只是 robot bridge 对 command envelope 的处理结果，不代表行为状态机完成 delivery/dropoff/cancel。
- 风险：手机 UI 如果为了好看写成“已完成”，会破坏 false-state 边界，必须测试防住。
- 阻塞：真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、HIL 和真实手机/browser 仍不在本轮计划范围。
- 证据链：后续 `tech-done.md` 必须贴出 Robot 和 Full-Stack 验证命令日志；`side2side_check.md` 必须核对用户 copy；`final.md` 决定 Objective 5 是否从约 72% 提升。

## 9. 需要创建或更新的 sprint 文档

本轮已创建：

- `sprints/2026.05.26_08-09_cloud-command-result-reconciliation/pre_start.md`
- `sprints/2026.05.26_08-09_cloud-command-result-reconciliation/prd.md`
- `sprints/2026.05.26_08-09_cloud-command-result-reconciliation/tech-plan.md`

实现完成后必须继续更新：

- `sprints/2026.05.26_08-09_cloud-command-result-reconciliation/tech-done.md`
- `sprints/2026.05.26_08-09_cloud-command-result-reconciliation/side2side_check.md`
- `sprints/2026.05.26_08-09_cloud-command-result-reconciliation/final.md`
