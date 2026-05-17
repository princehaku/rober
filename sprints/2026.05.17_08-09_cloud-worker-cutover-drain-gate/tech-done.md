# Sprint 2026.05.17_08-09 Cloud Worker Cutover Drain Gate - Tech Done

sprint_type: epic

## 1. 用户价值和产品北极星

用户价值：本轮把云端 worker cutover 时最容易影响普通手机用户体验的 pending command drain、cursor 对账、terminal ACK 边界、失败重跑和脱敏输出做成 Docker-only 可执行合同。它降低未来接入 production worker / DB / queue 时的丢任务、重复执行和误报成功风险。

产品北极星：`rober` 是面向普通手机用户的低成本 ROS2 自主垃圾投递机器人。云中转链路必须支持手机下发、机器人 outbound polling、状态回传、ACK 对账和恢复策略；本轮只证明 `software_proof_docker_cloud_worker_cutover_drain_gate`，不是 real external proof。

## 2. OKR 映射与 KR 拆解

- Objective 5：主目标。A/B implementation 已把 `cloud_worker_cutover_drain` 从计划推进为 CLI/env/artifact/preflight/Docker smoke/Robot diagnostics 共同消费的软件证明链路，可支撑 KR1、KR2、KR5、KR6 的本地 cutover readiness。
- Objective 1：不调整。本轮没有真实 WAVE ROVER、UART、HIL、`T=1001` feedback、`/odom`、`/imu/data`、`/battery` 或 PR #5 所需真实 2D LiDAR / ToF 材料。
- Objective 2 / Objective 3：不调整。本轮没有真实 Nav2/fixed-route、route/elevator field pass、task record、dropoff/cancel completion、delivery result 或 delivery success。
- Objective 4：不调整。本轮没有真实手机/browser、production app、PWA prompt/user choice 或真实量产验收。

## 3. 实际改动

Task A `full-stack-software-engineer` 已改动：

- `.env.example`
- `cloud-relay/README.md`
- `cloud-relay/scripts/docker_smoke.sh`
- `cloud-relay/src/ros2_trashbot_cloud_relay/remote_cloud_relay.py`
- `docs/product/cloud_4g_infrastructure.md`
- `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py`
- `onboard/src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py`

Task A 已实现 `cloud_worker_cutover_drain` Docker-only software proof：

- artifact schema：`trashbot.cloud_worker_cutover_drain.v1`
- summary schema：`trashbot.cloud_worker_cutover_drain_summary.v1`
- evidence boundary：`software_proof_docker_cloud_worker_cutover_drain_gate`
- CLI/env artifact generation and consumption
- preflight check：`cloud_worker_cutover_drain`
- drain records pending/drained count、cursor before/after、terminal ACK summary、idempotent rerun、partial-drain fail-closed、stale/schema/boundary/leak fail-closed、redaction self-check
- 固定保留 `production_ready=false`、`delivery_success=false`、`primary_actions_enabled=false`

Task B `robot-software-engineer` 已改动：

- `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py`
- `onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`
- `onboard/src/ros2_trashbot_behavior/test/test_remote_bridge.py`
- `onboard/src/ros2_trashbot_behavior/test/test_remote_bridge_protocol.py`
- `docs/interfaces/ros_contracts.md`

Task B 已实现 metadata-only diagnostics fence：

- safe summary builder、env/path consumption、diagnostics exposure、fail-closed guardrails
- summary 不触发 backend actions、ACKs 或 cursor persistence
- sidecar metadata 会从 normalized command payload 中剥离
- 固定保留 `production_ready=false`、`delivery_success=false`、`primary_actions_enabled=false`

Task C `product-okr-owner` 已改动：

- `sprints/2026.05.17_08-09_cloud-worker-cutover-drain-gate/tech-done.md`
- `sprints/2026.05.17_08-09_cloud-worker-cutover-drain-gate/side2side_check.md`
- `sprints/2026.05.17_08-09_cloud-worker-cutover-drain-gate/final.md`
- `OKR.md`
- `docs/process/okr_progress_log.md`

## 4. 验证结果

Task A 验证：

```text
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py
Ran 76 tests in 10.399s
OK
```

```text
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py cloud-relay/src/ros2_trashbot_cloud_relay/remote_cloud_relay.py
pass
```

```text
cd cloud-relay && TRASHBOT_REMOTE_CLOUD_BEARER_TOKEN=dev-smoke-token bash scripts/docker_smoke.sh
pass: build/start, artifact generation, preflight consumption, status/command/ACK, cutover drain rerun, backup/restore, restart recovery
```

Task A required `rg` passed；scoped `git diff --check` passed。

Task B 验证：

```text
python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_remote_bridge.py onboard/src/ros2_trashbot_behavior/test/test_remote_bridge_protocol.py onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py
Ran 335 tests in 101.917s
OK
```

```text
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_bridge.py onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_bridge_protocol.py onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py
pass
```

Task B required `rg` passed；scoped `git diff --check` passed。

Main-session integration read：

- `git diff --name-only` 只显示 A/B implementation files plus planning docs already committed in `a84b22f`。
- Marker scan for `cloud_worker_cutover_drain`、`software_proof_docker_cloud_worker_cutover_drain_gate`、schema and production flags passed across implementation/docs/sprint planning。

Task C closeout 验收：

```text
rg -n "cloud_worker_cutover_drain|software_proof_docker_cloud_worker_cutover_drain_gate|Objective 5|Docker-only|production_ready=false|delivery_success=false|primary_actions_enabled=false|PR #5|PR #4|not real external proof" sprints/2026.05.17_08-09_cloud-worker-cutover-drain-gate OKR.md docs/process/okr_progress_log.md
pass
```

```text
git diff --check -- sprints/2026.05.17_08-09_cloud-worker-cutover-drain-gate/tech-done.md sprints/2026.05.17_08-09_cloud-worker-cutover-drain-gate/side2side_check.md sprints/2026.05.17_08-09_cloud-worker-cutover-drain-gate/final.md OKR.md docs/process/okr_progress_log.md
pass
```

## 5. 偏差、失败定位和处理

- 本轮 Task A / Task B 最终验证均通过；Product closeout 没有发现需要工程返工的失败。
- A/B 证据仍是 Docker-only software proof。它不能作为真实 production worker / migration / cutover、真实 production DB/queue、真实 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、HIL、真实手机/browser、Nav2/fixed-route 或 delivery success。

## 6. 剩余风险和阻塞

- Objective 5 仍缺真实 production worker/migration/cutover、production DB/queue connectivity、公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、真实手机/browser、production app、PWA prompt/user choice、多实例一致性、真实 queue ordering、transaction isolation 和真实 backup/recovery 外部证据。
- PR #4 route/elevator field materials 仍是独立缺口：真实电梯门状态、目标楼层确认、人工协助记录、Nav2/fixed-route runtime log、route completion signal、task record、dropoff/cancel completion 和 delivery result 仍未提供。
- PR #5 2D LiDAR / ToF hardware materials 仍是独立缺口：真实 SKU/source、receipt、采购、安装、接线、电源、标定、HIL-entry 和 field evidence 仍未提供。
- 本轮没有真实 WAVE ROVER、真实串口/UART、HIL、真实 Nav2/fixed-route、真实 route/elevator field pass、真实投放或真实 delivery success。
