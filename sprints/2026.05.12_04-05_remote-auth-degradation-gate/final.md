# Sprint 2026.05.12_04-05 Remote Auth Degradation Gate - Final

## 状态

- 阶段：final
- 更新时间：2026-05-12 04:55 Asia/Shanghai
- Product Owner：`product-okr-owner`
- 收口结论：通过 Product Acceptance
- 证据边界：Docker/local `software_proof_docker_only`

## 用户价值和产品北极星

本轮让远程手机控制链路在进入真实云前更接近可产品化：用户未来能看到“需要重新授权、云不可达、状态过期、等待 ACK、响应异常”等可理解状态，而不是 raw exception、ROS topic、硬件参数或虚假的成功。

北极星仍是普通用户只用手机，通过 4G 云中转控制小车送垃圾；本轮只是补齐控制面安全与降级 contract，不是实机送达或真实 4G 验收。

## OKR 映射

| Objective | Final 处理 |
| --- | --- |
| O6 4G 云中转 + OSS/CDN | 从约 16% 保守提升到约 19%，理由是 local/mock auth gate、degradation、cursor safety、敏感字段过滤已有 targeted + smoke software proof。 |
| O5 手机体验与量产边界 | 从约 31% 保守提升到约 32%，理由是 `remote_readiness` 和 `safe_phone_copy` 支撑未来正式手机状态页。 |
| O1/HIL、真实云、真实 4G | 不提升；本轮没有真实硬件、真实云、SIM/4G、弱网、OSS/CDN 或实机送达证据。 |

## KR 拆解或更新

- O6 KR1：command/status/ack 契约新增 bearer auth gate 和 failure classification 证据。
- O6 KR5：凭证与敏感字段过滤证据补齐到 phone/status/diagnostics/mock persisted state。
- O6 KR6：cloud unreachable/auth failed/malformed response 的 graceful degradation 和 cursor safety 通过软件围栏验证。
- O5 KR1/KR5/KR7：手机可读 auth/degradation/retry/safe copy contract 已可供正式 UI 消费，但尚未完成正式 UI 或用户实机验收。

## 本轮核心抓手

`remote_auth_degradation_gate` 已完成：在 local/mock cloud 和 robot outbound bridge 之间固定 bearer auth、phone-safe readiness、failure degradation、ACK/cursor 安全边界。

## 做什么 / 不做什么

完成：

- 更新 `docs/product/remote_4g_mvp.md`：记录 bearer auth gate、`remote_readiness` 字段、remote bridge cursor/degradation 语义和软件证明边界。
- 更新 `docs/interfaces/ros_contracts.md`：记录 `remote_readiness` 字段、auth/degradation states、remote bridge failure/cursor contract。
- 创建 `side2side_check.md` 与 `final.md`。
- 保守更新 `OKR.md` 当前快照。

未做：

- 未改产品代码、测试代码、硬件、Nav2、vision 或 launch 参数。
- 未做真实云部署、HTTPS/TLS、公网入口、真实 4G/SIM、弱网、生产鉴权 rotate、OSS/CDN。
- 未做 WAVE ROVER、真实 UART、Nav2/fixed-route、相机或 HIL。

## 优先级和验收口径

| 优先级 | 结果 |
| --- | --- |
| P0 bearer auth gate | 通过 Task A targeted tests。 |
| P0 readiness/degradation phone-safe 字段 | 通过 Task A targeted tests，Product docs 已同步。 |
| P0 remote bridge failure/cursor safety | 通过 Task B targeted tests。 |
| P0 集成 smoke | Task C `Ran 89 tests in 25.691s OK`。 |
| P1 文档与 OKR 收口 | 本轮 Product Acceptance 已同步。 |

## 对应责任 Engineer

- `full-stack-software-engineer`：完成 local/mock bearer auth gate、readiness/degradation、敏感字段过滤和 mobile flow 文档。
- `robot-software-engineer`：完成 `RemoteCloudError` 分类、remote bridge failure/cursor safety 和 integration smoke。
- `product-okr-owner`：完成共享 docs、side-by-side check、final、OKR 保守更新。

## 验证结果

工程证据来自 `tech-done.md`：

```text
Task A targeted operator tests:
Ran 66 tests in 14.664s
OK

Task B remote bridge tests:
Ran 23 tests in 10.987s
OK

Task C integration smoke:
Ran 89 tests in 25.691s
OK
```

本次 Product Acceptance 额外运行 scoped 文档 diff check，结果见最终回复。

## 风险、阻塞和需要补齐的证据链

- O6 下一步仍需要真实云最小部署、HTTPS/TLS、公网入口、生产 token 管理/rotate、真实 4G/SIM 与弱网恢复验证。
- OSS/CDN 图片链路、STS 临时凭证或受限 AK、生产云端持久化队列仍未落地。
- 手机正式 UI 和普通用户实机验收仍未完成；本轮只提供可消费状态 contract。
- O1/HIL、真实 UART、WAVE ROVER feedback、Nav2/fixed-route 和真实送达证据仍缺，不得在后续文档中把本轮软件证明升级为实机完成。

