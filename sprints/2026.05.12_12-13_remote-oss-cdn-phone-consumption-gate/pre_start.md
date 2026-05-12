# Sprint 2026.05.12_12-13 Remote OSS/CDN Phone Consumption Gate - Pre Start

## 状态

- 阶段：pre_start
- 启动时间：2026-05-12 12:00 Asia/Shanghai
- Product Owner：`product-okr-owner`
- 主责 Engineer：`full-stack-software-engineer`
- 兼容性围栏：`robot-software-engineer`
- 目标 Objective：O6 4G 云中转 + OSS/CDN 数据通路产品化

## 用户价值和产品北极星

北极星仍是普通手机用户不需要同 WiFi、不接触 ROS2/SSH/命令行，也能通过云端控制小车并查看任务诊断引用。

上一轮已经把 OSS/CDN manifest 做成 Docker/local 可生成、可校验、可被 preflight 消费的 `software_proof_docker_oss_cdn_manifest` artifact。本轮用户价值不是继续堆 preflight，而是让手机/API 层能消费这份 manifest 摘要：普通用户在 operator 首屏或 `/api/status.phone_readiness` / `/api/diagnostics` 里看到“诊断对象引用已准备 / 缺失 / 损坏 / 已过期”的安全文案、恢复建议和证据边界，而不是看到 bucket、对象 key、AK/SK、ROS topic 或 traceback。

## OKR 映射

- O6 当前约 36%，仍低于 O5 约 38% 和 O1/O2/O3/O4 约 74%-76% 或更高，是当前最低完成度 Objective。
- O6 KR3：OSS 对象前缀、bucket、region 和 manifest 引用已经有 artifact proof；本轮推进到 API/phone-safe 摘要消费。
- O6 KR4：CDN base URL 组合规则已经能校验；本轮把规则摘要暴露给手机诊断，不暴露敏感云配置。
- O6 KR5：凭证不入仓库和 phone-safe redaction 已有 proof；本轮继续要求 API/UI 层不泄露 secret、Authorization、串口、ROS topic、`/cmd_vel`。
- O6 KR6：本轮只补“诊断对象引用可被用户理解和恢复”的 graceful degradation 文案，不证明真实 OSS 写入、CDN 可达、真实 4G 或生产云。

## 近期证据

- `OKR.md` 2026-05-12 09:10 快照显示 O6 约 36%，O5 约 38%，O1/O2/O3/O4 约 74%-76% 或更高；按“优先推进 OKR 完成度低的部分”，本轮继续深入 O6。
- `sprints/2026.05.12_11-12_remote-cloud-oss-cdn-manifest-proof/final.md` 已收口 `software_proof_docker_oss_cdn_manifest`，但明确缺口包括正式手机 UI 消费 manifest、真实 OSS upload、STS、CDN origin fetch、HTTPS/TLS 公网、真实 4G/SIM、生产 DB/queue。
- `sprints/2026.05.12_10-11_phone-ui-readiness-gate/final.md` 已证明本地 operator 首屏和 `/api/status.phone_readiness` 可以聚合 phone-safe readiness，但未消费 OSS/CDN manifest。
- 当前主机只有 Docker，没有真实硬件；本轮不得声明 HIL、WAVE ROVER、真实送达、真实 4G、真实 OSS/CDN 或公网生产云。

## 本轮核心抓手

把 O6 OSS/CDN manifest 从 relay/preflight artifact 推进到 phone/API 可消费的诊断引用摘要：

- `/api/status.phone_readiness` 或 `/api/diagnostics` 可返回 phone-safe `oss_cdn_manifest` / artifact summary。
- 摘要包含 schema/version、object_count、CDN URL 组合规则、evidence boundary、`not_proven`、`retry_hint` 和 manifest `ready/missing/invalid/stale` 状态。
- operator 首屏显示普通用户文案：“诊断对象引用已准备”“诊断引用缺失”“诊断引用损坏”“诊断引用已过期”，并给出安全恢复建议。
- Robot compatibility 只验证 remote bridge command/status/ack 和 command-status-ack 语义未退化；不扩大到大量测试。

## 做什么

- 由 `full-stack-software-engineer` 主责设计并实现 phone/API manifest consumption gate。
- 在现有 phone readiness 或 diagnostics 输出中增加 manifest 摘要，不把 artifact 原文整体透出给用户。
- 在 operator 首屏增加用户可读状态和 retry hint，避免 raw JSON、bucket/key 细节、ROS topic 或硬件参数。
- 同步相关 `docs/product/` 文档，说明 manifest phone consumption gate 与真实 OSS/CDN 的边界。
- 由 `robot-software-engineer` 执行 remote bridge 兼容性围栏，确认 command/status/ack/cursor 保守语义未退化。
- 实现完成后更新当前 sprint `tech-done.md`，验收后补 `side2side_check.md` / `final.md`。

## 不做什么

- 不做真实 OSS upload、STS、受限 AK 发放、CDN origin fetch、生命周期策略、生产账号或 rotate。
- 不做真实云部署、HTTPS/TLS 公网入口、真实 4G/SIM、弱网 carrier 测试。
- 不做生产 DB/queue、多实例一致性、生产备份策略或真实灾备。
- 不做 Nav2/fixed-route、真实送达、WAVE ROVER、串口反馈或 HIL。
- 不把 manifest ready、ACK、preflight pass、CDN URL shape 或 phone-ready 摘要写成 delivery success。
- 不新增大量测试；只列最小围栏、针对性 unit/API check、`py_compile` 和 scoped `git diff --check`。

## 优先级和验收口径

P0：

- API 输出包含 phone-safe `oss_cdn_manifest` 摘要，可区分 `ready`、`missing`、`invalid`、`stale`。
- 摘要字段至少包含 `schema`/`schema_version`、`object_count`、`cdn_url_rule`、`evidence_boundary`、`not_proven`、`safe_summary`、`retry_hint`、`updated_at` 或等价 freshness 字段。
- operator 首屏能显示诊断对象引用状态，不展示 secret、Authorization、AK/SK、bucket raw admin detail、root password、串口、baudrate、WAVE ROVER 参数、ROS topic 或 `/cmd_vel`。
- invalid/stale/missing manifest 不得让 phone readiness 误报 production ready；必须给出普通用户可理解的恢复建议。
- Robot compatibility fence 证明 remote bridge command/status/ack/cursor 语义不退化。

P1：

- 支持 manifest artifact path 或 env 配置的缺失/不可读错误分类。
- 支持 artifact staleness threshold 的可配置默认值。
- 支持 diagnostics 和 status 两个入口共享同一摘要 helper，减少 UI/API 口径漂移。

## 责任 Engineer

- 主责：`full-stack-software-engineer`
  - 范围：operator gateway status/diagnostics/API、operator 首屏、manifest summary helper、O6 产品文档、当前 sprint `tech-done.md`。
- 兼容性围栏：`robot-software-engineer`
  - 范围：remote bridge command/status/ack compatibility tests 或既有 remote bridge test 命令；不改 manifest 主实现，除非接口退化必须修复。
- Product Owner：
  - 负责验收口径、证据边界、sprint 收口和不得宣称事项。

## 风险、阻塞和证据链缺口

- 当前仍是 Docker/local software proof，不是真实手机 app、真实手机设备浏览器、真实云、真实 4G/SIM 或真实 OSS/CDN 流量。
- 如果 API 直接透出 manifest 原文，可能泄露对象路径、内部文件路径或未来云配置；必须只给 phone-safe 摘要。
- 如果 UI 文案把 “manifest ready” 写成“诊断已上传云端”或“CDN 可访问”，必须退回。
- 如果 stale/invalid/missing 被当成 green readiness，会误导普通用户和售后判断。
- 后续证据链仍需要真实 OSS upload、STS/受限 AK、CDN 回源探测、HTTPS/TLS 公网入口、真实 4G/SIM、生产鉴权/rotate、生产 DB/queue 和真实手机验收。

## 需要创建或更新的 sprint 文档

- 已创建：`pre_start.md`
- 本轮计划阶段创建：`prd.md`
- 本轮计划阶段创建：`tech-plan.md`
- 实现完成后必须更新：`tech-done.md`
- 验收后必须更新：`side2side_check.md`
- 收口后必须更新：`final.md`
