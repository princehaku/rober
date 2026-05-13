# Sprint 2026.05.13_10-11 Cloud DB/Queue Config Gate - Tech Plan

## OKR 最低优先级核对

1. 当前 `OKR.md` 4.1 完成度最低的 Objective 是 Objective 5：云中转 + OSS/CDN 数据通路产品化，约 61%。
2. 本 sprint 针对该最低 Objective。
3. 不选择 O1/O2/O3 的原因：本机没有真实硬件，且这些 Objective 的主要缺口依赖 WAVE ROVER、真实串口、Nav2/fixed-route 或真实送达证据；继续消费会重复硬件 blocker。Objective 4 约 62%，高于 Objective 5。

## 技术方案

新增 cloud DB/queue config gate，复用已有 cloud deployment / public ingress gate 模式：

- Schema：`trashbot.cloud_db_queue_config_gate`，`schema_version=1`。
- Evidence boundary：`software_proof_docker_cloud_db_queue_config_gate`。
- 状态：
  - `missing_cloud_db_queue_config`：DB/queue 配置包缺失；
  - `cloud_db_queue_config_present_not_externally_proven`：配置形态存在，但真实 DB/queue、多实例、备份、灾备和云端外部实证仍缺。
- Artifact 只保存枚举化配置状态和 phone-safe 缺口，不保存 DB URL、queue URL、credential-bearing URL、token、Authorization、root password、本地 state path、串口、WAVE ROVER 参数、ROS topic 或 `/cmd_vel`。
- Preflight 新增 `cloud_db_queue_config` check。有效 artifact 仍保持 `production_ready=false`、`overall_status=blocked`，并将该 gate 作为 O5 readiness 证据之一。

## 文件范围

### Task A - Full-Stack Engineer

允许改动：

- `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py`
- `onboard/src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py`
- `cloud-relay/scripts/docker_smoke.sh`
- `cloud-relay/README.md`
- `docs/product/cloud_4g_infrastructure.md`
- `docs/product/remote_4g_mvp.md`

接口边界：

- 不改变 `trashbot.remote.v1` command/status/ACK envelope。
- 新增字段只能作为 cloud readiness / phone-safe support metadata。
- 所有真实生产项保持 `production_ready=false`。

验收命令：

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py cloud-relay/src/ros2_trashbot_cloud_relay/remote_cloud_relay.py
cd cloud-relay && TRASHBOT_REMOTE_CLOUD_BEARER_TOKEN=dev-smoke-token bash scripts/docker_smoke.sh
git diff --check -- onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py onboard/src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py cloud-relay/scripts/docker_smoke.sh cloud-relay/README.md docs/product/cloud_4g_infrastructure.md docs/product/remote_4g_mvp.md
```

### Task B - Robot Platform Engineer

允许改动：

- `onboard/src/ros2_trashbot_behavior/test/test_remote_bridge.py`
- `onboard/src/ros2_trashbot_behavior/test/test_remote_bridge_protocol.py`
- `docs/interfaces/ros_contracts.md`

接口边界：

- 证明 `cloud_db_queue_config`、`cloud_db_queue_config_gate`、`db_queue_config` 等 metadata-only response 不触发 backend action、不 POST ACK、不推进或持久化 cursor。
- 证明 command envelope 外 DB/queue config metadata 被剥离，不进入 robot command payload。
- 不改 runtime，除非测试证明现有 runtime 会误消费 metadata；若必须改 runtime，先在输出中说明原因。

验收命令：

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_remote_bridge.py onboard/src/ros2_trashbot_behavior/test/test_remote_bridge_protocol.py
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_bridge.py onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_bridge_protocol.py
git diff --check -- onboard/src/ros2_trashbot_behavior/test/test_remote_bridge.py onboard/src/ros2_trashbot_behavior/test/test_remote_bridge_protocol.py docs/interfaces/ros_contracts.md
```

### Task C - Product Manager / OKR Owner

允许改动：

- `OKR.md`
- `docs/process/okr_progress_log.md`
- `sprints/2026.05.13_10-11_cloud-db-queue-config-gate/tech-done.md`
- `sprints/2026.05.13_10-11_cloud-db-queue-config-gate/side2side_check.md`
- `sprints/2026.05.13_10-11_cloud-db-queue-config-gate/final.md`

验收命令：

```bash
test -f docs/product/cloud_4g_infrastructure.md && test -f docs/product/remote_4g_mvp.md && test -f docs/interfaces/ros_contracts.md
git diff --check -- OKR.md docs/process/okr_progress_log.md sprints/2026.05.13_10-11_cloud-db-queue-config-gate/tech-done.md sprints/2026.05.13_10-11_cloud-db-queue-config-gate/side2side_check.md sprints/2026.05.13_10-11_cloud-db-queue-config-gate/final.md
```

## 风险边界

- Docker/local gate 不能证明真实 DB/queue、生产 queue ordering、真实 transaction isolation、多实例一致性、真实备份/灾备或云端上线许可。
- ACK 仍只是 accepted/processing evidence，不是 delivery success。
- 若 Docker smoke 因本机 Docker daemon 不可用失败，需要记录为环境阻塞，不得声明 smoke 通过。
