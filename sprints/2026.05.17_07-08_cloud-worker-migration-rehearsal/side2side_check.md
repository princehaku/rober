# Sprint 2026.05.17_07-08 Cloud Worker Migration Rehearsal - Side2Side Check

sprint_type: epic

## 1. PRD 对照

| PRD 项 | 验收结果 | 证据 |
| --- | --- | --- |
| 生成 `trashbot.cloud_worker_migration_rehearsal.v1` artifact | 通过 | Task A 新增 artifact writer、CLI/env 和 Docker smoke artifact generation。 |
| 生成 `trashbot.cloud_worker_migration_rehearsal_summary.v1` summary | 通过 | Task A/Task B 均消费 safe summary；Robot diagnostics metadata-only 展示。 |
| 固定 `software_proof_docker_cloud_worker_migration_rehearsal_gate` | 通过 | Task A artifact/preflight/docs 和 Task B diagnostics fence 均保留该 boundary。 |
| Valid artifact 也保持 blocked-by-design production 状态 | 通过 | `production_ready=false`、`delivery_success=false`、`primary_actions_enabled=false` 均被验证和文档化。 |
| Robot compatibility fence 不触发动作 | 通过 | Task B 证明 metadata 不进入 command payload，不触发 collect/dropoff/cancel/ACK，不推进 cursor。 |
| Docker smoke 消费 rehearsal artifact | 通过 | `cd cloud-relay && TRASHBOT_REMOTE_CLOUD_BEARER_TOKEN=dev-smoke-token bash scripts/docker_smoke.sh` passed。 |
| 文档同步 | 通过 | Task A 更新 `docs/product/cloud_4g_infrastructure.md` 与 `cloud-relay/README.md`；Task B 更新 `docs/interfaces/ros_contracts.md`。 |

## 2. Must Have / Won't Have 核对

Must Have 均已完成为 Docker-only software proof：

- 本地 migration rehearsal 可执行。
- 本地 queue worker rehearsal 可执行。
- Artifact 与 summary 可被 preflight / diagnostics 消费。
- Artifact boundary 为 `software_proof_docker_cloud_worker_migration_rehearsal_gate`。
- Valid artifact 不能把系统提升为 production ready。

Won't Have 均未被误写为完成：

- 不是真实公网 HTTPS/TLS。
- 不是真实 4G/SIM。
- 不是 OSS/CDN live traffic。
- 不是 production DB/queue connectivity。
- 不是真实 production worker 或 production migration。
- 不是多实例一致性、生产 transaction isolation、HIL、Nav2/fixed-route、真实手机/browser 或 delivery success。

## 3. 产品验收结论

本轮用户价值成立：Objective 5 不再只是列举 production DB/queue 缺口，而是有一个 Docker/local SQLite relay 的 worker/migration rehearsal gate。它能为后续真实 DB/queue 接入提供 schema、artifact、preflight 消费、worker invariant 和 Robot action-isolation 口径。

验收边界也成立：这是 `Docker-only` 的 `software_proof_docker_cloud_worker_migration_rehearsal_gate`，not real external proof。`production_ready=false`、`delivery_success=false`、`primary_actions_enabled=false` 必须继续作为后续外部 proof 前的默认状态。

PR #5 的硬件 2D LiDAR / ToF / source / material gap 仍独立存在，不因本轮 Objective 5 云 rehearsal 被关闭。

## 4. 剩余证据链

- Objective 5 仍需要真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue connectivity、真实 worker/migration、生产 queue ordering、transaction isolation、backup/recovery 和多实例材料。
- Objective 1 仍需要真实 WAVE ROVER、UART、HIL、2D LiDAR / ToF SKU/source/receipt/procurement/installation/wiring/power/calibration/HIL-entry。
- Objective 2/3 仍需要真实 Nav2/fixed-route、route completion signal、task record、dropoff/cancel completion、真实电梯材料和 delivery result。
- Objective 4 仍需要真实 iPhone/Android browser、production app 或 PWA prompt/user choice 现场验收。
