# Sprint 2026.05.13_06-07 Cloud External Probe Bundle Gate - Side2Side Check

## 验收结论

- Product side2side 结论：通过。
- 通过范围：`software_proof_docker_cloud_external_probe_bundle_gate` 的 Docker/local external probe bundle gate。
- 不通过或未覆盖范围：真实云、真实 HTTPS/TLS、公网入口、4G/SIM、OSS/CDN live traffic、production DB/queue、HIL、Nav2/fixed-route、WAVE ROVER、真实送达。

## PRD 对照

| PRD 要求 | 工程证据 | Product 验收 |
| --- | --- | --- |
| 固化 `trashbot.cloud_external_probe_bundle` schema_version=1 | Artifact 片段包含 `schema=trashbot.cloud_external_probe_bundle`、`schema_version=1` | 通过 |
| 覆盖 `/healthz`、`/readyz`、`/preflightz` | Docker smoke 输出 `probe covered /healthz`、`/readyz`、`/preflightz` | 通过 |
| 保持 `evidence_boundary=software_proof_docker_cloud_external_probe_bundle_gate` | Artifact 和 smoke 均输出该 boundary | 通过 |
| 保持 `production_ready=false` 和 blocked-by-design | Artifact 输出 `production_ready=false`、`overall_status=blocked`；`/preflightz` 503 被归为 pass | 通过 |
| 敏感信息不得泄漏 | Docker smoke 包含 redaction checks；文档声明不保存 base URL、header、token、响应体或本地路径 | 通过 |
| preflight 可消费 bundle 且不升级为 production ready | Full-stack validation 覆盖 preflight consumption，仍保持 `production_ready=false` | 通过 |
| Robot metadata-only response 不触发副作用 | Robot tests 证明无 backend action、无 ACK、无内存 cursor 推进、无持久化 cursor | 通过 |
| ACK 不代表 delivery success | `docs/interfaces/ros_contracts.md` 已同步 ACK 和 metadata 边界 | 通过 |

## 用户价值核对

本轮把未来真实公网 URL 上线前的健康检查，从临时 curl 和人工判断，收敛为可审计、可被 preflight 消费、可被 Product/Full-stack/Robot 三方共用的 artifact。普通手机用户不会直接看到 raw probe、token、traceback、ROS topic 或串口细节；产品侧可以把状态解释为“云部署检查仍阻塞，本地 fallback 仍是当前边界”。

## OKR 映射核对

- Objective 5 KR1：commands/status/ack 最小契约没有被破坏，external probe 只补充 HTTP endpoint contract 和 deployment metadata。
- Objective 5 KR2：部署基线继续公开真实云、公网入口、HTTPS/TLS、production DB/queue、OSS/CDN、4G/SIM 等缺口。
- Objective 5 KR5：凭证和敏感信息保持环境变量/占位值边界，artifact 和 summary 不承载真实 secret。
- Objective 5 KR6：probe bundle 让部署/网络问题与机器人问题分层；Robot fence 证明 metadata 不触发机器人动作。

## 非证明项

本轮不得声明：

- 真实云、真实 HTTPS/TLS、公网入口、公网 DNS、生产可用。
- 真实 4G/SIM、真实手机设备、production app、真实 PWA install prompt。
- OSS/CDN live traffic、production DB/queue、多实例一致性、production disaster recovery。
- Nav2/fixed-route、WAVE ROVER、HIL、真实送达或任务成功。

## 收口判断

可以将 Objective 5 从约 57% 保守上调到约 59%。理由是 external probe bundle 补齐了真实部署前的 endpoint artifact 与 robot side-effect fence，但仍停留在 Docker/local software proof，因此只做小幅进度调整，不影响 Objective 1/2/3/4。
