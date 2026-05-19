# Sprint 2026.05.20_06-07 Cloud Command Idempotency Visibility Guard - Pre Start

## 1. Sprint 类型和主题

- sprint_type: epic
- sprint 主题：`cloud_command_idempotency_visibility_guard`
- 启动时间：2026-05-20 06:07 Asia/Shanghai
- 当前阶段：planning only，本轮只创建 `pre_start.md`、`prd.md`、`tech-plan.md`，不实现产品代码。
- 目标证据边界：`software_proof_docker_cloud_command_idempotency_visibility_guard`

## 2. 开工输入和事实来源

- 已读 `AGENTS.md`：本轮为 Epic sprint planning，必须 fresh sprint folder，并在后续 implementation 阶段按 owner/file split 派发 `robot-software-engineer`、`full-stack-software-engineer` 和 `product-okr-owner`。
- 已读 `OKR.md`：4.1 显示 Objective 5 当前最低约 68%，但真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/cutover、真实手机/browser 仍缺，不能提高 O5 completion。
- 已读近期 O5 sprint final：
  - `cloud_ack_outage_replay_guard`
  - `cloud_pending_ack_status_guard`
  - `cloud_command_expiry_safety_guard`
- 已读 PR #5 closeout：`PRRT_kwDOSWB9286CJ3tQ` 与 `PRRT_kwDOSWB9286CJ3tU` resolved，`PRRT_kwDOSWB9286CJ3tX` unresolved / `is_resolved=false`，真实 2D LiDAR / ToF 和 HIL materials 仍缺。
- 已读 `docs/product/remote_4g_mvp.md` 与 `docs/product/mobile_user_flow.md`：当前 command/status/ack、pending ACK、expired command、mobile fail-closed copy 已有产品口径。

## 3. 上轮未完成项和阻塞

- O5 外部材料仍缺：公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue connectivity、production worker/migration/cutover、真实手机/browser。
- O1 / PR #5 真实材料仍缺：`PRRT_kwDOSWB9286CJ3tX` unresolved / `is_resolved=false`，缺真实 2D LiDAR / ToF SKU/source/receipt/procurement/installation/wiring/power/calibration/HIL-entry，也缺真实 WAVE ROVER/UART/HIL。
- 近期 O5 已连续推进 ACK outage replay、pending ACK status、command expiry safety，本轮不得再做纯阻塞包装；必须推进一个具体功能安全缺口。
- 当前 Robot test 已证明 duplicate command cached ACK 不重复提交 action，但 Robot/operator/mobile 状态仍缺显式可见的“重复云指令已去重，不代表 delivery success”安全状态。

## 4. 用户价值和产品北极星

用户价值：当普通手机用户或云端重试提交同一个 command id 时，机器人不重复执行本地 action，同时手机端能明确看到“重复云指令已去重，只复用 cached ACK，不代表真实送达成功”。用户不需要理解 ACK cursor、幂等 key 或 ROS2 action，也不会把 duplicate ACK 误读为 delivery success。

产品北极星：让普通手机用户通过云中转安全、可解释地控制送垃圾机器人；所有控制面重试、弱网和重复提交都必须 fail closed、可诊断、可复盘，且不暴露 `/cmd_vel`、ROS topic、硬件细节或凭证。

## 5. OKR 映射

- Objective 5：云中转 + OSS/CDN 数据通路产品化。
  - KR1：command/status/ack 契约补齐 command idempotency visibility，duplicate command 必须复用 cached ACK，不重复提交本地 action。
  - KR6：弱网/重试 graceful degradation 增加 duplicate command 去重可见状态，明确 ACK semantics 不是 delivery success。
- Objective 4：手机用户体验与低成本量产边界。
  - 手机端必须以中文安全文案展示 duplicate/deduped 状态，主操作保持 fail-closed，不允许自动重放、自动 resubmit 或扩展控制权限。
- Objective 1：保持不变。
  - 本轮不触碰 WAVE ROVER/UART/HIL，不关闭 `PRRT_kwDOSWB9286CJ3tX`，不提高 O1 completion。

## 6. 本轮核心抓手

把现有 duplicate command cached ACK 基础行为升级为跨 Robot/operator/mobile 可见的安全状态：

- Robot 侧输出 `degradation_state=command_duplicate_deduped` 或等价 phone-safe 状态。
- 状态包含 safe command id、cached ACK state、`remote_ready=false`、`primary_actions_enabled=false`、`ack_semantics=duplicate_cached_ack_not_delivery_success`、`retry_hint=refresh_status` 和 proof boundary。
- mobile/web 只读展示“重复云指令已去重；机器人没有重复执行；这不是送达成功”的中文文案。
- docs/product 同步 command idempotency visibility 的产品口径。

## 7. Owner 初始拆分

- `robot-software-engineer`：remote bridge / operator gateway status / diagnostics / Robot tests / `docs/product/remote_4g_mvp.md`。
- `full-stack-software-engineer`：mobile/web fixture、UI read-only panel/copy、mobile tests、`docs/product/mobile_user_flow.md`。
- `product-okr-owner`：sprint chain、OKR/progress log closeout、证据边界复核。

## 8. 风险和证据边界

- 本轮只能成为 `software_proof_docker_cloud_command_idempotency_visibility_guard`，不得写成真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、production worker/cutover、真实手机/browser、HIL、route/elevator field pass 或 delivery success。
- Duplicate ACK 只表示“重复 command id 已复用已知 ACK envelope”，不表示机器人完成送达、dropoff/cancel completion 或真实现场成功。
- 如果 implementation 阶段发现 duplicate state 会与 pending ACK / expired command 优先级冲突，Robot owner 必须先修状态优先级并用 focused unittest 围栏，不得扩大到生产 cloud redesign。

## 9. 需要创建或更新的 sprint 文档

- 本轮 planning 已创建：
  - `sprints/2026.05.20_06-07_cloud-command-idempotency-visibility-guard/pre_start.md`
  - `sprints/2026.05.20_06-07_cloud-command-idempotency-visibility-guard/prd.md`
  - `sprints/2026.05.20_06-07_cloud-command-idempotency-visibility-guard/tech-plan.md`
- 后续 implementation / acceptance 必须继续补齐：
  - `tech-done.md`
  - `side2side_check.md`
  - `final.md`
