# Sprint 2026.05.12_11-12 Remote Cloud OSS/CDN Manifest Proof - Pre Start

## 状态

- 阶段：pre_start
- 启动时间：2026-05-12 11:20 Asia/Shanghai
- Product Owner：`product-okr-owner`
- 主责 Engineer：`full-stack-software-engineer`
- 兼容性围栏：`robot-software-engineer`
- 目标 Objective：O6 4G 云中转 + OSS/CDN 数据通路产品化

## 用户价值和北极星

北极星仍是：普通手机用户不需要同 WiFi、不接触 ROS2/SSH/命令行，也能通过云端控制小车并查看任务诊断引用。

本轮用户价值不是“真实 OSS/CDN 已上线”，而是在没有真实云账号、4G SIM 和硬件的 Docker/local 环境里，先把大对象引用的产品 contract 固化下来：诊断图片、日志包或任务记录以后应该以什么 schema、对象前缀、CDN URL、脱敏摘要、checksum 和 evidence boundary 暴露给手机/云端。这样下一轮接真实 OSS upload、STS 和 CDN 回源时，不再把对象路径、密钥边界和手机可见字段临时拼出来。

## OKR 映射

- O6 当前约 34%，是当前最低完成度 Objective，必须优先推进。
- O6 KR3：OSS bucket、region、对象前缀和小车侧凭证边界需要从“配置形态检查”前进到“manifest artifact shape proof”。
- O6 KR4：CDN base URL 需要从文档值前进到可校验的对象引用 URL 组合 proof。
- O6 KR5：凭证和脱敏边界需要在 artifact/preflight 输出中被机器检查，不能泄露 AK/SK、bearer token、Authorization header、root password、串口、baudrate、ROS topic 或 `/cmd_vel`。
- O6 KR6：本轮只为后续 OSS 写失败/CDN 不可达降级提供 artifact 口径，不证明真实上传、回源或 4G 弱网恢复。

## 近期证据

- `OKR.md` 当前快照显示 O6 约 34%，低于 O5 约 38%、O2 约 74%、O1/O4 约 75%、O3 约 76%。
- `sprints/2026.05.12_10-11_phone-ui-readiness-gate/final.md` 已收口 O5 phone readiness gate，但明确 O6 保持约 34%，且没有真实云、4G/SIM、HTTPS/TLS、公网入口、OSS/CDN 实流量、生产 DB/queue。
- `docs/product/cloud_4g_infrastructure.md` 记录 O6 已有 relay、preflight、SQLite state、backup/restore drill；OSS/CDN 仍只有 bucket/region/prefix/CDN base URL 的目标和配置形态检查，没有上传、STS、CDN 回源或对象引用 artifact proof。
- `docs/product/remote_4g_mvp.md` 明确正式远程路径是 phone -> cloud -> robot outbound polling；local `operator_gateway` 只是 fallback，ACK 不等于 delivery success。
- 当前主机没有真实硬件，只有 Docker；本轮不得尝试或宣称 HIL、真实 4G、真实云、真实 OSS upload 或 CDN 回源。

## 本轮核心抓手

做一个 `software_proof_docker_oss_cdn_manifest` 级别的 OSS/CDN manifest proof：

- 生成一个 Docker/local 可验证的 manifest artifact，描述未来诊断大对象引用的 schema/version/checksum、robot/task/date/prefix、object refs、CDN URL、脱敏摘要和 not_proven 列表。
- preflight 能读取并验证该 artifact，通过时显示新的 evidence boundary，例如 `software_proof_docker_oss_cdn_manifest`。
- manifest 只证明对象引用 shape、prefix/CDN URL 组合、脱敏、artifact checksum、schema 和版本，不证明真实上传、STS 签发、CDN 回源、生命周期、生产账号、真实 4G 或真实云。
- Robot compatibility fence 只验证 `remote_bridge` command/status/ack shape 未退化，不新增大测试堆。

## 做什么

- 由 `full-stack-software-engineer` 实现 manifest artifact 生成和校验能力。
- 在 preflight 中接入 manifest artifact 检查，并将通过状态映射到清晰的 software proof evidence boundary。
- 更新 O6 相关产品文档，明确 manifest proof 与真实 OSS/CDN 的边界。
- 由 `robot-software-engineer` 做只读/轻量兼容性围栏，确认 remote command/status/ack/cursor 语义未被 manifest work 影响。
- 更新本 sprint 的 `tech-done.md`，实现完成后再进入 `side2side_check.md` 和 `final.md`。

## 不做什么

- 不修改 `OKR.md`，除非实现完成且有新证据后由 Product Owner 在收口阶段另行更新。
- 不做真实 OSS 上传、STS 签发、CDN 回源、生命周期策略、生产账号、生产 DB/queue、多实例或真实灾备。
- 不做真实云部署、HTTPS/TLS 公网入口、真实 4G/SIM、弱网 carrier 测试。
- 不做 Nav2/fixed-route、真实送达、WAVE ROVER、串口反馈或 HIL。
- 不把 ACK、preflight pass、manifest pass 或 CDN URL shape 写成 delivery success。
- 不扩大测试堆；只跑实现相关 targeted tests、`py_compile`、Docker/local smoke 和 scoped `git diff --check`。

## 优先级和验收口径

P0：

- manifest artifact schema/version/checksum 可生成、可校验、可被 preflight 读取。
- object refs 必须包含 bucket `bytegallop`、region `oss-cn-hangzhou`、prefix `rober/<robot_id>/<date>/<task_id>/` 与 CDN base `https://cdn.bytegallop.com/rober/` 的组合规则。
- 输出必须 phone-safe，不泄露 token、Authorization header、OSS secret、root password、串口、baudrate、WAVE ROVER 参数、raw ROS topic 或 `/cmd_vel`。
- preflight 通过 manifest artifact 时必须显示 `evidence_boundary=software_proof_docker_oss_cdn_manifest` 或等价清晰边界，并保留 `not_proven`。
- `remote_bridge` command/status/ack shape 和保守 ACK/cursor 语义不退化。

P1：

- artifact 支持多对象引用、过期时间或生命周期意图字段，但只能作为 local proof metadata。
- 手机/diagnostics 后续消费字段可以被文档化，但本轮不要求真实手机 UI 接入。

## 责任 Engineer

- 主责：`full-stack-software-engineer`
  - 文件范围：remote cloud relay / preflight / manifest artifact / O6 产品文档 / sprint `tech-done.md`。
- 兼容性围栏：`robot-software-engineer`
  - 文件范围：remote bridge compatibility tests 或已有 remote bridge test 命令；不改 manifest 主实现，除非主责 Engineer 明确需要接口修复。
- Product Owner：
  - 负责验收口径、sprint 收口、OKR 证据边界和不得宣称事项。

## 风险、阻塞和证据链缺口

- 当前没有真实云、4G/SIM、HTTPS/TLS、公网入口、OSS/CDN 实流量或生产账号，manifest pass 只能是 Docker/local software proof。
- 如果实现只拼 URL 但没有 checksum/schema/version/脱敏检查，则不能作为本轮 P0 通过。
- 如果 preflight pass 文案暗示 production ready、real cloud ready、upload done 或 CDN reachable，必须退回修正。
- 如果 remote bridge 兼容性围栏失败，优先定位 manifest work 是否污染 command/status/ack 契约。
- 后续真实证据链仍需要：真实 OSS upload、STS 或受限 AK、CDN 回源探测、生命周期/rotate、真实云 HTTPS、公网入口、4G/SIM、生产 DB/queue 和弱网恢复。

## 需要创建或更新的 sprint 文档

- 已创建：`pre_start.md`
- 本轮计划阶段创建：`prd.md`
- 本轮计划阶段创建：`tech-plan.md`
- 实现完成后必须更新：`tech-done.md`
- 验收后必须更新：`side2side_check.md`
- 收口后必须更新：`final.md`
