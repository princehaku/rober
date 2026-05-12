# Sprint 2026.05.12_21-22 Remote Queue Ordering Drill - Tech Done

## 状态

- 阶段：tech-done in progress
- Evidence boundary：`software_proof_docker_queue_ordering_drill`
- 当前记录：Task A full-stack queue ordering drill gate 已完成；Task B robot compatibility fence 已完成。

## Task A - Full-stack / Remote Queue Ordering Drill

### 用户旅程变化和触点收益

- `/api/status.phone_readiness.queue_ordering_drill` 新增 phone-safe 摘要，普通用户或支持人员能看到 queue ordering drill 是 `ready|missing|invalid|stale|failed`，而不是 raw artifact、DB/queue URL 或 ROS 细节。
- `/api/diagnostics.queue_ordering_drill` 使用同一摘要，支持复现“并发提交、相邻 command id、cursor/ACK 语义”是否已有 Docker/local 证据。
- ACK 文案继续保持 command accepted/processing evidence，不升级为 delivery success；本轮只产生 `software_proof_docker_queue_ordering_drill`。

### 实际改动

- `src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py`
  - 新增 `trashbot.queue_ordering_drill` artifact schema/version、`software_proof_docker_queue_ordering_drill` evidence boundary、`not_proven`、`safe_summary`、`retry_hint`、`updated_at` 和 checksum。
  - 新增 Docker/local ordering/concurrency/cursor/ACK invariant：并发本地提交、相邻 `cmd-9` / `cmd-10` 顺序、cursor 只在 terminal ACK 后推进、ACK 不等于 delivery success。
  - 新增 `--write-queue-ordering-drill-artifact`、`--queue-ordering-drill-artifact`、`--queue-ordering-drill-status`、`--queue-ordering-drill-robot-id` CLI 参数。
  - preflight 新增 `queue_ordering_drill` check；valid artifact 只让 `software_proof_ready=true`，继续保持 `production_ready=false`。
- `src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_http.py`
  - `/api/status.phone_readiness.queue_ordering_drill` 新增 phone-safe summary，不改变本地 action permission 或 robot state。
- `src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py`
  - `/api/diagnostics.queue_ordering_drill` 新增同口径 phone-safe summary。
- `src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway.py`
  - 新增 `queue_ordering_drill_artifact_ref` 参数，默认读取 `TRASHBOT_REMOTE_CLOUD_QUEUE_ORDERING_DRILL_ARTIFACT`。
- `src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py`
  - 覆盖 artifact generation、phone summary、ready/missing/invalid/stale/failed/hostile artifact、preflight pass/warning/blocked 和敏感字段不外泄。
- `src/ros2_trashbot_behavior/test/test_operator_gateway_http.py`
  - 覆盖 `/api/status.phone_readiness.queue_ordering_drill` 输出 shape 和路径/checksum/robot id 不外泄。
- `src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`
  - 覆盖 `/api/diagnostics.queue_ordering_drill` 输出 shape 和路径/checksum/robot id 不外泄。
- `.env.example`
  - 新增 `TRASHBOT_REMOTE_CLOUD_QUEUE_ORDERING_DRILL_ARTIFACT` 占位变量；未加入真实密钥、DB URL、queue URL 或账号。
- `docs/product/cloud_4g_infrastructure.md`
  - 记录 queue ordering drill artifact/preflight/phone-safe 摘要和 production gap。
- `docs/product/remote_4g_mvp.md`
  - 记录 CLI、artifact boundary、phone consumption boundary 和真实生产队列未证明项。
- `docs/product/mobile_user_flow.md`
  - 记录 `phone_readiness.queue_ordering_drill` 和 `diagnostics.queue_ordering_drill` 字段语义。

### 接口影响

- 新增 artifact schema：`trashbot.queue_ordering_drill`。
- 新增 evidence boundary：`software_proof_docker_queue_ordering_drill`。
- 新增 phone consumption boundary：`software_proof_docker_queue_ordering_phone_consumption`。
- 新增 preflight check：`queue_ordering_drill`。
- 新增 status/diagnostics summary：`queue_ordering_drill`。
- 不改变 `trashbot.remote.v1` command/status/ack envelope；不触发 robot action；不推进或持久化 robot cursor。

### 验证结果

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py src/ros2_trashbot_behavior/test/test_operator_gateway_http.py src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py
```

结果：

```text
Ran 117 tests in 26.630s
OK
```

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_http.py src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway.py
```

结果：通过，无输出。

```bash
git diff --check -- src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_http.py src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway.py src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py src/ros2_trashbot_behavior/test/test_operator_gateway_http.py src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py .env.example docs/product/cloud_4g_infrastructure.md docs/product/remote_4g_mvp.md docs/product/mobile_user_flow.md sprints/2026.05.12_21-22_remote-queue-ordering-drill/tech-done.md
```

结果：通过，无输出。

临时 CLI smoke：

```text
create ok= True status= passed boundary= software_proof_docker_queue_ordering_drill
preflight software_proof_ready= True production_ready= False boundary= software_proof_docker_queue_ordering_drill queue_ordering_drill= pass
```

### 偏差和失败定位

- 未运行真实云、真实 4G、真实生产 DB/queue、多实例 queue ordering、transaction isolation、Nav2/fixed-route、WAVE ROVER、HIL 或真实送达验证。
- 首轮 Task A 单测和 py_compile 均通过，未出现需定位的失败。

### 剩余风险

- 本轮只证明 Docker/local artifact、preflight、status 和 diagnostics 能表达 queue ordering drill；不证明真实生产队列、多实例一致性或事务隔离。
- `cmd-9` / `cmd-10` 顺序是本地 artifact invariant 和测试围栏，不代表生产队列已经具备数字排序或事务语义。
- ACK 仍只代表 command accepted/processing evidence；真实 delivery success 仍必须由后续 status/task record/实机证据证明。

## Task B - Robot Compatibility Fence

### 实际改动

- `src/ros2_trashbot_behavior/test/test_remote_bridge.py`
  - 新增 queue ordering drill 元数据兼容性围栏，确认 `status_response`、`command_response`、`ack_response` 中的 `queue_ordering_drill`、`ordering_status`、`delivery_success` 不会污染 `trashbot.remote.v1` command/status/ack envelope。
  - 新增 `cmd-10` 后接 `cmd-9` 的回归围栏，确认 robot bridge 只消费 relay 返回的下一条 command envelope，不依赖 command id 字符串排序，也不推断生产队列实现细节。
  - 新增 metadata-only `blocked` / `invalid` / `stale` 响应围栏，确认没有 command envelope 时不触发本地 action、不提交 ACK、不推进 `last_ack_id`、不持久化 cursor。
- `src/ros2_trashbot_behavior/test/test_remote_bridge_protocol.py`
  - 新增 protocol helper 围栏，确认 command envelope 之外的 queue ordering drill 元数据会被忽略。
  - 新增 `cmd-10` command id 保序围栏，确认 helper 不做字符串排序或队列语义推断。

### 验证结果

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest src/ros2_trashbot_behavior/test/test_remote_bridge.py src/ros2_trashbot_behavior/test/test_remote_bridge_protocol.py
```

结果：

```text
Ran 46 tests in 23.041s
OK
```

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_bridge.py src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_bridge_protocol.py
```

结果：通过，无输出。

### 偏差和失败定位

- 未发现需要修改 `remote_bridge.py` 或 `remote_bridge_protocol.py` 的真实兼容性缺口；本轮只新增测试围栏。
- 未运行真实云、真实 4G、真实生产 DB/queue、多实例队列、Nav2/fixed-route、WAVE ROVER、HIL 或真实送达验证。

### 剩余风险

- 当前证据只证明 robot bridge 对 queue ordering drill 元数据保持 fail-closed 和 envelope 兼容，不证明 Task A 的 queue ordering artifact、preflight、status 或 diagnostics 已完成。
- ACK 仍只代表 command accepted/processing evidence；真实 delivery success 仍必须由后续 status/task record/实机证据证明。
