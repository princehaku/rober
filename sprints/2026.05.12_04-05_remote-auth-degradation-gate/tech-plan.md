# Sprint 2026.05.12_04-05 Remote Auth Degradation Gate - Tech Plan

## 状态

- 阶段：tech-plan
- 创建时间：2026-05-12 Asia/Shanghai
- Product Owner：`product-okr-owner`
- 执行模式：两个 owner 并行执行，工程文件互不重叠；`tech-done.md` 仅按 Task A / Task B 段落分区填写
- 证据边界：Docker/local `software_proof_docker_only`

## 总体方案

本轮在 02-03、03-04 已有 local mock cloud 与 `remote_bridge` 的基础上，补齐真实云前必须固定的 auth/degradation gate。Full-stack owner 负责 cloud/operator API contract 和 phone-safe readiness；Robot owner 负责 robot-side polling/ACK/status/cursor 的失败保守语义。两条线通过 `trashbot.remote.v1` 状态枚举对齐，不共享代码文件，可以并行启动。共享产品/接口文档由 Integration/Product Acceptance 在两个工程结果返回后统一同步，避免并行 owner 写同一文件。

本轮不接真实云、不接 4G、不接硬件，所有验证均限定为 targeted unittest、`py_compile` 和 scoped diff check。

## 文件范围

### Task A - Full-stack Owner

Owner：`full-stack-software-engineer`

允许改动：

- `src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_http.py`
- `src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway.py`，仅当 HTTP auth/readiness 调用链必须调整时使用
- `src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py`，仅当敏感字段过滤入口必须调整时使用
- `src/ros2_trashbot_behavior/test/test_operator_gateway_http.py`
- `src/ros2_trashbot_behavior/test/test_operator_gateway_static.py`，仅当 static contract 随 HTTP gate 变化时使用
- `src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`，仅当 diagnostics 敏感字段过滤随 HTTP gate 变化时使用
- `docs/product/mobile_user_flow.md`
- `sprints/2026.05.12_04-05_remote-auth-degradation-gate/tech-done.md` 的 Task A 段落

不得改动：

- `remote_bridge` 实现和测试。
- `docs/product/remote_4g_mvp.md` 和 `docs/interfaces/ros_contracts.md`，交给 Integration/Product Acceptance 统一同步。
- 硬件、Nav2、vision、launch 参数。

### Task B - Robot Owner

Owner：`robot-software-engineer`

允许改动：

- `src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_bridge.py`
- `src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_bridge_protocol.py`，仅当 degraded status/ACK mapping 必须更新共享协议常量时使用
- `src/ros2_trashbot_behavior/test/test_remote_bridge.py`
- `sprints/2026.05.12_04-05_remote-auth-degradation-gate/tech-done.md` 的 Task B 段落

不得改动：

- operator gateway HTTP/static UI 实现。
- `docs/product/remote_4g_mvp.md` 和 `docs/interfaces/ros_contracts.md`，交给 Integration/Product Acceptance 统一同步。
- 硬件、Nav2、vision、launch 参数。

### Integration / Product Acceptance

Owner：`product-okr-owner` 做验收留档，不写产品代码。

允许更新：

- `docs/product/remote_4g_mvp.md`
- `docs/interfaces/ros_contracts.md`
- `sprints/2026.05.12_04-05_remote-auth-degradation-gate/tech-done.md`
- `sprints/2026.05.12_04-05_remote-auth-degradation-gate/side2side_check.md`
- `sprints/2026.05.12_04-05_remote-auth-degradation-gate/final.md`
- `OKR.md`，仅当执行证据足以保守更新 O6/O5 software proof 进度时更新。

## 接口影响

### `remote_readiness`

Full-stack 与 Robot 必须对齐以下 phone-safe 字段语义。字段可以按现有实现风格落地，但不得暴露 raw exception、token、串口、ROS topic 或硬件配置。

| Field | Required semantics |
| --- | --- |
| `remote_ready` | true 只表示当前 local/mock control-plane 条件允许手机继续，不证明真实云/4G/HIL |
| `cloud_reachable` | local/mock 进程可达时为 true；真实云不可由本轮证明 |
| `auth_state` | `mock_not_required`、`required`、`authorized`、`auth_failed` 等 phone-safe 状态 |
| `degradation_state` | `ok`、`status_stale`、`command_pending`、`auth_failed`、`cloud_unreachable`、`malformed_response` 等 |
| `retry_hint` | `ok`、`wait_for_robot_status`、`wait_for_command_ack`、`check_auth`、`retry_cloud`、`contact_support` 等 |
| `safe_phone_copy` | 给正式手机 UI 使用的普通用户文案，不包含 raw JSON/ROS/hardware 细节 |

### ACK / Cursor

- ACK 仍只表示 command envelope 处理状态，不是 delivery result。
- terminal ACK 只有成功提交到 cloud 后，`remote_bridge` 才能推进并持久化 `last_terminal_ack_id`。
- cloud outage、auth failed、malformed response 不得推进 cursor。
- malformed response 不得触发本地 action goal。

### Sensitive Field Filter

以下内容不得出现在 phone/status/diagnostics/mock persisted state：

- bearer token 或 Authorization header。
- 串口设备名、baudrate、WAVE ROVER 参数、硬件配置。
- ROS topic 名、`/cmd_vel`、内部 action topic。
- 带凭证的 cloud URL。

## 并行执行计划

### Task A：Full-stack Auth Gate And Phone Readiness

Owner：`full-stack-software-engineer`

目标：

- 为 `operator_gateway_http.py` 暴露的 local/mock cloud API 补 bearer auth gate。
- 扩展 `remote_readiness` 的 auth/degradation 字段。
- 补敏感信息过滤测试。
- 更新手机用户流程文档，并只填写 `tech-done.md` 的 Task A 段落。

建议步骤：

1. 阅读当前 `operator_gateway_http.py` 中 mock cloud command/status/ack、persistence 和 `remote_readiness` 生成路径；只有调用链确实要求时，才触碰 `operator_gateway.py` 或 diagnostics/static 测试。
2. 在已有 test 文件中先补 targeted failing tests：
   - 无 bearer 或错误 bearer 在 gate 开启时被拒绝。
   - 正确 bearer 能提交 command、读取 status/ack。
   - `remote_readiness.auth_state` 和 `degradation_state` phone-safe。
   - persisted mock state 与 diagnostics 不包含 token、串口、ROS topic、硬件参数。
3. 实现最小 auth gate 和 readiness 字段。
4. 更新 `docs/product/mobile_user_flow.md`。
5. 更新 `tech-done.md` 的 Task A 段落，粘贴验证结果和剩余风险。

验收命令：

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest \
  src/ros2_trashbot_behavior/test/test_operator_gateway_http.py \
  src/ros2_trashbot_behavior/test/test_operator_gateway_static.py \
  src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py

PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile \
  src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_http.py \
  src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway.py \
  src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py

git diff --check -- \
  src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_http.py \
  src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway.py \
  src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py \
  src/ros2_trashbot_behavior/test/test_operator_gateway_http.py \
  src/ros2_trashbot_behavior/test/test_operator_gateway_static.py \
  src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py \
  docs/product/mobile_user_flow.md \
  sprints/2026.05.12_04-05_remote-auth-degradation-gate/tech-done.md
```

### Task B：Robot Remote Bridge Degradation And Cursor Safety

Owner：`robot-software-engineer`

目标：

- 为 `remote_bridge` 补 cloud outage / auth failed / malformed response 的保守处理。
- 失败时输出 phone/cloud 可消费状态。
- 确保失败不推进 cursor、不伪造 ACK 成功、不触发本地 action。
- 只填写 `tech-done.md` 的 Task B 段落。

建议步骤：

1. 阅读当前 `remote_bridge.py` polling、ACK post、status post、cursor persist 路径。
2. 在 `test_remote_bridge.py` 中先补 targeted failing tests：
   - command polling cloud outage 时不推进 cursor。
   - auth failed 时 status/ACK 语义可解释且不持久化 terminal cursor。
   - malformed response 不提交 local action、不推进 cursor。
   - ACK post 失败时保留原 cursor，可重试同一 command。
3. 实现最小 degraded status/ACK mapping。
4. 更新 `tech-done.md` 的 Task B 段落，粘贴验证结果和剩余风险。

验收命令：

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest \
  src/ros2_trashbot_behavior/test/test_remote_bridge.py

PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile \
  src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_bridge.py \
  src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_bridge_protocol.py

git diff --check -- \
  src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_bridge.py \
  src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_bridge_protocol.py \
  src/ros2_trashbot_behavior/test/test_remote_bridge.py \
  sprints/2026.05.12_04-05_remote-auth-degradation-gate/tech-done.md
```

### Task C：Integration Smoke And Product Acceptance

Owner：`robot-software-engineer` 主责集成，`product-okr-owner` 只做验收留档。

目标：

- 确认 Task A + Task B 字段语义一致。
- 确认 auth/degradation/cursor safety 同时存在时不会互相破坏。
- 统一同步 `docs/product/remote_4g_mvp.md` 与 `docs/interfaces/ros_contracts.md`，不让并行工程 owner 抢写共享文档。
- 更新 sprint 收口文档，必要时保守更新 `OKR.md`。

验收命令：

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest \
  src/ros2_trashbot_behavior/test/test_operator_gateway_http.py \
  src/ros2_trashbot_behavior/test/test_operator_gateway_static.py \
  src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py \
  src/ros2_trashbot_behavior/test/test_remote_bridge.py

PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile \
  src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_http.py \
  src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway.py \
  src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py \
  src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_bridge.py \
  src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_bridge_protocol.py

git diff --check -- \
  src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_http.py \
  src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway.py \
  src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py \
  src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_bridge.py \
  src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_bridge_protocol.py \
  src/ros2_trashbot_behavior/test/test_operator_gateway_http.py \
  src/ros2_trashbot_behavior/test/test_operator_gateway_static.py \
  src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py \
  src/ros2_trashbot_behavior/test/test_remote_bridge.py \
  docs/product/mobile_user_flow.md \
  docs/product/remote_4g_mvp.md \
  docs/interfaces/ros_contracts.md \
  sprints/2026.05.12_04-05_remote-auth-degradation-gate/tech-done.md \
  sprints/2026.05.12_04-05_remote-auth-degradation-gate/side2side_check.md \
  sprints/2026.05.12_04-05_remote-auth-degradation-gate/final.md \
  OKR.md
```

## 子 Agent 启动要求

tech-plan 完成后，执行阶段必须在同一轮并行启动：

- `spawn_agent(agent_type=worker)` for `full-stack-software-engineer`
- `spawn_agent(agent_type=worker)` for `robot-software-engineer`

每个 prompt 必须包含：

1. 对应 `.codex/agents/<role>.toml` 的完整角色 System Prompt；如果文件不存在，使用 `AGENTS.md` 中对应角色边界。
2. 本轮任务。
3. 文件范围。
4. 验收命令。
5. 输出要求：实际改动文件、验证输出、失败定位、剩余风险。

主节点不得直接写产品代码、测试代码或硬件配置。

## 风险边界

- 本轮所有证据均为 Docker/local software proof。
- 不得宣称真实云、生产 TLS、公网入口、真实 4G/SIM、OSS/CDN 或 HIL 完成。
- ACK 不等于 delivery result；delivery result 仍来自 behavior/task status。
- 如果测试需要 broad sweep，必须说明原因；默认只跑本计划列出的围栏命令。
- 如果出现 repo-wide whitespace 噪声，使用 touched files 的 scoped `git diff --check`，不要把无关文件纳入本轮。
