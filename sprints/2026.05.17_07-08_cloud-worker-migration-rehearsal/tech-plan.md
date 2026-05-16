# Sprint 2026.05.17_07-08 Cloud Worker Migration Rehearsal - Tech Plan

sprint_type: epic

## 1. 总体方案

实现 `cloud_worker_migration_rehearsal`，作为 Objective 5 在 Docker-only host 上可执行的 worker/migration rehearsal gate。该 gate 使用本地 SQLite relay state 演练 migration 与 queue worker invariant，并输出 artifact / summary 供 preflight、Robot compatibility fence 和 Product closeout 使用。

统一 evidence boundary：

- `software_proof_docker_cloud_worker_migration_rehearsal_gate`
- `trashbot.cloud_worker_migration_rehearsal.v1`
- `trashbot.cloud_worker_migration_rehearsal_summary.v1`
- `production_ready=false`
- `delivery_success=false`
- `primary_actions_enabled=false`

本轮不得声明 production ready、真实 DB/queue、真实 worker、真实 migration、外部云、4G/SIM、OSS/CDN live traffic、HIL 或 delivery success。

## 2. Task A - Full-Stack Cloud Relay

Owner：`full-stack-software-engineer`

允许改动：

- `cloud-relay/src/ros2_trashbot_cloud_relay/remote_cloud_relay.py`
- `cloud-relay/README.md`
- `cloud-relay/scripts/docker_smoke.sh`
- `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py`
- `onboard/src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py`
- `.env.example`
- `docs/product/cloud_4g_infrastructure.md`

实现要求：

- 新增 `cloud_worker_migration_rehearsal` CLI 或等价入口，建议支持 `--write-cloud-worker-migration-rehearsal-artifact`、`--cloud-worker-migration-rehearsal-artifact`、`--preflight` 消费和本地 SQLite state 参数。
- Artifact schema 为 `trashbot.cloud_worker_migration_rehearsal`、`schema_version=1`，summary schema 为 `trashbot.cloud_worker_migration_rehearsal_summary`。
- Migration rehearsal 至少覆盖 SQLite state 初始化、schema version 标记、重复运行幂等、坏 schema / checksum / stale artifact fail closed。
- Worker rehearsal 至少覆盖 command enqueue、status write、ACK accepted/processing、terminal ACK 不等于 delivery success、cursor 只按既有语义推进。
- Preflight 消费 valid artifact 时新增 `cloud_worker_migration_rehearsal` check，但整体仍必须保持 `production_ready=false` 和 blocked-by-design。
- Artifact、preflight 和 summary 不得输出 DB URL、queue URL、credential-bearing URL、Authorization、bearer token、OSS AK/SK、root password、raw local path、serial/UART、WAVE ROVER、ROS topic 或 `/cmd_vel`。
- 新增代码技术注释必须使用中文，并解释为什么这是 Docker-only rehearsal、为什么 ACK 不代表 delivery success、为什么 artifact 必须脱敏。
- 同步文档说明本轮是 `software_proof_docker_cloud_worker_migration_rehearsal_gate`，不是真实 production worker/migration。

验收命令：

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py cloud-relay/src/ros2_trashbot_cloud_relay/remote_cloud_relay.py
cd cloud-relay && TRASHBOT_REMOTE_CLOUD_BEARER_TOKEN=dev-smoke-token bash scripts/docker_smoke.sh
rg -n "cloud_worker_migration_rehearsal|software_proof_docker_cloud_worker_migration_rehearsal_gate|trashbot.cloud_worker_migration_rehearsal|production_ready=false|delivery_success=false|primary_actions_enabled=false" cloud-relay/src/ros2_trashbot_cloud_relay/remote_cloud_relay.py onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py onboard/src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py cloud-relay/README.md cloud-relay/scripts/docker_smoke.sh .env.example docs/product/cloud_4g_infrastructure.md
git diff --check -- cloud-relay/src/ros2_trashbot_cloud_relay/remote_cloud_relay.py onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py onboard/src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py cloud-relay/README.md cloud-relay/scripts/docker_smoke.sh .env.example docs/product/cloud_4g_infrastructure.md
```

## 3. Task B - Robot Compatibility Fence

Owner：`robot-software-engineer`

允许改动：

- `onboard/src/ros2_trashbot_behavior/test/test_remote_bridge.py`
- `onboard/src/ros2_trashbot_behavior/test/test_remote_bridge_protocol.py`
- `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_bridge.py`，仅当测试暴露真实 metadata isolation 缺口时允许最小修改。
- `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_bridge_protocol.py`，仅当 protocol helper 需要最小修复时允许修改。
- `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py`
- `onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`
- `docs/interfaces/ros_contracts.md`

实现要求：

- 证明 `cloud_worker_migration_rehearsal` / summary 只能作为 metadata-only diagnostics 或 preflight summary 被消费。
- Rehearsal metadata 不得进入 robot command payload，不得触发 collect/dropoff/cancel/ACK action，不得推进或持久化 command cursor。
- Diagnostics 只暴露 safe summary、schema、boundary、migration rehearsal status、worker rehearsal status、retry hint、not_proven、`production_ready=false`、`delivery_success=false`、`primary_actions_enabled=false`。
- 对 missing、unsupported schema/boundary、unsafe copy、credential leak、success wording、`production_ready=true`、`delivery_success=true`、`primary_actions_enabled=true` fail closed。
- 不改变 `trashbot.remote.v1` command/status/ACK envelope，不改变 Nav2、HIL、route/elevator、delivery result 或 phone action 语义。
- 新增代码技术注释必须使用中文，并解释 metadata-only 隔离和动作安全边界。

验收命令：

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_remote_bridge.py onboard/src/ros2_trashbot_behavior/test/test_remote_bridge_protocol.py onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_bridge.py onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_bridge_protocol.py onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py
rg -n "cloud_worker_migration_rehearsal|software_proof_docker_cloud_worker_migration_rehearsal_gate|metadata-only|production_ready=false|delivery_success=false|primary_actions_enabled=false" onboard/src/ros2_trashbot_behavior/test/test_remote_bridge.py onboard/src/ros2_trashbot_behavior/test/test_remote_bridge_protocol.py onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py docs/interfaces/ros_contracts.md
git diff --check -- onboard/src/ros2_trashbot_behavior/test/test_remote_bridge.py onboard/src/ros2_trashbot_behavior/test/test_remote_bridge_protocol.py onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_bridge.py onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_bridge_protocol.py onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py docs/interfaces/ros_contracts.md
```

## 4. Task C - Product Closeout

Owner：`product-okr-owner`

后续允许改动：

- `sprints/2026.05.17_07-08_cloud-worker-migration-rehearsal/tech-done.md`
- `sprints/2026.05.17_07-08_cloud-worker-migration-rehearsal/side2side_check.md`
- `sprints/2026.05.17_07-08_cloud-worker-migration-rehearsal/final.md`
- `OKR.md`
- `docs/process/okr_progress_log.md`

要求：

- 汇总 Task A / Task B 的实际改动、验证结果、失败定位和剩余风险。
- 核对所有产物均保持 `software_proof_docker_cloud_worker_migration_rehearsal_gate`、`production_ready=false`、`delivery_success=false`、`primary_actions_enabled=false`。
- OKR 更新必须保守：Objective 5 只有在 worker/migration rehearsal 真正落地且验证通过后才允许小幅说明软件功能前进；不得写成真实 external proof。
- 明确本轮不是真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、真实 worker、真实 migration、HIL、真实手机/browser、Nav2/fixed-route 或 delivery success。
- 确认 PR #5 的真实 2D LiDAR / ToF 材料仍是独立缺口，没有被本轮替代。

验收命令：

```bash
rg -n "cloud_worker_migration_rehearsal|software_proof_docker_cloud_worker_migration_rehearsal_gate|Objective 5|Docker-only|production_ready=false|delivery_success=false|primary_actions_enabled=false|PR #5|not real external proof" sprints/2026.05.17_07-08_cloud-worker-migration-rehearsal OKR.md docs/process/okr_progress_log.md
git diff --check -- sprints/2026.05.17_07-08_cloud-worker-migration-rehearsal/tech-done.md sprints/2026.05.17_07-08_cloud-worker-migration-rehearsal/side2side_check.md sprints/2026.05.17_07-08_cloud-worker-migration-rehearsal/final.md OKR.md docs/process/okr_progress_log.md
```

## 5. 接口影响

- Cloud relay 新增 `trashbot.cloud_worker_migration_rehearsal.v1` artifact 和 `trashbot.cloud_worker_migration_rehearsal_summary.v1` summary。
- Preflight 新增 `cloud_worker_migration_rehearsal` check；有效 artifact 也不能把整体状态改成 production ready。
- Robot bridge 只允许 metadata-only diagnostics consumption，不改变 command/status/ACK envelope。
- 手机主操作不在本轮修改；如后续显示 summary，必须只读且不启用 Start Delivery、Confirm Dropoff 或 Cancel。
- 文档实现阶段同步更新 `docs/product/cloud_4g_infrastructure.md`、`cloud-relay/README.md` 和 `docs/interfaces/ros_contracts.md`。

## 6. 并行执行规则

- Task A 与 Task B 文件范围互不重叠，下一阶段必须并行派发 `full-stack-software-engineer` 和 `robot-software-engineer`。
- Task A 主责 cloud relay artifact / preflight，Task B 主责 robot metadata isolation fence。
- Task C 只在 A/B 返回验证证据后执行 Product closeout。
- 本轮不派 `hardware-engineer` 写文件，因为没有真实硬件材料；不派 `autonomy-engineer` 写文件，因为 route/elevator wrapper 已被上一轮明确停止。

## 7. OKR 最低优先级核对

1. 当前 `OKR.md` 4.1 节完成度最低的 Objective：Objective 5，约 66%。
2. 本 sprint 是否针对该最低 Objective：是，主目标为 Objective 5。
3. 为什么无法提供真实 O5 external proof：当前运行环境是 Docker-only，没有真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、真实 worker/migration、真实多实例、真实云账号或外部探测材料。
4. 为什么仍选择 Objective 5 可执行功能：CEO 明确本机没有真实硬件，只有 Docker，并要求“重新在功能往前走”。相比再做 blocked external probe 或 metadata wrapper，`cloud_worker_migration_rehearsal` 能把 production DB/queue 的 migration 与 worker 从配置/外部探测枚举推进为本地 SQLite relay 可执行 rehearsal artifact，属于 Objective 5 的真实软件功能前进。
5. 为什么不继续 O2/O3 wrapper：最新 `2026.05.17_06-07_route-task-field-retest-evidence-dispatch/final.md` 已明确不要再堆 route/elevator 本地 wrapper；没有真实现场材料时继续 O2/O3 只会重复包装同一 blocker。
6. 为什么不继续 O1 wrapper：PR #5 暴露的硬件 baseline、2D LiDAR / ToF、vendor/source citation 和 HIL-entry 材料近期已通过 source alignment、procurement、readiness/execution pack 消化为 `hardware_material_pending` / `not_proven`；本机没有真实硬件，继续 O1 本地 wrapper 不能产生真实 WAVE ROVER、UART、HIL 或传感器材料。
7. final.md 收口时必须复核：本轮是否仍保持 Docker-only、`software_proof_docker_cloud_worker_migration_rehearsal_gate`、`production_ready=false`、`delivery_success=false`、`primary_actions_enabled=false`，且没有把 rehearsal 写成真实 production DB/queue、真实 worker、真实 migration 或 external proof。

## 8. 本 planning 阶段验收命令

```bash
test -f sprints/2026.05.17_07-08_cloud-worker-migration-rehearsal/pre_start.md && test -f sprints/2026.05.17_07-08_cloud-worker-migration-rehearsal/prd.md && test -f sprints/2026.05.17_07-08_cloud-worker-migration-rehearsal/tech-plan.md
rg -n "cloud_worker_migration_rehearsal|software_proof_docker_cloud_worker_migration_rehearsal_gate|Objective 5|Docker-only|production_ready=false|delivery_success=false|primary_actions_enabled=false|OKR 最低优先级核对" sprints/2026.05.17_07-08_cloud-worker-migration-rehearsal
git diff --check -- sprints/2026.05.17_07-08_cloud-worker-migration-rehearsal/pre_start.md sprints/2026.05.17_07-08_cloud-worker-migration-rehearsal/prd.md sprints/2026.05.17_07-08_cloud-worker-migration-rehearsal/tech-plan.md
```
