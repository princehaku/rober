# Sprint 2026.05.12_05-06 Remote Cloud Service Docker Proof - Pre Start

## 状态

- 阶段：pre_start
- 创建时间：2026-05-12 05:00 Asia/Shanghai
- Product Owner：`product-okr-owner`
- 主责 Engineer：`full-stack-software-engineer`
- 支撑 Engineer：`robot-software-engineer`
- 证据边界：`software_proof_docker_only`
- 迭代目标：把上一轮 operator_gateway 内嵌 local/mock cloud 推进为可独立运行的 Docker-only HTTP cloud relay service proof。

## 用户价值和产品北极星

北极星仍是普通用户只用手机，通过 4G 云中转控制小车送垃圾，不要求手机和小车处于同一 WiFi。本轮的用户价值是把“远程控制面”从本地调试入口里拆出来：手机、云中转、小车 outbound polling 可以按 `trashbot.remote.v1` 在本机或 Docker 中形成独立服务 proof，后续才能接真实云、HTTPS/TLS、4G/SIM、OSS/CDN。

本轮不是 HIL、真实送达或真实 4G 验收；它只证明独立 cloud relay 服务的控制面语义、鉴权、持久化、降级文案和 robot client 兼容性。

## OKR 映射

| Objective | 当前证据 | 本轮处理 |
| --- | --- | --- |
| O6 4G 云中转 + OSS/CDN，约 19% | `OKR.md` 最新快照显示 O6 仍停在 local mock auth/degradation/cursor safety `software_proof_docker_only`，真实云、HTTPS/TLS、公网入口、真实 4G/SIM、OSS/CDN 均缺失。 | 优先推进最低完成度 O6，把 local/mock 内嵌 cloud 升级为独立 Docker-only cloud relay service proof。 |
| O5 手机体验与量产边界，约 32% | 04-05 final 写明 `remote_readiness` 和 `safe_phone_copy` 支撑未来正式手机状态页，但没有正式 UI 或用户实机验收。 | 只要求 cloud relay 返回 phone-safe errors/readiness，服务正式手机 UI 后续接入。 |
| O1/O2/O3 硬件/任务/路线 | OKR 快照仍缺真实 WAVE ROVER HIL、Nav2/fixed-route 实跑、同一 `evidence_ref` 上车证据。 | 本机只有 Docker，继续 HIL 会重复 blocked；本轮不推进硬件/HIL。 |

## 证据输入

- `OKR.md`：O6 是当前最低完成度，约 19%；剩余关键缺口包括真实云部署、HTTPS/TLS、公网入口、真实 4G/SIM、弱网/断网恢复、生产鉴权/rotate、STS/OSS/CDN 图片链路和生产持久化队列。
- `sprints/2026.05.12_04-05_remote-auth-degradation-gate/final.md`：上一轮已完成 local/mock bearer auth gate、remote_readiness/degradation、cursor safety，明确边界仍是 `software_proof_docker_only` / local mock cloud。
- `sprints/2026.05.12_04-05_remote-auth-degradation-gate/tech-done.md`：Task A targeted operator tests `Ran 66 tests ... OK`，Task B remote bridge tests `Ran 23 tests ... OK`，Task C integration smoke `Ran 89 tests ... OK`；这些是本轮复用语义的可靠起点。
- `docs/product/remote_4g_mvp.md`：已有 `trashbot.remote.v1` command/status/ack、bearer auth gate、cursor/restart boundary、remote_readiness、ACK 与 status 边界；当前限制明确没有真实云账号、SIM、生产身份、HTTPS/TLS 或公网入口。
- `docs/product/cloud_4g_infrastructure.md`：`OKR.md` 已引用该文件，但当前文件不存在，是 O6 产品化边界缺口。
- 反复出现的证据边界：local/mock 和 Docker proof 可以证明控制面语义，不能证明真实云、真实 4G、OSS/CDN、Nav2/fixed-route、WAVE ROVER 或 HIL。

## KR 拆解或更新

| KR | 本轮目标 | 非目标 |
| --- | --- | --- |
| O6 KR1 commands/status/ack | 独立 HTTP cloud relay 服务实现 `trashbot.remote.v1` commands/status/ack，保留 idempotency key、bearer auth、outbound polling 语义。 | 不暴露 `/cmd_vel`，不接受 inbound 直连小车，不做真实云部署。 |
| O6 KR2 云服务端基线 | 补齐 `docs/product/cloud_4g_infrastructure.md`，写清 4C 8G 无 GPU、公网入口、网络方向、防火墙、容量边界和本轮 Docker proof 边界。 | 不采购或配置真实服务器，不宣称 HTTPS/TLS/公网已完成。 |
| O6 KR5 凭证管理 | 独立服务以环境变量注入 bearer token，测试证明敏感字段不回显、不落入 phone payload。 | 不实现生产账号体系、token rotate 或 CI secret 管理。 |
| O6 KR6 graceful degradation | file-backed persistence、服务重启后 command/status/ack 保留；phone-safe error 区分 auth failed、not found、bad request、stale/missing status。 | 不做真实 4G 弱网压测，不做 OSS/CDN 写入失败恢复。 |

## 本轮核心抓手

核心抓手是 `remote_cloud_relay_service_docker_proof`：在本机/Docker 可启动的独立 HTTP 服务中复用上一轮已验证的 remote contract，把 operator_gateway 内嵌 mock cloud 的语义迁移成可替换真实云的服务边界。

## 做什么 / 不做什么

做：

- 创建独立 HTTP cloud relay 服务，服务端可在本机或 Docker 中运行。
- 复用 `trashbot.remote.v1` command/status/ack 语义、bearer auth、idempotent command submit、phone-safe errors。
- 使用 file-backed persistence 保存 commands/status/acks，验证重启后状态不丢。
- 更新 `docs/product/cloud_4g_infrastructure.md`，明确真实云与本轮 Docker proof 的边界。
- 保持 `remote_bridge` client 兼容新服务，并用 targeted tests/smoke 围栏验证。

不做：

- 不做真实云部署、域名、HTTPS/TLS、公网入口、防火墙实配或生产运维。
- 不做真实 4G/SIM、弱网/断网 carrier 测试。
- 不做 OSS/CDN 真实链路、STS 临时凭证、图片上传或 CDN 回源。
- 不做 WAVE ROVER、串口、Nav2/fixed-route、相机、HIL 或真实送达。
- 不扩大到正式手机 UI 重做；只提供 phone-safe API contract。

## 优先级和验收口径

| 优先级 | 验收口径 |
| --- | --- |
| P0 独立服务 | 本机/Docker 中可启动独立 HTTP relay，不依赖 ROS2 runtime 或 operator_gateway 进程。 |
| P0 contract 兼容 | commands/status/ack 路径、payload、ACK 终态、cursor 语义与 `docs/product/remote_4g_mvp.md` 保持一致。 |
| P0 bearer auth | 缺 token/错 token 拒绝；正确 token 可 submit/poll/status/ack；错误响应不泄露 Authorization 或 token。 |
| P0 file-backed persistence | command/status/ack 写入本地 state file；重启服务后可读取同一 robot 状态和 ACK。 |
| P0 phone-safe errors | auth failed、bad request、not found、status missing/stale、malformed JSON 都返回普通用户可读错误，不出现 raw traceback、ROS topic、硬件参数或密钥。 |
| P0 robot compatibility | `RemoteCloudClient` 或 `remote_bridge` targeted smoke 能对新服务完成 status -> command poll -> ack 流程。 |
| P1 产品边界文档 | `docs/product/cloud_4g_infrastructure.md` 明确真实云目标、本轮 Docker proof、未完成真实云/4G/OSS/CDN/HIL。 |

## 对应责任 Engineer

| Owner | 责任 | 可改范围 |
| --- | --- | --- |
| `full-stack-software-engineer` | 独立 HTTP cloud relay 服务、file persistence、bearer auth、phone-safe errors、产品文档和服务端 tests。 | `src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py`、`src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py`、`docs/product/cloud_4g_infrastructure.md`、必要时 `docs/product/remote_4g_mvp.md`。 |
| `robot-software-engineer` | robot client 兼容性和集成 smoke，必要时只对 `remote_bridge_protocol.py` 做兼容修正。 | `src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_bridge_protocol.py`、`src/ros2_trashbot_behavior/test/test_remote_bridge_protocol.py`、`src/ros2_trashbot_behavior/test/test_remote_bridge.py`、当前 sprint `tech-done.md`。 |
| `product-okr-owner` | 本轮计划、验收口径、后续 side-by-side/final、OKR 证据边界收口。 | `sprints/2026.05.12_05-06_remote-cloud-service-docker-proof/`、后续 acceptance 阶段可按范围更新 `OKR.md` 和产品 docs。 |

## 风险、阻塞和需要补齐的证据链

- 真实云、HTTPS/TLS、公网入口、真实 4G/SIM、生产 token rotate、OSS/CDN 仍是后续证据链；本轮不能升级为 real-cloud proof。
- 独立服务若复用过多 operator_gateway 代码，可能继续停留在 local mock 形态；验收必须确认它是单独进程/模块。
- file-backed persistence 只证明单机 proof，不证明数据库、并发队列、跨实例一致性或灾备。
- ACK 仍只代表 robot bridge 处理 command envelope，不代表垃圾送达结果；status 才是继续展示任务状态的 surface。
- 本轮不是硬件任务；任何提到串口、WAVE ROVER、ESP32、Orange Pi 引脚/电压/波特率的实现都应视为范围漂移。

## 需要创建或更新的 sprint 文档

- 已创建：`pre_start.md`
- 本阶段继续创建：`prd.md`
- 本阶段继续创建：`tech-plan.md`
- 工程执行后必须更新：`tech-done.md`
- Product Acceptance 后必须更新：`side2side_check.md`
- 阶段收口后必须更新：`final.md`
