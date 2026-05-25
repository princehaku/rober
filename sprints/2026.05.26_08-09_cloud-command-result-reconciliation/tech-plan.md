# Cloud Command Result Reconciliation Tech Plan

## OKR 最低优先级核对

1. 当前 `OKR.md` 4.1 完成度最低 Objective：Objective 5，约 72%。
2. 本 sprint 直接针对 Objective 5。
3. 选择理由：上一轮 `cloud_phone_command_api` 已完成 phone -> cloud command enqueue，但剩余风险明确是 command result reconciliation / production queue 等。本轮先补齐同源 API 和手机端能查询刚入队命令的 ack/result/pending 状态，避免继续只做只读 metadata wrapper。

## 方案总览

新增能力名：`cloud_command_result_reconciliation`。

目标：让手机端/同源 API 能用 phone-safe 方式查询刚入队命令的 lifecycle summary，并把 queued、processing、terminal、missing、store unavailable 都解释为“不是 delivery success”。Robot worker 与 Full-Stack worker 文件范围互不重叠，必须并行启动。

核心状态语义：

- `queued`：云端已接收并入队，机器人可能尚未领取；不是送达成功。
- `processing`：机器人或 bridge 已 accepted/processing；不是送达成功。
- `terminal_result_pending`：ACK 或 command lifecycle 已到 terminal，但缺 verified delivery/dropoff/cancel result；不是送达成功。
- `missing_or_expired`：按 command id 查询不到安全摘要；不是送达成功。
- `store_unavailable`：store 或查询失败，fail closed；不是送达成功。

全局 false-state 要求：

- 所有新 API、fixture、UI copy 和 docs 必须保留 `delivery_success=false`。
- 所有新 API、fixture、UI copy 和 docs 必须保留 `safe_to_control=false`。
- 所有新 API、fixture、UI copy 和 docs 必须保留 `primary_actions_enabled=false`，除非既有 command safety gate 已经独立允许，且本轮不得新增 control grant。
- terminal ACK / terminal state 不得被写成 delivery/dropoff/cancel success。
- 不得暴露 Authorization、bearer token、raw state path、DB/queue URL、ROS topic、`/cmd_vel`、serial/UART/WAVE ROVER、完整 artifact、checksum 或 traceback。

## Task A：Robot Software Engineer

### 文件范围

允许修改：

- `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py`
- `onboard/src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py`
- `docs/product/remote_4g_mvp.md`
- `docs/product/cloud_4g_infrastructure.md`
- `cloud-relay/README.md`

不得修改：

- `mobile/web/**`
- `OKR.md`
- 本 sprint 计划文件之外的 `sprints/**` closeout 文件
- 硬件、launch、串口、WAVE ROVER、UART 配置

### 接口边界

建议新增 phone-safe route，可按实现实际命名，但必须满足同源 API 查询语义：

- `GET /api/commands/{command_id}/result?robot_id=<robot_id>`
- 或 `GET /api/commands/result?robot_id=<robot_id>&command_id=<command_id>`

响应建议字段：

- `schema=trashbot.cloud_command_result_reconciliation.v1`
- `capability=cloud_command_result_reconciliation`
- `evidence_boundary=software_proof_docker_cloud_command_result_reconciliation_gate`
- `robot_id`
- `command_id`
- `command_state`: `queued` / `processing` / `terminal_result_pending` / `missing_or_expired` / `store_unavailable`
- `ack_state`: phone-safe enum or `ack_pending`
- `result_state`: `result_pending` / `verified_result_missing` / `store_unavailable`
- `ack_semantics`: `queued_not_delivery_success` / `accepted_processing_only_not_delivery_success` / `terminal_ack_not_delivery_success`
- `delivery_success=false`
- `safe_to_control=false`
- `primary_actions_enabled=false`
- `next_required_evidence`
- `safe_copy`

实现要求：

- 复用现有 command store / ACK / status 结构；不要新增 bypass robot polling 的控制路径。
- 如果 command 已入队但未 ACK，返回 queued / ack pending。
- 如果 ACK 是 accepted / processing，返回 processing。
- 如果 ACK 是 terminal state，但没有 verified delivery/dropoff/cancel result，返回 terminal_result_pending。
- 如果 command id 不存在或过期，返回 phone-safe missing_or_expired。
- 如果 store 读取失败，返回 phone-safe 503 或等价 fail-closed payload，不能返回成功 receipt。
- 技术注释必须使用中文，且新增代码注释比例超过 20%，解释 false-state、脱敏和 ACK 不等于送达成功的原因。

### 验收命令

Robot Software Engineer 必须运行并回贴关键日志：

```bash
python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py
```

```bash
PYTHONPATH=onboard/src/ros2_trashbot_behavior python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py -k "cloud_command_result_reconciliation or cloud_phone_command_api"
```

```bash
git diff --check -- onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py onboard/src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py docs/product/remote_4g_mvp.md docs/product/cloud_4g_infrastructure.md cloud-relay/README.md
```

### 输出要求

必须返回：

1. 实际改动的文件列表。
2. 新 route / helper / schema 名称。
3. queued、processing、terminal_result_pending、missing/store unavailable 的测试覆盖证据。
4. 验证命令输出。
5. 失败定位和剩余风险。

## Task B：User Touchpoint Full-Stack Engineer

### 文件范围

允许修改：

- `mobile/web/app.js`
- `mobile/web/test_mobile_web_entrypoint.py`
- `mobile/web/fixtures/robot_diagnostics_cloud_phone_command_api.json`
- 可新增：`mobile/web/fixtures/robot_diagnostics_cloud_command_result_reconciliation.json`
- `docs/product/mobile_user_flow.md`

不得修改：

- `onboard/src/ros2_trashbot_behavior/**`
- `cloud-relay/**`
- `OKR.md`
- 本 sprint 计划文件之外的 `sprints/**` closeout 文件
- 硬件、launch、串口、WAVE ROVER、UART 配置

### 接口边界

实现要求：

- 在上一轮 receipt 展示基础上，消费 Robot worker 新增的同源查询 contract。
- 支持用户或页面基于 `command_id` 查询 lifecycle summary；可以是按钮刷新、自动轻量轮询或 receipt 后的手动刷新，但不得自动重放、自动 resubmit 或请求 raw diagnostics。
- 展示至少四类中文 copy：
  - 已入队，等待机器人处理；不是送达成功。
  - 命令已接收/处理中；尚无真实 delivery/dropoff/cancel result。
  - 命令已终态，但 verified terminal result 仍缺失；不是送达成功。
  - 暂时无法确认命令状态；请等待或联系支持。
- UI 和 fixture 必须保持 `delivery_success=false`、`safe_to_control=false`、`primary_actions_enabled=false`。
- 不暴露 raw `/robots/*`、ROS topic、`/cmd_vel`、serial/UART/WAVE ROVER、token、Authorization、DB/queue URL、raw state path、完整 artifact、checksum 或 traceback。
- 技术注释必须使用中文，且新增代码注释比例超过 20%，解释为什么 terminal ACK 仍不能当成送达成功。

### 验收命令

User Touchpoint Full-Stack Engineer 必须运行并回贴关键日志：

```bash
node --check mobile/web/app.js
```

```bash
PYTHONPATH=mobile python3 -m unittest mobile/web/test_mobile_web_entrypoint.py -k "cloud_command_result_reconciliation or cloud_phone_command_api"
```

```bash
git diff --check -- mobile/web/app.js mobile/web/test_mobile_web_entrypoint.py mobile/web/fixtures/robot_diagnostics_cloud_phone_command_api.json mobile/web/fixtures/robot_diagnostics_cloud_command_result_reconciliation.json docs/product/mobile_user_flow.md
```

### 输出要求

必须返回：

1. 实际改动的文件列表。
2. UI 查询入口和 fixture 名称。
3. queued、processing、terminal_result_pending、missing/store unavailable 的展示证据。
4. 验证命令输出。
5. 失败定位和剩余风险。

## 并行启动要求

主节点进入实现阶段时，必须在同一轮并行启动两个 Codex worker：

- `robot-software-engineer`：执行 Task A。
- `full-stack-software-engineer`：执行 Task B。

两个 worker 都必须在 prompt 中包含完整角色 System Prompt、本轮任务、文件范围、验收命令和输出要求。主节点不得自己写产品代码、测试代码或硬件配置。

## 集成验收

两个 worker 返回后，主节点只做验收与留档：

- 核对 Robot API contract 是否 phone-safe。
- 核对 mobile/web copy 是否没有把任何状态写成送达成功。
- 核对 `docs/product/` 是否同步。
- 核对 `tech-done.md` 是否记录实际改动、验证结果、偏差和剩余风险。
- 如果任何验证失败或证据不足，必须把失败定位和重试任务派回对应 worker。

## 后续 closeout 要求

实现完成后必须继续创建或更新：

- `sprints/2026.05.26_08-09_cloud-command-result-reconciliation/tech-done.md`
- `sprints/2026.05.26_08-09_cloud-command-result-reconciliation/side2side_check.md`
- `sprints/2026.05.26_08-09_cloud-command-result-reconciliation/final.md`

`final.md` 必须总结 Objective 5 是否从约 72% 提升；如果只证明 Docker/local software proof，必须清楚写明不是公网 HTTPS/TLS、真实 4G/SIM、OSS/CDN live traffic、production DB/queue、true phone/browser proof、HIL、Nav2/fixed-route 或 delivery success。
