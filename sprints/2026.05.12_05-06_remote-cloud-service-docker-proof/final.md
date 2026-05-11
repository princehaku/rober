# Sprint 2026.05.12_05-06 Remote Cloud Service Docker Proof - Final

## 状态

- 阶段：final
- 更新时间：2026-05-12 06:50 Asia/Shanghai
- Product Owner：`product-okr-owner`
- 收口结论：通过 Product Acceptance
- 证据边界：`software_proof_docker_only`

## 用户价值和产品北极星

本轮把远程控制面从本地 operator fallback 继续推向真实产品架构：手机未来访问云端 API，小车继续 outbound polling，云中转只承担轻量 JSON command/status/ack。对普通用户的价值是后续可以在不懂 ROS2、串口、`/cmd_vel` 或硬件参数的情况下，通过手机看到可理解的授权、状态、ACK 和降级提示。

北极星仍是普通用户只用手机，通过 4G 云中转控制小车完成 trash delivery。本轮不是 delivery close loop；它是 O6 的 independent Docker/local relay service software proof。

## OKR 映射

| Objective | Final 处理 |
| --- | --- |
| O6 4G 云中转 + OSS/CDN | 从约 19% 保守提升到约 23%。理由是 independent Docker/local relay service、file-backed persistence、bearer auth、phone-safe errors、client compatibility 和 `docs/product/cloud_4g_infrastructure.md` 已有 software proof。 |
| O5 手机体验与量产边界 | 从约 32% 保守提升到约 33%。理由仅限 phone-safe errors、status_missing/status_stale、retry hint 和 future phone UI API contract；不声明正式手机 UI。 |
| O1/O2/O3/O4 | 不提升。本轮没有真实硬件、真实云、4G/SIM、OSS/CDN、Nav2/fixed-route、相机、WAVE ROVER 或 HIL。 |

## KR 拆解或更新

- O6 KR1：`trashbot.remote.v1` commands/status/ack 已从 local/mock fallback 推进到 independent relay service proof。
- O6 KR2：`docs/product/cloud_4g_infrastructure.md` 已补齐 4C 8G 无 GPU、公网 HTTPS 目标、网络方向、防火墙、容量、OSS/CDN 和 Docker/local proof 边界。
- O6 KR5：bearer token 环境变量注入、错误响应/state file 敏感字段不回显的本地软件证据已补齐。
- O6 KR6：file-backed persistence、status_missing/status_stale、phone-safe errors、auth failed/not found/bad request/malformed JSON 的 graceful degradation 已有软件围栏。
- O5 KR1/KR5/KR7：本轮只补 future phone UI 可消费的 API contract 和普通用户可读错误，不等于正式手机 UI、美观验收或普通用户实机验收。

## 本轮核心抓手

核心抓手 `remote_cloud_relay_service_docker_proof` 已完成：独立 HTTP relay service module、file-backed store、bearer auth、phone-safe JSON errors、robot client compatibility 和 O6 云基础设施产品文档边界已经形成闭环。

## 做什么 / 不做什么

完成：

- 新增 independent Docker/local HTTP relay service proof。
- 保持 `trashbot.remote.v1` command/status/ack 语义和 robot outbound polling 兼容。
- 完成 file-backed persistence、bearer auth、phone-safe errors 和敏感字段过滤软件围栏。
- 补齐 `docs/product/cloud_4g_infrastructure.md`，并同步 `docs/product/remote_4g_mvp.md` 的 independent relay 边界。
- 创建 `side2side_check.md` 和 `final.md`，保守更新 `OKR.md`。

未做：

- 未部署真实云、域名、公网入口、HTTPS/TLS 或防火墙。
- 未接真实 4G/SIM、弱网、断网、生产 token rotate、生产 DB。
- 未实现 OSS/CDN 上传、STS、受限 AK、CDN 回源或生命周期。
- 未做正式手机 UI、普通用户实机验收。
- 未做 Nav2/fixed-route、WAVE ROVER、真实运动、真实送达或 HIL。

## 优先级和验收口径

| 优先级 | 结果 |
| --- | --- |
| P0 独立服务 | 通过；`remote_cloud_relay.py` 可作为独立 HTTP service module 启动。 |
| P0 contract 兼容 | 通过；commands/status/ack API 与 `trashbot.remote.v1` 对齐。 |
| P0 bearer auth | 通过；缺 token/错 token/正确 token 和 auth_failed 映射已被 targeted tests 覆盖。 |
| P0 file-backed persistence | 通过；commands/status/acks 可写入本地 state file 并重读。 |
| P0 phone-safe errors | 通过；错误响应避免 raw traceback、ROS topic、硬件参数和密钥。 |
| P0 robot compatibility | 通过；`RemoteCloudClient.post_status -> get_next_command -> post_ack` 对 independent relay 兼容。 |
| P1 产品边界文档 | 通过；`cloud_4g_infrastructure.md` 已补真实云和 Docker proof 边界。 |

## 对应责任 Engineer

- `full-stack-software-engineer`：完成 independent relay service、service tests、file persistence、auth、phone-safe errors、`cloud_4g_infrastructure.md` 和 `remote_4g_mvp.md` 同步。
- `robot-software-engineer`：完成 robot client compatibility tests 和合并集成围栏。
- `product-okr-owner`：完成 Product Acceptance、side-by-side check、final 和 OKR 保守更新。

## 验证结果

工程验证来自 `tech-done.md`：

```text
Task A targeted relay tests:
Ran 6 tests in 2.593s
OK

Task B remote bridge compatibility tests:
Ran 31 tests in 15.249s
OK

Task C merged integration fence:
Ran 37 tests in 17.884s
OK
```

```text
py_compile:
通过，无输出。

scoped git diff --check:
通过，无输出。
```

本次 Product Acceptance 额外运行 scoped 文档/OKR diff check，结果见最终回复。

## Next Recommendations

1. 先做 O6 最小真实云入口 proof。
   - 证据依据：当前 OKR 快照 O6 仍约 23%；05-06 只完成 independent Docker/local relay；`cloud_4g_infrastructure.md` 明确缺真实云、HTTPS/TLS、公网入口、防火墙实配和生产持久化。
   - Owner：`full-stack-software-engineer`。

2. 再做 O6 OSS/CDN 最小对象链路 proof。
   - 证据依据：04-05 final 和 05-06 tech-done 都只覆盖 JSON 控制面；`cloud_4g_infrastructure.md` 只有 bucket、region、prefix 和 CDN base URL 的目标边界，没有 STS、上传、回源或生命周期证据。
   - Owner：`full-stack-software-engineer`。

3. O5 只在正式手机 UI 接入后再继续提升。
   - 证据依据：本轮 O5 只因为 phone-safe errors 和 future phone UI API contract 小幅 +1pp；没有正式手机 UI、美观验收或普通用户实机验收。
   - Owner：`full-stack-software-engineer`。

4. O1/O2/O3 必须回到真实上车证据链。
   - 证据依据：当前 OKR 快照、04-05 final、05-06 tech-done 都没有真实串口、WAVE ROVER feedback、Nav2/fixed-route 实跑、同一 `evidence_ref` 复盘或 HIL。
   - Owner：`hardware-engineer`、`autonomy-engineer`、`robot-software-engineer`。

## 风险、阻塞和需要补齐的证据链

- Product Acceptance 仍是 `software_proof_docker_only`，不等于真实云、4G、OSS/CDN、Nav2/fixed-route、WAVE ROVER 或 HIL。
- 真实云仍缺域名、公网入口、HTTPS/TLS、防火墙、生产 token rotate、生产 DB/queue、多实例一致性和灾备。
- 真实 4G/SIM、弱网/断网恢复、OSS/CDN、STS、CDN 回源和生命周期都未验证。
- ACK 仍只是 command envelope 处理状态，不代表小车完成导航、投放、返回或真实送达。
- 手机端仍未完成正式 UI、美观验收和普通用户实机验收。
