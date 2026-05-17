# 4G Cloud Infrastructure Boundary

## 目标

O6 的真实产品目标是让手机通过云端 API 控制小车，小车通过 4G 主动 outbound polling 云端控制面。云端只承载轻量 JSON command/status/ack，不承载图片大对象，不暴露底层机器人控制入口，也不要求手机和小车处于同一 WiFi。

`2026.05.12_06-07_remote-cloud-entry-docker-deploy` 将 independent relay 从 local Python proof 推进到 `software_proof_docker_deploy`：`remote_cloud_relay.py` 可通过专用 Dockerfile 和 compose service 启动，使用 env 注入 host/port/state path/bearer token，并提供 `/healthz` 与 `/readyz`。

本轮 `2026.05.12_07-08_remote-cloud-production-preflight` 在同一 relay 上新增 production preflight gate，证据边界是 `software_proof_docker_preflight_gate`。Gate 只做 Docker/local 可执行的上线前配置检查：凭证注入、HTTPS/公网入口、OSS/CDN、state store 和 phone-safe 输出。它会把本地 HTTP、缺真实 TLS、缺公网入口、OSS/CDN 占位、file-backed store 和生产 DB/队列缺失标成 blocked 或 warning，不等于真实云、真实 4G、OSS/CDN 实流量、Nav2/fixed-route、WAVE ROVER 或 HIL。

本轮 `2026.05.12_08-09_remote-cloud-sqlite-state-proof` 在 independent relay 内新增 SQLite-backed state store proof，证据边界是 `software_proof_docker_sqlite_state_store`。SQLite backend 只证明单机 Docker/local 环境中 command/status/ack 可跨 store reopen 或 relay restart 恢复；它仍不是生产 DB/queue、多实例一致性、备份恢复、灾备、真实云、真实 4G、OSS/CDN 或 HIL 证据。

本轮 `2026.05.12_09-10_remote-cloud-backup-restore-drill` 在 SQLite proof store 上增加 Docker/local backup/restore drill，证据边界是 `software_proof_docker_backup_restore_drill`。该 drill 会从已填充的 SQLite state 生成 JSON backup artifact，校验 schema/version/checksum 后恢复到新的 SQLite state，并验证恢复后的 command/status/ack envelope shape 与 ACK cursor 保守语义。它只证明单实例本地软件演练，不等于生产备份策略、生产 DB/queue、多实例一致性、真实灾备、真实云或真实 4G。

本轮 `2026.05.12_11-12_remote-cloud-oss-cdn-manifest-proof` 在同一 relay/preflight 体系上新增 OSS/CDN manifest proof，证据边界是 `software_proof_docker_oss_cdn_manifest`。Manifest artifact 会固定 bucket、region、`rober/<robot_id>/<date>/<task_id>/` 前缀、CDN URL 组合规则、对象引用、checksum 和 `not_proven` 缺口；preflight 可通过 `TRASHBOT_REMOTE_CLOUD_OSS_CDN_MANIFEST_ARTIFACT` 或 CLI 参数消费该 artifact。它只证明 Docker/local 对象引用 shape、schema/version、prefix/CDN URL 和 checksum 可校验，不等于真实 OSS upload、STS issuance、CDN origin fetch、lifecycle policy、production account、真实云、真实 4G/SIM、HTTPS/TLS 公网入口、生产 DB/queue、Nav2/fixed-route、WAVE ROVER 或 HIL。

本轮 `2026.05.12_12-13_remote-oss-cdn-phone-consumption-gate` 将上一轮 manifest artifact proof 接入本地 operator/API 消费面，新增 `software_proof_docker_phone_manifest_consumption` 边界。`/api/status.phone_readiness.oss_cdn_manifest` 和 `/api/diagnostics.oss_cdn_manifest` 共用同一 phone-safe summary helper，覆盖 `ready`、`missing`、`invalid`、`stale`，只显示普通用户文案和 retry hint，不返回 full artifact、object key、checksum、本地路径或任何凭证。`ready` 仍只表示手机/API 能消费对象引用摘要，不等于真实 OSS 上传、CDN 回源、真实云、真实 4G、送达成功或 HIL。

本轮 `2026.05.12_14-15_remote-network-recovery-drill` 在 independent relay 上新增 Docker/local network recovery drill，证据边界是 `software_proof_docker_network_recovery_drill`。该 drill 会构造本地等价连接失败、验证 ACK post failure 不等于 delivery success、恢复后 command/status/ack envelope 可重新对账，并把 status stale 输出成 phone-safe blocked/warning 摘要。产物可被 `--preflight`、`/api/status.phone_readiness.network_recovery` 和 `/api/diagnostics.network_recovery_drill` 消费；missing、invalid、stale、failed 都不能显示绿色 ready，passed 也只能表示 software proof ready。它仍不是真实云、真实 4G/SIM、HTTPS/TLS 公网、生产 incident recovery、真实送达、Nav2/fixed-route、WAVE ROVER 或 HIL 证据。

本轮 `2026.05.12_16-17_remote-credential-rotation-gate` 在同一 relay/preflight/phone-safe 摘要体系上新增 credential rotation artifact gate，证据边界是 `software_proof_docker_credential_rotation_gate`。Artifact 只记录 schema/version、Docker/local bearer rotate gate 状态、OSS 凭证模式边界、STS/account/provisioning/audit-log 缺口、`not_proven`、safe summary、retry hint 和 checksum；preflight 消费后新增 `credential_rotation` check，`/api/status.phone_readiness.credential_rotation` 和 `/api/diagnostics.credential_rotation` 只输出摘要，不返回完整 artifact、checksum、路径、token、Authorization、OSS secret、AK/SK、root password、串口、baudrate、WAVE ROVER、ROS topic 或 `/cmd_vel`。该 gate 仍不是生产 token rotate、真实 STS issuance、真实 OSS upload、CDN origin fetch、生产账号 provisioning、真实审计日志、真实云、真实 4G/SIM、Nav2/fixed-route、WAVE ROVER、HIL 或真实送达证据。

本轮 `2026.05.12_17-18_remote-provisioning-audit-gate` 在同一 relay/preflight/phone-safe 摘要体系上新增 provisioning audit artifact gate，证据边界是 `software_proof_docker_provisioning_audit_gate`。Artifact 覆盖 robot provisioning、STS issuance boundary、audit log contract 三类上线前阻断项，但只证明 Docker/local schema、checksum、phone-safe 摘要和 `not_proven` 缺口可被 preflight、`/api/status.phone_readiness.provisioning_audit`、`/api/diagnostics.provisioning_audit` 消费。它必须保持 `production_ready=false`、`overall_status=blocked`，不得声明真实云、真实 4G/SIM、真实 STS issuance、真实 audit log、真实 OSS upload、production-ready、Nav2/fixed-route、WAVE ROVER、HIL 或真实送达。

本轮 `2026.05.12_21-22_remote-queue-ordering-drill` 在同一 relay/preflight/phone-safe 摘要体系上新增 queue ordering drill artifact gate，证据边界是 `software_proof_docker_queue_ordering_drill`。Artifact 覆盖 Docker/local 并发提交、相邻 command id、`cmd-9`/`cmd-10` 数字顺序、cursor 只在 terminal ACK 后推进、ACK 不等于 delivery success 等 invariant；preflight 可通过 `TRASHBOT_REMOTE_CLOUD_QUEUE_ORDERING_DRILL_ARTIFACT` 或 CLI 参数消费，`/api/status.phone_readiness.queue_ordering_drill` 和 `/api/diagnostics.queue_ordering_drill` 只输出 phone-safe summary。它必须保持 `production_ready=false`，不得声明真实生产 queue ordering、生产 DB/queue、多实例一致性、transaction isolation、真实云、真实 4G/SIM、Nav2/fixed-route、WAVE ROVER、HIL 或真实送达。

本轮 `2026.05.12_23-24_remote-transaction-isolation-gate` 在同一 relay/preflight/phone-safe 摘要体系上新增 transaction isolation drill artifact gate，证据边界是 `software_proof_docker_transaction_isolation_gate`。Artifact 构造同一 robot 的 interleaved command/status/ACK 场景：command A 仍是 non-terminal，command B 后发并出现 terminal ACK，status update 与 ACK 交错写入；有效 proof 要求 ACK cursor 不得越过未完成 command A，且 terminal ACK 不得升级为 delivery success。Preflight 可通过 `TRASHBOT_REMOTE_CLOUD_TRANSACTION_ISOLATION_ARTIFACT` 或 `--transaction-isolation-artifact` 消费，`/api/status.phone_readiness.transaction_isolation` 和 `/api/diagnostics.transaction_isolation` 只输出 phone-safe summary。它必须保持 `production_ready=false`，不得声明真实生产 DB/queue、多实例一致性、真实生产 transaction isolation、真实云、真实 4G/SIM、Nav2/fixed-route、WAVE ROVER、HIL 或真实送达。

本轮 `2026.05.12_25-26_remote-production-recovery-gate` 在同一 relay/preflight/phone-safe 摘要体系上新增 production recovery artifact gate，证据边界是 `software_proof_docker_production_recovery_gate`。Artifact 覆盖 Docker/local backup/restore 输入、schema/checksum/invariant 校验、生产备份策略、灾备恢复、DB/queue、多实例、保留周期和 RPO/RTO 的上线前缺口；preflight 可通过 `TRASHBOT_REMOTE_CLOUD_PRODUCTION_RECOVERY_ARTIFACT` 或 `--production-recovery-artifact` 消费，`/api/status.phone_readiness.production_recovery` 和 `/api/diagnostics.production_recovery` 只输出 phone-safe summary。它必须保持 `production_ready=false` 和 `overall_status=blocked`，不得声明真实生产 DB/queue、真实生产备份/灾备、多实例一致性、真实云、真实 4G/SIM、OSS/CDN 实流量、Nav2/fixed-route、WAVE ROVER、HIL 或真实送达。

本轮 `2026.05.13_04-05_cloud-deployment-readiness-gate` 新增 cloud deployment readiness gate，证据边界是 `software_proof_docker_cloud_deployment_readiness_gate`。Artifact schema 为 `trashbot.cloud_deployment_readiness`、`schema_version=1`，检查公网 base URL/TLS/public ingress、healthcheck endpoint、bearer credential 占位、state backend、production DB/queue gap、OSS/CDN gap、4G/SIM gap、deployment runbook 或 Docker smoke 入口。该 gate 是 blocked-by-design：`production_ready=false`、`overall_status=blocked`、`not_proven`、`safe_summary` 和 `retry_hint` 必须保留；它不得声明真实云、真实 HTTPS/TLS、公网入口、真实 4G/SIM、OSS/CDN 实流量、生产 DB/queue、HIL 或真实送达。

本轮 `2026.05.13_06-07_cloud-external-probe-bundle-gate` 新增 cloud external probe bundle gate，证据边界是 `software_proof_docker_cloud_external_probe_bundle_gate`。Artifact schema 为 `trashbot.cloud_external_probe_bundle`、`schema_version=1`，用本地或未来公网 base URL 探测 `/healthz`、`/readyz`、`/preflightz`，但 artifact 只保存 endpoint path、HTTP status、JSON 合同状态、`redaction_status`、`safe_summary`、`retry_hint` 和 `not_proven`，不保存 base URL、header、token、响应体或本地路径。本轮 Docker smoke 只证明本地 relay probe contract 和 artifact 校验，preflight 即使消费有效 bundle，也必须保持 `production_ready=false`、`overall_status=blocked`；它不得声明真实云、真实 HTTPS/TLS、公网入口、真实 4G/SIM、OSS/CDN live traffic、production DB/queue、HIL 或真实送达。

本轮 `2026.05.13_08-09_cloud-public-ingress-tls-gate` 新增 cloud public ingress/TLS/reverse-proxy 配置 gate，证据边界是 `software_proof_docker_cloud_public_ingress_tls_gate`。Artifact schema 为 `trashbot.cloud_public_ingress_tls_gate`、`schema_version=1`，只保存枚举化配置状态和缺口摘要，用来区分 `missing_public_ingress_tls_config` 与 `public_ingress_tls_config_present_not_externally_proven`。前者表示公网入口/TLS/反向代理配置包仍缺失；后者表示配置包形态存在，但没有真实外部 HTTPS/TLS、公网入口、DNS、反向代理转发或防火墙实证。两种状态都必须保持 `production_ready=false`、`overall_status=blocked`；artifact、preflight 和 phone-safe summary 不得输出真实 URL、credential-bearing URL、Authorization header、bearer token、TLS private key、证书私钥路径、root password、OSS AK/SK、DB/queue URL、本地 state path、串口、WAVE ROVER 参数、ROS topic 或 `/cmd_vel`。

本轮 `2026.05.13_10-11_cloud-db-queue-config-gate` 新增 cloud DB/queue 配置 gate，证据边界是 `software_proof_docker_cloud_db_queue_config_gate`。Artifact schema 为 `trashbot.cloud_db_queue_config_gate`、`schema_version=1`，只保存枚举化配置状态和缺口摘要，用来区分 `missing_cloud_db_queue_config` 与 `cloud_db_queue_config_present_not_externally_proven`。前者表示生产 DB/queue 配置包仍缺失；后者表示配置包形态存在，但没有真实连接探测、多实例一致性、生产队列顺序、事务隔离、备份策略或灾备实证。两种状态都必须保持 `production_ready=false`、`overall_status=blocked`；artifact 和 preflight 不得输出 DB/queue endpoint、credential-bearing endpoint、Authorization header、bearer token、token、root password、本地 state path、串口、WAVE ROVER 参数、ROS topic 或 `/cmd_vel`。

本轮 `2026.05.13_12-13_cloud-db-queue-external-probe-gate` 新增 cloud DB/queue external probe bundle gate，证据边界是 `software_proof_docker_cloud_db_queue_external_probe_gate`。Artifact schema 为 `trashbot.cloud_db_queue_external_probe_bundle`、`schema_version=1`，只保存 DB connectivity、queue connectivity、migration check、worker check、multi-instance consistency、ordering、transaction isolation、backup/recovery 的枚举化外部探测入口状态、`redaction_status`、`safe_summary`、`retry_hint` 和 `not_proven`。当前本机只有 Docker，没有真实云、真实 DB/queue 或凭证，因此有效 artifact 也必须保持 `production_ready=false`、`overall_status=blocked`、`external_probe_complete=false`；preflight 只能说明 schema、checksum、redaction 和 consumption 可验证，不得声明真实 production DB/queue、真实队列顺序、真实事务隔离、生产备份/灾备、多实例一致性、真实云、真实 4G/SIM、OSS/CDN 实流量、Nav2/fixed-route、WAVE ROVER、HIL 或真实送达。

本轮 `2026.05.13_14-15_oss-cdn-live-probe-gate` 新增 OSS/CDN live probe gate，证据边界是 `software_proof_docker_oss_cdn_live_probe_gate`。Artifact schema 为 `trashbot.oss_cdn_live_probe`、`schema_version=1`，可复用现有 `trashbot.oss_cdn_manifest` artifact 作为对象输入，并只保存 endpoint path、object key hash、HTTP 状态枚举、object count、`redaction_status`、`safe_summary`、`retry_hint` 和 `not_proven`。当前本机只有 Docker，没有真实 OSS/CDN 凭证、真实云或 4G/SIM；因此即使本地或 future mock HTTP HEAD 返回 2xx，有效 artifact 也必须保持 `production_ready=false`、`overall_status=blocked`、`live_probe_complete=false`。该 gate 只证明 live probe artifact、脱敏规则和 preflight consumption 可验证，不得声明真实 OSS 上传、STS 签发、CDN 回源、真实 CDN live traffic、真实云、真实 4G/SIM、production DB/queue、Nav2/fixed-route、WAVE ROVER、HIL 或真实送达。

本轮 `2026.05.13_17-18_o5_external-evidence-intake-gate` 新增 external evidence intake gate，证据边界是 `software_proof_docker_external_evidence_intake_gate`。Artifact schema 为 `trashbot.external_evidence_intake`、`schema_version=1`，覆盖 `public_ingress_tls`、`oss_cdn`、`production_db_queue`、`four_g_sim` 四类未来真实外部材料的安全收件状态。当前本机没有真实外部材料，因此 artifact 只保存枚举状态、材料时间、固定脱敏摘要、`redaction_status`、`safe_summary`、`retry_hint`、`not_proven` 和 checksum；有效 artifact 与 preflight check 也必须保持 `production_ready=false`、`overall_status=blocked`、`external_evidence_complete=false`。该 gate 只证明 intake schema、checksum、脱敏规则和 preflight consumption 可验证，不得声明真实云、真实 HTTPS/TLS、公网入口、真实 OSS 上传、CDN 回源、STS 签发、production DB/queue、生产队列顺序、事务隔离、真实 4G/SIM、Nav2/fixed-route、WAVE ROVER、HIL 或真实送达。

本轮 `2026.05.17_07-08_cloud-worker-migration-rehearsal` 新增 cloud worker/migration rehearsal gate，证据边界是 `software_proof_docker_cloud_worker_migration_rehearsal_gate`。Artifact schema 为 `trashbot.cloud_worker_migration_rehearsal.v1`，summary schema 为 `trashbot.cloud_worker_migration_rehearsal_summary.v1`，在本地 SQLite relay state 上演练 state 初始化、schema version 标记、重复运行幂等、坏 schema/checksum/stale artifact fail closed、command enqueue、status write、ACK accepted/processing 和 terminal ACK cursor 语义。有效 artifact 与 preflight check 仍必须保持 `production_ready=false`、`overall_status=blocked`、`delivery_success=false`、`primary_actions_enabled=false`。该 gate 只证明 Docker/local SQLite rehearsal 可执行，不得声明真实 production worker、真实 migration、真实 production DB/queue、多实例一致性、真实云、真实 4G/SIM、Nav2/fixed-route、WAVE ROVER、HIL 或真实送达。

本轮 `2026.05.17_08-09_cloud-worker-cutover-drain-gate` 新增 cloud worker cutover/drain gate，证据边界是 `software_proof_docker_cloud_worker_cutover_drain_gate`。Artifact schema 为 `trashbot.cloud_worker_cutover_drain.v1`，summary schema 为 `trashbot.cloud_worker_cutover_drain_summary.v1`，在 Docker/local File 或 SQLite relay state 上 drain pending command，记录 pending count、drained count、cursor before/after、terminal ACK summary、幂等重跑、partial drain fail closed、stale/unsupported schema/unsupported boundary/unsafe copy/credential leak fail closed 和 redaction self-check。有效 artifact 与 preflight check 仍必须保持 `production_ready=false`、`overall_status=blocked`、`delivery_success=false`、`primary_actions_enabled=false`。terminal ACK 只代表云端 envelope 已收口，不代表真实送达、真实 production worker cutover/drain、真实 production DB/queue、多实例一致性、真实云、真实 4G/SIM、Nav2/fixed-route、WAVE ROVER、HIL 或 real external proof。

## 云端基线规格

目标服务端基线：

- 规格：4C 8G，无 GPU。
- 入口：公网 HTTPS API，后续由网关或反向代理终止 TLS。
- 管理：SSH 仅允许运维来源地址访问，禁止作为产品流量入口。
- 产品流量：手机访问云端 API；机器人只主动访问云端 API。
- 数据面：大对象走 OSS/CDN，云中转节点不做图片和视频大流量中转。

本轮 proof 仅在本机 HTTP 中验证控制面语义，没有申请域名、没有配置 TLS 证书、没有开放公网入口，也没有做云主机防火墙实配。

Production preflight 要求新增环境变量：

- `TRASHBOT_REMOTE_CLOUD_PUBLIC_BASE_URL`：生产公网入口，必须是 HTTPS；本地 HTTP 会保持 blocked。
- `TRASHBOT_REMOTE_CLOUD_TLS_MODE`：生产 TLS 终止方式，当前 Docker 默认 `future_reverse_proxy` 只代表未完成。
- `TRASHBOT_REMOTE_CLOUD_PUBLIC_INGRESS`：公网入口状态，生产期应明确为 `public_https` 并另附外网探测证据。
- `TRASHBOT_REMOTE_CLOUD_STATE_BACKEND`：`file` 代表 JSON 文件 proof，`sqlite` 代表单机 SQLite 恢复 proof；生产仍需要数据库或队列证据。

## 网络方向

正式网络方向：

```text
phone web/app -> cloud HTTPS API
robot remote_bridge -> cloud HTTPS API outbound polling
cloud API -> file/db queue for commands/status/acks
robot snapshots -> OSS object storage
phone diagnostics -> CDN or cloud API references
```

安全边界：

- 不接受公网 inbound 直连小车。
- 不把底层速度控制、硬件参数或调试端口暴露给手机用户。
- 手机端只看到任务命令、机器人状态、ACK 和普通用户可读错误。
- ACK 只表示 robot bridge 已处理 command envelope，不表示真实送达完成。

## 防火墙和端口边界

目标云端防火墙策略：

- 对公网开放：HTTPS 443。
- 可选临时调试：HTTP 80 仅用于证书签发或跳转 HTTPS。
- 运维 SSH：限制来源地址；不与产品 API 共用凭证。
- 数据库、队列、对象存储凭证：不直接暴露公网。

本轮 Docker/local proof 不配置真实防火墙。`remote_cloud_relay.py` 本机默认建议监听 `127.0.0.1`；容器内通过 compose 监听 `0.0.0.0`，主机暴露端口由 `TRASHBOT_REMOTE_CLOUD_PUBLISHED_PORT` 控制。

## 容量边界

4C 8G 无 GPU 的基线只承担控制面：

- command/status/ack 是小 JSON，适合短轮询或后续升级为 WebSocket/MQTT。
- 单机器人轮询间隔应由机器人侧参数控制，避免低价值高频空轮询。
- file-backed store 和 SQLite-backed store 都只用于单机 proof；SQLite 能证明重启/重开后的 command/status/ack 恢复，但生产环境仍需要数据库或队列来处理并发、一致性、备份和灾备。
- 图片、日志包、视频片段不得通过 relay service 主通道传输。

本轮没有做压测、跨实例一致性、多租户隔离或生产数据库迁移。

## OSS/CDN 目标

大对象目标链路：

- OSS bucket：`bytegallop`
- region：`oss-cn-hangzhou`
- 对象前缀：`rober/<robot_id>/<date>/<task_id>/`
- CDN base URL：`https://cdn.bytegallop.com/rober/`

凭证原则：

- 小车侧使用 STS 临时凭证或受限 AK。
- 主 AK/SK 不直放小车，不写入仓库，不进入 state file。
- CDN 只做公开只读视图入口；私有任务数据走云端 API 网关和 bearer auth。

本轮没有实现 OSS 上传、STS 签发、CDN 回源、图片生命周期回收或真实凭证 rotate。

Production preflight 会检查 OSS/CDN 配置形态，但不会真实上传对象或探测 CDN 回源。`TRASHBOT_REMOTE_CLOUD_OSS_CREDENTIAL_MODE` 只有 `sts`、`restricted_ak` 或 `managed_identity` 才可进入后续外部实证；`.env.example` 中的 `placeholder` 必须保持 blocked。即使 bucket、region、prefix 和 CDN URL 均配置齐全，缺真实上传、回源、生命周期和 rotate 证据时仍只能是 warning。

OSS/CDN manifest proof 进一步把对象引用 contract 落成 artifact：

```bash
PYTHONPATH=cloud-relay/src:onboard/src/ros2_trashbot_behavior \
python3 -m ros2_trashbot_cloud_relay.remote_cloud_relay \
  --write-oss-cdn-manifest /tmp/trashbot_oss_cdn_manifest.json \
  --manifest-robot-id robot-local-proof \
  --manifest-task-id task-local-proof \
  --manifest-date 2026-05-12
```

Artifact 必须包含 `schema=trashbot.oss_cdn_manifest`、`schema_version=1`、`evidence_boundary=software_proof_docker_oss_cdn_manifest`、`bucket=bytegallop`、`region=oss-cn-hangzhou`、`prefix=rober/<robot_id>/<date>/<task_id>/`、`cdn_base_url=https://cdn.bytegallop.com/rober/`、`objects`、`not_proven` 和 `checksum`。每个 `object_key` 必须以 prefix 开头；每个 `cdn_url` 必须等于 CDN base URL 加去掉 `rober/` 根前缀后的对象相对路径。Artifact 和 preflight 摘要不得包含 bearer token、Authorization header、OSS secret、AK/SK、root password、raw state path、串口、baudrate、WAVE ROVER 参数、ROS topic 或 `/cmd_vel`。

Preflight 消费 manifest artifact 示例：

```bash
PYTHONPATH=cloud-relay/src:onboard/src/ros2_trashbot_behavior \
TRASHBOT_REMOTE_CLOUD_OSS_CDN_MANIFEST_ARTIFACT=/tmp/trashbot_oss_cdn_manifest.json \
python3 -m ros2_trashbot_cloud_relay.remote_cloud_relay --preflight
```

有效 artifact 会新增 `oss_cdn_manifest` pass check，并把本地证据边界提升到 `software_proof_docker_oss_cdn_manifest`。缺失 artifact 是 warning；schema、version、prefix、CDN URL、checksum 或 phone-safe 校验失败是 blocked。无论 manifest 是否通过，preflight 都必须继续保留真实上传、STS、CDN 回源、生命周期、生产账号、真实云、真实 4G/SIM、HTTPS/TLS 公网入口、生产 DB/queue、Nav2/fixed-route、WAVE ROVER/HIL 等未证明项。

Operator/API 消费 manifest artifact 时输出的是更小的 phone-safe summary：

- `state=ready`：artifact 存在，schema/version/prefix/CDN URL/checksum 校验通过，且时间仍在 freshness window 内；仍必须携带 `not_proven`。
- `state=missing`：artifact 未配置、不存在或无法读取；手机首屏不得显示绿色 ready。
- `state=invalid`：schema、version、prefix、CDN URL、checksum 或 phone-safe 校验失败；手机只显示 "诊断对象引用损坏。"，不显示 traceback 或内部路径。
- `state=stale`：artifact 时间字段缺失、不可解析或超过 freshness window；手机提示重新生成诊断引用。

该 summary 字段包括 `schema=trashbot.oss_cdn_manifest`、`schema_version=1`、`object_count`、`cdn_url_rule`、`evidence_boundary=software_proof_docker_phone_manifest_consumption`、`safe_summary`、`retry_hint`、`updated_at`、`staleness` 和 `not_proven`。它不得返回 full manifest、object key、checksum、bearer token、Authorization header、OSS secret、AK/SK、root password、raw state path、串口、baudrate、WAVE ROVER 参数、ROS topic 或 `/cmd_vel`。

OSS/CDN live probe gate 复用 manifest artifact 作为输入，并生成更小的 probe artifact：

```bash
PYTHONPATH=cloud-relay/src:onboard/src/ros2_trashbot_behavior \
python3 -m ros2_trashbot_cloud_relay.remote_cloud_relay \
  --write-oss-cdn-live-probe-artifact /tmp/trashbot_oss_cdn_live_probe.json \
  --oss-cdn-manifest-artifact /tmp/trashbot_oss_cdn_manifest.json
```

Preflight 消费 live probe artifact：

```bash
PYTHONPATH=cloud-relay/src:onboard/src/ros2_trashbot_behavior \
TRASHBOT_REMOTE_CLOUD_OSS_CDN_LIVE_PROBE_ARTIFACT=/tmp/trashbot_oss_cdn_live_probe.json \
python3 -m ros2_trashbot_cloud_relay.remote_cloud_relay --preflight
```

Artifact 必须包含 `schema=trashbot.oss_cdn_live_probe`、`schema_version=1`、`evidence_boundary=software_proof_docker_oss_cdn_live_probe_gate`、`object_count`、`probe_results`、`redaction_status`、`not_proven` 和 `checksum`。`probe_results` 只允许保存 endpoint path、object key hash、HTTP status、reachable、method 和 latency，不保存完整 CDN URL、完整 object key、Authorization header、bearer token、OSS secret、AK/SK、credential-bearing URL、本地路径或响应体。Preflight 中有效 artifact 会新增 `oss_cdn_live_probe` pass check，但仍必须保持 `production_ready=false`、`overall_status=blocked`、`live_probe_complete=false`；它是 `software_proof_docker_oss_cdn_live_probe_gate`，不是真实 CDN live traffic 证据。

## 凭证边界

服务端、CI 和上车机器人均通过环境变量或安全配置注入凭证：

- `TRASHBOT_REMOTE_CLOUD_BEARER_TOKEN`：本轮 independent relay proof 的 bearer token。
- `TRASHBOT_REMOTE_CLOUD_HOST` / `TRASHBOT_REMOTE_CLOUD_PORT`：容器内监听地址和端口。
- `TRASHBOT_REMOTE_CLOUD_PUBLISHED_PORT`：compose 暴露到开发主机的端口。
- `TRASHBOT_REMOTE_CLOUD_STATE`：proof store 路径；file backend 通常是 `.json`，SQLite backend 通常是 `.sqlite`。
- `TRASHBOT_REMOTE_CLOUD_STATE_BACKEND`：`file` 或 `sqlite`。未知值会降级为 phone-safe 的 proof 口径，不回显原始 env 文本。
- `TRASHBOT_REMOTE_CLOUD_BACKUP_ARTIFACT`：可选的本地 backup/restore drill artifact 路径，只供 preflight 验证 schema/checksum 和软件演练状态；不得作为生产备份策略或真实 DR 证据。
- `TRASHBOT_REMOTE_CLOUD_OSS_CDN_MANIFEST_ARTIFACT`：可选的本地 OSS/CDN manifest artifact 路径，只供 preflight 验证对象引用 schema、prefix、CDN URL 和 checksum；不得作为真实 OSS 上传、STS 或 CDN 回源证据。
- `TRASHBOT_REMOTE_CLOUD_OSS_CDN_LIVE_PROBE_ARTIFACT`：可选的本地 OSS/CDN live probe artifact 路径，只供 preflight 消费 endpoint path、object key hash 和 HTTP 状态摘要；不得作为真实 OSS 上传、STS、CDN 回源、真实 CDN live traffic 或 4G 证据。
- `TRASHBOT_REMOTE_CLOUD_NETWORK_RECOVERY_ARTIFACT`：可选的本地 network recovery drill artifact 路径，只供 preflight、operator status 和 diagnostics 消费脱敏摘要；不得作为真实云、真实 4G、生产 incident recovery 或真实送达证据。
- `TRASHBOT_REMOTE_CLOUD_CREDENTIAL_ROTATION_ARTIFACT`：可选的本地 credential rotation artifact 路径，只供 preflight、operator status 和 diagnostics 消费脱敏摘要；不得作为生产 token rotate、真实 STS 签发、真实 OSS 上传、生产账号 provisioning 或真实审计日志证据。
- `TRASHBOT_REMOTE_CLOUD_PROVISIONING_AUDIT_ARTIFACT`：可选的本地 provisioning audit artifact 路径，只供 preflight、operator status 和 diagnostics 消费脱敏摘要；不得作为生产账号发放、真实 STS 签发、真实审计日志、真实云或真实 4G 证据。
- `TRASHBOT_REMOTE_CLOUD_PRODUCTION_STORE_QUEUE_ARTIFACT`：可选的本地 production store/queue artifact 路径，只供 preflight、operator status 和 diagnostics 消费脱敏摘要；不得作为真实生产 DB/queue、多实例一致性、生产备份或真实灾备证据。
- `TRASHBOT_REMOTE_CLOUD_QUEUE_ORDERING_DRILL_ARTIFACT`：可选的本地 queue ordering drill artifact 路径，只供 preflight、operator status 和 diagnostics 消费脱敏摘要；不得作为真实生产 queue ordering、transaction isolation、生产 DB/queue、多实例一致性或真实云证据。
- `TRASHBOT_REMOTE_CLOUD_TRANSACTION_ISOLATION_ARTIFACT`：可选的本地 transaction isolation drill artifact 路径，只供 preflight、operator status 和 diagnostics 消费脱敏摘要；不得作为真实生产 transaction isolation、生产 DB/queue、多实例一致性、真实云或真实 4G 证据。
- `TRASHBOT_REMOTE_CLOUD_PRODUCTION_RECOVERY_ARTIFACT`：可选的本地 production recovery artifact 路径，只供 preflight、operator status 和 diagnostics 消费脱敏摘要；不得作为真实生产 DB/queue、真实生产备份策略、真实灾备恢复、多实例一致性、真实云或真实 4G 证据。
- `TRASHBOT_REMOTE_CLOUD_DEPLOYMENT_RUNBOOK`：可选的部署 readiness runbook 标识，当前 `.env.example` 只允许 `local_docker_smoke` 这类占位，不得写入真实凭证或 credential-bearing URL。
- `TRASHBOT_REMOTE_CLOUD_DEPLOYMENT_READINESS_ARTIFACT`：可选的本地 cloud deployment readiness artifact 路径，只供 preflight 消费脱敏摘要；不得作为真实云、真实 HTTPS/TLS、公网入口、真实 4G/SIM、OSS/CDN 实流量或生产 DB/queue 证据。
- `TRASHBOT_REMOTE_CLOUD_EXTERNAL_PROBE_BASE_URL`：可选的外部探测 base URL；`.env.example` 只能放本地占位，本字段不写入 artifact。
- `TRASHBOT_REMOTE_CLOUD_EXTERNAL_PROBE_ARTIFACT`：可选的本地 cloud external probe bundle artifact 路径，只供 preflight 消费 endpoint 覆盖摘要；不得作为真实云、真实 HTTPS/TLS、公网入口、真实 4G/SIM、OSS/CDN 实流量或生产 DB/queue 证据。
- `TRASHBOT_REMOTE_CLOUD_EXTERNAL_PROBE_TIMEOUT`：可选的 endpoint 探测超时秒数，仅影响本地/未来公网探测命令。
- `TRASHBOT_REMOTE_CLOUD_REVERSE_PROXY_CONFIG`：可选枚举，`missing`、`planned` 或 `present`；只参与 public ingress/TLS 配置包形态判断，不读取或输出真实反向代理配置正文。
- `TRASHBOT_REMOTE_CLOUD_FIREWALL_CONFIG`：可选枚举，`missing`、`planned` 或 `present`；只参与 public ingress/TLS 配置包形态判断，不读取或输出真实防火墙规则。
- `TRASHBOT_REMOTE_CLOUD_PUBLIC_INGRESS_TLS_ARTIFACT`：可选的本地 public ingress/TLS/reverse-proxy 配置 gate artifact 路径，只供 preflight 消费脱敏摘要；不得作为真实 HTTPS/TLS、公网入口、DNS、反向代理、防火墙、真实云或真实 4G/SIM 证据。
- `TRASHBOT_REMOTE_CLOUD_DB_CONFIG`：可选枚举，`missing`、`planned` 或 `present`；只参与生产 DB 配置包形态判断，不读取或输出真实连接信息。
- `TRASHBOT_REMOTE_CLOUD_QUEUE_CONFIG`：可选枚举，`missing`、`planned` 或 `present`；只参与生产 queue 配置包形态判断，不读取或输出真实连接信息。
- `TRASHBOT_REMOTE_CLOUD_DB_MIGRATION_CONFIG`：可选枚举，`missing`、`planned` 或 `present`；只记录迁移配置形态，不代表生产迁移已执行。
- `TRASHBOT_REMOTE_CLOUD_QUEUE_WORKER_CONFIG`：可选枚举，`missing`、`planned` 或 `present`；只记录队列 worker 配置形态，不代表生产 worker 已上线。
- `TRASHBOT_REMOTE_CLOUD_DB_QUEUE_CONFIG_ARTIFACT`：可选的本地 cloud DB/queue config gate artifact 路径，只供 preflight 消费脱敏摘要；不得作为真实生产 DB/queue、多实例一致性、生产队列顺序、事务隔离、备份策略或灾备恢复证据。
- `TRASHBOT_REMOTE_CLOUD_EXTERNAL_EVIDENCE_INTAKE_ARTIFACT`：可选的本地 external evidence intake artifact 路径，只供 preflight 消费四类外部材料的枚举状态和固定脱敏摘要；不得作为真实云、真实 HTTPS/TLS、公网入口、真实 OSS 上传、CDN 回源、STS 签发、production DB/queue、真实 4G/SIM 或 HIL 证据。
- `TRASHBOT_REMOTE_CLOUD_WORKER_MIGRATION_REHEARSAL_ARTIFACT`：可选的本地 cloud worker/migration rehearsal artifact 路径，只供 preflight 消费本地 SQLite migration/worker 演练摘要；不得作为真实 production worker、真实 migration、真实 production DB/queue、多实例一致性或 delivery success 证据，且必须保持 `production_ready=false`、`delivery_success=false`、`primary_actions_enabled=false`。
- `TRASHBOT_REMOTE_CLOUD_EXTERNAL_EVIDENCE_PUBLIC_INGRESS_TLS_STATUS` / `TRASHBOT_REMOTE_CLOUD_EXTERNAL_EVIDENCE_OSS_CDN_STATUS` / `TRASHBOT_REMOTE_CLOUD_EXTERNAL_EVIDENCE_DB_QUEUE_STATUS` / `TRASHBOT_REMOTE_CLOUD_EXTERNAL_EVIDENCE_4G_SIM_STATUS`：可选枚举，允许 `missing`、`not_proven`、`redacted_summary_received` 或 `invalid_or_unsupported`；只影响 intake artifact 中的脱敏状态，不读取或输出真实 URL、凭证、响应体、连接串或本地路径。
- `.env` 不入仓库；`.env.example` 只能放占位符。
- 错误响应和 state file 不得包含 bearer token、Authorization header、credential-bearing URL、串口设备、baudrate、WAVE ROVER 参数、底层速度控制入口或 raw ROS topic 名。
- token rotate、账号分级、机器人 provisioning 和审计日志是后续真实云 sprint 的范围。
- Production preflight 输出不得包含 bearer token、Authorization header、OSS secret、root password、串口、baudrate、WAVE ROVER 参数、ROS topic 或 `/cmd_vel`；输出只保留 `safe_summary`、`retry_hint`、check code 和布尔/枚举化细节。

## 本轮 Docker Deploy Proof

本轮新增 independent relay service module 的 Docker 启动入口：

```bash
cd cloud-relay
TRASHBOT_REMOTE_CLOUD_BEARER_TOKEN=dev-placeholder \
  docker compose -f docker-compose.yml build remote-cloud-relay
TRASHBOT_REMOTE_CLOUD_BEARER_TOKEN=dev-placeholder \
  docker compose -f docker-compose.yml up -d remote-cloud-relay
curl -fsS http://127.0.0.1:8088/healthz
curl -fsS http://127.0.0.1:8088/readyz
```

已覆盖 API：

```text
POST /robots/{robot_id}/commands
GET  /robots/{robot_id}/commands/next?last_ack_id=<id>
POST /robots/{robot_id}/status
GET  /robots/{robot_id}/status
POST /robots/{robot_id}/commands/{command_id}/ack
GET  /robots/{robot_id}/commands/{command_id}/ack
```

health/readiness：

- `GET /healthz`：只证明进程存活、service 名称、protocol version 和 `software_proof_docker_deploy` evidence boundary。
- `GET /readyz`：覆盖 protocol/version、credential gate 是否配置、state store 是否可写、phone-safe failure 脱敏自检。未配置 bearer token 或 state store 不可写时返回 503 和 `not_ready`，不回显 token、state path、credential URL、串口、baudrate、WAVE ROVER 参数、ROS topic、`/cmd_vel` 或 traceback。
- `GET /preflightz`：返回 production preflight gate 的 machine-readable JSON。当前 Docker-only deployment readiness gate 的默认 evidence boundary 为 `software_proof_docker_cloud_deployment_readiness_gate`；更窄的 SQLite、backup/restore、OSS/CDN、queue 等 proof 只作为检查项或后续 artifact 证据出现。本地 HTTP、占位 token、缺 TLS/公网入口、OSS/CDN 占位、file/SQLite proof store、生产 DB/queue 缺失或 state path 不可写会返回 blocked/warning，并用 phone-safe `safe_summary` / `retry_hint` 指导下一步。

CLI gate：

```bash
PYTHONPATH=cloud-relay/src:onboard/src/ros2_trashbot_behavior \
TRASHBOT_REMOTE_CLOUD_BEARER_TOKEN=replace-with-local-dev-token \
TRASHBOT_REMOTE_CLOUD_PUBLIC_BASE_URL=http://127.0.0.1:8088 \
TRASHBOT_REMOTE_CLOUD_STATE=/tmp/trashbot_remote_cloud_relay.json \
python3 -m ros2_trashbot_cloud_relay.remote_cloud_relay --preflight
```

本地占位配置预期返回非 0，并输出 `production_ready=false`、`overall_status=blocked` 和 `evidence_boundary=software_proof_docker_cloud_deployment_readiness_gate`。这正是上线前 gate 的目标：真实生产入口、TLS、公网、防火墙、OSS/CDN、4G/SIM 和生产 state store 未补齐前，不能把 Docker/local proof 包装成生产完成。

SQLite state proof 示例：

```bash
PYTHONPATH=cloud-relay/src:onboard/src/ros2_trashbot_behavior \
TRASHBOT_REMOTE_CLOUD_STATE_BACKEND=sqlite \
TRASHBOT_REMOTE_CLOUD_STATE=/tmp/trashbot_remote_cloud_relay.sqlite \
python3 -m ros2_trashbot_cloud_relay.remote_cloud_relay --preflight
```

SQLite backend 可让本地 proof 验证 command/status/ack 跨 restart 恢复。preflight 必须继续输出 `production_ready=false`，并把 production DB/queue、多实例一致性、backup/restore、disaster recovery、真实云和真实 4G 标为未证明。

Backup/restore drill CLI 示例：

```bash
PYTHONPATH=cloud-relay/src:onboard/src/ros2_trashbot_behavior \
TRASHBOT_REMOTE_CLOUD_STATE_BACKEND=sqlite \
python3 -m ros2_trashbot_cloud_relay.remote_cloud_relay \
  --state-backend sqlite \
  --state-path /tmp/trashbot_remote_cloud_relay.sqlite \
  --backup-state-to /tmp/trashbot_remote_cloud_relay_backup.json \
  --restore-state-path /tmp/trashbot_remote_cloud_relay_restored.sqlite \
  --backup-restore-drill
```

成功输出必须包含 `evidence_boundary=software_proof_docker_backup_restore_drill`、`backup_status=passed`、`restore_status=passed`、`drill_status=passed`，并继续把 `production_backup_policy`、`real_disaster_recovery`、`production_db_or_queue`、`multi_instance_consistency`、真实云和真实 4G 列为未证明。输出和 artifact 摘要不得包含 bearer token、Authorization header、OSS secret、root password、原始 state path、ROS topic、串口、baudrate、WAVE ROVER 参数或 `/cmd_vel`。

Credential rotation gate CLI 示例：

```bash
PYTHONPATH=cloud-relay/src:onboard/src/ros2_trashbot_behavior \
python3 -m ros2_trashbot_cloud_relay.remote_cloud_relay \
  --write-credential-rotation-artifact /tmp/trashbot_credential_rotation_gate.json \
  --credential-rotation-robot-id robot-local-proof
```

Artifact 必须包含 `schema=trashbot.credential_rotation_gate`、`schema_version=1`、`evidence_boundary=software_proof_docker_credential_rotation_gate`、`robot_id`、`generated_at`、`bearer_rotation_status`、`oss_credential_mode`、`sts_boundary_status`、`account_tier_status`、`robot_provisioning_status`、`audit_log_status`、`not_proven`、`safe_summary`、`retry_hint` 和 `checksum`。Preflight 可通过 `TRASHBOT_REMOTE_CLOUD_CREDENTIAL_ROTATION_ARTIFACT` 消费该 artifact；有效 artifact 会新增 `credential_rotation=pass` check，并把本地证据边界推进到 `software_proof_docker_credential_rotation_gate`，但 `production_ready=false` 必须保持，`not_proven` 必须继续列出 production credential rotation、STS issuance、真实 OSS upload、CDN origin fetch、production account、robot provisioning、audit log、真实云、真实 4G/SIM、Nav2/fixed-route、WAVE ROVER/HIL 和真实送达缺口。

Provisioning audit gate CLI 示例：

```bash
PYTHONPATH=cloud-relay/src:onboard/src/ros2_trashbot_behavior \
python3 -m ros2_trashbot_cloud_relay.remote_cloud_relay \
  --write-provisioning-audit-artifact /tmp/trashbot_provisioning_audit_gate.json \
  --provisioning-audit-robot-id robot-local-proof
```

Artifact 必须包含 `schema=trashbot.provisioning_audit_gate`、`schema_version=1`、`evidence_boundary=software_proof_docker_provisioning_audit_gate`、`robot_id`、`generated_at`、`robot_provisioning_status`、`sts_issuance_status`、`audit_log_status`、`credential_delivery_status`、`production_ready=false`、`overall_status=blocked`、`not_proven`、`safe_summary`、`retry_hint` 和 `checksum`。Preflight 可通过 `TRASHBOT_REMOTE_CLOUD_PROVISIONING_AUDIT_ARTIFACT` 或 `--provisioning-audit-artifact` 消费该 artifact；有效 artifact 会新增 `provisioning_audit=pass` check，并把本地证据边界推进到 `software_proof_docker_provisioning_audit_gate`，但 `production_ready=false` 和 `overall_status=blocked` 必须保持，`not_proven` 必须继续列出 production robot provisioning、真实 STS issuance、真实 audit log、真实云、真实 4G/SIM、Nav2/fixed-route、WAVE ROVER/HIL 和真实送达缺口。

Production store/queue gate CLI 示例：

```bash
PYTHONPATH=cloud-relay/src:onboard/src/ros2_trashbot_behavior \
python3 -m ros2_trashbot_cloud_relay.remote_cloud_relay \
  --write-production-store-queue-artifact /tmp/trashbot_production_store_queue_gate.json \
  --production-store-queue-robot-id robot-local-proof
```

Artifact 必须包含 `schema=trashbot.production_store_queue_gate`、`schema_version=1`、`evidence_boundary=software_proof_docker_production_store_queue_gate`、`robot_id`、`generated_at`、`store_contract_status`、`queue_contract_status`、`ordering_status`、`consistency_status`、`migration_status`、`production_ready=false`、`overall_status=blocked`、`not_proven`、`safe_summary`、`retry_hint` 和 `checksum`。Preflight 可通过 `TRASHBOT_REMOTE_CLOUD_PRODUCTION_STORE_QUEUE_ARTIFACT` 或 `--production-store-queue-artifact` 消费该 artifact；有效 artifact 会新增 `production_store_queue=pass` check，并把本地证据边界推进到 `software_proof_docker_production_store_queue_gate`，但 `production_ready=false` 和 `overall_status=blocked` 必须保持，`not_proven` 必须继续列出 production DB/queue、多实例一致性、生产 queue ordering、transaction isolation、生产备份、真实灾备、真实云、真实 4G/SIM、Nav2/fixed-route、WAVE ROVER/HIL 和真实送达缺口。

Queue ordering drill CLI 示例：

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=cloud-relay/src:onboard/src/ros2_trashbot_behavior \
python3 -m ros2_trashbot_cloud_relay.remote_cloud_relay \
  --write-queue-ordering-drill-artifact /tmp/trashbot_queue_ordering_drill.json \
  --queue-ordering-drill-robot-id robot-local-proof
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=cloud-relay/src:onboard/src/ros2_trashbot_behavior \
python3 -m ros2_trashbot_cloud_relay.remote_cloud_relay \
  --preflight \
  --queue-ordering-drill-artifact /tmp/trashbot_queue_ordering_drill.json
```

Artifact 必须包含 `schema=trashbot.queue_ordering_drill`、`schema_version=1`、`evidence_boundary=software_proof_docker_queue_ordering_drill`、`robot_id`、`updated_at`、`ordering_invariant`、`concurrency_invariant`、`cursor_invariant`、`ack_invariant`、`adjacent_command_ids=["cmd-9","cmd-10"]`、`observed_order=["cmd-9","cmd-10"]`、`production_ready=false`、`overall_status=passed|failed`、`not_proven`、`safe_summary`、`retry_hint` 和 `checksum`。Preflight 有效时只新增 `queue_ordering_drill=pass` check，并把本地证据边界推进到 `software_proof_docker_queue_ordering_drill`；`production_ready=false` 必须保持，`not_proven` 必须继续列出真实生产 queue ordering、生产 DB/queue、多实例一致性、transaction isolation、真实云、真实 4G/SIM、Nav2/fixed-route、WAVE ROVER/HIL 和真实送达缺口。

## Transaction Isolation Drill

Transaction isolation drill 是 queue ordering 之后的下一层 Docker/local 软件证明。它验证同一 robot 的 command/status/ACK interleaving 不会让 ACK cursor 越过未完成 command，也不会把 ACK 当成真实送达成功：

```bash
PYTHONPATH=cloud-relay/src:onboard/src/ros2_trashbot_behavior \
python3 -m ros2_trashbot_cloud_relay.remote_cloud_relay \
  --write-transaction-isolation-artifact /tmp/trashbot_transaction_isolation_drill.json \
  --transaction-isolation-robot-id robot-local-proof
```

Artifact 必须包含 `schema=trashbot.transaction_isolation_drill`、`schema_version=1`、`evidence_boundary=software_proof_docker_transaction_isolation_gate`、`robot_id`、`updated_at`、`scenario=same_robot_interleaved_command_status_ack`、`command_a_id`、`command_b_id`、`command_a_ack_state=processing`、`command_b_ack_state=acked`、`terminal_ack_ids`、`cursor_before`、`cursor_after_interleaving`、`cursor_invariant`、`ack_invariant`、`delivery_success=false`、`production_ready=false`、`overall_status=passed|failed`、`not_proven`、`safe_summary`、`retry_hint` 和 `checksum`。Preflight 有效时新增 `transaction_isolation=pass` check，并把本地证据边界推进到 `software_proof_docker_transaction_isolation_gate`；`production_ready=false` 必须保持，`not_proven` 必须继续列出真实生产 transaction isolation、生产 DB/queue、多实例一致性、真实云、真实 4G/SIM、Nav2/fixed-route、WAVE ROVER/HIL 和真实送达缺口。

## Production Recovery Gate

Production recovery gate 是 backup/restore、production store/queue、queue ordering 和 transaction isolation 之后的上线前缺口汇总 gate。它只验证 Docker/local artifact 的 schema、checksum、状态分层和 phone-safe 摘要；本地恢复演练不能当成真实生产备份策略或灾备恢复：

```bash
PYTHONPATH=cloud-relay/src:onboard/src/ros2_trashbot_behavior \
python3 -m ros2_trashbot_cloud_relay.remote_cloud_relay \
  --write-production-recovery-artifact /tmp/trashbot_production_recovery_gate.json \
  --production-recovery-robot-id robot-local-proof
PYTHONPATH=cloud-relay/src:onboard/src/ros2_trashbot_behavior \
python3 -m ros2_trashbot_cloud_relay.remote_cloud_relay \
  --preflight \
  --production-recovery-artifact /tmp/trashbot_production_recovery_gate.json
```

Artifact 必须包含 `schema=trashbot.production_recovery_gate`、`schema_version=1`、`evidence_boundary=software_proof_docker_production_recovery_gate`、`robot_id`、`updated_at`、`local_backup_restore_status`、`recovery_drill_status`、`production_backup_policy_status=blocked_not_proven`、`disaster_recovery_status=blocked_not_proven`、`state_backend_status`、`db_queue_status`、`multi_instance_status`、`retention_status`、`restore_objective_status`、`ack_semantics`、`production_ready=false`、`overall_status=blocked`、`not_proven`、`safe_summary`、`retry_hint` 和 `checksum`。Preflight 有效时新增 `production_recovery=pass` check，并把本地证据边界推进到 `software_proof_docker_production_recovery_gate`；`production_ready=false` 与 `overall_status=blocked` 必须保持，`not_proven` 必须继续列出真实生产 DB/queue、多实例一致性、真实生产备份策略、真实灾备恢复、真实云、真实 4G/SIM、OSS/CDN 实流量、Nav2/fixed-route、WAVE ROVER/HIL 和真实送达缺口。

Preflight 可用 `TRASHBOT_REMOTE_CLOUD_BACKUP_ARTIFACT` 验证本地 artifact：

```bash
PYTHONPATH=cloud-relay/src:onboard/src/ros2_trashbot_behavior \
TRASHBOT_REMOTE_CLOUD_STATE_BACKEND=sqlite \
TRASHBOT_REMOTE_CLOUD_BACKUP_ARTIFACT=/tmp/trashbot_remote_cloud_relay_backup.json \
python3 -m ros2_trashbot_cloud_relay.remote_cloud_relay --preflight
```

## Cloud Deployment Readiness Gate

Cloud deployment readiness gate 是上线前总门禁，只把本地 Docker 能证明的内容变成可复核 artifact。它不会探测真实公网、不会申请 TLS、不会连接真实 4G/SIM、不会上传 OSS/CDN、不会连接生产 DB/queue，也不会证明 WAVE ROVER、Nav2/fixed-route、HIL 或真实送达。

生成 artifact：

```bash
PYTHONPATH=cloud-relay/src:onboard/src/ros2_trashbot_behavior \
TRASHBOT_REMOTE_CLOUD_BEARER_TOKEN=dev-smoke-token \
python3 -m ros2_trashbot_cloud_relay.remote_cloud_relay \
  --write-cloud-deployment-readiness-artifact /tmp/trashbot_cloud_deployment_readiness.json
```

传给 preflight：

```bash
PYTHONPATH=cloud-relay/src:onboard/src/ros2_trashbot_behavior \
TRASHBOT_REMOTE_CLOUD_DEPLOYMENT_READINESS_ARTIFACT=/tmp/trashbot_cloud_deployment_readiness.json \
python3 -m ros2_trashbot_cloud_relay.remote_cloud_relay --preflight
```

有效 artifact 只表示本地 schema、checksum、检查项覆盖和脱敏边界通过。Preflight 和 artifact 都必须保持 `evidence_boundary=software_proof_docker_cloud_deployment_readiness_gate`、`production_ready=false`、`overall_status=blocked`，并继续输出真实云、真实 HTTPS/TLS、公网入口、4G/SIM、OSS/CDN 实流量、生产 DB/queue、多实例、生产备份/灾备、Nav2/fixed-route、WAVE ROVER/HIL 和真实送达的 `not_proven`。输出不得包含 bearer token、Authorization header、OSS secret、AK/SK、root password、DB URL、queue URL、credential-bearing URL、raw state path、串口、baudrate、WAVE ROVER 参数、ROS topic、`/cmd_vel` 或 traceback。

如果 artifact schema、version 或 checksum 不匹配，preflight 必须返回 phone-safe blocked reason；如果 artifact 有效，preflight 只允许声明本地 backup/restore drill artifact 通过，不能声明生产 backup policy、真实 DR 或生产 DB/queue ready。

Network recovery drill CLI 示例：

```bash
PYTHONPATH=cloud-relay/src:onboard/src/ros2_trashbot_behavior \
python3 -m ros2_trashbot_cloud_relay.remote_cloud_relay \
  --network-recovery-drill \
  --state-backend sqlite \
  --state-path /tmp/trashbot_network_recovery.sqlite \
  --write-network-recovery-artifact /tmp/trashbot_network_recovery_drill.json
```

Preflight 可用 `TRASHBOT_REMOTE_CLOUD_NETWORK_RECOVERY_ARTIFACT` 验证本地 artifact：

```bash
PYTHONPATH=cloud-relay/src:onboard/src/ros2_trashbot_behavior \
TRASHBOT_REMOTE_CLOUD_NETWORK_RECOVERY_ARTIFACT=/tmp/trashbot_network_recovery_drill.json \
python3 -m ros2_trashbot_cloud_relay.remote_cloud_relay --preflight
```

有效 artifact 会新增 `network_recovery_drill=pass`，设置
`software_proof_ready=true`，并把本地证据边界提升到
`software_proof_docker_network_recovery_drill`。缺失 artifact 是 warning；
schema、version、checksum、必需 steps、cursor invariant、stale 或
phone-safe 校验失败是 blocked。无论 artifact 是否通过，preflight 都必须
继续保留真实云、真实 4G/SIM、HTTPS/TLS 公网入口、生产 DB/queue、多实例
一致性、真实 OSS/CDN 流量、生产 incident recovery、Nav2/fixed-route、
WAVE ROVER/HIL 和 delivery success 等未证明项。

## External Evidence Intake Gate

External evidence intake gate 是 O5 外部材料交接入口，不直接接收原始材料正文：

```bash
PYTHONPATH=cloud-relay/src:onboard/src/ros2_trashbot_behavior \
python3 -m ros2_trashbot_cloud_relay.remote_cloud_relay \
  --write-external-evidence-intake-artifact /tmp/trashbot_external_evidence_intake.json
```

传给 preflight：

```bash
PYTHONPATH=cloud-relay/src:onboard/src/ros2_trashbot_behavior \
TRASHBOT_REMOTE_CLOUD_EXTERNAL_EVIDENCE_INTAKE_ARTIFACT=/tmp/trashbot_external_evidence_intake.json \
python3 -m ros2_trashbot_cloud_relay.remote_cloud_relay --preflight
```

Artifact 必须包含 `schema=trashbot.external_evidence_intake`、`schema_version=1`、`evidence_boundary=software_proof_docker_external_evidence_intake_gate`、四类 `material_statuses`、`production_ready=false`、`overall_status=blocked`、`external_evidence_complete=false`、`redaction_status`、`not_proven` 和 checksum。Preflight 可通过环境变量或 `--external-evidence-intake-artifact` 消费该 artifact；有效时只新增 `external_evidence_intake=pass` check，并把本地证据边界推进到 `software_proof_docker_external_evidence_intake_gate`。它不得保存或输出 URL、credential-bearing endpoint、Authorization header、bearer token、OSS AK/SK、DB/queue URL、本地路径、响应体、traceback、串口、WAVE ROVER 参数、ROS topic 或 `/cmd_vel`。

## Cloud Worker Migration Rehearsal Gate

Cloud worker/migration rehearsal gate 是 O5 production DB/queue 的本地可执行演练入口：

```bash
PYTHONPATH=cloud-relay/src:onboard/src/ros2_trashbot_behavior \
python3 -m ros2_trashbot_cloud_relay.remote_cloud_relay \
  --state-backend sqlite \
  --state-path /tmp/trashbot_worker_migration_rehearsal.sqlite \
  --write-cloud-worker-migration-rehearsal-artifact /tmp/trashbot_cloud_worker_migration_rehearsal.json
```

传给 preflight：

```bash
PYTHONPATH=cloud-relay/src:onboard/src/ros2_trashbot_behavior \
TRASHBOT_REMOTE_CLOUD_WORKER_MIGRATION_REHEARSAL_ARTIFACT=/tmp/trashbot_cloud_worker_migration_rehearsal.json \
python3 -m ros2_trashbot_cloud_relay.remote_cloud_relay --preflight
```

Artifact 必须包含 `schema=trashbot.cloud_worker_migration_rehearsal.v1`、`summary_schema=trashbot.cloud_worker_migration_rehearsal_summary.v1`、`evidence_boundary=software_proof_docker_cloud_worker_migration_rehearsal_gate`、`production_ready=false`、`delivery_success=false`、`primary_actions_enabled=false`、migration rehearsal、worker rehearsal、`redaction_status`、`not_proven` 和 checksum。Preflight 可通过环境变量或 `--cloud-worker-migration-rehearsal-artifact` 消费该 artifact；有效时只新增 `cloud_worker_migration_rehearsal=pass` check，并把本地证据边界推进到 `software_proof_docker_cloud_worker_migration_rehearsal_gate`。它不得保存或输出 DB/queue URL、credential-bearing URL、Authorization header、bearer token、OSS AK/SK、root password、raw local path、串口、UART、WAVE ROVER 参数、ROS topic 或 `/cmd_vel`。

该 gate 的产品含义很窄：SQLite `user_version` 标记只证明本地 schema rehearsal，command enqueue/status write/ACK accepted/processing 只证明 relay envelope 和 worker loop 语义，terminal ACK 不等于 delivery success。真实 production migration、真实 production queue worker、生产 DB/queue 连接、多实例一致性、真实云、真实 4G/SIM、Nav2/fixed-route、WAVE ROVER/HIL 和真实送达仍是未证明项。

proof 边界：

- bearer auth：缺 token 或错 token 返回 `auth_failed`。
- command：`id` 作为幂等键，支持 `collect`、`confirm_dropoff`、`cancel`，过期 command 不作为 next 返回。
- status：缺失返回 `status_missing`，过期返回 `status_stale`。
- ACK：终态只允许 `acked`、`failed`、`ignored`。
- persistence：commands/status/acks 可写入本地 JSON state file，使用临时文件加 `os.replace` 做原子替换；也可通过 `TRASHBOT_REMOTE_CLOUD_STATE_BACKEND=sqlite` 写入单机 SQLite proof store，并在 relay restart 后恢复。
- backup/restore：SQLite proof store 可生成带 schema/version/metadata/checksum 的 JSON artifact，并恢复到新的 SQLite proof state；该恢复只验证 command/status/ack envelope 和 ACK cursor 语义，不证明生产备份策略或真实灾备。
- phone-safe errors：覆盖 `auth_failed`、`bad_request`、`not_found`、`status_missing`、`status_stale`、`malformed_json`。
- Docker deploy smoke：`cloud-relay/scripts/docker_smoke.sh` 覆盖 compose build、容器启动、health/readiness、post status、enqueue command、robot-style next command、post ack、read ack/status、停止容器并输出相关日志。

未完成项：

- 真实云部署、域名、公网入口、HTTPS/TLS、防火墙实配。
- 真实 4G/SIM、弱网/断网 carrier 测试。
- 生产数据库、队列、多实例一致性、备份和灾备。
- OSS/CDN 上传、STS、受限 AK、生命周期和 rotate。
- Nav2/fixed-route、WAVE ROVER、真实硬件运动、HIL 和用户实机验收。
