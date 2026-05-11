# Sprint 2026.05.12_05-06 Remote Cloud Service Docker Proof - PRD

## 状态

- 阶段：prd
- 创建时间：2026-05-12 05:00 Asia/Shanghai
- Product Owner：`product-okr-owner`
- 主责 Engineer：`full-stack-software-engineer`
- 支撑 Engineer：`robot-software-engineer`
- 证据边界：`software_proof_docker_only`

## 用户价值和产品北极星

普通用户只用手机发起送垃圾任务时，真实产品不能要求手机和小车在同一 WiFi，也不能要求用户理解 ROS2、串口或 `/cmd_vel`。O6 的产品北极星是：手机走云端 API，小车只做 outbound polling，云中转只承担轻量 JSON 控制面，未来图片和大对象走 OSS/CDN。

上一轮 04-05 已把 local/mock control-plane 的 auth、readiness、degradation 和 cursor safety 做到可测；本轮要把它从 operator_gateway 调试入口中拆出，形成独立 HTTP cloud relay service 的 Docker-only software proof。

## 问题背景和证据

1. `OKR.md` 最新快照显示 O6 约 19%，是当前最低完成度；剩余缺口集中在真实云部署、HTTPS/TLS、公网入口、真实 4G/SIM、弱网恢复、生产鉴权/rotate、STS/OSS/CDN 和生产持久化队列。
2. 04-05 final 写明 local/mock bearer auth gate、remote_readiness/degradation、cursor safety 已完成，但证据边界仍是 `software_proof_docker_only` / local mock cloud。
3. 04-05 tech-done 给出可靠围栏：operator targeted tests `Ran 66 tests ... OK`，remote bridge tests `Ran 23 tests ... OK`，integration smoke `Ran 89 tests ... OK`。
4. `docs/product/remote_4g_mvp.md` 已定义 `trashbot.remote.v1` command/status/ack、bearer auth、cursor/restart boundary、ACK 与 status 边界，以及 current limits。
5. `OKR.md` 已引用 `docs/product/cloud_4g_infrastructure.md`，但该文件当前不存在，导致 O6 服务端基线、网络方向、容量边界和真实云 vs Docker proof 边界没有产品事实源。
6. 本机只有 Docker，没有真实硬件；继续追 O1/O2/O3 HIL 会重复 blocked，且不能增加真实 4G 或 WAVE ROVER 证据。

## OKR 映射

| Objective / KR | PRD 要求 |
| --- | --- |
| O6 KR1 commands/status/ack | 服务必须按 `trashbot.remote.v1` 实现 `POST /robots/{robot_id}/commands`、`GET /robots/{robot_id}/commands/next`、`POST/GET status`、`POST/GET ack`。 |
| O6 KR2 服务端基线 | `docs/product/cloud_4g_infrastructure.md` 必须说明 4C 8G 无 GPU、公网入口、网络方向、防火墙、容量边界、运维与产品流量分离，以及本轮未部署真实云。 |
| O6 KR5 凭证管理 | bearer token 从环境变量或服务启动配置注入；`.env` 不入仓库；错误和持久化文件不得包含真实 token、Authorization header 或 credential-bearing URL。 |
| O6 KR6 graceful degradation | 服务端错误必须 phone-safe；robot client 对 auth failed、cloud unreachable、malformed response 仍保持上一轮不推进 cursor、不执行不可信 command 的语义。 |
| O5 KR1/KR5/KR7 支撑 | API 响应必须提供普通用户可理解的 `safe_phone_copy` / retry hints，正式手机 UI 后续可直接消费。 |

## 产品需求

### P0 独立 HTTP cloud relay service

- 服务是独立模块，可由本机 Python 或 Docker 启动，不依赖 ROS2 node、operator_gateway 进程或真实 cloud account。
- 服务监听本机端口，提供 JSON HTTP API；默认仅用于 Docker/local proof。
- 服务名和入口由工程决定，但必须能在 `python3 -m ...` 或测试 helper 中启动。

### P0 API contract

必须实现以下路径，并与 `docs/product/remote_4g_mvp.md` 语义一致：

```text
POST /robots/{robot_id}/commands
GET  /robots/{robot_id}/commands/next?last_ack_id=<id>
POST /robots/{robot_id}/status
GET  /robots/{robot_id}/status
POST /robots/{robot_id}/commands/{command_id}/ack
GET  /robots/{robot_id}/commands/{command_id}/ack
```

命令 contract：

- `protocol_version` 必须为 `trashbot.remote.v1`。
- `id` 是 idempotency key；重复提交同一 id 返回已有 command，不创建第二个任务。
- 支持 `collect`、`confirm_dropoff`、`cancel`。
- `collect` 必须包含非空 `payload.target`。
- 过期 command 不应作为下一条可执行命令返回。

ACK contract：

- 支持 `acked`、`failed`、`ignored`。
- ACK 表示 robot bridge 对 command envelope 的处理状态，不代表真实送达完成。
- 手机端必须继续读 status 才能展示 `completed`、`needs_human_help` 或失败状态。

### P0 bearer auth

- 受保护路径必须支持 `Authorization: Bearer <token>`。
- 缺失 token 或错误 token 返回 phone-safe auth failure。
- 无论成功或失败，响应、日志测试断言和 state file 都不得包含 bearer token、Authorization header、credential-bearing URL、串口、baudrate、WAVE ROVER 参数、`/cmd_vel` 或 ROS topic 名。

### P0 file-backed persistence

- commands/status/acks 必须写入本地 state file。
- 服务重启或重新实例化 store 后，同一 robot 的 command/status/ack 可读。
- 写入必须尽量原子化，避免半写 JSON 导致重启后 state 不可恢复。
- 本轮只证明单机 file persistence，不承诺生产数据库、跨实例一致性或灾备。

### P0 phone-safe errors and degradation

服务端必须把错误归一成手机可显示语义：

- auth failed：提示检查授权或登录状态。
- bad request / malformed JSON：提示请求格式异常，不回显 raw traceback。
- command not found / ack not found：提示等待小车处理或重新发起。
- status missing：提示机器人尚未上报状态。
- status stale：提示机器人状态过期，建议等待或检查网络。

### P0 robot client compatibility

- `RemoteCloudClient` 或 `remote_bridge` targeted smoke 必须能对独立服务完成 `post_status -> get_next_command -> post_ack -> get_ack/status` 的闭环。
- 失败语义必须保持上一轮边界：auth failed、malformed response、cloud unreachable 不执行不可信 command、不推进 terminal cursor、不伪造 ACK 成功。

### P1 产品文档

- 创建 `docs/product/cloud_4g_infrastructure.md`。
- 文档必须写明：
  - 目标真实云基线：4C 8G 无 GPU、公网入口、HTTPS/TLS、SSH 管理边界、防火墙、容量边界。
  - 网络方向：phone -> cloud API；robot -> cloud outbound polling；不接受 inbound 直连小车。
  - OSS/CDN 目标：bucket `bytegallop`、region `oss-cn-hangzhou`、前缀 `rober/<robot_id>/<date>/<task_id>/`、CDN base URL `https://cdn.bytegallop.com/rober/`。
  - 凭证边界：环境变量注入、`.env` 不入仓库、主 AK 不直放小车、rotate 后续流程。
  - 本轮只完成 Docker/local independent relay proof，不完成真实云、真实 4G、OSS/CDN 或 HIL。

## 不做什么

- 不部署真实云服务器，不申请域名，不配置 HTTPS/TLS、公网入口、防火墙或生产 SSH。
- 不接真实 4G/SIM，不做 carrier NAT、弱网、断网恢复实测。
- 不实现 OSS/CDN 上传、STS、受限 AK、图片流转或 CDN 回源验证。
- 不改硬件、串口、WAVE ROVER、ESP32、Orange Pi、Nav2、fixed-route、vision 或 HIL。
- 不把 ACK 当作送达完成，不把 Docker/local proof 写成 real cloud proof。

## 优先级和验收口径

| 优先级 | 验收 |
| --- | --- |
| P0 服务可启动 | targeted test 或 smoke 启动独立 HTTP service 并完成请求。 |
| P0 contract | API path、payload、command idempotency、ack/status 语义测试通过。 |
| P0 auth | 缺 token/错 token/正确 token 三类测试通过，敏感字段不泄露。 |
| P0 persistence | 重启 store 后 command/status/ack 仍可读，坏 JSON 有保守错误或恢复策略。 |
| P0 phone safety | 错误响应不包含 raw traceback、token、ROS topic、串口或硬件参数。 |
| P0 robot compatibility | `RemoteCloudClient`/`remote_bridge` 兼容新服务的 targeted smoke 通过。 |
| P1 docs | `cloud_4g_infrastructure.md` 与 `remote_4g_mvp.md` 的边界一致。 |

## 对应责任 Engineer

- `full-stack-software-engineer`：P0 独立服务、服务端 tests、file persistence、auth、phone-safe errors、`docs/product/cloud_4g_infrastructure.md`。
- `robot-software-engineer`：P0 robot client compatibility smoke，必要时最小修正 `RemoteCloudClient` 与服务响应 shape 的兼容性。
- `product-okr-owner`：本轮需求、验收口径、后续 Product Acceptance 和 OKR 证据边界。

## 风险、阻塞和证据链缺口

- 本轮完成后最多支持 O6 从 local/mock proof 向 independent Docker relay proof 前进；不能声明真实云、真实 4G、OSS/CDN 或 HIL 完成。
- file-backed store 不是生产数据库；如果后续需要多实例或高并发，必须进入新的云部署 sprint。
- cloud relay 只处理控制面 JSON；大对象仍需后续 OSS/CDN sprint。
- 本轮仍不解决 O1/O2/O3 实景缺口；若后续有硬件环境，应回到真实 HIL 与同一 `evidence_ref` route replay。
