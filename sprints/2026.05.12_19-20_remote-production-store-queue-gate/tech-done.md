# Sprint 2026.05.12_19-20 Remote Production Store Queue Gate - Tech Done

## 状态

- 阶段：tech-done
- Task：A / full-stack-software-engineer
- Evidence boundary：`software_proof_docker_production_store_queue_gate`
- Phone consumption boundary：`software_proof_docker_production_store_queue_phone_consumption`

## 实际改动

- `remote_cloud_relay.py` 新增 `trashbot.production_store_queue_gate` artifact：包含 schema/version、checksum、`production_ready=false`、`overall_status=blocked`、`not_proven`、phone-safe forbidden marker 校验、missing/invalid/stale/ready 摘要、CLI 生成参数和 preflight 环境变量/CLI 消费路径。
- `production_preflight_payload` 新增 `production_store_queue` check；有效 artifact 会让本地软件证明边界进入 `software_proof_docker_production_store_queue_gate`，但仍保持 `production_ready=false`，且 `not_proven` 继续列出真实生产 DB/queue、多实例一致性、生产 queue ordering、transaction isolation、生产备份、真实灾备、真实云、真实 4G/SIM、Nav2/fixed-route、WAVE ROVER/HIL 和真实送达。
- `operator_gateway_http.py` 的 `/api/status.phone_readiness.production_store_queue` 新增 phone-safe 摘要；`operator_gateway_diagnostics.py` 的 `/api/diagnostics.production_store_queue` 新增同源摘要。
- `operator_gateway.py` 新增 `production_store_queue_artifact_ref` 参数，支持 ROS launch/参数链路注入 artifact ref。
- `.env.example`、`docs/product/cloud_4g_infrastructure.md`、`docs/product/remote_4g_mvp.md`、`docs/product/mobile_user_flow.md` 同步本轮 evidence boundary、环境变量、CLI 和手机/diagnostics 字段口径。
- Targeted tests 覆盖 artifact 生成、checksum/schema、phone-safe 摘要、missing/invalid/stale fail-closed、preflight 消费、status/diagnostics 消费和路径/checksum/robot_id 不外泄。

## 验证结果

```text
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py src/ros2_trashbot_behavior/test/test_operator_gateway_http.py src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py
Ran 112 tests in 26.526s
OK
```

```text
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_http.py src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway.py
passed
```

```text
git diff --check -- src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_http.py src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway.py src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py src/ros2_trashbot_behavior/test/test_operator_gateway_http.py src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py .env.example docs/product/cloud_4g_infrastructure.md docs/product/remote_4g_mvp.md docs/product/mobile_user_flow.md sprints/2026.05.12_19-20_remote-production-store-queue-gate/tech-done.md
passed
```

## 失败定位

- 本轮 Task A 验证未出现失败。

## 剩余风险

- 当前 artifact 仍是 Docker/local software proof，只证明 production store/queue contract artifact 可生成、校验并被 preflight/status/diagnostics 消费。
- 仍未证明真实生产 DB/queue、多实例一致性、生产 queue ordering、transaction isolation、生产备份策略、真实灾备、真实云、HTTPS/TLS 公网入口、真实 4G/SIM、Nav2/fixed-route、WAVE ROVER、HIL 或真实送达。
- Task B 已确认新增 gate metadata 不改变 remote bridge command/status/ack envelope、ACK 语义或 cursor 推进规则。

## Task B - Robot Compatibility Fence

### 实际改动

- `src/ros2_trashbot_behavior/test/test_remote_bridge.py` 新增 production store/queue metadata 兼容性围栏。
- 正常 command response 混入 `production_store_queue`、`preflight`、`delivery_success` 等诊断字段时，worker 仍只按 `trashbot.remote.v1` command envelope 执行一次 `collect`，ACK payload 不携带 production store/queue 元数据，也不把 ACK 升级成 delivery success。
- metadata-only blocked response 只有 `production_store_queue` / `preflight` 而没有 `command` envelope 时，worker fail-closed：不触发本地 action、不发 ACK、不推进 `last_ack_id`、不写 cursor state。

### 验证结果

```text
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest src/ros2_trashbot_behavior/test/test_remote_bridge.py src/ros2_trashbot_behavior/test/test_remote_bridge_protocol.py
Ran 39 tests in 19.385s
OK
```

```text
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_bridge.py src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_bridge_protocol.py
passed
```

### 失败定位

- Task B 测试和编译验证未出现失败。

### 剩余风险

- 本轮只覆盖 robot bridge 的 Python/unit compatibility fence，没有真实 ROS2 runtime、真实云、真实 4G/SIM、生产 DB/queue、多实例一致性、Nav2/fixed-route、WAVE ROVER、HIL 或真实送达证据。

## Product Acceptance

- Product/OKR 结论：本轮按 `software_proof_docker_production_store_queue_gate` 收口，可计入 O6 小幅进展；不计入真实云、4G、HIL、Nav2/fixed-route 或真实送达。
- OKR 调整：O6 从约 45% 保守上调到约 47%；O5/O1/O2/O3/O4 保持不变。
- 验收边界：Task A `Ran 112 tests in 26.526s OK` 与 Task B `Ran 39 tests in 19.385s OK` 只证明 Docker/local artifact、phone-safe consumption 和 robot compatibility fence。
- 剩余风险：真实生产 DB/queue、多实例一致性、queue ordering、transaction isolation、生产备份/灾备、真实云、HTTPS/TLS、公网入口、真实 4G/SIM、WAVE ROVER、HIL 和真实送达仍未证明。
