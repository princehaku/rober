# Sprint 2026.05.13_12-13 Cloud DB/Queue External Probe Gate - PRD

## 用户价值和产品北极星

普通手机用户和售后同学需要知道“云 DB/queue 为什么还不能上线”，而不是看到配置包存在就误以为生产通路已可用。本轮把 DB/queue 外部探测做成可审计的 phone-safe bundle：未来接入真实云时能复用同一入口；当前 Docker-only 环境下继续明确 blocked。

产品北极星仍是普通手机用户能用云中转控制和诊断小车，但每一步必须区分 local proof、外部生产 proof、机器人动作 proof 和真实送达 proof。

## OKR 映射

- Objective 5 KR1：云中转服务端契约继续保持 commands/status/ack envelope 不变，external probe 只作为 readiness metadata。
- Objective 5 KR2：补齐云端 DB/queue external probe 的上线前检查入口，服务端基线文档同步。
- Objective 5 KR5：credential redaction 和 `.env` 边界继续保持，不泄漏 DB/queue 凭证。
- Objective 5 KR6：DB/queue 不可达、未证明或 artifact 缺失时给出 graceful degradation 和恢复建议。

## 本轮核心抓手

新增 `trashbot.cloud_db_queue_external_probe_bundle` schema_version=1：

- 描述 DB connectivity、queue connectivity、migration check、worker check、multi-instance consistency、ordering、transaction isolation、backup/recovery 的外部探测状态。
- 本轮 Docker-only 默认状态是 `not_run` / `not_externally_proven`，不能假装真实连接。
- Preflight 能消费该 artifact，生成 phone-safe blocked check。
- Robot bridge 证明这些 metadata 不触发 backend action、不 POST ACK、不推进或持久化 cursor。

## 验收口径

- 生成 valid external-probe bundle artifact 后，preflight 出现 `cloud_db_queue_external_probe_bundle` check，`production_ready=false`，`overall_status=blocked`，evidence boundary 为 `software_proof_docker_cloud_db_queue_external_probe_gate`。
- 缺失、invalid、hostile artifact 必须 fail closed，且不泄漏敏感字段。
- Remote bridge/protocol 对 `cloud_db_queue_external_probe` / `cloud_db_queue_external_probe_bundle` / `db_queue_external_probe` metadata-only response 兼容，不触发动作和 ACK。
- 文档同步到 `docs/product/remote_4g_mvp.md`、`docs/product/cloud_4g_infrastructure.md`、`docs/interfaces/ros_contracts.md`。

## 非目标

- 不连接真实 production DB/queue。
- 不证明真实 HTTPS/TLS、公网入口、真实云、4G/SIM、OSS/CDN live traffic。
- 不证明 Nav2/fixed-route、WAVE ROVER、HIL 或真实送达。
