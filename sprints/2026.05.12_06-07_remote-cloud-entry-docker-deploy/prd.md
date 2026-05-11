# Sprint 2026.05.12_06-07 Remote Cloud Entry Docker Deploy - PRD

## 状态

- 阶段：prd
- 创建时间：2026-05-12 Asia/Shanghai
- Product Owner：`product-okr-owner`
- 主责 Engineer：`full-stack-software-engineer`
- 支撑 Engineer：`robot-software-engineer`
- 证据边界：目标为 `software_proof_docker_deploy`

## 用户价值和产品北极星

本轮要让 O6 从“本机 independent relay service proof”继续前进到“可作为云入口雏形部署的 Docker proof”。这对普通手机用户的间接价值是：未来手机入口可以依赖一个可启动、可检查、可鉴权、可持久化、可对接 robot polling client 的云控制面，而不是依赖开发者手动运行 Python module。

北极星仍是普通用户只用手机，通过 4G 云中转控制小车完成 trash delivery。当前 PRD 不把云入口 proof 包装成真实云，也不把 status/ACK 包装成真实送达结果。

## 背景和证据

1. `OKR.md` 当前快照：
   - O6 约 23%，是当前低完成度目标之一。
   - O5 约 33%，但主要缺正式手机 UI 和普通用户实机验收。
   - O1/O2/O3 仍受真实硬件、Nav2、fixed-route 和 HIL 限制，本机 Docker 环境无法补齐。
2. `sprints/2026.05.12_05-06_remote-cloud-service-docker-proof/final.md`：
   - Next Recommendations 明确“先做 O6 最小真实云入口 proof”。
   - 05-06 只完成 independent Docker/local relay service，不等于真实云、HTTPS、4G、OSS/CDN。
3. `sprints/2026.05.12_05-06_remote-cloud-service-docker-proof/tech-done.md`：
   - 已有 `remote_cloud_relay.py`。
   - 已有 file-backed persistence、bearer auth、phone-safe errors、robot client compatibility。
   - 证据边界仍是 `software_proof_docker_only`。
4. `docs/product/cloud_4g_infrastructure.md`：
   - 真实云目标包括公网 HTTPS、TLS、防火墙、生产持久化、OSS/CDN、运维边界。
   - 当前 Docker/local proof 默认建议监听 `127.0.0.1`。

## OKR 映射

| KR | 本轮产品诉求 |
| --- | --- |
| O6 KR1 云中转服务端最小契约 | 继续保持 `trashbot.remote.v1` commands/status/ack，并证明容器化入口不破坏契约。 |
| O6 KR2 云服务端基线 | 增加 Docker deploy proof，明确它距离真实公网 HTTPS、防火墙和生产部署的边界。 |
| O6 KR5 凭证管理 contract | 用 env/`.env.example` 占位和错误脱敏守住 bearer token/credential 不入仓库。 |
| O6 KR6 graceful degradation | readiness/phone-safe errors 让手机和运维能区分服务未就绪、状态缺失、鉴权失败和存储问题。 |
| O5 KR5/KR7 支撑项 | 只提供 phone-safe readiness/status 文案和 API 支撑，不做正式 UI。 |

## KR 拆解或更新

### P0 - Docker entry proof

- relay service 可以通过 Docker image 或 compose 启动。
- 容器启动参数由环境变量或 compose 显式传入，不要求开发者记住长命令。
- 默认监听仍应偏安全，开发本机 proof 可绑定 `127.0.0.1` 或 compose 明确暴露端口。

### P0 - Health/readiness proof

- 提供 `/healthz`、`/readyz` 或等价检查。
- readiness 至少能覆盖 bearer token 配置、state store 可写、服务版本/contract 和 phone-safe error 输出。
- 如果实现上不新增 endpoint，也必须提供等价 CLI/container smoke，并在文档里说明原因。

### P0 - Contract and robot compatibility

- 保持 API：

```text
POST /robots/{robot_id}/commands
GET  /robots/{robot_id}/commands/next?last_ack_id=<id>
POST /robots/{robot_id}/status
GET  /robots/{robot_id}/status
POST /robots/{robot_id}/commands/{command_id}/ack
GET  /robots/{robot_id}/commands/{command_id}/ack
```

- container smoke 必须覆盖 status post/get、command enqueue/next、ack post/get。
- robot client compatibility smoke 必须覆盖 `post_status -> get_next_command -> post_ack`。

### P0 - Security and phone-safe boundary

- `.env.example` 只能有占位，不提交真实 bearer token、OSS AK/SK、root password、credential-bearing URL。
- 错误响应和 state file 不回显 Authorization header、bearer token、串口、baudrate、WAVE ROVER 参数、ROS topic 或底层速度入口。
- 手机端可见错误继续使用 `auth_failed`、`bad_request`、`not_found`、`status_missing`、`status_stale`、`malformed_json` 等可解释语义。

### P1 - Product docs sync

- 更新 `docs/product/cloud_4g_infrastructure.md` 或相关产品文档，补 Docker deploy proof 的运行方式、验证命令和边界。
- sprint `tech-done.md` 必须记录实际命令、输出摘要、失败定位和剩余风险。

## 做什么 / 不做什么

做：

- Docker/compose/env/readiness 的最小可部署形态。
- 有限 host/container smoke。
- robot client compatibility smoke。
- phone-safe status/readiness 语义和文档同步。

不做：

- 不购买或配置真实云服务器。
- 不配置域名、公网 HTTPS、TLS 证书、防火墙实配。
- 不接 4G/SIM，不跑弱网 carrier 测试。
- 不实现 OSS/CDN 上传、STS、CDN 回源或生命周期。
- 不做正式手机 UI。
- 不补 HIL、Nav2/fixed-route 或 WAVE ROVER 实机证据。

## 优先级和验收口径

| 优先级 | 用户可感知价值 | 验收口径 |
| --- | --- | --- |
| P0 Docker startup | 云入口服务不再依赖手工 Python 命令 | 容器可启动，日志明确 host/port/state path/contract，不泄露密钥。 |
| P0 Readiness | 手机和运维未来能判断服务是否可用 | readiness/health 或等价 smoke 能返回可解释状态。 |
| P0 Contract smoke | 手机/机器人控制面契约稳定 | 容器内外完成 command/status/ack 最小闭环。 |
| P0 Robot compatibility | 机器人 outbound polling 兼容容器入口 | `RemoteCloudClient` compatibility smoke 通过。 |
| P0 Credential boundary | 凭证不进入仓库、不进入错误响应 | scoped checks 和 tests/smoke 证明敏感字段不回显。 |
| P1 Docs | 后续团队知道 Docker proof 与真实云差距 | docs/product 和 sprint tech-done 写清边界。 |

## 对应责任 Engineer

- 主责：`full-stack-software-engineer`
  - Dockerfile/compose/env/readiness/container smoke。
  - 产品文档同步。
  - 当前 sprint `tech-done.md`。
- 支撑：`robot-software-engineer`
  - robot client compatibility smoke。
  - 确认 ACK 仍不是 delivery result，remote bridge 保守语义不退化。
- Product Acceptance：`product-okr-owner`
  - 检查 O6/O5/O1-O3 边界。
  - 维护 `side2side_check.md`、`final.md` 和必要 OKR 更新。

## 风险、阻塞和需要补齐的证据链

- Docker proof 若失败，不能降级成只写文档；必须记录失败命令、原因和最小复现。
- 通过 container smoke 也不等于真实云公网、HTTPS/TLS、防火墙、4G/SIM、OSS/CDN 或生产数据库。
- O5 只能获得 readiness/status API 支撑；正式手机 UI 不在本轮验收范围。
- O1/O2/O3 不因本轮 Docker cloud entry proof 提升。
- 若修改代码，必须满足中文技术注释规范，并同步 `docs/` 相关文档。
