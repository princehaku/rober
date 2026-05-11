# Sprint 2026.05.12_04-05 Remote Auth Degradation Gate - Tech Done

## 状态

- 阶段：tech-done
- 更新时间：2026-05-12 02:16:41 CST
- 证据边界：Docker/local `software_proof_docker_only`
- 并行边界：Task A 只改 operator HTTP / phone flow / Task A 留档；未改 `remote_bridge` 文件。

## Task A - Full-stack Auth Gate And Phone Readiness

### 实际改动

- `src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_http.py`
  - 为 `/robots/{robot_id}/...` local/mock cloud API 增加 bearer auth gate，支持通过 gateway 属性或环境变量注入 token。
  - 扩展 `remote_readiness`：新增 `degradation_state` 与 `safe_phone_copy`，并补齐 `authorized`、`auth_failed`、`status_stale`、`command_pending`、`ok` 等 phone-safe 状态。
  - 扩展敏感字段过滤，避免 bearer/auth、串口、baudrate、ROS topic、`/cmd_vel`、硬件字段、带凭证 URL 进入 phone payload 或 mock persistence proof。
- `src/ros2_trashbot_behavior/test/test_operator_gateway_http.py`
  - 增加 bearer gate 缺失/错误 token 拒绝、正确 token 可提交 command/status/ack、readiness 降级状态、敏感信息不回显/不持久化测试。
- `src/ros2_trashbot_behavior/test/test_operator_gateway_static.py`
  - 增加 `degradation_state`、`safe_phone_copy`、auth gate 相关静态 contract 检查。
- `docs/product/mobile_user_flow.md`
  - 更新手机用户流程，明确 `remote_ready=true` 只代表 local/mock control-plane 可继续，不证明真实云、4G、HIL 或送达成功。
  - 补充 `auth_state`、`degradation_state`、`retry_hint`、`safe_phone_copy` 的 phone-safe 语义和用户提示。

### 用户旅程变化和触点收益

- 手机端在 local/mock remote control-plane 上可以区分“未登录/凭证错误”“等待小车状态”“等待命令确认”“可继续操作”等状态，不再只看到泛化失败。
- 授权失败响应不会回显 bearer token 或 Authorization header，普通用户看到的是重新登录/检查访问码建议。
- `safe_phone_copy` 给正式手机 UI 提供普通用户可读文案，不暴露 raw JSON、ROS topic、硬件参数或带凭证 URL。

### 接口影响

- Remote mock endpoints 在配置 token 后要求 `Authorization: Bearer <token>`。
- `remote_readiness` 新增：
  - `degradation_state`: `ok`、`status_stale`、`command_pending`、`auth_failed`、`cloud_unreachable`、`malformed_response`。
  - `safe_phone_copy`: 普通用户可读提示。
- `auth_state` 在无 gate 时保持 `mock_not_required`；开启 gate 后，成功请求返回 `authorized`，失败请求返回 `auth_failed`。

### 验证结果

```text
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest src/ros2_trashbot_behavior/test/test_operator_gateway_http.py
Ran 28 tests in 14.674s
OK
```

```text
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest \
  src/ros2_trashbot_behavior/test/test_operator_gateway_http.py \
  src/ros2_trashbot_behavior/test/test_operator_gateway_static.py \
  src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py
Ran 66 tests in 14.664s
OK
```

```text
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile \
  src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_http.py \
  src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway.py \
  src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py
exit 0, no output
```

```text
git diff --check -- \
  src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_http.py \
  src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway.py \
  src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py \
  src/ros2_trashbot_behavior/test/test_operator_gateway_http.py \
  src/ros2_trashbot_behavior/test/test_operator_gateway_static.py \
  src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py \
  docs/product/mobile_user_flow.md \
  sprints/2026.05.12_04-05_remote-auth-degradation-gate/tech-done.md
exit 0, no output
```

### 失败定位

- 第一轮单测失败于 `operator_gateway_http.py` 新增 `_remote_auth_state` 方法缩进错误，已根据 Python `IndentationError` 定位并修复。

### 剩余风险

- 本轮仅证明 local/mock control-plane bearer gate 和 phone-safe readiness；不证明真实云部署、HTTPS/TLS、公网入口、真实 4G/SIM、生产账号、Robot side cursor safety、Nav2/fixed-route、WAVE ROVER 或 HIL。
- `remote_bridge` 并行 Task B 尚未由本 Task 验收，最终接口一致性需 Integration/Product Acceptance 做合并 smoke。

## Task B - Robot Remote Bridge Degradation And Cursor Safety

Owner：`robot-software-engineer`

### 实际改动

- `src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_bridge_protocol.py`
  - 新增 `RemoteCloudError`，把 cloud outage、HTTP 401/403 auth failed、非 JSON/非对象 malformed response 映射为 phone-safe reason/retry hint。
  - HTTP error 不再把 raw body、Authorization header 或 bearer token 拼入异常消息，避免错误状态泄露敏感字段。
- `src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_bridge.py`
  - `RemoteBridgeWorker.poll_once()` 在 status post 失败、command poll auth failed、cloud unreachable、malformed response 时进入保守降级状态。
  - 降级时不拉取或执行不可信 command、不提交本地 action、不推进 `last_ack_id`，也不持久化 `last_terminal_ack_id`。
  - terminal ACK 只有 `post_ack()` 成功后才推进内存 cursor 并原子写入 cursor state；ACK post 失败时缓存本地执行结果用于重试，但不伪造云端 ACK 成功。
- `src/ros2_trashbot_behavior/test/test_remote_bridge.py`
  - 增加 cloud outage、auth failed、malformed response、ACK 失败重试 targeted 覆盖。
  - 断言 phone-safe 状态不包含 token、Authorization、`/cmd_vel` 等敏感内容。

### 接口影响

- ACK 仍只表示 command envelope 处理状态，不代表 delivery result。
- `remote_bridge` 降级状态使用 `remote_ready=false`、`degradation_state`、`auth_state`、`retry_hint`、`safe_phone_copy` 等 phone/cloud 可消费字段。
- malformed cloud response 不触发本地 action goal；auth/cloud outage 不推进 cursor；ACK post 失败不持久化 terminal cursor。

### 验证结果

```text
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest \
  src/ros2_trashbot_behavior/test/test_remote_bridge.py

Ran 23 tests in 10.987s
OK
```

```text
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile \
  src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_bridge.py \
  src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_bridge_protocol.py

exit 0, no output
```

```text
git diff --check -- \
  src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_bridge.py \
  src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_bridge_protocol.py \
  src/ros2_trashbot_behavior/test/test_remote_bridge.py \
  sprints/2026.05.12_04-05_remote-auth-degradation-gate/tech-done.md

exit 0, no output
```

### 失败定位

- 第一轮 `git diff --check` 失败于 `remote_bridge_protocol.py` 原 CRLF 文件新增行造成 trailing whitespace 报告；已将该文件机械归一为 LF 后重跑通过。

### 剩余风险

- 本轮只验证 local mock HTTP/client 行为，没有真实云、真实 4G/SIM、TLS、生产鉴权或弱网实测。
- 本轮未执行 Task A + Task B 合并后的 integration smoke；共享接口文档仍需 Integration/Product Acceptance 统一收口。

## Task C - Integration Smoke And Product Acceptance Handoff

Owner：`robot-software-engineer`

### 实际改动

- `sprints/2026.05.12_04-05_remote-auth-degradation-gate/tech-done.md`
  - 补充 Task C integration smoke 结果、失败定位和剩余风险。

### 集成结论

- Task A operator gateway auth/readiness 与 Task B remote bridge degradation/cursor safety 合并后 targeted integration smoke 通过。
- 未发现需要修复的集成冲突；未改动产品代码、测试代码或共享 docs。
- 共享文档 `docs/product/remote_4g_mvp.md`、`docs/interfaces/ros_contracts.md` 仍按计划留给 Product Owner 统一同步。

### 验证结果

```text
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest \
  src/ros2_trashbot_behavior/test/test_operator_gateway_http.py \
  src/ros2_trashbot_behavior/test/test_operator_gateway_static.py \
  src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py \
  src/ros2_trashbot_behavior/test/test_remote_bridge.py

Ran 89 tests in 25.691s
OK
```

```text
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile \
  src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_http.py \
  src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway.py \
  src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py \
  src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_bridge.py \
  src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_bridge_protocol.py

exit 0, no output
```

```text
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
  sprints/2026.05.12_04-05_remote-auth-degradation-gate/tech-done.md

exit 0, no output
```

### 失败定位

- Task C integration smoke 未复现失败；未发现 Task A 与 Task B 的字段语义或 cursor safety 合并冲突。

### 剩余风险

- 本轮仍是 local/mock software proof，不证明真实云、生产 TLS、公网入口、真实 4G/SIM、弱网、Nav2/fixed-route、WAVE ROVER 或 HIL。
- Product Owner 仍需统一同步共享接口/产品文档并做 side2side/final 收口；本 Task 未按用户范围改 `side2side_check.md`、`final.md` 或 `OKR.md`。
