# Sprint 2026.05.13_12-13 Cloud DB/Queue External Probe Gate - Tech Done

## sprint_type

sprint_type: epic

## 用户价值和产品北极星

本轮把 production DB/queue 的"外部探测仍未完成"变成可审计、可被 preflight 消费、可被手机/云端安全解释的 readiness gate。用户价值不是宣称真实云 DB/queue 已可用，而是避免普通手机用户、售后和部署同学把"配置形态存在"误读成"生产链路已经闭环"。

产品北极星保持不变：普通手机用户通过云中转控制和诊断小车，但每一层证据都要可区分。本轮证据边界严格是 `software_proof_docker_cloud_db_queue_external_probe_gate`，不是真实 DB/queue、真实云、4G、手机、OSS/CDN live traffic、HIL 或真实送达。

## OKR 映射和 KR 拆解

- Objective 5 KR1：`trashbot.remote.v1` command/status/ack envelope 保持不变，DB/queue external probe 只作为 readiness metadata。
- Objective 5 KR2：补齐 production DB/queue external probe bundle 的上线前检查入口，服务端 preflight 可消费。
- Objective 5 KR5：artifact、preflight 和 compatibility fence 均保持 phone-safe redaction，不输出 DB/queue URL、credential-bearing endpoint、Authorization、bearer token、root password、本机路径、ROS topic、`/cmd_vel` 或硬件字段。
- Objective 5 KR6：DB/queue 外部探测未完成时继续 fail closed，`production_ready=false`、`overall_status=blocked`、`external_probe_complete=false`。

## 本轮核心抓手

本轮完成 `trashbot.cloud_db_queue_external_probe_bundle` schema v1，并把它接入 remote cloud relay preflight 与 robot metadata-only compatibility fence。该抓手把下一阶段真实 production DB/queue 外部探测的入口固定下来，同时保留 Docker-only blocked-by-design 语义。

## 实际改动汇总

Task A - `full-stack-software-engineer`：

- 新增 `trashbot.cloud_db_queue_external_probe_bundle` schema v1。
- 新增 `--write-cloud-db-queue-external-probe-artifact`、`--cloud-db-queue-external-probe-artifact`、`TRASHBOT_REMOTE_CLOUD_DB_QUEUE_EXTERNAL_PROBE_ARTIFACT` preflight consumption。
- valid artifact 仍保持 `production_ready=false`、`overall_status=blocked`、`external_probe_complete=false`。
- 同步 cloud relay 和产品文档，证据边界为 `software_proof_docker_cloud_db_queue_external_probe_gate`。

Task B - `robot-software-engineer`：

- 增加 `cloud_db_queue_external_probe` / `cloud_db_queue_external_probe_bundle` / `db_queue_external_probe` metadata-only compatibility fence。
- 验证 metadata-only response 不触发 backend action、不 POST ACK、不推进内存 cursor、不持久化 cursor。
- 验证 protocol normalization 剥离 command envelope 外的 DB/queue external probe metadata。

Task C - `product-okr-owner`：

- 更新本 sprint `tech-done.md`、`side2side_check.md`、`final.md`。
- 更新 `OKR.md` 当前快照和 `docs/process/okr_progress_log.md`。
- 将 Objective 5 从约 63% 保守上调到约 65%，仅基于 Docker/local software proof，不上调 Objective 1/2/3/4。

## 验证结果

Task A 验证结果：

```text
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py
Ran 62 tests ... OK

PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py cloud-relay/src/ros2_trashbot_cloud_relay/remote_cloud_relay.py
exit 0

git diff --check -- onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py onboard/src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py cloud-relay/README.md docs/product/remote_4g_mvp.md docs/product/cloud_4g_infrastructure.md
exit 0

extra CLI smoke: artifact write and preflight consumption passed; preflight evidence_boundary=software_proof_docker_cloud_db_queue_external_probe_gate
```

Task B 验证结果：

```text
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_remote_bridge.py onboard/src/ros2_trashbot_behavior/test/test_remote_bridge_protocol.py
Ran 83 tests in 42.262s OK

PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_bridge.py onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_bridge_protocol.py
exit 0

git diff --check -- onboard/src/ros2_trashbot_behavior/test/test_remote_bridge.py onboard/src/ros2_trashbot_behavior/test/test_remote_bridge_protocol.py docs/interfaces/ros_contracts.md
exit 0
```

Task C 验收结果：

```text
test -f OKR.md && test -f docs/process/okr_progress_log.md && test -f docs/product/remote_4g_mvp.md && test -f docs/interfaces/ros_contracts.md
exit 0

git diff --check -- OKR.md docs/process/okr_progress_log.md sprints/2026.05.13_12-13_cloud-db-queue-external-probe-gate
exit 0
```

## 偏差和失败定位

未发现需要转交 Engineer 重试的失败。Task A/B 均完成计划内验证；Task C 当前只做 sprint closeout 和 OKR/progress log 收口，不修改产品代码、测试代码或硬件配置。

## 剩余风险

- 没有真实 production DB/queue connectivity、migration、worker、多实例一致性、queue ordering、transaction isolation、backup/recovery 外部证明。
- 没有真实 HTTPS/TLS、公网入口、真实云、真实 4G/SIM、OSS/CDN live traffic。
- 没有真实手机设备/browser、Nav2/fixed-route、WAVE ROVER、HIL 或真实送达。
- ACK 仍只是 accepted/processing evidence，不是 delivery success。
