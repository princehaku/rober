# cloud-relay/ — 4G 云中转 / 公网部署单位

本目录是 `ros_rbs` 的 **公网云中转服务部署单位**：把 onboard 上车机器人和手机用户在公网上撮合起来。部署入口独立于 onboard/mobile/pc-tools；当前协议实现仍复用 onboard behavior 包中的纯 Python relay 模块，避免复制第二套 `trashbot.remote.v1` 语义。

> **当前状态（本轮）**：`cloud-relay/src/ros2_trashbot_cloud_relay/` 已提供 Python runtime 入口；Dockerfile / `docker-compose.yml` / `scripts/docker_smoke.sh` 均从该入口启动。镜像构建 **context 为仓库根 `..`**，只为复用 onboard behavior 里的唯一 relay 协议实现；证据边界仍是 Docker/local software proof。
>
> **当前增量**：relay HTTP handler 可同源托管 `mobile/web/` dependency-free PWA 静态壳，并提供免 bearer 的 phone-safe `GET /api/status` / `GET /api/diagnostics` fail-closed adapter。证据边界是 `software_proof_docker_cloud_hosted_mobile_web_gate`，只证明 Docker/local cloud-relay shell route、静态路径围栏和同源只读状态/诊断 adapter；不证明真实公网 HTTPS/TLS、真实 4G/SIM、真实手机设备/browser、production app、PWA install prompt、OSS/CDN live traffic、production DB/queue、Nav2/fixed-route、WAVE ROVER、HIL 或真实送达。

## 用途（What lives here）

- **HTTP 反向桥**：
  - 接收 onboard 的 `remote_bridge` POST 上来的机器人状态（`/robots/{robot_id}/status`）
  - 持久化 commands、status、ack（file-backed JSON 或 sqlite；生产仍需替换为真实 DB / queue）
  - 把命令分发给 onboard（`/robots/{robot_id}/commands/next`）
  - 接收 onboard 的 ack 回执（`/robots/{robot_id}/commands/{id}/ack`）
- **phone-safe JSON API**：
  - 向手机 PWA 暴露 `trashbot.phone_readiness.v1`、`trashbot.command_safety.v1`、`trashbot.phone_offline_resume_readiness.v1` 等 schema 的 JSON
  - **schema 字段、值域、`evidence_boundary` 由本目录单一维护**，onboard / mobile 不发明
- **健康检查 & 生产 preflight**：
  - `/healthz` / `/readyz` 容器存活与就绪探针
  - `/preflightz` 生产就绪检查（HTTPS、OSS 凭证、DR backup 等还没就位时会显式 503）
  - `trashbot.cloud_deployment_readiness` artifact，汇总公网入口、TLS、healthcheck、凭证、state backend、生产 DB/queue、OSS/CDN、4G/SIM 和 runbook/smoke 缺口；证据边界固定为 `software_proof_docker_cloud_deployment_readiness_gate`
  - `trashbot.cloud_external_probe_bundle` artifact，用 base URL 探测 `/healthz`、`/readyz`、`/preflightz` 并只记录 endpoint path、HTTP 状态、JSON 合同和脱敏状态；证据边界固定为 `software_proof_docker_cloud_external_probe_bundle_gate`，`production_ready=false` 必须保持
  - `trashbot.cloud_public_ingress_tls_gate` artifact，区分完全缺公网入口/TLS/反向代理配置与配置包存在但缺真实外部 HTTPS、DNS、反向代理、防火墙实证；证据边界固定为 `software_proof_docker_cloud_public_ingress_tls_gate`，`overall_status=blocked` 必须保持
  - `trashbot.cloud_db_queue_config_gate` artifact，区分完全缺生产 DB/queue 配置包与配置包存在但缺真实连接、多实例、一致性、备份和灾备实证；证据边界固定为 `software_proof_docker_cloud_db_queue_config_gate`，`production_ready=false` 和 `overall_status=blocked` 必须保持
  - `trashbot.cloud_db_queue_external_probe_bundle` artifact，记录 DB/queue connectivity、migration、worker、多实例、ordering、transaction isolation、backup/recovery 外部探测入口的枚举状态；证据边界固定为 `software_proof_docker_cloud_db_queue_external_probe_gate`，只证明 schema/checksum/redaction/preflight consumption
  - `trashbot.oss_cdn_live_probe` artifact，复用 OSS/CDN manifest 输入，只记录 endpoint path、object key hash、HTTP 状态和脱敏摘要；证据边界固定为 `software_proof_docker_oss_cdn_live_probe_gate`，`production_ready=false`、`overall_status=blocked`、`live_probe_complete=false` 必须保持
  - `trashbot.external_evidence_intake` artifact，为未来公网入口/TLS、OSS/CDN、production DB/queue、4G/SIM 真实外部材料提供安全收件 gate；证据边界固定为 `software_proof_docker_external_evidence_intake_gate`，只证明 schema/checksum/redaction/preflight consumption，`production_ready=false`、`overall_status=blocked`、`external_evidence_complete=false` 必须保持

## 子目录

| 目录 | 用途 | 现状 |
| --- | --- | --- |
| `cloud-relay/src/` | Python runtime 入口 | `ros2_trashbot_cloud_relay.remote_cloud_relay` 包装 onboard relay 实现，保持协议单一来源 |
| `cloud-relay/docker/` | Dockerfile | 复制 cloud-relay 入口、onboard 纯 Python relay 模块和 `mobile/web/` 静态壳，不拉入 ROS2/Humble 构建链路 |
| `cloud-relay/test/` | 单测 + 集成测试 | 后续可迁入 cloud relay 专属测试；当前仍复用 onboard compatibility fence |
| `cloud-relay/scripts/` | 部署脚本 | `cloud-relay/scripts/docker_smoke.sh` 以 cloud-relay runtime 为主入口 |
| `cloud-relay/docker-compose.yml` | compose 入口（公网 8088 端口） | 在 `cloud-relay/` 下执行，使用仓库根 context 复用唯一协议实现 |

## 部署目标（Deployment target）

- **公网 VM**：4C8G Linux（Ubuntu 22.04 / Debian 12 等），独立 IP，TCP 8088 入口（未来反向代理加 TLS）。
- **依赖**：Docker 24+、Docker Compose 2.x。**不依赖 ROS2**（Python 3.12 slim 镜像即可）。
- **持久化**：当前 file-backed JSON / sqlite 仅作 deploy proof；生产仍需替换为真实 DB（PostgreSQL / MySQL）+ 消息队列（Redis / RabbitMQ / NATS）。

## 标准入口

构建上下文为仓库根，请在 **`cloud-relay/`** 下执行 compose（相对路径 `dockerfile: cloud-relay/docker/Dockerfile` 已写死）：

```bash
cd cloud-relay
TRASHBOT_REMOTE_CLOUD_BEARER_TOKEN=dev-placeholder docker compose up -d
sleep 3
curl http://127.0.0.1:8088/healthz
curl http://127.0.0.1:8088/readyz
docker compose down
```

完整 smoke（含 backup-restore drill / preflight assert / sqlite 状态恢复）：

```bash
cd cloud-relay
TRASHBOT_REMOTE_CLOUD_BEARER_TOKEN=dev-smoke-token bash scripts/docker_smoke.sh
```

## Cloud-hosted mobile web shell

`remote_cloud_relay` 现在在同一个 HTTP server 上服务 `mobile/web/` 静态壳：

```text
GET /                         -> mobile/web/index.html
GET /index.html               -> mobile/web/index.html
GET /app.js                   -> mobile/web/app.js
GET /styles.css               -> mobile/web/styles.css
GET /manifest.webmanifest     -> mobile/web/manifest.webmanifest
GET /service-worker.js        -> mobile/web/service-worker.js
GET /offline.html             -> mobile/web/offline.html
GET /icon-192.svg             -> mobile/web/icon-192.svg
GET /icon-512.svg             -> mobile/web/icon-512.svg
```

API/probe/control routes stay ahead of static serving: `/api/*`, `/robots/*`, `/healthz`, `/readyz`, `/preflightz`, command routes, and ACK routes are never served by static fallback. Unknown static names and traversal attempts return phone-safe JSON 404 without local absolute paths. The handler accepts optional `TRASHBOT_REMOTE_CLOUD_MOBILE_WEB_ROOT` for a mounted asset directory; otherwise it discovers the repo-local `mobile/web/` layout.

The same handler also exposes `GET /api/status` and `GET /api/diagnostics` for the hosted shell without bearer auth. These endpoints select `TRASHBOT_REMOTE_CLOUD_DEFAULT_ROBOT_ID` or `trashbot-001`, read the latest relay `/robots/{robot_id}/status` when available, then return a phone-safe copy plus a blocked `cloud_hosted_mobile_web_gate` summary. Missing or stale status returns `overall_status=blocked` / `state=status_missing|status_stale` instead of 404. Primary controls always fail closed: `can_collect=false`, `can_confirm_dropoff=false`, `can_cancel=false`, `phone_readiness.can_continue=false`, and `command_safety.actions.*.enabled=false`.

This shell and the same-origin static APIs do not require bearer auth because they are read-only phone surfaces. Any command/status/ACK robot contract path still uses the existing `trashbot.remote.v1` contract and bearer gate. The static APIs must not expose raw ROS topics, `/cmd_vel`, serial devices, WAVE ROVER parameters, credentials, DB/queue URLs, local state paths, tracebacks, or complete artifacts.

生成 cloud deployment readiness artifact：

```bash
cd cloud-relay
PYTHONPATH=src:../onboard/src/ros2_trashbot_behavior \
TRASHBOT_REMOTE_CLOUD_BEARER_TOKEN=dev-smoke-token \
python3 -m ros2_trashbot_cloud_relay.remote_cloud_relay \
  --write-cloud-deployment-readiness-artifact /tmp/trashbot_cloud_deployment_readiness.json
```

该 artifact 的 `schema=trashbot.cloud_deployment_readiness`、`schema_version=1`、`evidence_boundary=software_proof_docker_cloud_deployment_readiness_gate`。它必须保持 `production_ready=false`、`overall_status=blocked`，并列出 `not_proven`、`safe_summary`、`retry_hint`。本地占位配置不得被 Docker smoke 或 CLI preflight 判成生产 ready。

生成 cloud external probe bundle artifact：

```bash
cd cloud-relay
PYTHONPATH=src:../onboard/src/ros2_trashbot_behavior \
python3 -m ros2_trashbot_cloud_relay.remote_cloud_relay \
  --write-cloud-external-probe-artifact /tmp/trashbot_cloud_external_probe.json \
  --cloud-external-probe-base-url http://127.0.0.1:8088
```

Preflight 消费该 artifact：

```bash
cd cloud-relay
PYTHONPATH=src:../onboard/src/ros2_trashbot_behavior \
TRASHBOT_REMOTE_CLOUD_EXTERNAL_PROBE_ARTIFACT=/tmp/trashbot_cloud_external_probe.json \
python3 -m ros2_trashbot_cloud_relay.remote_cloud_relay --preflight
```

该 bundle 的 `schema=trashbot.cloud_external_probe_bundle`、`schema_version=1`、`evidence_boundary=software_proof_docker_cloud_external_probe_bundle_gate`。它只证明本地或未来公网 base URL 的 `/healthz`、`/readyz`、`/preflightz` 合同可被探测并生成 phone-safe artifact；本轮 Docker smoke 只跑本地 relay，因此必须继续输出 `production_ready=false`、`overall_status=blocked` 和真实云、HTTPS/TLS、公网入口、4G/SIM、OSS/CDN live traffic、production DB/queue、HIL、真实送达等 `not_proven`。

生成 cloud public ingress/TLS gate artifact：

```bash
cd cloud-relay
PYTHONPATH=src:../onboard/src/ros2_trashbot_behavior \
TRASHBOT_REMOTE_CLOUD_PUBLIC_BASE_URL=https://relay.example.invalid \
TRASHBOT_REMOTE_CLOUD_TLS_MODE=reverse_proxy \
TRASHBOT_REMOTE_CLOUD_PUBLIC_INGRESS=public_https \
TRASHBOT_REMOTE_CLOUD_REVERSE_PROXY_CONFIG=present \
TRASHBOT_REMOTE_CLOUD_FIREWALL_CONFIG=present \
python3 -m ros2_trashbot_cloud_relay.remote_cloud_relay \
  --write-cloud-public-ingress-tls-artifact /tmp/trashbot_cloud_public_ingress_tls.json
```

Preflight 消费该 artifact：

```bash
cd cloud-relay
PYTHONPATH=src:../onboard/src/ros2_trashbot_behavior \
TRASHBOT_REMOTE_CLOUD_PUBLIC_INGRESS_TLS_ARTIFACT=/tmp/trashbot_cloud_public_ingress_tls.json \
python3 -m ros2_trashbot_cloud_relay.remote_cloud_relay --preflight
```

该 gate 的 `state` 只允许 `missing_public_ingress_tls_config` 或 `public_ingress_tls_config_present_not_externally_proven`。前者表示还没有形成配置包；后者表示 HTTPS 公网入口、TLS mode、反向代理和防火墙配置形态存在，但仍没有真实外部 HTTPS/TLS、公网入口、DNS、反向代理转发或防火墙实证。两种状态都必须保持 `production_ready=false`、`overall_status=blocked`，并且不得输出真实 URL、Authorization、Bearer、证书私钥、私钥路径、DB/queue URL、本地 state path、串口、WAVE ROVER 参数、ROS topic 或 `/cmd_vel`。

生成 cloud DB/queue config gate artifact：

```bash
cd cloud-relay
PYTHONPATH=src:../onboard/src/ros2_trashbot_behavior \
TRASHBOT_REMOTE_CLOUD_DB_CONFIG=present \
TRASHBOT_REMOTE_CLOUD_QUEUE_CONFIG=present \
TRASHBOT_REMOTE_CLOUD_DB_MIGRATION_CONFIG=present \
TRASHBOT_REMOTE_CLOUD_QUEUE_WORKER_CONFIG=present \
python3 -m ros2_trashbot_cloud_relay.remote_cloud_relay \
  --write-cloud-db-queue-config-artifact /tmp/trashbot_cloud_db_queue_config.json
```

Preflight 消费该 artifact：

```bash
cd cloud-relay
PYTHONPATH=src:../onboard/src/ros2_trashbot_behavior \
TRASHBOT_REMOTE_CLOUD_DB_QUEUE_CONFIG_ARTIFACT=/tmp/trashbot_cloud_db_queue_config.json \
python3 -m ros2_trashbot_cloud_relay.remote_cloud_relay --preflight
```

该 gate 的 `state` 只允许 `missing_cloud_db_queue_config` 或 `cloud_db_queue_config_present_not_externally_proven`。前者表示生产 DB/queue 配置包仍缺失；后者表示配置包形态存在，但仍没有真实连接探测、多实例一致性、生产队列顺序、事务隔离、备份策略或灾备实证。两种状态都必须保持 `production_ready=false`、`overall_status=blocked`，并且不得输出 DB/queue endpoint、credential-bearing endpoint、Authorization、Bearer、token、root password、本地 state path、串口、WAVE ROVER 参数、ROS topic 或 `/cmd_vel`。

生成 cloud DB/queue external probe bundle artifact：

```bash
cd cloud-relay
PYTHONPATH=src:../onboard/src/ros2_trashbot_behavior \
python3 -m ros2_trashbot_cloud_relay.remote_cloud_relay \
  --write-cloud-db-queue-external-probe-artifact /tmp/trashbot_cloud_db_queue_external_probe.json
```

Preflight 消费该 artifact：

```bash
cd cloud-relay
PYTHONPATH=src:../onboard/src/ros2_trashbot_behavior \
TRASHBOT_REMOTE_CLOUD_DB_QUEUE_EXTERNAL_PROBE_ARTIFACT=/tmp/trashbot_cloud_db_queue_external_probe.json \
python3 -m ros2_trashbot_cloud_relay.remote_cloud_relay --preflight
```

该 bundle 的 `schema=trashbot.cloud_db_queue_external_probe_bundle`、`schema_version=1`、`evidence_boundary=software_proof_docker_cloud_db_queue_external_probe_gate`。它覆盖 DB connectivity、queue connectivity、migration check、worker check、multi-instance consistency、ordering、transaction isolation、backup/recovery 的外部探测入口状态；当前 Docker-only 默认只能是 `not_run` 或 `not_externally_proven` 一类 blocked 状态。有效 artifact 也必须保持 `production_ready=false`、`overall_status=blocked` 和 `external_probe_complete=false`，只说明 schema、checksum、redaction 和 preflight consumption 已可验证；不得输出 DB/queue endpoint、credential-bearing endpoint、Authorization、Bearer、token、root password、本地 state path、串口、WAVE ROVER 参数、ROS topic 或 `/cmd_vel`。

生成 OSS/CDN live probe artifact：

```bash
cd cloud-relay
PYTHONPATH=src:../onboard/src/ros2_trashbot_behavior \
python3 -m ros2_trashbot_cloud_relay.remote_cloud_relay \
  --write-oss-cdn-live-probe-artifact /tmp/trashbot_oss_cdn_live_probe.json \
  --oss-cdn-manifest-artifact /tmp/trashbot_oss_cdn_manifest.json
```

Preflight 消费该 artifact：

```bash
cd cloud-relay
PYTHONPATH=src:../onboard/src/ros2_trashbot_behavior \
TRASHBOT_REMOTE_CLOUD_OSS_CDN_LIVE_PROBE_ARTIFACT=/tmp/trashbot_oss_cdn_live_probe.json \
python3 -m ros2_trashbot_cloud_relay.remote_cloud_relay --preflight
```

该 artifact 的 `schema=trashbot.oss_cdn_live_probe`、`schema_version=1`、`evidence_boundary=software_proof_docker_oss_cdn_live_probe_gate`。它复用 manifest artifact 的对象引用，但结果只允许保存 endpoint path、object key hash、HTTP status、reachable、method、latency、redaction 状态和 not_proven；不得保存完整 CDN URL、完整 object key、Authorization、Bearer、token、OSS secret、AK/SK、credential-bearing URL、本地路径、响应体、串口、WAVE ROVER 参数、ROS topic 或 `/cmd_vel`。即使本地或 mock HTTP probe 返回 2xx，也必须保持 `production_ready=false`、`overall_status=blocked` 和 `live_probe_complete=false`，不能声明真实 OSS/CDN live traffic。

生成 external evidence intake artifact：

```bash
cd cloud-relay
PYTHONPATH=src:../onboard/src/ros2_trashbot_behavior \
python3 -m ros2_trashbot_cloud_relay.remote_cloud_relay \
  --write-external-evidence-intake-artifact /tmp/trashbot_external_evidence_intake.json
```

Preflight 消费该 artifact：

```bash
cd cloud-relay
PYTHONPATH=src:../onboard/src/ros2_trashbot_behavior \
TRASHBOT_REMOTE_CLOUD_EXTERNAL_EVIDENCE_INTAKE_ARTIFACT=/tmp/trashbot_external_evidence_intake.json \
python3 -m ros2_trashbot_cloud_relay.remote_cloud_relay --preflight
```

该 artifact 的 `schema=trashbot.external_evidence_intake`、`schema_version=1`、`evidence_boundary=software_proof_docker_external_evidence_intake_gate`。它覆盖 `public_ingress_tls`、`oss_cdn`、`production_db_queue`、`four_g_sim` 四类未来外部材料状态，但当前只保存枚举状态、材料时间、固定脱敏摘要、`safe_summary`、`retry_hint`、`not_proven`、`redaction_status` 和 checksum。有效 artifact 也必须保持 `production_ready=false`、`overall_status=blocked`、`external_evidence_complete=false`，只说明外部材料 intake schema、checksum、脱敏规则和 preflight consumption 可验证；不得输出 URL、credential-bearing endpoint、Authorization、Bearer、token、OSS AK/SK、DB/queue URL、本地路径、响应体、traceback、串口、WAVE ROVER 参数、ROS topic 或 `/cmd_vel`。

## 运行时契约（Runtime contracts）

- **与 `onboard/` 的契约**：
  - 接收：`POST /robots/{robot_id}/status`、`POST /robots/{robot_id}/commands/{id}/ack`
  - 提供：`GET /robots/{robot_id}/commands/next?last_ack_id=...`
  - 鉴权：`Authorization: Bearer {TRASHBOT_REMOTE_CLOUD_BEARER_TOKEN}`
- **与 `mobile/` 的契约**：
  - 提供：phone-safe JSON API（无 Bearer / 无 robot_id 暴露 / 无 `/cmd_vel` / 无 `ttyUSB` 等字段）
  - schema：`trashbot.phone_readiness.v1`、`trashbot.command_safety.v1`、`trashbot.phone_offline_resume_readiness.v1` 等版本号化字段
- **与 `pc-tools/evidence/`**：phone_browser_acceptance_gate 等工具可消费 cloud-relay 的 phone-safe JSON 做交叉验证；只读、不回写。

## 后续工作

- 后续若要彻底缩小 Docker build context，需先由 robot/full-stack 共同确认 `remote_bridge`、operator fallback 与测试导入路径，再决定是否把实现模块迁入 `cloud-relay/src/`。
- `operator_gateway` 仍属于 onboard local fallback；本轮没有把本地调试 UI 合并进 cloud relay server。
- 可选：在实现完全迁移后启用 `cloud-relay/.dockerignore` 进一步减小镜像构建发送量。

## Agent 工作纪律

- 修改本目录前必读 `AGENTS.md`、`OKR.md`、对应 sprint 文档。
- **不允许变更已存在的 phone-safe schema 字段、值域、`evidence_boundary`**；如确需新增，新建 `.v2` 版本，保留 `.v1` 兼容。
- 不允许向 phone-safe 输出泄漏 `Authorization` / `Bearer` / `/cmd_vel` / `ttyUSB` / `baudrate` / `WAVE ROVER` / 本地文件路径等敏感字段。
- Deployment readiness / preflight 输出不得泄漏 bearer token、Authorization header、OSS secret、AK/SK、root password、DB URL、queue URL、credential-bearing URL、raw state path、串口、baudrate、WAVE ROVER 参数、ROS topic、`/cmd_vel` 或 traceback。
- Cloud external probe bundle 不得写入 base URL、Authorization header、响应体、credential-bearing URL、本地 state path、串口、baudrate、WAVE ROVER 参数、ROS topic 或 `/cmd_vel`；只允许 endpoint path、HTTP status、JSON 合同状态和脱敏状态进入 artifact。
- Cloud public ingress/TLS gate 不得写入真实 URL、Authorization header、Bearer token、证书私钥、证书私钥路径、root password、OSS AK/SK、DB/queue URL、本地 state path、串口、baudrate、WAVE ROVER 参数、ROS topic 或 `/cmd_vel`；只允许枚举化配置状态和外部实证缺口进入 artifact。
- Cloud DB/queue config gate 不得写入 DB/queue endpoint、credential-bearing endpoint、Authorization header、Bearer token、root password、本地 state path、串口、baudrate、WAVE ROVER 参数、ROS topic 或 `/cmd_vel`；只允许枚举化配置状态和外部实证缺口进入 artifact。
- Cloud DB/queue external probe bundle 不得写入 DB/queue endpoint、credential-bearing endpoint、Authorization header、Bearer token、root password、本地 state path、串口、baudrate、WAVE ROVER 参数、ROS topic 或 `/cmd_vel`；当前只允许枚举化 probe 状态、脱敏状态、not_proven 和恢复建议进入 artifact。
- OSS/CDN live probe artifact 不得写入完整 CDN URL、完整 object key、Authorization header、Bearer token、OSS secret、AK/SK、credential-bearing URL、本地路径、响应体、串口、baudrate、WAVE ROVER 参数、ROS topic 或 `/cmd_vel`；当前只允许 endpoint path、object key hash、HTTP 状态、脱敏状态和恢复建议进入 artifact。
- External evidence intake artifact 不得写入 URL、credential-bearing endpoint、Authorization header、Bearer token、OSS AK/SK、DB/queue URL、本地路径、响应体、traceback、串口、baudrate、WAVE ROVER 参数、ROS topic 或 `/cmd_vel`；当前只允许四类外部材料的枚举状态、固定脱敏摘要、not_proven 和恢复建议进入 artifact。
- 修改 Docker / compose / scripts / Dockerfile 时必须更新本 README 的"标准入口"段落。
- 中文注释比例 >20%，注释解释"为什么"而非"做什么"。

## 路线图（Roadmap）

| 阶段 | 工作 |
| --- | --- |
| 本 sprint P2A（已完成） | Dockerfile / compose / scripts 搬到本目录；context 改 `..`；过渡注释 |
| 本 sprint P5（当前） | 新增 `ros2_trashbot_cloud_relay` runtime；Docker/smoke 从 cloud-relay 入口启动，协议实现继续复用 onboard |
| 下一个 sprint | TLS / 反向代理、生产 DB（PostgreSQL）、多实例一致性、灾备 backup 策略 |
| 后续 | 真实 4G / 真实公网 / 真实 OSS / CDN 凭证、监控、告警 |
