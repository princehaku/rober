# Cloud Command Terminal Result Mainline Tech Plan

## OKR 最低优先级核对

1. 当前 `OKR.md` 4.1 完成度最低 Objective：Objective 5，约 76%。
2. 本 sprint 直接针对 Objective 5。
3. 选择理由：上一轮 `cloud_command_result_reconciliation` 已把 queued、processing、terminal_result_pending、missing/store unavailable 展示给 phone，但缺真正 robot/relay 写入并持久化的 terminal result 主链路。本轮必须补 `cloud_command_terminal_result` API/store/UI，不再做 metadata-only wrapper。

## 方案总览

新增能力名：`cloud_command_terminal_result`。

目标：让 robot/relay 通过 outbound cloud path 写入同一 `robot_id + command_id` 的 phone-safe terminal result，command store 持久化该结果，`GET /api/commands/{command_id}/result?robot_id=<robot_id>` 返回新的 terminal result 状态，mobile/web 显示该终态，同时继续 fail-closed。

核心设计：

- Robot-facing 写入口：接收 terminal result，不对普通 phone 暴露写权限。
- Store 主路径：terminal result 与 command/ACK/status 同仓或同抽象持久化。
- Query 主路径：现有 result reconciliation route 读取 terminal result 并升级状态。
- UI 主路径：现有 command result panel 显示 terminal result recorded，不新增孤立材料面板冒充结果。
- False-state：没有真实 field/HIL/送达材料时，永远保持 `delivery_success=false`。

必须保留的安全字段：

- `delivery_success=false`
- `safe_to_control=false`
- `primary_actions_enabled=false`
- `real_world_delivery_proven=false`
- `evidence_boundary=software_proof_docker_cloud_command_terminal_result_gate`
- `not_proven`
- `next_required_evidence`

禁止输出：

- Authorization、bearer token、raw state path、DB/queue URL、ROS topic、`/cmd_vel`、serial/UART、baudrate、WAVE ROVER 参数、完整 artifact、checksum、traceback、真实公网 URL、OSS secret、AK/SK。

## Task A：Robot Software Engineer

### 文件范围

允许修改：

- `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py`
- `onboard/src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py`
- `cloud-relay/README.md`
- `docs/product/remote_4g_mvp.md`
- `docs/product/cloud_4g_infrastructure.md`

不得修改：

- `mobile/web/**`
- `OKR.md`
- `.idea/rober.iml`
- 本 sprint 计划文件之外的 `sprints/**` closeout 文件
- 硬件、launch、串口、WAVE ROVER、UART、Nav2、fixed-route 配置

### 接口设计

新增 robot-facing 写入口，建议使用以下路径之一，按现有 relay router 风格选择：

```text
POST /robots/{robot_id}/commands/{command_id}/terminal-result
POST /robots/{robot_id}/command-results
```

请求体建议字段：

```json
{
  "schema": "trashbot.cloud_command_terminal_result.v1",
  "schema_version": 1,
  "robot_id": "robot-local-proof",
  "command_id": "cmd-local-proof",
  "terminal_result_type": "delivery_terminal",
  "terminal_result_state": "completed",
  "result_code": "task_terminal_completed",
  "error_code": "",
  "task_record_ref": "safe_task_record_ref",
  "evidence_ref": "safe_evidence_ref",
  "completed_at": "2026-05-26T07:08:00+08:00",
  "source": "robot_remote_bridge",
  "delivery_success": false,
  "real_world_delivery_proven": false
}
```

响应建议字段：

- `schema=trashbot.cloud_command_terminal_result.v1`
- `capability=cloud_command_terminal_result`
- `evidence_boundary=software_proof_docker_cloud_command_terminal_result_gate`
- `robot_id`
- `command_id`
- `terminal_result_state`: `terminal_result_recorded` / `terminal_result_conflict` / `terminal_result_rejected` / `store_unavailable`
- `terminal_result_type`
- `result_code`
- `error_code`
- `task_record_ref`
- `evidence_ref`
- `delivery_success=false`
- `safe_to_control=false`
- `primary_actions_enabled=false`
- `real_world_delivery_proven=false`
- `safe_copy`
- `next_required_evidence`

### 实现要求

- 写入前必须确认 command 存在，且 `robot_id` 与 `command_id` 匹配；不允许 terminal result 创建孤儿 command。
- 写入必须持久化到现有 file-backed / SQLite-backed command store 或其统一抽象，不能只存在内存响应中。
- 同一 command 的相同 terminal result 重复写入必须幂等。
- 同一 command 的冲突 terminal result 必须返回 `terminal_result_conflict`，不得覆盖既有结果。
- `GET /api/commands/{command_id}/result?robot_id=<robot_id>` 必须读取持久化结果，并返回 `terminal_result_recorded` 或等价新状态。
- `terminal_result_recorded` 仍必须保留 `delivery_success=false`，因为本轮只证明 software proof terminal result，不证明真实送达。
- 技术注释必须使用中文，且新增代码注释比例超过 20%，重点解释为什么 ACK/terminal result 不等于真实送达成功、为什么要脱敏、为什么要幂等。

### 测试要求

`test_remote_cloud_relay.py` 至少覆盖：

- 写入 terminal result 成功后，result reconciliation 返回 terminal result recorded。
- ACK terminal 但未写入 terminal result 时，仍返回 terminal_result_pending。
- 重复写入同一 terminal result 幂等。
- 冲突写入返回 conflict 且不覆盖。
- command missing / robot_id mismatch fail closed。
- store unavailable 返回脱敏错误，不输出路径或 traceback。
- 所有响应保持 `delivery_success=false`、`safe_to_control=false`、`primary_actions_enabled=false`。

### 验收命令

Robot Software Engineer 必须运行并回贴关键日志：

```bash
python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py
```

```bash
PYTHONPATH=onboard/src/ros2_trashbot_behavior python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py -k "cloud_command_terminal_result or cloud_command_result_reconciliation or cloud_phone_command_api"
```

```bash
git diff --check -- onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py onboard/src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py cloud-relay/README.md docs/product/remote_4g_mvp.md docs/product/cloud_4g_infrastructure.md
```

### 输出要求

必须返回：

1. 实际改动的文件列表。
2. 新写入口、store helper、query schema 名称。
3. terminal_result_recorded、terminal_result_pending、conflict、missing、store_unavailable 的测试证据。
4. 验证命令输出。
5. 失败定位和剩余风险。

## Task B：User Touchpoint Full-Stack Engineer

### 文件范围

允许修改：

- `mobile/web/app.js`
- `mobile/web/test_mobile_web_entrypoint.py`
- `mobile/web/fixtures/robot_diagnostics_cloud_command_result_reconciliation.json`
- 可新增：`mobile/web/fixtures/robot_diagnostics_cloud_command_terminal_result.json`
- `docs/product/mobile_user_flow.md`

不得修改：

- `onboard/src/ros2_trashbot_behavior/**`
- `cloud-relay/**`
- `OKR.md`
- `.idea/rober.iml`
- 本 sprint 计划文件之外的 `sprints/**` closeout 文件
- 硬件、launch、串口、WAVE ROVER、UART、Nav2、fixed-route 配置

### UI 要求

- 复用现有 `cloud_command_result_reconciliation` 查询入口或结果面板。
- 当 backend 返回 terminal result recorded 状态时，显示：
  - 命令已返回终态结果。
  - result type / result code / error code。
  - safe `command_id` 与 safe `evidence_ref`。
  - 下一步仍需真实 field/HIL/送达材料。
  - `delivery_success=false`、`safe_to_control=false`、`primary_actions_enabled=false`。
- 缺 terminal result 时继续显示 `terminal_result_pending`。
- conflict、missing、store_unavailable 必须显示普通中文解释。
- Start Delivery、Confirm Dropoff、Cancel 继续 disabled，除非既有 command safety gate 独立允许；本轮不得新增 control grant。

### 禁止行为

- 不自动 replay。
- 不自动 resubmit。
- 不请求 ACK cursor。
- 不拉 raw diagnostics。
- 不暴露 raw `/robots/*`、ROS topic、`/cmd_vel`、serial/UART/WAVE ROVER、token、Authorization、DB/queue URL、raw state path、完整 artifact、checksum 或 traceback。
- 不把 `completed`、`dropoff_completed`、`cancel_completed` 写成真实 delivery success。

### 测试要求

`test_mobile_web_entrypoint.py` 至少覆盖：

- terminal_result_recorded 中文 copy 和 result fields 显示。
- terminal_result_pending 仍保持等待 copy。
- conflict/missing/store unavailable fail-closed copy。
- Start/Confirm/Cancel 不因 terminal result recorded 自动启用。
- fixture 不包含 token、raw path、checksum、traceback、ROS topic、serial/UART/WAVE ROVER 字段。
- 所有 fixture 和渲染状态保持 `delivery_success=false`、`safe_to_control=false`、`primary_actions_enabled=false`。

### 验收命令

User Touchpoint Full-Stack Engineer 必须运行并回贴关键日志：

```bash
node --check mobile/web/app.js
```

```bash
PYTHONPATH=mobile python3 -m unittest mobile/web/test_mobile_web_entrypoint.py -k "cloud_command_terminal_result or cloud_command_result_reconciliation or cloud_phone_command_api"
```

```bash
git diff --check -- mobile/web/app.js mobile/web/test_mobile_web_entrypoint.py mobile/web/fixtures/robot_diagnostics_cloud_command_result_reconciliation.json mobile/web/fixtures/robot_diagnostics_cloud_command_terminal_result.json docs/product/mobile_user_flow.md
```

### 输出要求

必须返回：

1. 实际改动的文件列表。
2. UI 查询入口、fixture 名称和 terminal result recorded 展示位置。
3. terminal_result_recorded、pending、conflict、missing、store_unavailable 的展示证据。
4. 验证命令输出。
5. 失败定位和剩余风险。

## 并行启动要求

进入实现阶段时，主节点必须在同一轮并行启动两个 Codex worker：

- `robot-software-engineer`：执行 Task A。
- `full-stack-software-engineer`：执行 Task B。

两个 worker prompt 必须包含完整角色 System Prompt、本轮任务、文件范围、验收命令和输出要求。主节点不得自己写产品代码、测试代码或硬件配置。

本轮 2 个 owner 文件范围互不重叠，且接口通过本 `tech-plan.md` 固化；必须并行启动，不允许降级为单线 worker，除非运行时缺少子 agent 能力并在 `final.md` 明确记录流程降级原因。

## 集成验收

两个 worker 返回后，主节点只做验收与留档：

- 核对 terminal result 是否真实持久化并被 query route 读取。
- 核对 query route 是否新增 terminal result recorded 状态。
- 核对 mobile/web 是否显示终态但不启用主操作。
- 核对 `docs/product/` 是否同步。
- 核对新增代码中文注释比例是否超过 20%。
- 核对 `tech-done.md` 是否记录实际改动、验证结果、偏差和剩余风险。
- 如果任何验证失败或证据不足，必须把失败定位和重试任务派回对应 worker。

## 后续 closeout 要求

实现完成后必须继续创建或更新：

- `sprints/2026.05.26_07-08_cloud-command-terminal-result-mainline/tech-done.md`
- `sprints/2026.05.26_07-08_cloud-command-terminal-result-mainline/side2side_check.md`
- `sprints/2026.05.26_07-08_cloud-command-terminal-result-mainline/final.md`
- `OKR.md`

`final.md` 必须写明 Objective 5 是否从约 76% 提升；如果只证明 Docker/local software proof terminal result，必须清楚写明不是公网 HTTPS/TLS、真实 4G/SIM、OSS/CDN live traffic、production DB/queue、true phone/browser proof、HIL、Nav2/fixed-route 或 delivery success。

## 本计划自检

- 覆盖用户价值：手机用户能看到同一 command 的 terminal result，不再停在 pending。
- 覆盖 OKR：直接针对 Objective 5 全局最低项。
- 覆盖工程主路径：API、store、query、UI、tests、docs 都有 owner。
- 覆盖 fail-closed：所有状态保留 `delivery_success=false`。
- 覆盖反范围：硬件、真实现场、生产外部环境不在本轮宣称范围。
