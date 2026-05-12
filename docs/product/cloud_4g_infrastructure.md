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
PYTHONPATH=src/ros2_trashbot_behavior \
python3 -m ros2_trashbot_behavior.remote_cloud_relay \
  --write-oss-cdn-manifest /tmp/trashbot_oss_cdn_manifest.json \
  --manifest-robot-id robot-local-proof \
  --manifest-task-id task-local-proof \
  --manifest-date 2026-05-12
```

Artifact 必须包含 `schema=trashbot.oss_cdn_manifest`、`schema_version=1`、`evidence_boundary=software_proof_docker_oss_cdn_manifest`、`bucket=bytegallop`、`region=oss-cn-hangzhou`、`prefix=rober/<robot_id>/<date>/<task_id>/`、`cdn_base_url=https://cdn.bytegallop.com/rober/`、`objects`、`not_proven` 和 `checksum`。每个 `object_key` 必须以 prefix 开头；每个 `cdn_url` 必须等于 CDN base URL 加去掉 `rober/` 根前缀后的对象相对路径。Artifact 和 preflight 摘要不得包含 bearer token、Authorization header、OSS secret、AK/SK、root password、raw state path、串口、baudrate、WAVE ROVER 参数、ROS topic 或 `/cmd_vel`。

Preflight 消费 manifest artifact 示例：

```bash
PYTHONPATH=src/ros2_trashbot_behavior \
TRASHBOT_REMOTE_CLOUD_OSS_CDN_MANIFEST_ARTIFACT=/tmp/trashbot_oss_cdn_manifest.json \
python3 -m ros2_trashbot_behavior.remote_cloud_relay --preflight
```

有效 artifact 会新增 `oss_cdn_manifest` pass check，并把本地证据边界提升到 `software_proof_docker_oss_cdn_manifest`。缺失 artifact 是 warning；schema、version、prefix、CDN URL、checksum 或 phone-safe 校验失败是 blocked。无论 manifest 是否通过，preflight 都必须继续保留真实上传、STS、CDN 回源、生命周期、生产账号、真实云、真实 4G/SIM、HTTPS/TLS 公网入口、生产 DB/queue、Nav2/fixed-route、WAVE ROVER/HIL 等未证明项。

Operator/API 消费 manifest artifact 时输出的是更小的 phone-safe summary：

- `state=ready`：artifact 存在，schema/version/prefix/CDN URL/checksum 校验通过，且时间仍在 freshness window 内；仍必须携带 `not_proven`。
- `state=missing`：artifact 未配置、不存在或无法读取；手机首屏不得显示绿色 ready。
- `state=invalid`：schema、version、prefix、CDN URL、checksum 或 phone-safe 校验失败；手机只显示 "诊断对象引用损坏。"，不显示 traceback 或内部路径。
- `state=stale`：artifact 时间字段缺失、不可解析或超过 freshness window；手机提示重新生成诊断引用。

该 summary 字段包括 `schema=trashbot.oss_cdn_manifest`、`schema_version=1`、`object_count`、`cdn_url_rule`、`evidence_boundary=software_proof_docker_phone_manifest_consumption`、`safe_summary`、`retry_hint`、`updated_at`、`staleness` 和 `not_proven`。它不得返回 full manifest、object key、checksum、bearer token、Authorization header、OSS secret、AK/SK、root password、raw state path、串口、baudrate、WAVE ROVER 参数、ROS topic 或 `/cmd_vel`。

## 凭证边界

服务端、CI 和上车机器人均通过环境变量或安全配置注入凭证：

- `TRASHBOT_REMOTE_CLOUD_BEARER_TOKEN`：本轮 independent relay proof 的 bearer token。
- `TRASHBOT_REMOTE_CLOUD_HOST` / `TRASHBOT_REMOTE_CLOUD_PORT`：容器内监听地址和端口。
- `TRASHBOT_REMOTE_CLOUD_PUBLISHED_PORT`：compose 暴露到开发主机的端口。
- `TRASHBOT_REMOTE_CLOUD_STATE`：proof store 路径；file backend 通常是 `.json`，SQLite backend 通常是 `.sqlite`。
- `TRASHBOT_REMOTE_CLOUD_STATE_BACKEND`：`file` 或 `sqlite`。未知值会降级为 phone-safe 的 proof 口径，不回显原始 env 文本。
- `TRASHBOT_REMOTE_CLOUD_BACKUP_ARTIFACT`：可选的本地 backup/restore drill artifact 路径，只供 preflight 验证 schema/checksum 和软件演练状态；不得作为生产备份策略或真实 DR 证据。
- `TRASHBOT_REMOTE_CLOUD_OSS_CDN_MANIFEST_ARTIFACT`：可选的本地 OSS/CDN manifest artifact 路径，只供 preflight 验证对象引用 schema、prefix、CDN URL 和 checksum；不得作为真实 OSS 上传、STS 或 CDN 回源证据。
- `TRASHBOT_REMOTE_CLOUD_NETWORK_RECOVERY_ARTIFACT`：可选的本地 network recovery drill artifact 路径，只供 preflight、operator status 和 diagnostics 消费脱敏摘要；不得作为真实云、真实 4G、生产 incident recovery 或真实送达证据。
- `TRASHBOT_REMOTE_CLOUD_CREDENTIAL_ROTATION_ARTIFACT`：可选的本地 credential rotation artifact 路径，只供 preflight、operator status 和 diagnostics 消费脱敏摘要；不得作为生产 token rotate、真实 STS 签发、真实 OSS 上传、生产账号 provisioning 或真实审计日志证据。
- `TRASHBOT_REMOTE_CLOUD_PROVISIONING_AUDIT_ARTIFACT`：可选的本地 provisioning audit artifact 路径，只供 preflight、operator status 和 diagnostics 消费脱敏摘要；不得作为生产账号发放、真实 STS 签发、真实审计日志、真实云或真实 4G 证据。
- `.env` 不入仓库；`.env.example` 只能放占位符。
- 错误响应和 state file 不得包含 bearer token、Authorization header、credential-bearing URL、串口设备、baudrate、WAVE ROVER 参数、底层速度控制入口或 raw ROS topic 名。
- token rotate、账号分级、机器人 provisioning 和审计日志是后续真实云 sprint 的范围。
- Production preflight 输出不得包含 bearer token、Authorization header、OSS secret、root password、串口、baudrate、WAVE ROVER 参数、ROS topic 或 `/cmd_vel`；输出只保留 `safe_summary`、`retry_hint`、check code 和布尔/枚举化细节。

## 本轮 Docker Deploy Proof

本轮新增 independent relay service module 的 Docker 启动入口：

```bash
cp .env.example .env
# 修改 .env 中的 TRASHBOT_REMOTE_CLOUD_BEARER_TOKEN 为本地占位值，不提交真实密钥。
docker compose -f docker-compose.remote-cloud-relay.yml build remote-cloud-relay
docker compose -f docker-compose.remote-cloud-relay.yml up -d remote-cloud-relay
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
- `GET /preflightz`：返回 production preflight gate 的 machine-readable JSON。file backend 的 evidence boundary 为 `software_proof_docker_preflight_gate`；SQLite backend 的 evidence boundary 为 `software_proof_docker_sqlite_state_store`。本地 HTTP、占位 token、缺 TLS/公网入口、OSS/CDN 占位、file/SQLite proof store、生产 DB/queue 缺失或 state path 不可写会返回 blocked/warning，并用 phone-safe `safe_summary` / `retry_hint` 指导下一步。

CLI gate：

```bash
PYTHONPATH=src/ros2_trashbot_behavior \
TRASHBOT_REMOTE_CLOUD_BEARER_TOKEN=replace-with-local-dev-token \
TRASHBOT_REMOTE_CLOUD_PUBLIC_BASE_URL=http://127.0.0.1:8088 \
TRASHBOT_REMOTE_CLOUD_STATE=/tmp/trashbot_remote_cloud_relay.json \
python3 -m ros2_trashbot_behavior.remote_cloud_relay --preflight
```

本地占位配置预期返回非 0，并输出 `production_ready=false`、`overall_status=blocked` 和 `evidence_boundary=software_proof_docker_preflight_gate`。这正是上线前 gate 的目标：真实生产入口、TLS、公网、防火墙、OSS/CDN 和生产 state store 未补齐前，不能把 Docker/local proof 包装成生产完成。

SQLite state proof 示例：

```bash
PYTHONPATH=src/ros2_trashbot_behavior \
TRASHBOT_REMOTE_CLOUD_STATE_BACKEND=sqlite \
TRASHBOT_REMOTE_CLOUD_STATE=/tmp/trashbot_remote_cloud_relay.sqlite \
python3 -m ros2_trashbot_behavior.remote_cloud_relay --preflight
```

SQLite backend 可让本地 proof 验证 command/status/ack 跨 restart 恢复。preflight 必须继续输出 `production_ready=false`，并把 production DB/queue、多实例一致性、backup/restore、disaster recovery、真实云和真实 4G 标为未证明。

Backup/restore drill CLI 示例：

```bash
PYTHONPATH=src/ros2_trashbot_behavior \
TRASHBOT_REMOTE_CLOUD_STATE_BACKEND=sqlite \
python3 -m ros2_trashbot_behavior.remote_cloud_relay \
  --state-backend sqlite \
  --state-path /tmp/trashbot_remote_cloud_relay.sqlite \
  --backup-state-to /tmp/trashbot_remote_cloud_relay_backup.json \
  --restore-state-path /tmp/trashbot_remote_cloud_relay_restored.sqlite \
  --backup-restore-drill
```

成功输出必须包含 `evidence_boundary=software_proof_docker_backup_restore_drill`、`backup_status=passed`、`restore_status=passed`、`drill_status=passed`，并继续把 `production_backup_policy`、`real_disaster_recovery`、`production_db_or_queue`、`multi_instance_consistency`、真实云和真实 4G 列为未证明。输出和 artifact 摘要不得包含 bearer token、Authorization header、OSS secret、root password、原始 state path、ROS topic、串口、baudrate、WAVE ROVER 参数或 `/cmd_vel`。

Credential rotation gate CLI 示例：

```bash
PYTHONPATH=src/ros2_trashbot_behavior \
python3 -m ros2_trashbot_behavior.remote_cloud_relay \
  --write-credential-rotation-artifact /tmp/trashbot_credential_rotation_gate.json \
  --credential-rotation-robot-id robot-local-proof
```

Artifact 必须包含 `schema=trashbot.credential_rotation_gate`、`schema_version=1`、`evidence_boundary=software_proof_docker_credential_rotation_gate`、`robot_id`、`generated_at`、`bearer_rotation_status`、`oss_credential_mode`、`sts_boundary_status`、`account_tier_status`、`robot_provisioning_status`、`audit_log_status`、`not_proven`、`safe_summary`、`retry_hint` 和 `checksum`。Preflight 可通过 `TRASHBOT_REMOTE_CLOUD_CREDENTIAL_ROTATION_ARTIFACT` 消费该 artifact；有效 artifact 会新增 `credential_rotation=pass` check，并把本地证据边界推进到 `software_proof_docker_credential_rotation_gate`，但 `production_ready=false` 必须保持，`not_proven` 必须继续列出 production credential rotation、STS issuance、真实 OSS upload、CDN origin fetch、production account、robot provisioning、audit log、真实云、真实 4G/SIM、Nav2/fixed-route、WAVE ROVER/HIL 和真实送达缺口。

Provisioning audit gate CLI 示例：

```bash
PYTHONPATH=src/ros2_trashbot_behavior \
python3 -m ros2_trashbot_behavior.remote_cloud_relay \
  --write-provisioning-audit-artifact /tmp/trashbot_provisioning_audit_gate.json \
  --provisioning-audit-robot-id robot-local-proof
```

Artifact 必须包含 `schema=trashbot.provisioning_audit_gate`、`schema_version=1`、`evidence_boundary=software_proof_docker_provisioning_audit_gate`、`robot_id`、`generated_at`、`robot_provisioning_status`、`sts_issuance_status`、`audit_log_status`、`credential_delivery_status`、`production_ready=false`、`overall_status=blocked`、`not_proven`、`safe_summary`、`retry_hint` 和 `checksum`。Preflight 可通过 `TRASHBOT_REMOTE_CLOUD_PROVISIONING_AUDIT_ARTIFACT` 或 `--provisioning-audit-artifact` 消费该 artifact；有效 artifact 会新增 `provisioning_audit=pass` check，并把本地证据边界推进到 `software_proof_docker_provisioning_audit_gate`，但 `production_ready=false` 和 `overall_status=blocked` 必须保持，`not_proven` 必须继续列出 production robot provisioning、真实 STS issuance、真实 audit log、真实云、真实 4G/SIM、Nav2/fixed-route、WAVE ROVER/HIL 和真实送达缺口。

Preflight 可用 `TRASHBOT_REMOTE_CLOUD_BACKUP_ARTIFACT` 验证本地 artifact：

```bash
PYTHONPATH=src/ros2_trashbot_behavior \
TRASHBOT_REMOTE_CLOUD_STATE_BACKEND=sqlite \
TRASHBOT_REMOTE_CLOUD_BACKUP_ARTIFACT=/tmp/trashbot_remote_cloud_relay_backup.json \
python3 -m ros2_trashbot_behavior.remote_cloud_relay --preflight
```

如果 artifact schema、version 或 checksum 不匹配，preflight 必须返回 phone-safe blocked reason；如果 artifact 有效，preflight 只允许声明本地 backup/restore drill artifact 通过，不能声明生产 backup policy、真实 DR 或生产 DB/queue ready。

Network recovery drill CLI 示例：

```bash
PYTHONPATH=src/ros2_trashbot_behavior \
python3 -m ros2_trashbot_behavior.remote_cloud_relay \
  --network-recovery-drill \
  --state-backend sqlite \
  --state-path /tmp/trashbot_network_recovery.sqlite \
  --write-network-recovery-artifact /tmp/trashbot_network_recovery_drill.json
```

Preflight 可用 `TRASHBOT_REMOTE_CLOUD_NETWORK_RECOVERY_ARTIFACT` 验证本地 artifact：

```bash
PYTHONPATH=src/ros2_trashbot_behavior \
TRASHBOT_REMOTE_CLOUD_NETWORK_RECOVERY_ARTIFACT=/tmp/trashbot_network_recovery_drill.json \
python3 -m ros2_trashbot_behavior.remote_cloud_relay --preflight
```

有效 artifact 会新增 `network_recovery_drill=pass`，设置
`software_proof_ready=true`，并把本地证据边界提升到
`software_proof_docker_network_recovery_drill`。缺失 artifact 是 warning；
schema、version、checksum、必需 steps、cursor invariant、stale 或
phone-safe 校验失败是 blocked。无论 artifact 是否通过，preflight 都必须
继续保留真实云、真实 4G/SIM、HTTPS/TLS 公网入口、生产 DB/queue、多实例
一致性、真实 OSS/CDN 流量、生产 incident recovery、Nav2/fixed-route、
WAVE ROVER/HIL 和 delivery success 等未证明项。

proof 边界：

- bearer auth：缺 token 或错 token 返回 `auth_failed`。
- command：`id` 作为幂等键，支持 `collect`、`confirm_dropoff`、`cancel`，过期 command 不作为 next 返回。
- status：缺失返回 `status_missing`，过期返回 `status_stale`。
- ACK：终态只允许 `acked`、`failed`、`ignored`。
- persistence：commands/status/acks 可写入本地 JSON state file，使用临时文件加 `os.replace` 做原子替换；也可通过 `TRASHBOT_REMOTE_CLOUD_STATE_BACKEND=sqlite` 写入单机 SQLite proof store，并在 relay restart 后恢复。
- backup/restore：SQLite proof store 可生成带 schema/version/metadata/checksum 的 JSON artifact，并恢复到新的 SQLite proof state；该恢复只验证 command/status/ack envelope 和 ACK cursor 语义，不证明生产备份策略或真实灾备。
- phone-safe errors：覆盖 `auth_failed`、`bad_request`、`not_found`、`status_missing`、`status_stale`、`malformed_json`。
- Docker deploy smoke：`scripts/remote_cloud_relay_docker_smoke.sh` 覆盖 compose build、容器启动、health/readiness、post status、enqueue command、robot-style next command、post ack、read ack/status、停止容器并输出相关日志。

未完成项：

- 真实云部署、域名、公网入口、HTTPS/TLS、防火墙实配。
- 真实 4G/SIM、弱网/断网 carrier 测试。
- 生产数据库、队列、多实例一致性、备份和灾备。
- OSS/CDN 上传、STS、受限 AK、生命周期和 rotate。
- Nav2/fixed-route、WAVE ROVER、真实硬件运动、HIL 和用户实机验收。
