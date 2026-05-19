# Sprint 2026.05.20_02-03 Cloud Command Expiry Safety Guard - Pre Start

## 1. Sprint 类型和主题

- sprint_type: epic
- Sprint 主题：`cloud_command_expiry_safety_guard`。
- 证据边界：`software_proof_docker_cloud_command_expiry_safety_guard`。
- 本机环境：Docker/local software proof only；没有真实硬件、真实 4G/SIM、真实公网 HTTPS/TLS、OSS/CDN live traffic、production DB/queue、真实手机/browser、WAVE ROVER/UART/HIL 或真实 delivery success。

## 2. 上轮状态和证据

- 最新 sprint `sprints/2026.05.20_01-02_cloud-pending-ack-status-guard/final.md` 已完成 pending ACK replay failure 的 phone-safe `command_pending` 降级状态：`remote_ready=false`、`primary_actions_enabled=false`，pending ACK 成功前不 fetch new command、不推进 `last_terminal_ack_id`、不重复本地 action。
- `OKR.md` 4.1 当前最低仍是 Objective 5，约 68%。但 O5 completion 仍缺真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、production worker/cutover、真实手机/browser 等外部材料。
- GitHub PR #5 的评审证据仍未完全关闭：`PRRT_kwDOSWB9286CJ3tX` unresolved / `blocked_pending_real_materials`，原因是 mandatory sensor assumptions 缺真实 2D LiDAR / ToF vendor/source/receipt/procurement/installation/wiring/power/calibration/HIL-entry 材料。该缺口不能由本轮 O5 软件证明关闭。
- 近期 PRD/评审主线反复出现的问题是：ACK/cursor/command 状态容易被误解成 delivery success 或真实云证明。上一轮修复 pending ACK，本轮继续补 stale/expired command 的用户可见 fail-closed 状态，避免过期云命令被执行或被手机端误读。

## 3. 本轮目标

在已有 `command_expired(command)` 和 expired command ignored ACK 基础上，补齐过期云命令的端到端可见安全语义：

- Robot 侧遇到 expired remote command 时，不提交本地 action，ACK `ignored`，并输出 `degradation_state=command_expired`、`remote_ready=false`、`expired_command_id`、`primary_actions_enabled=false`、phone-safe copy 和 proof boundary。
- Operator gateway / phone readiness 能识别 `command_expired`，把 Start / Confirm Dropoff / Cancel 保持 fail-closed，并提示用户重新下发新指令，而不是等待 ACK 或误认为送达成功。
- mobile/web 只读展示该状态，沿用现有 cloud readiness / command safety gate，不新增控制 endpoint。
- Product closeout 更新 `OKR.md`、`docs/process/okr_progress_log.md` 和 sprint 六文档，明确本轮不提升 O5 百分比，也不关闭 PR #5 unresolved thread。

## 4. Owner 和分工

- `robot-software-engineer`：`remote_bridge` expired command status、operator gateway readiness classification、focused tests、`docs/product/remote_4g_mvp.md`。
- `full-stack-software-engineer`：mobile/web cloud readiness consumption、fixture/test、`docs/product/mobile_user_flow.md`。
- `product-okr-owner`：OKR / progress log / sprint closeout，核对证据边界和 PR #5 unresolved 状态。

## 5. 重复 blocker 核对

本轮不继续包装 O5 external-material blocker，也不新增真实材料 wrapper。它针对 command/status/ack 主链路的一个具体功能缺口：过期云命令的可见 fail-closed 状态。若实现发现该状态已完整覆盖，则 Product 应停止本轮或转为只读 closeout，不得堆重复 metadata。
