# Sprint 2026.05.20_00-01 Cloud ACK Outage Replay Guard - PRD

## 1. 用户价值

普通手机用户不关心 ACK、cursor 或 worker 重启；他们只需要机器人在网络抖动后不要重复执行同一条本地命令，并且手机端不要把“云端没收到终态 ACK”误解释成任务已经成功送达。

`cloud_ack_outage_replay_guard` 的用户价值是：在 4G / 云端 ACK 上报短暂失败后，机器人重启仍能保守恢复终态上报链路，先补发已执行命令的 terminal ACK，再推进 `last_terminal_ack_id`，让云端 command/status/ack 契约保持可复盘。

## 2. OKR 映射

- Objective 5：云中转 + OSS/CDN 数据通路产品化。
  - 相关 KR：KR1 command/status/ack 契约、KR6 4G 中断 graceful degradation。
  - 本轮只补强 `remote_bridge` 在 ACK outage + worker restart 下的本地恢复语义。
- Objective 4：手机用户体验与低成本量产边界。
  - 只读确认现有 phone-safe degradation copy 是否足够解释 pending ACK / remote degraded；默认不新增 UI。

本轮不提升 Objective 5 百分比。`OKR.md` 4.1 当前 O5 约 68%，但 completion 需要真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/cutover 或真实手机/browser 外部材料。本轮边界固定为 `software_proof_docker_cloud_ack_outage_replay_guard`。

## 3. 产品需求

### P0：pending ACK 可持久化恢复

- 当本地命令已经执行并形成 terminal ACK payload，但 `cloud.post_ack(...)` 因网络、鉴权以外的云端临时错误或 malformed ACK response 失败时，worker 必须把待补发 ACK 持久化为不含凭证、不含 raw ROS topic、不含硬件细节的 pending ACK state。
- worker 重启后必须先加载 pending ACK，并在下一轮 poll 中优先补发 pending ACK。
- pending ACK 成功发到云端后，才允许推进并持久化 `last_terminal_ack_id`。

### P0：避免重复执行本地命令

- 如果 pending ACK 对应命令已经在本地执行过，重启后的 worker 不能因为 `last_terminal_ack_id` 尚未推进而再次调用 `start_collection`、`confirm_dropoff` 或 `cancel_collection`。
- 补发 ACK 只代表云端接收到了本地终态上报，不代表真实 delivery success。

### P1：状态和文档边界清晰

- `docs/product/remote_4g_mvp.md` 必须写清 ACK outage replay 的恢复顺序、持久化字段、清理时机和 proof boundary。
- 若 phone-safe degradation copy 已能覆盖 pending ACK / remote degraded，本轮 full-stack 只读确认即可；若不能覆盖，后续实现阶段应升级风险并决定是否新增 UI 文案。

## 4. 非目标

- 不实现 production DB/queue、multi-instance worker consistency、worker migration/cutover 或真实云部署。
- 不把本地 ACK replay 测试写成真实 4G 恢复、真实手机/browser、HIL、真实送达或 delivery success。
- 不关闭 PR #5 review thread `PRRT_kwDOSWB9286CJ3tX`，也不把本轮结果计入真实 2D LiDAR / ToF hardware material evidence。

## 5. 验收口径

本轮 implementation 后应能用 targeted unit tests 和 py_compile 证明：

- ACK POST 失败后 pending ACK 被持久化，`last_terminal_ack_id` 不推进。
- worker 重启后先补发 pending ACK，补发成功后才推进 cursor。
- 重启补发 pending ACK 不重复执行本地命令。
- pending ACK state 不包含 bearer token、cloud URL credential、serial device、WAVE ROVER 参数、raw ROS topic、`/cmd_vel`、traceback 或 delivery success claim。
- `docs/product/remote_4g_mvp.md` 和 sprint closeout 继续标注 `software_proof_docker_cloud_ack_outage_replay_guard`。

## 6. 风险

- 当前 `remote_bridge` 已有 in-memory command result replay 和 cursor persistence，但 ACK outage 后 worker 重启会丢失 in-memory result；本轮需要把这个 gap 收敛到持久化 pending ACK。
- 本轮计划不改变 cloud relay production backing store，后续真实生产仍可能遇到多 worker、队列顺序、DB transaction 和 cutover 风险。
- 如果现有 mobile/web 文案把 pending ACK 误导成 delivery success，需要在实现阶段重新评估 UI 改动范围；当前 planning 默认只读确认。
