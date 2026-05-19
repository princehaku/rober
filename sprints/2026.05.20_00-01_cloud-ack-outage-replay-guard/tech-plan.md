# Sprint 2026.05.20_00-01 Cloud ACK Outage Replay Guard - Tech Plan

## 1. 方案摘要

实现 `cloud_ack_outage_replay_guard`：在 `remote_bridge` 已执行本地命令但 terminal ACK 上报云端失败时，将 pending ACK 以 redacted durable state 保存；worker 重启后优先补发 pending ACK，补发成功后再推进 `last_terminal_ack_id`。

边界固定为 `software_proof_docker_cloud_ack_outage_replay_guard`。本轮不证明真实 4G、production DB/queue、worker/cutover、HIL、真实手机/browser 或 delivery success。

## 2. Owner/File Scopes

### robot-software-engineer 主责实现

允许修改：

- `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_bridge.py`
- `onboard/src/ros2_trashbot_behavior/test/test_remote_bridge.py`
- `docs/product/remote_4g_mvp.md`

实现任务：

- 为 `RemoteBridgeWorker` 增加 pending terminal ACK durable state。
- ACK POST 失败或 ACK response malformed 时，保存 pending ACK，但不推进 `last_terminal_ack_id`。
- worker 初始化时加载 pending ACK；`poll_once()` 在拉取新 command 前优先补发 pending ACK。
- pending ACK 补发成功后，推进并持久化 `last_terminal_ack_id`，随后清理 pending ACK。
- 新增 targeted tests 覆盖 outage、restart replay、no duplicate local execution、redacted state 和 malformed ACK response。
- 更新 `docs/product/remote_4g_mvp.md` 的 cursor/restart boundary，写明本轮 proof boundary。

### product-okr-owner 收口

允许在 implementation 完成后修改：

- `OKR.md`
- `docs/process/okr_progress_log.md`
- `sprints/2026.05.20_00-01_cloud-ack-outage-replay-guard/tech-done.md`
- `sprints/2026.05.20_00-01_cloud-ack-outage-replay-guard/side2side_check.md`
- `sprints/2026.05.20_00-01_cloud-ack-outage-replay-guard/final.md`

收口要求：

- 保持 Objective 5 约 68%，不得因为本地 software proof 提升完成度。
- 明确 `PRRT_kwDOSWB9286CJ3tX` 仍 unresolved / `blocked_pending_real_materials`。
- 记录本轮只证明 ACK outage replay guard，不证明真实 4G、production DB/queue、worker/cutover、HIL 或 delivery success。

### full-stack-software-engineer 只读确认

默认只读范围：

- `mobile/web/app.js`
- `mobile/web/index.html`
- `mobile/web/styles.css`
- `docs/product/mobile_user_flow.md`

确认任务：

- 核对现有 phone-safe degradation copy 是否足够解释 pending ACK、cloud unreachable、malformed response、remote degraded。
- 默认不改 UI；如果发现文案会把 pending ACK 误读为 delivery success，返回风险和建议，由 Product 决定是否扩大文件范围。

## 3. 接口影响

- `trashbot.remote.v1` cloud command/status/ack HTTP envelope 不变。
- `last_terminal_ack_id` 的推进规则不变：只有 terminal ACK 成功提交云端后才能推进。
- `cursor_state_path` 语义扩展：同一 durable state 可保存 redacted pending ACK；字段必须只包含 command id、ACK state/message/result safe subset、protocol version、robot id、updated_at 和 proof boundary，不保存 bearer token、cloud URL credential、serial device、WAVE ROVER 参数、raw ROS topic、`/cmd_vel`、traceback 或完整敏感 payload。
- 本轮不新增 phone endpoint，不新增 ROS topic，不改变 operator backend command semantics。
- pending ACK replay 不等于 delivery success；ACK state 仍只能反映本地 command 处理终态和云端 ACK 接收状态。

## 4. 实现步骤

1. 在 `test_remote_bridge.py` 先写 failing tests：
   - ACK POST 失败后 state file 包含 pending ACK，`last_terminal_ack_id` 未推进。
   - 新 worker 使用同一 state file 启动后，先补发 pending ACK，并且 backend calls 仍为空。
   - pending ACK 补发成功后，state file 中 `last_terminal_ack_id` 更新为 command id，pending ACK 被清理。
   - malformed ACK response 与 HTTP outage 走同一 pending ACK replay 保护。
   - state file 不包含敏感 marker：`Bearer`、`Authorization`、`/cmd_vel`、`WAVE ROVER`、`serial`、`baudrate`、`traceback`、`delivery_success=true`。
2. 在 `remote_bridge.py` 实现最小 durable pending ACK：
   - 读取 cursor state 时兼容旧 `{last_terminal_ack_id}` 文件。
   - ACK 失败时先保存 pending ACK，再记录 degraded status。
   - `poll_once()` 开头在 status POST 成功后优先补发 pending ACK；补发成功前不拉取新 command。
   - 原子写 state file，避免重启读到半截 JSON。
3. 更新 `docs/product/remote_4g_mvp.md`：
   - 增加 `cloud_ack_outage_replay_guard` 小节。
   - 写明 `software_proof_docker_cloud_ack_outage_replay_guard`、not real 4G、not production DB/queue、not worker/cutover、not delivery success。
4. 跑验收命令并修复失败；验证失败不得直接收口。

## 5. 验收命令

在 `/Users/m4/apps/rober` 运行：

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_remote_bridge.py
```

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_bridge.py
```

```bash
rg -n "cloud_ack_outage_replay_guard|pending ACK|last_terminal_ack_id|software_proof_docker_cloud_ack_outage_replay_guard|delivery success|production DB/queue|4G" onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_bridge.py onboard/src/ros2_trashbot_behavior/test/test_remote_bridge.py docs/product/remote_4g_mvp.md
```

```bash
git diff --check -- onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_bridge.py onboard/src/ros2_trashbot_behavior/test/test_remote_bridge.py docs/product/remote_4g_mvp.md sprints/2026.05.20_00-01_cloud-ack-outage-replay-guard
```

Product planning 文件验收命令：

```bash
test -f sprints/2026.05.20_00-01_cloud-ack-outage-replay-guard/pre_start.md && test -f sprints/2026.05.20_00-01_cloud-ack-outage-replay-guard/prd.md && test -f sprints/2026.05.20_00-01_cloud-ack-outage-replay-guard/tech-plan.md
```

```bash
rg -n "cloud_ack_outage_replay_guard|Objective 5|PRRT_kwDOSWB9286CJ3tX|software_proof_docker_cloud_ack_outage_replay_guard|OKR 最低优先级核对|robot-software-engineer" sprints/2026.05.20_00-01_cloud-ack-outage-replay-guard
```

```bash
git diff --check -- sprints/2026.05.20_00-01_cloud-ack-outage-replay-guard
```

## 6. 风险边界

- 本轮只能证明本地 worker state file + targeted unit tests 下的 ACK outage replay guard。
- 不证明真实公网 HTTPS/TLS、真实 4G/SIM、OSS/CDN live traffic、production DB/queue connectivity、production worker migration/cutover、多实例一致性、backup/recovery、真实手机/browser、Nav2/fixed-route、WAVE ROVER、HIL 或真实 delivery success。
- PR #5 `PRRT_kwDOSWB9286CJ3tX` 继续 blocked_pending_real_materials；本轮不提供真实 2D LiDAR / ToF vendor/source/procurement/material evidence。
- 如果 pending ACK state 设计需要保存完整 operator status，必须做 safe subset/redaction；不能把 raw ROS topic、硬件细节、token 或 traceback 写入持久化 state。
- 如果实现发现 `cursor_state_path` 兼容性不足，优先保持旧 cursor file 可读，不做破坏性迁移。

## 7. OKR 最低优先级核对

1. 当前 `OKR.md` 4.1 完成度最低 Objective：Objective 5，约 68%。
2. 本 sprint 是否针对最低 Objective：是，针对 Objective 5 的 command/status/ack 可靠性缺口，但只作为 `software_proof_docker_cloud_ack_outage_replay_guard`。
3. 不提升 O5 百分比的理由：O5 completion 仍需要真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/cutover 或真实手机/browser 外部材料；本机只有 Docker，本轮只能补强 local worker restart ACK replay 语义。
4. 重复 blocker 核对：上一轮 `real_material_followup_escalation_status` 已明确“下一步不应继续堆本地 wrapper”。本轮不是再包装外部材料缺失，而是推进已存在 `remote_bridge` command/status/ack 主链路的一个具体故障恢复能力；收口时仍必须写明不构成 O5 external proof。
