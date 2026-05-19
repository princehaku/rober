# Sprint 2026.05.20_01-02 Cloud Pending ACK Status Guard - Pre Start

## 1. Sprint 类型

- sprint_type: epic
- 启动时间：2026-05-20 01:02 Asia/Shanghai。
- Sprint 主题：`cloud_pending_ack_status_guard`。
- 证据边界：`software_proof_docker_cloud_pending_ack_status_guard`。
- 本轮只做 Docker/local software proof，不证明真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、production worker/cutover、真实手机/browser、Nav2/fixed-route、WAVE ROVER、HIL 或 delivery success。

## 2. 背景证据

- `OKR.md` 4.1 显示 Objective 5 当前约 68%，是数字最低 Objective；主要缺口仍是真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、production worker/cutover、多实例一致性、真实手机/browser 和外部生产材料。本机只有 Docker，因此本轮不能把本地软件 proof 写成 O5 completion 提升。
- 上一轮 `sprints/2026.05.20_00-01_cloud-ack-outage-replay-guard/final.md` 完成 `cloud_ack_outage_replay_guard`：本地命令已终态但 terminal ACK POST 失败或 malformed response 时，`remote_bridge` 会持久化 redacted `pending_terminal_ack`，worker restart / next poll 先补发 pending ACK，成功后才推进 `last_terminal_ack_id`。边界是 `software_proof_docker_cloud_ack_outage_replay_guard`。
- `sprints/2026.05.19_23-24_real-material-followup-escalation-status/final.md` 明确“下一步不应继续堆本地 wrapper”，因此本轮不再包装真实材料缺失，而是推进 command/status/ack 主链路的具体用户可见降级状态。
- GitHub PR #5 review thread 状态：`PRRT_kwDOSWB9286CJ3tQ` 与 `PRRT_kwDOSWB9286CJ3tU` 已 resolved；`PRRT_kwDOSWB9286CJ3tX` 仍 unresolved / `blocked_pending_real_materials`，说明 O1/PR #5 不能被本轮关闭或计入真实硬件材料完成。
- GitHub PR #4 电梯 assisted delivery 已合并为主线要求，且无开放 review threads；真实 route/elevator field materials 仍缺。本轮不消费 PR #4 blocker，也不声明真实 route/elevator field pass。

## 3. 用户价值和产品北极星

用户价值：普通手机用户在云端 ACK 仍未确认时，不应看到“可以继续发新命令”或“任务已完成”的错误信号；他们需要看到保守、可理解、可恢复的状态，例如“本地命令已终态，但云端 ACK 还没确认，暂不能拉取新命令”。

产品北极星：把 `rober` 做成普通手机用户可安全使用的远程垃圾投递机器人。手机端必须隐藏 ACK/cursor/replay 细节，但要清楚表达 remote control 是否安全可用，不能把云端未确认状态伪装成 delivery success。

## 4. 本轮目标

在 `cloud_ack_outage_replay_guard` 已经能持久化/补发 pending terminal ACK 的基础上，补齐 pending ACK replay 失败时的 phone-safe degraded status：

- Robot 侧在 pending ACK 仍未被云端确认时产生稳定 status/readiness 语义，例如 `degradation_state=command_pending`、`remote_ready=false`、`pending_terminal_ack_id` 和 phone-safe copy。
- Full-Stack 侧只消费/展示现有 status/readiness 语义，必要时补 fixture/copy 和测试，不新增控制动作。
- 系统必须保持 fail-closed：不触发新命令、不推进 cursor、不拉取新 command、不声称 delivery success、不打开 primary actions。

## 5. Team 分工

- `robot-software-engineer` 主责 Robot/cloud worker 语义：
  - pending ACK replay 失败时输出 phone-safe degraded status/readiness。
  - 保持 `last_terminal_ack_id` 不推进，且 pending ACK 成功前不拉取新 command。
  - 用 targeted tests 和 `py_compile` 验证。
- `full-stack-software-engineer` 主责手机端只读消费：
  - 消费 existing status/readiness 语义，展示 remote degraded / command pending copy。
  - 保持 Start Delivery、Confirm Dropoff、Cancel 等主操作 disabled，不新增控制动作。
  - 用 existing mobile/web test fence、`node --check` 和 fixture 检查验证。
- `product-okr-owner` 负责 sprint 留档、验收口径、OKR closeout 和 evidence boundary：
  - 本轮 planning docs、后续 `tech-done.md`、`side2side_check.md`、`final.md`。
  - 后续 implementation 完成后再更新 `OKR.md` 和 `docs/process/okr_progress_log.md`。
- `autonomy-engineer` 与 `hardware-engineer` 本轮不改文件；如实现阶段需要确认不影响 route/elevator 或 WAVE ROVER/HIL 证据边界，只做只读咨询。

## 6. Blocker 和不做事项

- 不做真实云部署、公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker migration/cutover、多实例一致性或 backup/recovery。
- 不关闭 PR #5 unresolved thread `PRRT_kwDOSWB9286CJ3tX`，不把本轮写成真实 2D LiDAR / ToF hardware material evidence。
- 不做真实手机/browser 验收、PWA prompt/user choice 现场验收、真实 route/elevator field pass、Nav2/fixed-route 实跑、WAVE ROVER/UART/HIL 或 delivery success。
- 不新增手机端控制动作，不暴露 raw ROS topic、`/cmd_vel`、bearer token、cloud credential、serial device、WAVE ROVER 参数或 traceback。

## 7. 需要创建或更新的 sprint 文档

本 planning 阶段必须创建：

- `sprints/2026.05.20_01-02_cloud-pending-ack-status-guard/pre_start.md`
- `sprints/2026.05.20_01-02_cloud-pending-ack-status-guard/prd.md`
- `sprints/2026.05.20_01-02_cloud-pending-ack-status-guard/tech-plan.md`

Implementation 完成后必须继续补齐：

- `tech-done.md`
- `side2side_check.md`
- `final.md`

后续 closeout 才能更新 `OKR.md` 和 `docs/process/okr_progress_log.md`；本 planning 任务不改这些文件。
