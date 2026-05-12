# Sprint 2026.05.12_12-13 Remote OSS/CDN Phone Consumption Gate - Side By Side Check

## 状态

- 阶段：side2side_check
- Product Owner：`product-okr-owner`
- 主责 Engineer：`full-stack-software-engineer`
- 兼容性围栏：`robot-software-engineer`
- 验收结论：通过 Product acceptance，可收口为 `software_proof_docker_phone_manifest_consumption`。

## 用户价值和产品北极星

本轮把 O6 OSS/CDN manifest 从 relay/preflight artifact 推进到手机/API 可消费的诊断引用摘要。普通手机用户或售后同学可以看到“诊断对象引用已准备/缺失/损坏/过期”和恢复建议，而不需要理解 OSS bucket、CDN 回源、ROS topic、串口或命令 ACK。

北极星保持不变：普通手机用户通过云端链路控制小车并查看任务状态/诊断，不接触命令行、ROS2、SSH、硬件参数或云密钥。

## OKR 映射

- Objective：O6 4G 云中转 + OSS/CDN 数据通路产品化。
- KR3：manifest artifact 已被 API/phone-safe 摘要消费，仍不证明真实 OSS upload 或 STS issuance。
- KR4：CDN URL rule 以 phone-safe `cdn_url_rule`/safe summary 形式进入诊断引用，不证明 CDN origin fetch。
- KR5：UI/API 输出继续保持凭证和敏感字段 redaction，不展示 AK/SK、Authorization、root password、串口、ROS topic 或 `/cmd_vel`。
- KR6：`missing/invalid/stale` 均有 safe summary 和 retry hint，支持用户可理解的降级路径，但不证明真实 4G 弱网恢复。

## KR 拆解验收

| PRD / Tech Plan 验收项 | 证据 | Product 判断 |
| --- | --- | --- |
| `/api/status.phone_readiness` 可返回 phone-safe `oss_cdn_manifest` 摘要 | `operator_gateway_http.py` 已接入 helper；Full-stack targeted tests `Ran 62 tests in 16.283s OK` | 通过 |
| `/api/diagnostics.oss_cdn_manifest` 与 status 共用 helper | `operator_gateway_diagnostics.py` 接入同一 summary helper；diagnostics tests 包含在 62 tests | 通过 |
| 覆盖 `ready/missing/invalid/stale` | `build_phone_oss_cdn_manifest_summary()` 和 tests 覆盖状态分类；`tech-done.md` 已列明 | 通过 |
| operator 首屏显示用户可读状态 | 首屏文案为“诊断对象引用已准备/缺失/损坏/过期”并包含 retry hint | 通过 |
| 不泄露 secret、Authorization、AK/SK、root password、串口、baudrate、WAVE ROVER 参数、ROS topic 或 `/cmd_vel` | summary 不返回 full artifact、object key、checksum、本地路径或凭证；PRD 红线未被工程证据突破 | 通过 |
| `missing/invalid/stale` 不聚合成 green readiness | `operator_gateway_http.py` 明确阻止 missing/invalid/stale 进入 green ready | 通过 |
| Robot bridge command/status/ack/cursor 语义未退化 | Robot compatibility fence：`Ran 31 tests in 15.206s OK`；仅一次 `ResourceWarning`，不影响通过 | 通过，保留轻微运行时警告记录 |

## 做什么 / 不做什么

已做：

- API/status 和 diagnostics 接入 phone-safe `oss_cdn_manifest` 摘要。
- operator 首屏消费 manifest 状态并显示普通用户可读文案。
- 复用 manifest 校验 helper，避免 status/diagnostics 口径分叉。
- 同步产品文档和 sprint `tech-done.md`。
- 完成 Full-stack targeted tests、remote relay tests、py_compile、scoped diff check 和 Robot compatibility fence。

未做且不得宣称：

- 真实 OSS upload、STS issuance、受限 AK 发放、CDN origin fetch、生命周期策略或 production account。
- 真实云部署、HTTPS/TLS 公网入口、真实 4G/SIM、carrier 弱网测试。
- 生产 DB/queue、多实例一致性、生产备份策略或真实灾备。
- 正式手机 app、真实手机浏览器/设备验收。
- Nav2/fixed-route 送达、WAVE ROVER、真实串口、T1001 feedback 或 HIL。

## 优先级和验收口径结论

P0 已满足。本轮可以把 O6 从“manifest artifact 可生成/校验”推进为“手机/API 可消费 manifest 诊断引用摘要”。验收边界必须写为 `software_proof_docker_phone_manifest_consumption`，不能写成 production ready、真实 OSS/CDN 可达、真实 4G 可用或真实送达成功。

## 对应责任 Engineer

- `full-stack-software-engineer`：完成 API summary、operator 首屏、状态分类、产品文档同步和 `tech-done.md`。
- `robot-software-engineer`：完成 remote bridge compatibility fence，只读无改动。
- `product-okr-owner`：完成本文件、`final.md` 和 OKR 保守进度更新。

## 风险、阻塞和需要补齐的证据链

- 当前证据仍是 Docker/local software proof，不是生产云或真实 4G/SIM。
- `ready` 只表示本地 manifest 摘要可被手机/API 消费，不表示对象已经上传 OSS 或 CDN 可 fetch。
- 后续需要真实 OSS upload、STS/受限 AK、CDN 回源、HTTPS/TLS 公网入口、真实 4G/SIM、生产鉴权/rotate、生产 DB/queue、真实手机浏览器和售后诊断验收。
- O1/O2/O3/O4/O5 不因本轮证据提升；本轮只支持 O6 小幅保守上调。
