# Sprint 2026.05.13_12-13 Cloud DB/Queue External Probe Gate - Tech Plan

## OKR 最低优先级核对

当前 `OKR.md` 4.1 完成度最低的 Objective 是 Objective 5，约 63%。本 sprint 直接针对 Objective 5。Objective 1/2/3 仍需要真实硬件、真实路线或真实送达证据，本机只有 Docker；Objective 4 约 64%，略高于 Objective 5，且上一轮刚完成手机摘要。故本轮优先推进 O5。

## 分工和文件范围

### Task A - full-stack-software-engineer

允许改动：

- `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py`
- `onboard/src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py`
- `cloud-relay/README.md`
- `docs/product/remote_4g_mvp.md`
- `docs/product/cloud_4g_infrastructure.md`

目标：

- 新增 `trashbot.cloud_db_queue_external_probe_bundle` artifact 生成、校验、summary 和 CLI 写入参数。
- `production_preflight_payload()` 消费 artifact 或报告 missing warning；valid artifact 仍 blocked-by-design。
- 保持 artifact 与 preflight 输出 phone-safe，不输出 DB/queue URL、credential、token、本机路径、ROS 或硬件字段。

验收命令：

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py cloud-relay/src/ros2_trashbot_cloud_relay/remote_cloud_relay.py
git diff --check -- onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py onboard/src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py cloud-relay/README.md docs/product/remote_4g_mvp.md docs/product/cloud_4g_infrastructure.md
```

### Task B - robot-software-engineer

允许改动：

- `onboard/src/ros2_trashbot_behavior/test/test_remote_bridge.py`
- `onboard/src/ros2_trashbot_behavior/test/test_remote_bridge_protocol.py`
- `docs/interfaces/ros_contracts.md`

目标：

- 增加 `cloud_db_queue_external_probe` / `cloud_db_queue_external_probe_bundle` / `db_queue_external_probe` metadata-only response 兼容性围栏。
- 验证这些 metadata 不触发 backend action、不 POST ACK、不推进内存 cursor、不持久化 cursor_state_path，并从 command envelope normalization 中剥离。

验收命令：

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_remote_bridge.py onboard/src/ros2_trashbot_behavior/test/test_remote_bridge_protocol.py
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_bridge.py onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_bridge_protocol.py
git diff --check -- onboard/src/ros2_trashbot_behavior/test/test_remote_bridge.py onboard/src/ros2_trashbot_behavior/test/test_remote_bridge_protocol.py docs/interfaces/ros_contracts.md
```

### Task C - product-okr-owner

允许改动：

- `sprints/2026.05.13_12-13_cloud-db-queue-external-probe-gate/tech-done.md`
- `sprints/2026.05.13_12-13_cloud-db-queue-external-probe-gate/side2side_check.md`
- `sprints/2026.05.13_12-13_cloud-db-queue-external-probe-gate/final.md`
- `OKR.md`
- `docs/process/okr_progress_log.md`

目标：

- 汇总 Task A/B 证据，更新 sprint closeout。
- 若 A/B 均完成，将 Objective 5 保守上调；若只完成局部，则保持或小幅调整并写明边界。

验收命令：

```bash
test -f OKR.md && test -f docs/process/okr_progress_log.md && test -f docs/product/remote_4g_mvp.md && test -f docs/interfaces/ros_contracts.md
git diff --check -- OKR.md docs/process/okr_progress_log.md sprints/2026.05.13_12-13_cloud-db-queue-external-probe-gate
```

## 接口影响

新增字段只属于 phone-safe readiness/deployment metadata，不改变 `trashbot.remote.v1` command/status/ACK envelope。旧客户端可以忽略这些字段。

## 风险边界

- Docker-only validation 不代表真实 production DB/queue。
- Valid artifact 只证明 schema、checksum、redaction 和 preflight consumption。
- ACK 不代表送达成功。
