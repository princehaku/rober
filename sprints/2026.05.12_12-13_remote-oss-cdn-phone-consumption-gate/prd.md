# Sprint 2026.05.12_12-13 Remote OSS/CDN Phone Consumption Gate - PRD

## 状态

- 阶段：prd
- Product Owner：`product-okr-owner`
- 主责 Engineer：`full-stack-software-engineer`
- 兼容性围栏：`robot-software-engineer`
- Product acceptance boundary：`software_proof_docker_phone_manifest_consumption`

## 背景

O6 已经连续完成 local/mock command loop、independent relay、Docker deploy、production preflight gate、SQLite state proof、backup/restore drill 和 OSS/CDN manifest artifact proof。最新 11-12 sprint 已经证明 manifest 可以描述 bucket `bytegallop`、region `oss-cn-hangzhou`、prefix `rober/<robot_id>/<date>/<task_id>/`、CDN base URL `https://cdn.bytegallop.com/rober/`、对象引用、checksum 和 `not_proven`。

但这个 proof 仍停在 relay/preflight artifact 层。正式手机 UI 和诊断 API 还不能消费 manifest，也不能告诉普通用户“诊断对象引用是否准备好、缺什么、坏在哪里、下一步怎么恢复”。本轮 PRD 要把 manifest 从工程 artifact 推进到 phone-safe status/diagnostics 摘要，同时继续保持 Docker-only 证据边界。

## 用户价值

普通用户和售后同学不应该理解 OSS bucket、object key、CDN 回源、ROS topic 或命令 ACK。他们需要在手机首屏看到安全、短句、可恢复的状态：

- “诊断对象引用已准备”
- “诊断引用缺失，稍后重试或重新生成诊断”
- “诊断引用损坏，需要重新生成”
- “诊断引用已过期，刷新后再查看”

这让 O6 从“我们有 manifest artifact”前进到“手机入口可以消费诊断引用摘要”，但不把它夸大成真实云、真实 OSS/CDN 或真实 4G 已上线。

## 产品北极星

普通手机用户通过云端链路控制小车并查看任务状态/诊断，不接触命令行、ROS2、SSH、串口、硬件参数或云密钥。本轮只推进诊断引用消费这一个抓手，服务于 O6 的 4G 云中转 + OSS/CDN 数据通路产品化。

## OKR 映射

- Objective：O6 4G 云中转 + OSS/CDN 数据通路产品化。
- KR3：从 manifest artifact proof 推进到 API/phone-safe 摘要消费，仍不证明真实上传或 STS。
- KR4：从 CDN URL rule proof 推进到手机可理解的 `cdn_url_rule` 摘要，不暴露 raw secret 或底层控制面。
- KR5：继续要求凭证和敏感字段不进入 tracked files、API 输出和 UI 文案。
- KR6：用 `missing/invalid/stale` 状态和 retry hint 表达降级路径，但不证明真实 4G 弱网或 CDN 不可达恢复。

## KR 拆解或更新

KR6.1 Phone/API manifest summary：

- `/api/status.phone_readiness` 或 `/api/diagnostics` 返回 `oss_cdn_manifest` 摘要。
- 摘要包含 `state`、`schema`、`schema_version`、`object_count`、`cdn_url_rule`、`evidence_boundary`、`not_proven`、`safe_summary`、`retry_hint`、`updated_at` 或 `staleness`。
- 摘要不得把 manifest artifact 全量透出给手机。

KR6.2 状态分类：

- `ready`：manifest 可读取、schema/checksum/prefix/CDN rule 有效，但仍保留 `not_proven`。
- `missing`：manifest path/env 未提供或文件不存在。
- `invalid`：schema/checksum/prefix/CDN rule 不合法，输出 safe error 和 retry hint。
- `stale`：manifest 超过 freshness threshold 或 `created_at` 无法证明新鲜度。

KR6.3 Operator 首屏消费：

- operator 首屏显示诊断对象引用状态和短句。
- 文案面向普通用户，不出现 raw JSON、ROS topic、`/cmd_vel`、串口、baudrate、AK/SK、Authorization header、root password、traceback。
- 状态不得和 delivery success、HIL 或真实 OSS/CDN 可达混淆。

KR6.4 Robot compatibility fence：

- `remote_bridge` 仍按 `trashbot.remote.v1` command/status/ack 轮询。
- terminal ACK/cursor 保守语义不变。
- Phone manifest consumption 不改变 robot command envelope 和 status ack shape。

## 范围

做：

- phone/API `oss_cdn_manifest` 摘要 contract。
- `ready/missing/invalid/stale` 状态和 retry hint。
- operator 首屏 manifest consumption gate 文案。
- 产品文档同步，说明 manifest phone consumption 与真实 OSS/CDN 的差异。
- remote bridge compatibility fence。
- 当前 sprint `tech-done.md` 留档。

不做：

- 真实 OSS upload、STS、受限 AK、CDN origin fetch、生命周期策略、生产账号、rotate。
- 真实云部署、HTTPS/TLS、公网入口、真实 4G/SIM、carrier 弱网测试。
- 生产 DB/queue、多实例一致性、生产备份策略、真实灾备。
- 正式原生手机 app、真实手机设备/浏览器验收。
- Nav2/fixed-route、真实送达、WAVE ROVER、串口反馈、HIL。
- 大量新增测试；只做最小围栏和针对性状态分类验证。

## 优先级和验收口径

P0 acceptance：

- API 可返回 phone-safe `oss_cdn_manifest` 摘要，至少覆盖 `ready/missing/invalid/stale`。
- `ready` 只代表 Docker/local manifest 可消费，不代表真实 OSS upload、CDN reachable、真实云或 production ready。
- invalid/stale/missing 都必须有 `safe_summary` 和 `retry_hint`。
- operator 首屏显示普通用户文案，且不展示 secret、Authorization、AK/SK、root password、串口、baudrate、WAVE ROVER 参数、ROS topic 或 `/cmd_vel`。
- `not_proven` 必须包含 real OSS upload、STS issuance、CDN origin fetch、HTTPS/TLS public ingress、real cloud、real 4G/SIM、production DB/queue、Nav2/fixed-route delivery、WAVE ROVER/HIL 或等价清晰项。
- Remote bridge compatibility targeted fence 通过。
- scoped `git diff --check` 通过。

P0 不通过条件：

- UI/API 文案暗示诊断对象已经真实上传、CDN 可访问、production ready、真实 4G 可用、真实送达成功或 HIL 通过。
- API 输出泄露 raw manifest secret、Authorization、OSS secret、AK/SK、root password、串口、baudrate、ROS topic、`/cmd_vel` 或 traceback。
- `missing/invalid/stale` 被聚合成 green readiness。
- manifest work 破坏 command/status/ack 或 ACK/cursor 保守语义。

## 对应责任 Engineer

- `full-stack-software-engineer`
  - 主责 phone/API manifest summary、operator 首屏文案、状态分类、产品文档同步和当前 sprint `tech-done.md`。
- `robot-software-engineer`
  - 主责 remote bridge compatibility fence；只有发现 status/ack shape 退化时才做最小修复。
- `product-okr-owner`
  - 主责验收口径、风险边界、side-by-side acceptance、final 和必要 OKR 证据更新。

## 风险、阻塞和需要补齐的证据链

- 当前只有 Docker/local，无真实硬件、真实 4G、真实云账号、真实 OSS/CDN 流量或真实手机验收。
- 本轮只证明手机/API 可以消费 manifest 摘要，不证明对象实际存在于 OSS，也不证明 CDN URL 可以 fetch。
- manifest freshness 规则如果过严可能让本地 proof 假阴性；如果过松会把旧 artifact 当成当前诊断。
- operator 文案如果写得过技术，会削弱 O5/O6 对普通手机用户的价值。
- 后续仍需真实 OSS upload、STS/受限 AK、CDN 回源、HTTPS/TLS、公网入口、真实 4G/SIM、生产鉴权/rotate、生产 DB/queue、真实手机浏览器和售后诊断验收。

## 需要创建或更新的 sprint 文档

- 当前已创建/更新：`pre_start.md`、`prd.md`、`tech-plan.md`。
- 实现完成后必须更新：`tech-done.md`。
- Product 验收后必须更新：`side2side_check.md`。
- 收口后必须更新：`final.md`。
