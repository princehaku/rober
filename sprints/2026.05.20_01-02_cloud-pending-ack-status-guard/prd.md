# Sprint 2026.05.20_01-02 Cloud Pending ACK Status Guard - PRD

## 1. 用户价值

普通手机用户不理解 pending ACK、cursor 或 worker replay。他们只需要知道当前机器人是否能安全接收下一条远程命令。

`cloud_pending_ack_status_guard` 的用户价值是：当本地命令已经终态，但云端 ACK 仍未确认或补发失败时，手机端能看到保守降级状态，而不是继续显示远程通路可用、允许新命令，或误把“本地终态”当成“云端已确认交付成功”。

## 2. 产品北极星

北极星仍是普通手机用户可安全使用的低成本 ROS2 自主垃圾投递机器人。本轮只改 command/status/ack 可靠性和用户可见状态，不改变硬件事实、不新增控制入口、不把 Docker proof 写成真实云/4G/手机/HIL/送达完成。

## 3. OKR 映射

- Objective 5：云中转 + OSS/CDN 数据通路产品化。
  - KR1 command/status/ack 契约：pending terminal ACK 未确认时，remote worker 必须 fail closed 并输出一致的 status/readiness。
  - KR6 4G 中断 graceful degradation：ACK replay 失败属于远程控制降级，必须区分“网络/云 ACK 未确认”和“机器人任务成功”。
- Objective 4：手机用户体验与低成本量产边界。
  - 手机端只读展示 remote degraded / command pending 状态，中文 copy 面向普通用户，不暴露 raw JSON、ROS topic 或 ACK 内部细节。

本轮不提升 Objective 5 百分比。`OKR.md` 4.1 当前 O5 约 68%，但 completion 仍需要真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/cutover 或真实手机/browser 外部材料。本轮边界固定为 `software_proof_docker_cloud_pending_ack_status_guard`。

## 4. KR 拆解或更新

### P0：pending ACK replay 失败时 remote readiness 必须 fail closed

- 当 pending terminal ACK 存在且补发仍失败时，Robot 侧 status/readiness 必须包含稳定降级语义，例如：
  - `degradation_state=command_pending`
  - `remote_ready=false`
  - `pending_terminal_ack_id=<redacted safe command id>`
  - `primary_actions_enabled=false`
  - phone-safe copy：本地命令已终态，但云端 ACK 还没确认，暂不能拉取新命令。
- pending ACK 成功前不得推进 `last_terminal_ack_id`，不得拉取新 command，不能触发本地新命令。

### P0：手机端只消费状态，不新增控制动作

- Full-Stack 侧只读消费 Robot/status readiness 语义，并在 existing panel / fixture / copy 中展示 command pending degraded 状态。
- Start Delivery、Confirm Dropoff、Cancel 等主操作必须保持 disabled 或沿用 existing gating。
- UI copy 不能写成 delivery success、route/elevator field pass、real phone acceptance 或 cloud production ready。

### P1：文档和证据边界同步

- `docs/product/remote_4g_mvp.md` 必须说明 pending ACK status guard 的触发条件、状态字段、fail-closed 行为和 `software_proof_docker_cloud_pending_ack_status_guard` 证据边界。
- `docs/product/mobile_user_flow.md` 如被 Full-Stack 修改，必须写明这是 Docker/local browser/UI fixture proof，不是真实手机/browser 现场验收。

## 5. 本轮核心抓手

核心抓手是 `cloud_pending_ack_status_guard`：把上一轮“pending ACK 可以持久化和补发”的内部恢复能力，推进为“pending ACK 仍失败时，Robot 和手机端都能看到同一套保守状态”的用户可感知 fail-closed 能力。

这不是新的 cloud wrapper，也不是 external proof。它必须直接作用于 command/status/ack 主链路，减少用户在云 ACK 未确认期间误操作或重复下发命令的风险。

## 6. 需要做什么

1. Robot Platform Engineer：
   - 在 pending terminal ACK 补发失败路径输出 degraded status/readiness。
   - 确保 status 字段为 safe subset，不包含 token、cloud URL credential、serial device、WAVE ROVER 参数、raw ROS topic、`/cmd_vel`、traceback 或 delivery success claim。
   - 用 focused unit tests 覆盖 pending ACK replay failure、no new command fetch、no cursor advance 和 status redaction。
2. User Touchpoint Full-Stack Engineer：
   - 消费现有 status/readiness 语义，补充 command pending degraded fixture/copy。
   - 确认主操作仍 disabled，且不会把 pending ACK 状态展示成成功送达。
   - 用 existing mobile/web test fence 和 `node --check` 验证。
3. Product Manager / OKR Owner：
   - 验收 docs、OKR 边界和 sprint closeout。
   - 确认 `PRRT_kwDOSWB9286CJ3tX` 仍 unresolved / `blocked_pending_real_materials`，不能因本轮关闭。

## 7. 优先级和验收口径

- P0：pending ACK 补发失败时，remote readiness fail closed，`remote_ready=false`，pending ACK 成功前不推进 cursor、不拉取新 command、不执行新控制。
- P0：手机端展示 command pending degraded copy，主操作不可用，copy 明确“本地命令已终态但云 ACK 未确认”。
- P0：证据边界明确为 `software_proof_docker_cloud_pending_ack_status_guard`，不声明真实 4G、公网 HTTPS/TLS、production DB/queue、真实手机/browser、HIL 或 delivery success。
- P1：文档同步更新，保留 Objective 5 约 68% 的保守口径。

## 8. 风险、阻塞和需要补齐的证据链

- 最大阻塞仍是 O5 external proof：真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、production worker/cutover、多实例一致性和真实手机/browser 仍不可用。
- O1/PR #5 仍 blocked：`PRRT_kwDOSWB9286CJ3tX` 缺真实 2D LiDAR / ToF SKU/source/receipt/procurement/installation/wiring/power/calibration/HIL-entry 材料。
- PR #4 route/elevator field materials 仍缺：真实 Nav2/fixed-route runtime log、route completion signal、field task record、elevator door state、target floor confirmation、human assistance record、dropoff/cancel material 和 delivery result。
- 本轮只能补齐 software-proof 状态链，不能作为 OKR 百分比提升、真实材料回填、PR thread closure、真实手机通过或真实送达证据。
