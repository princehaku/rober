# Sprint 2026.05.20_08-09 Cloud Command ID Conflict Visibility Guard - PRD

## 1. 产品问题

上一轮 `cloud_command_idempotency_visibility_guard` 已证明：同一 `command.id` 的重复请求可以复用 cached ACK，并让手机端看到 duplicate/deduped 状态。但这个前提只适用于“同一个命令内容重复提交”。

如果同一 `command.id` 携带不同 `type` 或 `payload`，它不是普通 duplicate，而是控制面一致性冲突。Robot bridge 必须 fail closed，operator/diagnostics/mobile 必须显示 `command_id_conflict`，不能复用 cached ACK，也不能让手机端主操作可用。

## 2. 用户价值和产品北极星

用户价值：

- 弱网、云端重试、客户端 bug 或人工重放造成 command id 冲突时，机器人拒绝执行冲突命令。
- 手机用户看到“命令 ID 冲突，机器人已拒绝执行”，而不是把旧 ACK 当成新命令结果。
- 支持人员能用 safe diagnostics 判断冲突来自 command id reuse with mismatched type/payload，而不是机器人硬件故障或真实送达结果。

产品北极星：

- 云中转控制面在错误重试和冲突重放下仍默认安全、可解释、可复盘。
- 普通用户只看中文安全状态，不接触 raw JSON、ROS topic、`/cmd_vel`、串口、WAVE ROVER 参数或凭证。

## 3. OKR 映射

### Objective 5：云中转 + OSS/CDN 数据通路产品化

- KR1 command/status/ack 契约：同一 command id 的内容一致 duplicate 才能走 cached ACK；内容不一致必须输出 conflict guard。
- KR6 graceful degradation：冲突命令保持 `remote_ready=false`、`primary_actions_enabled=false`，并给出支持诊断入口。

Objective 5 completion 保守保持约 68%。本轮没有真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/cutover 或真实手机/browser，只能形成 Docker/local software proof。

### Objective 4：手机用户体验与低成本量产边界

- mobile/web 只读展示 `command_id_conflict`。
- Start Delivery、Confirm Dropoff、Cancel 在冲突状态下保持 disabled。
- 手机 copy 必须中文优先，说明冲突命令已拒绝执行，不能当作送达成功。

Objective 4 不因本轮提高 completion。本轮不是真实手机/browser proof。

### Objective 1：硬件协议可信底盘

本轮不触碰 WAVE ROVER、UART、HIL、2D LiDAR / ToF 材料，也不关闭 PR #5 `PRRT_kwDOSWB9286CJ3tX`。Objective 1 不提高 completion。

## 4. KR 拆解或更新

- KR-A Robot conflict guard：Robot bridge 记录 command id 的 canonical command identity；同一 id 但 `type` 或 `payload` 不一致时，输出 `command_id_conflict` 并拒绝执行。
- KR-B ACK 安全：conflict 不得复用 cached ACK，不得再次调用 collect / confirm_dropoff / cancel backend，不得推进 cursor 成功语义。
- KR-C Diagnostics 可见性：operator gateway 和 diagnostics 输出 safe command id、conflict reason、mismatched fields summary、`remote_ready=false`、`primary_actions_enabled=false`。
- KR-D 手机只读展示：mobile/web 渲染冲突状态，显示中文 fail-closed copy，主操作保持 disabled。
- KR-E 文档同步：`docs/product/remote_4g_mvp.md` 和 `docs/product/mobile_user_flow.md` 写清 command id conflict 与 duplicate deduped 的差异。
- KR-F 证据边界：所有实现、测试和 closeout 使用 `software_proof_docker_cloud_command_id_conflict_visibility_guard`，显式否定 delivery success、real phone/browser、real cloud、OSS/CDN live traffic、HIL 和真实送达。

## 5. 范围内

- Robot bridge duplicate-id conflict detection。
- Operator gateway / diagnostics phone-safe conflict summary。
- mobile/web read-only `command_id_conflict` panel/copy。
- Focused Robot unittest、mobile unittest、`node --check`、`py_compile`、scoped `git diff --check`。
- 产品文档、sprint closeout、OKR/progress log 保守同步。

## 6. 范围外

- 不实现真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/cutover。
- 不实现真实手机/browser/device acceptance。
- 不触碰 WAVE ROVER、UART、串口、HIL、2D LiDAR、ToF、Nav2/fixed-route 或 route/elevator field proof。
- 不新增自动重放、自动 resubmit、自动 conflict recovery command。
- 不把 conflict rejection、ACK、accepted、acked、ignored、cached ACK 或 diagnostics pass 写成真实送达。

## 7. 本轮核心抓手

把云控制面的 idempotency 从“重复同内容去重可见”推进到“同 id 不同内容冲突可见且 fail closed”。

建议用户可见状态字段：

```text
degradation_state=command_id_conflict
conflict_command_id=<safe command id or [redacted]>
conflict_reason=duplicate_id_mismatched_type_or_payload
ack_semantics=conflict_rejected_not_delivery_success
remote_ready=false
primary_actions_enabled=false
retry_hint=contact_support_or_refresh_status
proof_boundary=software_proof_docker_cloud_command_id_conflict_visibility_guard
```

字段名可由 `robot-software-engineer` 按现有 schema 最小调整，但必须保留同等语义并能被 tests/docs/rg 证明。

## 8. 优先级和验收口径

- P0：Robot bridge 对同一 `command.id` + mismatched `type` fail closed，不执行本地 action。
- P0：Robot bridge 对同一 `command.id` + mismatched `payload` fail closed，不复用 cached ACK。
- P0：operator/diagnostics/mobile 可见 `command_id_conflict`，并保持 `remote_ready=false`、`primary_actions_enabled=false`。
- P1：mobile/web 中文 copy 明确“命令 ID 冲突；机器人已拒绝执行；这不是送达成功”。
- P1：产品文档同步 duplicate deduped 与 conflict rejected 的差异。
- P1：Product closeout 不提高 Objective 5 / Objective 4 / Objective 1 completion。

## 9. 对应责任 Engineer

- `robot-software-engineer`：Robot bridge conflict guard、operator diagnostics summary、Robot focused tests、`docs/product/remote_4g_mvp.md`。
- `full-stack-software-engineer`：mobile/web fixture/UI/test、`docs/product/mobile_user_flow.md`。
- `product-okr-owner`：OKR/progress log、sprint `tech-done.md`、`side2side_check.md`、`final.md` 和验收口径收口。

## 10. 风险、阻塞和需要补齐的证据链

- 风险：payload 比较若基于 raw JSON 字符串，字段顺序差异可能误报 conflict；实现应定义 canonical identity 或明确 hash 规则。
- 风险：conflict 状态若覆盖 pending ACK / expired command，手机端会显示错误 recovery advice；验收必须覆盖优先级。
- 风险：mobile copy 若只写“冲突已处理”，用户可能误解为任务成功；必须包含 delivery success 否定边界。
- 阻塞：真实 external cloud / phone / hardware 材料仍缺；这不阻塞本轮 software proof，但阻止 OKR completion 提升。
- 证据链：Robot conflict tests、operator diagnostics rg、mobile fixture/test、product docs rg、sprint closeout rg、scoped `git diff --check`。
