# Sprint 2026.05.12_06-07 Remote Cloud Entry Docker Deploy - Final

## 状态

- 阶段：final
- 更新时间：2026-05-12 07:00 Asia/Shanghai
- Product Owner：`product-okr-owner`
- 主责 Engineer：`full-stack-software-engineer`
- 支撑 Engineer：`robot-software-engineer`
- 结论：收口完成
- 证据边界：`software_proof_docker_deploy`

## 用户价值和产品北极星

本轮把 4G 云中转控制面从 independent local relay proof 推进到 Docker deploy proof。对最终用户的价值是间接但必要的：未来手机端不需要依赖开发者手动运行 Python 服务，而是可以依赖一个容器化、可检查、可鉴权、可持久化、可与 robot polling client 对接的云入口雏形。

产品北极星仍是普通手机用户通过 4G 云中转完成 trash delivery；本轮没有完成正式手机 UI，也没有完成真实云或实机送达。

## OKR 映射

| Objective | 本轮结论 |
| --- | --- |
| O6 4G 云中转 + OSS/CDN | 主线推进。Docker deploy proof、health/readiness、compose env、container smoke、robot compatibility fence 成立，建议从约 23% 保守上调到约 27%。 |
| O5 手机体验与量产边界 | 只获得 phone-safe readiness/status 支撑，不建议上调；仍约 33%。 |
| O1 硬件协议可信底盘 | 不提升。无 WAVE ROVER、UART、反馈或 HIL。 |
| O2 可恢复送垃圾任务闭环 | 不提升。ACK 不等于 delivery result，无真实任务闭环。 |
| O3 导航与固定路线 | 不提升。无 Nav2/fixed-route 实跑。 |
| O4 感知模块产品化 | 不涉及，不提升。 |

## KR 拆解或更新

- O6 KR1：`trashbot.remote.v1` commands/status/ack 在容器入口 smoke 中跑通。
- O6 KR2：Dockerfile、compose、env、health/readiness 让云入口具备 production-shaped proof，但仍不是真实公网云。
- O6 KR5：`.env.example` 占位和 phone-safe redaction contract 继续守住凭证边界。
- O6 KR6：readiness/status 支撑未来手机和运维区分服务未就绪、鉴权失败、状态缺失和存储问题；真实 4G 弱网恢复仍缺。
- O5 KR5/KR7：只记录 API/readiness 支撑，不升级正式手机 UI 完成度。

## 本轮核心抓手

核心抓手 `remote_cloud_entry_docker_deploy_proof` 已完成：

- 可通过 Docker/compose 启动 independent relay。
- 配置通过 env 注入，`.env.example` 只提供占位。
- `/healthz`、`/readyz` 可区分服务存活和控制面 readiness。
- Docker smoke 覆盖 status、command、next、ack 和 readback。
- Robot client compatibility 通过 targeted fence 复核。

## 做什么 / 不做什么

已完成：

- Docker deploy proof。
- health/readiness endpoint。
- command/status/ack container smoke。
- robot client compatibility validation。
- `docs/product/cloud_4g_infrastructure.md` 与 `docs/product/remote_4g_mvp.md` 同步。
- `tech-done.md`、`side2side_check.md`、`final.md` sprint 收口。

未完成且不得计入本轮完成：

- 真实云主机、公网 HTTPS/TLS、域名、防火墙。
- 真实 4G/SIM、弱网恢复、carrier proof。
- OSS/CDN、STS、受限 AK、CDN 回源、生命周期和 rotate。
- 生产 DB/queue、多实例一致性、备份、审计和 provisioning。
- 正式手机 UI、美观验收、普通用户实机验收。
- Nav2/fixed-route、WAVE ROVER、真实送达、HIL。

## 优先级和验收口径

| 验收口径 | 结果 |
| --- | --- |
| P0 容器入口 | 通过。Docker smoke build/start/readiness/cleanup passed。 |
| P0 readiness | 通过。`/readyz` 覆盖 protocol、credential gate、state store、phone-safe failure。 |
| P0 command/status/ack smoke | 通过。容器入口完成最小控制面闭环。 |
| P0 robot client compatibility | 通过。`Ran 31 tests in 15.223s OK`，py_compile 和 Docker smoke exit 0。 |
| P0 安全边界 | 通过本轮软件围栏。真实 production secret provisioning 尚未完成。 |
| P1 文档同步 | 通过。相关 docs/product 已同步 Docker proof 和真实云缺口。 |

## 对应责任 Engineer

- `full-stack-software-engineer`：完成 Docker deploy proof、health/readiness、container smoke、docs sync 和 Task A/B `tech-done.md`。
- `robot-software-engineer`：完成 Task C robot compatibility fence，确认 ACK、cursor 和 conservative failure 语义不退化。
- `product-okr-owner`：完成 side-by-side acceptance、final、OKR 保守更新。

## 验证结果摘要

```text
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py
Ran 8 tests in 4.167s
OK
```

```text
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest \
  src/ros2_trashbot_behavior/test/test_remote_bridge_protocol.py \
  src/ros2_trashbot_behavior/test/test_remote_bridge.py
Ran 31 tests in 15.223s
OK
```

```text
TRASHBOT_REMOTE_CLOUD_PUBLISHED_PORT=18088 \
TRASHBOT_REMOTE_CLOUD_BEARER_TOKEN=dev-smoke-token \
scripts/remote_cloud_relay_docker_smoke.sh
build/start/readiness/healthz/status/command/next/ack/readback/cleanup passed
```

其他围栏：

- `remote_cloud_relay.py` py_compile exit 0。
- `remote_bridge_protocol.py` 与 `remote_bridge.py` py_compile exit 0。
- Task A/B scoped diff check exit 0。
- Task C scoped diff check exit 0。

已记录非阻断现象：

- Python 3.13 robot unittest 有一次 `ResourceWarning`，测试最终 `OK`。
- Docker readiness 首次 retry 出现 connection reset，随后 readiness 成功。

## 风险、阻塞和证据链缺口

- 证据边界严格限定为 `software_proof_docker_deploy`。
- 该证据不等于真实云、HTTPS/TLS、公网、4G/SIM、OSS/CDN、正式手机 UI、Nav2/fixed-route、WAVE ROVER 或 HIL。
- 下一轮 O6 若继续推进，应优先选择真实云最小入口：公网 HTTPS/TLS、防火墙、环境注入、生产 secret provisioning、健康检查和最小运维日志。
- 若产品优先级回到上车闭环，则仍应按 O1/O2/O3 顺序补真实 HIL、fixed-route/Nav2 和同一 evidence_ref 复盘。

## OKR 更新

- O6：建议从约 23% 上调到约 27%，理由是 Docker deploy proof、health/readiness、compose env 和 robot compatibility 已形成可复现软件证据。
- O5：保持约 33%，只记录 phone-safe readiness/status 支撑。
- O1/O2/O3/O4：保持不变。
