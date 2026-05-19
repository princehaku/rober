# Sprint 2026.05.20_06-07 Cloud Command Idempotency Visibility Guard - PRD

## 1. 产品问题

云中转 command id 是幂等键，现有 Robot test 已覆盖 duplicate command cached ACK 不重复提交 action。但这个安全行为目前对 operator/mobile 用户不够显式：用户可能只看到 ACK 被再次返回，误以为机器人重复执行了动作，或误把 ACK 当成 delivery success。

本轮要解决的不是生产云外部证明，而是一个具体功能安全缺口：重复云指令必须被去重，并且去重状态必须在 Robot/operator/mobile 上可见、可解释、fail-closed。

## 2. 用户价值和产品北极星

用户价值：

- 手机用户重复点击、弱网重试或云端重放同一 command id 时，不会触发第二次本地 action。
- 手机端能直接看到“重复云指令已去重；机器人没有重复执行；这不是送达成功”。
- 支持人员能从 diagnostics 看到 safe command id、cached ACK state 和 proof boundary，快速判断这是幂等保护而非真实交付完成。

产品北极星：

- 普通手机用户不理解 ROS2、ACK、cursor 或幂等键，也能安全使用远程控制。
- 云控制面必须可恢复、可解释、默认安全，不能把 accepted/acked/ignored/cached ACK 包装成真实送达。

## 3. OKR 映射

### Objective 5：云中转 + OSS/CDN 数据通路产品化

- KR1 command/status/ack 契约：新增 duplicate command 去重可见状态，复用 cached ACK 时不重复提交本地 action。
- KR6 graceful degradation：重复提交、弱网重试、用户重复点击时保持 fail-closed 状态与可恢复提示。

Objective 5 completion 仍保持约 68%。本轮没有真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、production worker/cutover 或真实手机/browser，因此不能提高 O5 completion。

### Objective 4：手机用户体验与低成本量产边界

- 手机端展示去重状态和中文安全文案。
- Start Delivery、Confirm Dropoff、Cancel 在 duplicate/deduped 状态下继续 disabled。
- ACK semantics 必须显示为 `duplicate_cached_ack_not_delivery_success` 或等价安全字段。

Objective 4 不因本轮提高 completion。本轮不是真实手机/browser proof。

### Objective 1：硬件协议可信底盘

本轮不触碰 WAVE ROVER、UART、HIL、2D LiDAR / ToF 材料，也不关闭 PR #5 `PRRT_kwDOSWB9286CJ3tX`。Objective 1 不提高 completion。

## 4. KR 拆解

- KR-A Robot 可见性：duplicate command 复用 cached ACK 时，Robot/operator status 必须输出 phone-safe duplicate/deduped 状态。
- KR-B 本地 action 安全：duplicate command 不得再次调用 collect / confirm_dropoff / cancel backend。
- KR-C 手机可见性：mobile/web 渲染 read-only duplicate command panel/copy，并保持所有主操作 disabled。
- KR-D 文档同步：`docs/product/remote_4g_mvp.md` 与 `docs/product/mobile_user_flow.md` 写清 duplicate command 的产品语义和证据边界。
- KR-E 证据边界：所有实现、测试和 closeout 必须使用 `software_proof_docker_cloud_command_idempotency_visibility_guard`，并显式否定 delivery success、real phone/browser、real cloud 和 HIL。

## 5. 范围内

- `remote_bridge` duplicate command cached ACK 状态输出。
- `operator_gateway_http` / diagnostics 对 duplicate/deduped 状态的 phone-safe 聚合。
- `mobile/web` 对 duplicate/deduped 状态的只读展示和 fail-closed gating。
- Focused Robot unittest、mobile unittest、`node --check`、`py_compile` 和 scoped `git diff --check`。
- 产品文档和 sprint closeout 同步。

## 6. 范围外

- 不实现真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/cutover。
- 不实现真实手机/browser/device acceptance。
- 不触碰 WAVE ROVER、UART、串口、HIL、2D LiDAR、ToF、Nav2/fixed-route 或 route/elevator field proof。
- 不新增自动重放、自动 resubmit、自动 delivery success 推断。
- 不把 cached ACK、accepted、acked、ignored 或 duplicate 状态写成真实送达。

## 7. 优先级

- P0：duplicate command 不重复执行本地 action，且有 Robot/operator 可见状态。
- P0：mobile/web 展示 duplicate/deduped 中文安全文案，并保持主操作 disabled。
- P1：docs/product 同步产品口径和 evidence boundary。
- P1：sprint closeout / OKR / progress log 保守同步，不提高 O5/O1/O4 completion。

## 8. 验收口径

实现完成后必须满足：

- Robot test 证明 duplicate command 只调用一次 backend，但 ACK 可按 contract 复用或重新上报 cached envelope。
- Robot/operator status 包含 duplicate/deduped 状态、safe command id、cached ACK state、`remote_ready=false`、`primary_actions_enabled=false`、`ack_semantics=duplicate_cached_ack_not_delivery_success`、proof boundary。
- mobile/web fixture 和测试证明该状态可见，主操作 disabled，copy 不包含 raw ROS topic、`/cmd_vel`、serial/UART、baudrate、WAVE ROVER、credentials、traceback、delivery success claims。
- docs/product 和 sprint closeout 均明确：本轮不是 real cloud、real 4G、real phone/browser、HIL、route/elevator field pass 或 delivery success。

## 9. 责任 Engineer

- `robot-software-engineer`：P0 Robot/operator contract 和 Robot tests。
- `full-stack-software-engineer`：P0 mobile/web visible state 和 mobile tests。
- `product-okr-owner`：P1 sprint/OKR/docs closeout 和 evidence boundary。

## 10. 风险、阻塞和证据链

- 主要风险：duplicate 状态与 pending ACK / expired command 状态优先级冲突，导致手机端显示错误。验收必须覆盖状态优先级。
- 主要阻塞：真实 external cloud / phone / hardware 材料仍缺；这不阻塞本轮 software proof，但阻止 OKR completion 提升。
- 必须补齐证据链：Robot duplicate test、operator status/diagnostics rg、mobile fixture/test、product docs rg、sprint closeout rg、scoped diff check。
