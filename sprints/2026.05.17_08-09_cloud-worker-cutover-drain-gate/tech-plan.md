# Sprint 2026.05.17_08-09 Cloud Worker Cutover Drain Gate - Tech Plan

sprint_type: epic

## 1. 总体方案

实现 `cloud_worker_cutover_drain`，作为 Objective 5 在 Docker-only host 上的 worker cutover / drain gate。该 gate 消费本地 SQLite / File relay state 中的 pending command，输出 artifact / summary，并被 preflight、Docker smoke、Robot diagnostics metadata-only fence 和 Product closeout 消费。

统一 evidence boundary：

- `software_proof_docker_cloud_worker_cutover_drain_gate`
- `trashbot.cloud_worker_cutover_drain.v1`
- `trashbot.cloud_worker_cutover_drain_summary.v1`
- `Docker-only`
- `production_ready=false`
- `delivery_success=false`
- `primary_actions_enabled=false`
- not real external proof

本轮不得声明真实 production worker/migration、真实 production DB/queue、真实公网 HTTPS/TLS、真实 4G/SIM、OSS/CDN live traffic、真实手机、HIL、Nav2/fixed-route、真实投放或 delivery success。

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

- 新增 `cloud_worker_cutover_drain` CLI 或等价入口，建议支持 `--write-cloud-worker-cutover-drain-artifact`、`--cloud-worker-cutover-drain-artifact`、relay state 参数和 env override。
- Artifact schema 为 `trashbot.cloud_worker_cutover_drain.v1`，summary schema 为 `trashbot.cloud_worker_cutover_drain_summary.v1`。
- Drain 本地 SQLite / File relay state 中 pending command，记录 pending count、drained count、cursor before/after、terminal ACK summary、retry hint 和 redaction self-check。
- 覆盖 idempotency：重复运行不重复推进 cursor、不重复触发 robot action、不把 terminal ACK 写成 delivery success。
- 覆盖失败重跑：partial drain、stale artifact、unsupported schema、unsupported boundary、unsafe copy 和 credential leak 必须 fail closed。
- Preflight 消费 valid artifact 时新增 `cloud_worker_cutover_drain` check，但整体仍必须保持 `production_ready=false`。
- Docker smoke 覆盖 build/start、artifact generation、preflight consumption、status/command/ACK、cutover drain rerun。
- Artifact、preflight 和 summary 不得输出 DB URL、queue URL、credential-bearing URL、Authorization、bearer token、OSS AK/SK、root password、raw local path、serial/UART、WAVE ROVER、ROS topic 或 `/cmd_vel`。
- 新增代码技术注释必须使用中文，并解释为什么这是 Docker-only drain gate、为什么 terminal ACK 不代表 delivery success、为什么 artifact 必须脱敏。
- 同步 cloud docs 说明本轮是 `software_proof_docker_cloud_worker_cutover_drain_gate`，不是真实 production worker/migration 或 real external proof。

验收命令：

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py cloud-relay/src/ros2_trashbot_cloud_relay/remote_cloud_relay.py
cd cloud-relay && TRASHBOT_REMOTE_CLOUD_BEARER_TOKEN=dev-smoke-token bash scripts/docker_smoke.sh
rg -n "cloud_worker_cutover_drain|software_proof_docker_cloud_worker_cutover_drain_gate|trashbot.cloud_worker_cutover_drain|production_ready=false|delivery_success=false|primary_actions_enabled=false" cloud-relay/src/ros2_trashbot_cloud_relay/remote_cloud_relay.py onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py onboard/src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py cloud-relay/README.md cloud-relay/scripts/docker_smoke.sh .env.example docs/product/cloud_4g_infrastructure.md
git diff --check -- cloud-relay/src/ros2_trashbot_cloud_relay/remote_cloud_relay.py onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py onboard/src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py cloud-relay/README.md cloud-relay/scripts/docker_smoke.sh .env.example docs/product/cloud_4g_infrastructure.md
```

## 3. Task B - Robot Diagnostics Metadata Fence

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

- 证明 `cloud_worker_cutover_drain` summary 只能作为 metadata-only diagnostics 或 preflight summary 被消费。
- Summary 不得进入 robot command payload，不得触发 collect/dropoff/cancel/ACK action，不得推进或持久化 command cursor。
- Diagnostics 只暴露 safe summary、schema、boundary、drain status、cursor summary、terminal ACK summary、retry hint、not_proven、`production_ready=false`、`delivery_success=false`、`primary_actions_enabled=false`。
- 对 missing、unsupported schema、unsupported boundary、unsafe copy、credential leak、success wording、`production_ready=true`、`delivery_success=true`、`primary_actions_enabled=true` fail closed。
- 不改变 `trashbot.remote.v1` command/status/ACK envelope，不改变 Nav2、HIL、route/elevator、delivery result 或 phone action 语义。
- 新增代码技术注释必须使用中文，并解释 metadata-only 隔离和动作安全边界。
- 同步接口文档，说明 cutover drain summary 不属于 command payload、delivery result 或 ACK completion。

验收命令：

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_remote_bridge.py onboard/src/ros2_trashbot_behavior/test/test_remote_bridge_protocol.py onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_bridge.py onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_bridge_protocol.py onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py
rg -n "cloud_worker_cutover_drain|software_proof_docker_cloud_worker_cutover_drain_gate|metadata-only|production_ready=false|delivery_success=false|primary_actions_enabled=false" onboard/src/ros2_trashbot_behavior/test/test_remote_bridge.py onboard/src/ros2_trashbot_behavior/test/test_remote_bridge_protocol.py onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py docs/interfaces/ros_contracts.md
git diff --check -- onboard/src/ros2_trashbot_behavior/test/test_remote_bridge.py onboard/src/ros2_trashbot_behavior/test/test_remote_bridge_protocol.py onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_bridge.py onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_bridge_protocol.py onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py docs/interfaces/ros_contracts.md
```

## 4. Task C - Product Closeout

Owner：`product-okr-owner`

后续允许改动：

- `sprints/2026.05.17_08-09_cloud-worker-cutover-drain-gate/tech-done.md`
- `sprints/2026.05.17_08-09_cloud-worker-cutover-drain-gate/side2side_check.md`
- `sprints/2026.05.17_08-09_cloud-worker-cutover-drain-gate/final.md`
- `OKR.md`
- `docs/process/okr_progress_log.md`

要求：

- 汇总 Task A / Task B 的实际改动、验证结果、失败定位和剩余风险。
- 核对所有产物均保持 `software_proof_docker_cloud_worker_cutover_drain_gate`、`production_ready=false`、`delivery_success=false`、`primary_actions_enabled=false`。
- OKR 更新必须保守：Objective 5 只有在 cutover drain 真正落地且验证通过后才允许小幅说明软件功能前进；不得写成真实 external proof。
- 明确本轮不是真实 production worker/migration、真实 production DB/queue、真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、HIL、真实手机/browser、Nav2/fixed-route 或 delivery success。
- 确认 PR #4 的真实 elevator / field materials 和 PR #5 的真实 2D LiDAR / ToF 材料仍是独立缺口，没有被本轮替代。

验收命令：

```bash
rg -n "cloud_worker_cutover_drain|software_proof_docker_cloud_worker_cutover_drain_gate|Objective 5|Docker-only|production_ready=false|delivery_success=false|primary_actions_enabled=false|PR #5|PR #4|not real external proof" sprints/2026.05.17_08-09_cloud-worker-cutover-drain-gate OKR.md docs/process/okr_progress_log.md
git diff --check -- sprints/2026.05.17_08-09_cloud-worker-cutover-drain-gate/tech-done.md sprints/2026.05.17_08-09_cloud-worker-cutover-drain-gate/side2side_check.md sprints/2026.05.17_08-09_cloud-worker-cutover-drain-gate/final.md OKR.md docs/process/okr_progress_log.md
```

## 5. 接口影响

- Cloud relay 新增 `trashbot.cloud_worker_cutover_drain.v1` artifact 和 `trashbot.cloud_worker_cutover_drain_summary.v1` summary。
- Preflight 新增 `cloud_worker_cutover_drain` check；有效 artifact 也不能把整体状态改成 production ready。
- Robot bridge 只允许 metadata-only diagnostics consumption，不改变 command/status/ACK envelope。
- 手机主操作不在本轮修改；如后续显示 summary，必须只读且不启用 Start Delivery、Confirm Dropoff 或 Cancel。
- 文档实现阶段同步更新 `docs/product/cloud_4g_infrastructure.md`、`cloud-relay/README.md` 和 `docs/interfaces/ros_contracts.md`。

## 6. 并行执行规则

- Task A 与 Task B 文件范围互不重叠，下一阶段必须并行派发 `full-stack-software-engineer` 和 `robot-software-engineer`。
- Task A 主责 cloud relay cutover drain artifact / preflight / Docker smoke，Task B 主责 robot metadata isolation fence。
- Task C 只在 A/B 返回验证证据后执行 Product closeout。
- 本轮不派 `hardware-engineer` 写文件，因为 PR #5 真实硬件材料不可得且硬件 blocker 已多轮消费。
- 本轮不派 `autonomy-engineer` 写文件，因为 `06-07_route-task-field-retest-evidence-dispatch/final.md` 已要求没有真实现场材料时不要继续堆 O2/O3 wrapper。

## 7. OKR 最低优先级核对

1. 当前 `OKR.md` 4.1 节完成度最低的 Objective：Objective 5，约 67%。
2. 本 sprint 是否针对该最低 Objective：是，主目标为 Objective 5。
3. 为什么选 Objective 5：上一轮 `cloud_worker_migration_rehearsal` 已完成 Docker-only worker/migration rehearsal，但 final 明确不是真实 production worker/migration。本轮继续把该软件链路推进到 cutover / drain 这一步，属于 O5 cloud relay 的可执行功能前进，而不是单纯重复 blocked external proof。
4. 为什么不是 O5 external wrapper：真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、production worker/migration 和外部云材料当前不可得；本轮只做 local drain gate，并固定 `production_ready=false`。
5. 为什么不是 O2/O3 wrapper：`sprints/2026.05.17_06-07_route-task-field-retest-evidence-dispatch/final.md` 已明确没有真实现场材料时不要继续堆 route/elevator wrapper；继续做本地包装不能证明真实 Nav2/fixed-route、真实电梯或 delivery success。
6. 为什么不是 O1 wrapper：PR #5 硬件材料 blocker 已在多轮 hardware wrapper 中消费，仍缺真实 2D LiDAR / ToF SKU/source/receipt/procurement/installation/wiring/power/calibration/HIL-entry 和 field evidence；本机没有真实硬件，继续硬件 wrapper 不能产生 HIL 或真实传感器材料。
7. 为什么不是 O4 wrapper：Objective 4 已约 99%，且当前缺口是真实手机设备/browser、production app、真实 PWA prompt/user choice 和外部 O5 proof；本轮 cloud worker drain 不应包装成手机验收。
8. final.md 收口时必须复核：本轮是否仍保持 Docker-only、`software_proof_docker_cloud_worker_cutover_drain_gate`、`production_ready=false`、`delivery_success=false`、`primary_actions_enabled=false`，且没有把 drain 写成真实 production DB/queue、真实 worker、真实 migration 或 real external proof。

## 8. 本 planning 阶段验收命令

```bash
test -f sprints/2026.05.17_08-09_cloud-worker-cutover-drain-gate/pre_start.md && test -f sprints/2026.05.17_08-09_cloud-worker-cutover-drain-gate/prd.md && test -f sprints/2026.05.17_08-09_cloud-worker-cutover-drain-gate/tech-plan.md
rg -n "cloud_worker_cutover_drain|software_proof_docker_cloud_worker_cutover_drain_gate|Objective 5|Docker-only|production_ready=false|delivery_success=false|primary_actions_enabled=false|OKR 最低优先级核对|PR #5|PR #4" sprints/2026.05.17_08-09_cloud-worker-cutover-drain-gate
git diff --check -- sprints/2026.05.17_08-09_cloud-worker-cutover-drain-gate/pre_start.md sprints/2026.05.17_08-09_cloud-worker-cutover-drain-gate/prd.md sprints/2026.05.17_08-09_cloud-worker-cutover-drain-gate/tech-plan.md
```
