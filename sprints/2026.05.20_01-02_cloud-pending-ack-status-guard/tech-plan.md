# Sprint 2026.05.20_01-02 Cloud Pending ACK Status Guard - Tech Plan

## 1. 方案摘要

实现 `cloud_pending_ack_status_guard`：在上一轮 `cloud_ack_outage_replay_guard` 已经持久化并补发 pending terminal ACK 的基础上，补齐 pending ACK replay 失败时的 phone-safe degraded status。Robot 侧输出 `degradation_state=command_pending`、`remote_ready=false` 等 fail-closed readiness；Full-Stack 侧只读展示 existing status/readiness 语义，不新增控制动作。

边界固定为 `software_proof_docker_cloud_pending_ack_status_guard`。本轮不证明真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/cutover、真实手机/browser、Nav2/fixed-route、WAVE ROVER、HIL 或 delivery success。

## 2. Owner/File Scopes

### robot-software-engineer 主责实现

允许修改：

- `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_bridge.py`
- `onboard/src/ros2_trashbot_behavior/test/test_remote_bridge.py`
- `docs/product/remote_4g_mvp.md`

实现任务：

- pending terminal ACK 存在且补发失败时，输出 phone-safe degraded status/readiness。
- 目标字段建议：`degradation_state=command_pending`、`remote_ready=false`、`pending_terminal_ack_id`、`primary_actions_enabled=false`、`safe_phone_copy`、`retry_hint` 和 `proof_boundary=software_proof_docker_cloud_pending_ack_status_guard`。
- pending ACK 成功前不推进 `last_terminal_ack_id`，不拉取新 command，不重复执行本地命令。
- 持久化和 status payload 必须做 safe subset / redaction，不保存 bearer token、Authorization header、cloud URL credential、serial device、WAVE ROVER 参数、raw ROS topic、`/cmd_vel`、traceback 或 delivery success claim。
- 更新 `docs/product/remote_4g_mvp.md`，写清触发条件、状态字段、fail-closed 行为和证据边界。

### full-stack-software-engineer 主责只读消费

允许修改：

- `mobile/web/app.js`
- `mobile/web/styles.css`
- `mobile/web/test_mobile_web_entrypoint.py`
- `mobile/web/fixtures/robot_diagnostics_cloud_pending_ack_status_guard.json`
- `docs/product/mobile_user_flow.md`

实现任务：

- 消费 Robot/status readiness 中的 command pending degraded 状态。
- 在 existing mobile/web 状态面板展示中文 phone-safe copy：本地命令已终态，但云端 ACK 还没确认，暂不能拉取新命令。
- 保持 Start Delivery、Confirm Dropoff、Cancel 等 primary actions disabled，不新增新 endpoint、不新增控制动作。
- fixture/test 必须覆盖 copy、disabled actions、`remote_ready=false` 和 no delivery success claim。
- 如现有代码已有等价 copy，只允许做最小 fixture/test/doc 补齐；不得为了视觉重做扩大范围。

### product-okr-owner 收口

允许在 implementation 完成后修改：

- `OKR.md`
- `docs/process/okr_progress_log.md`
- `sprints/2026.05.20_01-02_cloud-pending-ack-status-guard/tech-done.md`
- `sprints/2026.05.20_01-02_cloud-pending-ack-status-guard/side2side_check.md`
- `sprints/2026.05.20_01-02_cloud-pending-ack-status-guard/final.md`

收口要求：

- Objective 5 保持约 68%，除非真实外部材料到位；本轮默认不得提升百分比。
- 明确 `PRRT_kwDOSWB9286CJ3tX` 仍 unresolved / `blocked_pending_real_materials`。
- 明确本轮只证明 pending ACK status guard，不证明真实 4G、公网 HTTPS/TLS、production DB/queue、真实手机/browser、HIL 或 delivery success。

### autonomy-engineer / hardware-engineer 只读咨询

默认不改文件。仅在实现阶段需要确认边界时只读回答：

- 本轮状态不能写成真实 route/elevator field pass。
- 本轮状态不能写成真实 WAVE ROVER/UART/HIL 或 PR #5 hardware materials。

## 3. 接口影响

- `trashbot.remote.v1` commands/status/ack HTTP envelope 不变。
- Robot 侧 status/readiness 增加或稳定化 fail-closed 字段；字段语义必须面向手机安全展示，不能暴露内部 raw payload。
- `last_terminal_ack_id` 推进规则不变：只有 pending terminal ACK 成功提交云端后才能推进。
- pending ACK 成功前，worker 不拉取新 command，不执行新 backend action，不推进 cursor。
- Full-Stack 只消费 existing status/readiness，不新增 phone endpoint，不新增 remote control action。

## 4. 实现步骤

1. Robot tests 先覆盖失败路径：
   - pending ACK replay 失败后 status/readiness 包含 `degradation_state=command_pending` 与 `remote_ready=false`。
   - pending ACK 成功前 `last_terminal_ack_id` 不推进。
   - pending ACK 成功前不 fetch new command，不调用 `start_collection`、`confirm_dropoff` 或 `cancel_collection`。
   - status/persisted state 不包含敏感 marker：`Bearer`、`Authorization`、`/cmd_vel`、`WAVE ROVER`、`serial`、`baudrate`、`traceback`、`delivery_success=true`。
2. Robot 实现最小 status/readiness：
   - 在 pending ACK replay failure branch 产生 safe degraded status。
   - 若已有 status post 失败语义，复用现有字段并补 `command_pending` 区分。
   - 保持旧 state file 兼容，不做破坏性迁移。
3. Full-Stack 只读消费：
   - 增加或更新 command pending fixture。
   - UI copy 用普通用户语言，不出现 ACK/cursor/raw JSON 作为主文案。
   - primary actions 继续 disabled。
4. 文档同步：
   - `docs/product/remote_4g_mvp.md` 记录 Robot status guard。
   - 若 Full-Stack 改动 UI/copy，`docs/product/mobile_user_flow.md` 同步本地 proof boundary。
5. 跑围栏验收并修复失败；不得把第一轮失败作为最终结果。

## 5. 验收命令

Robot fence：

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_remote_bridge.py
```

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_bridge.py
```

```bash
rg -n "cloud_pending_ack_status_guard|command_pending|remote_ready=false|pending_terminal_ack|last_terminal_ack_id|software_proof_docker_cloud_pending_ack_status_guard|delivery success|production DB/queue|4G" onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_bridge.py onboard/src/ros2_trashbot_behavior/test/test_remote_bridge.py docs/product/remote_4g_mvp.md
```

Full-Stack fence：

```bash
PYTHONDONTWRITEBYTECODE=1 python3 mobile/web/test_mobile_web_entrypoint.py
```

```bash
node --check mobile/web/app.js
```

```bash
rg -n "cloud_pending_ack_status_guard|command_pending|remote_ready=false|primary_actions_enabled=false|software_proof_docker_cloud_pending_ack_status_guard|delivery success" mobile/web docs/product/mobile_user_flow.md
```

Scoped diff fence：

```bash
git diff --check -- onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_bridge.py onboard/src/ros2_trashbot_behavior/test/test_remote_bridge.py docs/product/remote_4g_mvp.md mobile/web/app.js mobile/web/styles.css mobile/web/test_mobile_web_entrypoint.py mobile/web/fixtures/robot_diagnostics_cloud_pending_ack_status_guard.json docs/product/mobile_user_flow.md sprints/2026.05.20_01-02_cloud-pending-ack-status-guard
```

Product planning 文件验收命令：

```bash
test -f sprints/2026.05.20_01-02_cloud-pending-ack-status-guard/pre_start.md && test -f sprints/2026.05.20_01-02_cloud-pending-ack-status-guard/prd.md && test -f sprints/2026.05.20_01-02_cloud-pending-ack-status-guard/tech-plan.md
```

```bash
rg -n "sprint_type: epic|cloud_pending_ack_status_guard|Objective 5|PRRT_kwDOSWB9286CJ3tX|cloud_ack_outage_replay_guard|real_material_followup_escalation_status|OKR 最低优先级核对|software_proof_docker_cloud_pending_ack_status_guard" sprints/2026.05.20_01-02_cloud-pending-ack-status-guard
```

```bash
git diff --check -- sprints/2026.05.20_01-02_cloud-pending-ack-status-guard
```

## 6. 风险边界

- 本轮只能证明 local Docker / unit test / fixture 下的 pending ACK status guard。
- 不证明真实公网 HTTPS/TLS、真实 4G/SIM、OSS/CDN live traffic、production DB/queue connectivity、production worker migration/cutover、多实例一致性、queue ordering、transaction isolation、backup/recovery 或真实手机/browser。
- 不证明 Nav2/fixed-route、WAVE ROVER、UART、HIL、真实 route/elevator field pass、dropoff/cancel completion 或 delivery success。
- PR #5 `PRRT_kwDOSWB9286CJ3tX` 继续 blocked_pending_real_materials；本轮不提供真实 2D LiDAR / ToF vendor/source/procurement/material evidence。
- 如果 implementation 发现现有 status schema 无法表达 `command_pending`，优先最小扩展 safe readiness 字段，不扩大到新 command/control contract。

## 7. OKR 最低优先级核对

1. 当前 `OKR.md` 4.1 完成度最低 Objective：Objective 5，约 68%。
2. 本 sprint 是否针对最低 Objective：是，针对 Objective 5 的 command/status/ack graceful degradation 缺口。
3. 为什么不提升 Objective 5 百分比：O5 completion 仍需要真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/cutover 或真实手机/browser 外部材料；本机只有 Docker，本轮只能提供 `software_proof_docker_cloud_pending_ack_status_guard`。
4. 重复 blocker 核对：`real_material_followup_escalation_status` 已明确不应继续堆本地真实材料 wrapper。本轮不是新的材料 wrapper，而是继 `cloud_ack_outage_replay_guard` 后推进 remote command/status/ack 主链路的具体 fail-closed 状态能力。

## 8. 子 Agent 派发建议

Implementation 阶段应并行启动 2 个 worker：

- `robot-software-engineer`：负责 Robot/cloud worker 状态语义与 `remote_bridge` tests/docs。
- `full-stack-software-engineer`：负责手机端 fixture/copy/test/docs，只消费 status/readiness，不新增控制动作。

Product closeout 在两位 Engineer 返回验证证据后进行；如任一 fence 失败，必须把失败定位和重试任务派回对应 owner。
