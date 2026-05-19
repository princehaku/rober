# Sprint 2026.05.20_00-01 Cloud ACK Outage Replay Guard - Pre Start

## 1. Sprint 类型

- sprint_type: epic
- 启动时间：2026-05-20 00:01 Asia/Shanghai。
- Sprint 主题：`cloud_ack_outage_replay_guard`。
- 证据边界：`software_proof_docker_cloud_ack_outage_replay_guard`。
- 本轮只做 Docker/local software proof，不证明真实 4G、公网 HTTPS/TLS、production DB/queue、worker/cutover、HIL、真实手机/browser 或 delivery success。

## 2. 背景证据

- `OKR.md` 4.1 显示 Objective 5 当前约 68%，是数值最低 Objective；但 O5 completion 需要真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/cutover 或真实手机/browser 外部材料。本机只有 Docker，不能用本轮本地软件 proof 提升 O5 百分比。
- 最新 sprint `sprints/2026.05.19_23-24_real-material-followup-escalation-status/final.md` 明确写明“下一步不应继续堆本地 wrapper”，因此本轮不能再做一个只描述外部材料缺失的 wrapper。
- PR #5 review thread `PRRT_kwDOSWB9286CJ3tX` 仍 unresolved / `blocked_pending_real_materials`，缺真实 2D LiDAR / ToF vendor/source/procurement/material evidence；本轮不触碰该 thread closure，也不写成 O1 进度提升。
- `docs/product/remote_4g_mvp.md` 已有 `remote_bridge` terminal ACK cursor 边界：ACK POST 失败不能推进 `last_terminal_ack_id`，成功提交 terminal ACK 后才能持久化 cursor。

## 3. 本轮目标

当 remote bridge 已经执行本地命令，但 terminal ACK 上报云端失败时，worker 重启后必须能从持久化 pending ACK 恢复，先补发 ACK，再推进 `last_terminal_ack_id`。

本轮要避免两个产品级事故：

- 重启后重复执行已经被本地接收或完成的命令。
- ACK 补发成功前就推进 cursor，导致云端和本地状态分叉，并把未被云端确认的终态误写成 delivery success。

## 4. Owner 和分工

- `robot-software-engineer` 主责实现：
  - `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_bridge.py`
  - `onboard/src/ros2_trashbot_behavior/test/test_remote_bridge.py`
  - `docs/product/remote_4g_mvp.md`
- `product-okr-owner` 负责收口：
  - 本 sprint 文档
  - 后续 implementation 完成后的 `OKR.md`
  - 后续 implementation 完成后的 `docs/process/okr_progress_log.md`
- `full-stack-software-engineer` 只读确认：
  - 检查 `mobile/web` 是否已有 phone-safe degradation copy 能解释 pending ACK / remote degraded 状态。
  - 默认不改 UI，除非实现阶段发现现有文案会误导用户以为 delivery success。

## 5. Blocker 和不做事项

- 不做真实云部署、公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue 或 production worker/cutover。
- 不关闭 PR #5 unresolved thread `PRRT_kwDOSWB9286CJ3tX`。
- 不把 ACK replay guard 写成真实送达、真实 HIL、真实手机/browser 或 Objective 5 百分比提升。
- 不扩大到 cloud relay 多实例一致性、生产队列、备份恢复或 worker migration；这些仍需要真实生产环境材料。

## 6. 启动验收

本 pre-start 的完成标准是：本 sprint 目录已有 `pre_start.md`、`prd.md`、`tech-plan.md`，并且 `tech-plan.md` 给出 owner/file scopes、接口影响、验收命令、风险边界和 `OKR 最低优先级核对`。
