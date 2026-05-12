# Sprint 2026.05.12_19-20 Remote Production Store Queue Gate - Tech Plan

## 状态

- 阶段：tech-plan
- 主责：`full-stack-software-engineer`
- 兼容性围栏：`robot-software-engineer`
- Evidence boundary：`software_proof_docker_production_store_queue_gate`

## Task A - Full-stack / Remote Cloud Gate

### 文件范围

- `src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py`
- `src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_http.py`
- `src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py`
- `src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway.py`
- `src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py`
- `src/ros2_trashbot_behavior/test/test_operator_gateway_http.py`
- `src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`
- `.env.example`
- `docs/product/cloud_4g_infrastructure.md`
- `docs/product/remote_4g_mvp.md`
- `docs/product/mobile_user_flow.md`
- `sprints/2026.05.12_19-20_remote-production-store-queue-gate/tech-done.md`

### 实现要求

- 新增 production store/queue gate artifact，schema/version/evidence boundary/checksum/not_proven 与既有 artifact 风格一致。
- 新增 CLI 参数和环境变量消费路径，用于生成 artifact 与 preflight 消费。
- `production_preflight_payload` 新增 `production_store_queue` check；有效 artifact 只代表 Docker/local software proof，不得让 `production_ready=true`。
- Operator status/diagnostics 新增 phone-safe summary，沿用 missing/invalid/stale/ready 模式。
- 文档同步说明本轮只证明 store/queue contract consumption，不证明真实生产 DB/queue 或多实例一致性。

### 验收命令

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py src/ros2_trashbot_behavior/test/test_operator_gateway_http.py src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_http.py src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway.py
git diff --check -- src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_http.py src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway.py src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py src/ros2_trashbot_behavior/test/test_operator_gateway_http.py src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py .env.example docs/product/cloud_4g_infrastructure.md docs/product/remote_4g_mvp.md docs/product/mobile_user_flow.md sprints/2026.05.12_19-20_remote-production-store-queue-gate/tech-done.md
```

## Task B - Robot Compatibility Fence

### 文件范围

- `src/ros2_trashbot_behavior/test/test_remote_bridge.py`
- `src/ros2_trashbot_behavior/test/test_remote_bridge_protocol.py`
- `sprints/2026.05.12_19-20_remote-production-store-queue-gate/tech-done.md`

### 验收要求

- 优先不改产品代码；只在发现真实兼容性缺口时补围栏。
- 确认 production store/queue metadata 不改变 `trashbot.remote.v1` command/status/ack envelope。
- 确认 ACK 仍不是 delivery success，cloud/outage/invalid response 不触发本地 action、不推进或持久化 cursor。

### 验收命令

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest src/ros2_trashbot_behavior/test/test_remote_bridge.py src/ros2_trashbot_behavior/test/test_remote_bridge_protocol.py
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_bridge.py src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_bridge_protocol.py
git diff --check -- src/ros2_trashbot_behavior/test/test_remote_bridge.py src/ros2_trashbot_behavior/test/test_remote_bridge_protocol.py sprints/2026.05.12_19-20_remote-production-store-queue-gate/tech-done.md
```
