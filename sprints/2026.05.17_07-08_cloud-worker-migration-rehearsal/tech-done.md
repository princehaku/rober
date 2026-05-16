# Sprint 2026.05.17_07-08 Cloud Worker Migration Rehearsal - Tech Done

sprint_type: epic

## 1. 实际改动

### Task A - Full-stack cloud relay

Task A 已把 Objective 5 的 cloud worker/migration rehearsal 从规划推进到 Docker-only 可执行 gate。

Changed:

- `.env.example`
- `cloud-relay/README.md`
- `cloud-relay/scripts/docker_smoke.sh`
- `cloud-relay/src/ros2_trashbot_cloud_relay/remote_cloud_relay.py`
- `docs/product/cloud_4g_infrastructure.md`
- `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py`
- `onboard/src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py`

实际能力：

- 新增 `--write-cloud-worker-migration-rehearsal-artifact`、`--cloud-worker-migration-rehearsal-artifact` 和 `TRASHBOT_REMOTE_CLOUD_WORKER_MIGRATION_REHEARSAL_ARTIFACT`。
- 新增 artifact schema `trashbot.cloud_worker_migration_rehearsal.v1` 与 summary schema `trashbot.cloud_worker_migration_rehearsal_summary.v1`。
- 固定 evidence boundary 为 `software_proof_docker_cloud_worker_migration_rehearsal_gate`。
- Preflight / Docker smoke 能消费 rehearsal artifact，但仍保持 `production_ready=false`、`delivery_success=false`、`primary_actions_enabled=false`。

### Task B - Robot compatibility fence

Task B 已把 cloud worker/migration rehearsal 限定为 Robot diagnostics metadata-only summary。

Changed:

- `docs/interfaces/ros_contracts.md`
- `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py`
- `onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`
- `onboard/src/ros2_trashbot_behavior/test/test_remote_bridge.py`
- `onboard/src/ros2_trashbot_behavior/test/test_remote_bridge_protocol.py`

未改：

- `remote_bridge.py`
- `remote_bridge_protocol.py`

实际能力：

- Robot diagnostics 只暴露 safe summary、schema、boundary、migration/worker rehearsal status、retry hint、not-proven 状态和 fail-closed production flags。
- `cloud_worker_migration_rehearsal` 不进入 command payload，不触发 collect/dropoff/cancel/ACK，不推进或持久化 command cursor。
- ACK 仍是 accepted/processing evidence，不等于 delivery success。

## 2. 验证结果

Task A verification:

```text
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py
Ran 74 tests ... OK

PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py cloud-relay/src/ros2_trashbot_cloud_relay/remote_cloud_relay.py
passed

cd cloud-relay && TRASHBOT_REMOTE_CLOUD_BEARER_TOKEN=dev-smoke-token bash scripts/docker_smoke.sh
passed: Docker build/start, artifact generation, preflight consumption, status/command/ACK, backup/restore, restart recovery

required rg
passed

scoped git diff --check
passed
```

Task B verification:

```text
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_remote_bridge.py onboard/src/ros2_trashbot_behavior/test/test_remote_bridge_protocol.py onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py
Ran 329 tests in 100.453s OK
existing HTTP socket ResourceWarning only

PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_bridge.py onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_bridge_protocol.py onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py
passed

required rg
passed

scoped git diff --check
passed
```

## 3. 失败定位与修复

- Task A 首轮 artifact redaction self-check 将合法字段名 `db_queue_urls_recorded` / `serial_or_ros_control_recorded` 误判为敏感内容。已重命名为 `db_queue_locations_recorded` / `robot_control_details_recorded` 并复验通过。
- Task B 首轮新增测试错误要求 summary 不包含 `command_payload`。实现侧已收敛为更窄的 metadata-only diagnostics，移除额外 `command_payload_allowed` / ACK / cursor diagnostics 字段；action isolation 由 remote bridge tests 证明。

## 4. 偏差与边界

本轮完成的是 `Docker-only` 的 `software_proof_docker_cloud_worker_migration_rehearsal_gate`，不是 real external proof。

保持：

- `production_ready=false`
- `delivery_success=false`
- `primary_actions_enabled=false`
- `not real external proof`

不证明：

- 真实 production DB/queue
- 真实 production migration
- 真实 production worker
- 多实例一致性
- 生产 queue ordering 或 transaction isolation
- 真实公网 HTTPS/TLS
- 真实 4G/SIM
- OSS/CDN live traffic
- HIL、WAVE ROVER、Nav2/fixed-route、真实手机/browser 或 delivery success

PR #5 的硬件 2D LiDAR / ToF / source / material gap 仍是独立缺口，本轮云 worker/migration rehearsal 不解决该硬件证据链。

## 5. 剩余风险

- Objective 5 的真实外部证据仍缺：公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue connectivity、真实 worker/migration、生产凭证、生产队列、多实例和灾备材料。
- Robot 侧只证明 metadata-only isolation，不代表真实任务执行、真实 ACK 到 delivery 的闭环或上车联调。
- 本轮不涉及 Objective 1/2/3/4 的真实硬件、真实 route/elevator field pass、真实手机设备或 production app proof。
