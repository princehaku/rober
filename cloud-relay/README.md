# cloud-relay/ — 4G 云中转 / 公网部署单位

本目录是 `ros_rbs` 的 **公网云中转服务部署单位**：把 onboard 上车机器人和手机用户在公网上撮合起来。**独立于 onboard、独立于 mobile，独立于 pc-tools**，可在任意 4C8G 公网 VM 上 `docker compose up` 起来。

> **当前状态（本轮）**：Dockerfile / `docker-compose.yml` / `scripts/docker_smoke.sh` 已在本目录；镜像构建 **context 为仓库根 `..`**，Dockerfile `COPY onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/...`。Phase 5（operator_gateway 与 relay 源码迁入 `cloud-relay/src/`、缩小 build context）尚未实施。

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

## 子目录

| 目录 | 用途 | 现状 |
| --- | --- | --- |
| `cloud-relay/src/` | Python 源码（`remote_cloud_relay.py` + `operator_gateway*.py`） | **占位**；当前实现仍在 `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/`，由 Dockerfile COPY 进镜像 |
| `cloud-relay/docker/` | Dockerfile | `COPY onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior` → `/app/ros2_trashbot_behavior` |
| `cloud-relay/test/` | 单测 + 集成测试 | 占位（P5 把 `test_operator_gateway_*.py` + `test_remote_cloud_relay.py` 搬入） |
| `cloud-relay/scripts/` | 部署脚本 | `cloud-relay/scripts/docker_smoke.sh`（P2A 已搬入） |
| `cloud-relay/docker-compose.yml` | compose 入口（公网 8088 端口） | P2A 已搬入并改造 context |

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

## 运行时契约（Runtime contracts）

- **与 `onboard/` 的契约**：
  - 接收：`POST /robots/{robot_id}/status`、`POST /robots/{robot_id}/commands/{id}/ack`
  - 提供：`GET /robots/{robot_id}/commands/next?last_ack_id=...`
  - 鉴权：`Authorization: Bearer {TRASHBOT_REMOTE_CLOUD_BEARER_TOKEN}`
- **与 `mobile/` 的契约**：
  - 提供：phone-safe JSON API（无 Bearer / 无 robot_id 暴露 / 无 `/cmd_vel` / 无 `ttyUSB` 等字段）
  - schema：`trashbot.phone_readiness.v1`、`trashbot.command_safety.v1`、`trashbot.phone_offline_resume_readiness.v1` 等版本号化字段
- **与 `pc-tools/evidence/`**：phone_browser_acceptance_gate 等工具可消费 cloud-relay 的 phone-safe JSON 做交叉验证；只读、不回写。

## 后续工作（P5，未在本轮完成）

- 将 `remote_cloud_relay.py` 与 `operator_gateway*.py` 迁入 `cloud-relay/src/`，按需缩小 Docker build context。
- 可选：启用 `cloud-relay/.dockerignore` 进一步减小镜像构建发送量。

## Agent 工作纪律

- 修改本目录前必读 `AGENTS.md`、`OKR.md`、对应 sprint 文档。
- **不允许变更已存在的 phone-safe schema 字段、值域、`evidence_boundary`**；如确需新增，新建 `.v2` 版本，保留 `.v1` 兼容。
- 不允许向 phone-safe 输出泄漏 `Authorization` / `Bearer` / `/cmd_vel` / `ttyUSB` / `baudrate` / `WAVE ROVER` / 本地文件路径等敏感字段。
- 修改 Docker / compose / scripts / Dockerfile 时必须更新本 README 的"标准入口"段落。
- 中文注释比例 >20%，注释解释"为什么"而非"做什么"。

## 路线图（Roadmap）

| 阶段 | 工作 |
| --- | --- |
| 本 sprint P2A（已完成） | Dockerfile / compose / scripts 搬到本目录；context 改 `..`；过渡注释 |
| 本 sprint P5 | 源码搬入 `cloud-relay/src/`、operator_gateway 集成到同一 HTTP server、context 切回 `./`、`.dockerignore` 激活 |
| 下一个 sprint | TLS / 反向代理、生产 DB（PostgreSQL）、多实例一致性、灾备 backup 策略 |
| 后续 | 真实 4G / 真实公网 / 真实 OSS / CDN 凭证、监控、告警 |
