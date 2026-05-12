# Sprint 2026.05.12_16-17 Remote Credential Rotation Gate - PRD

## 状态

- 阶段：prd
- Product Owner：`product-okr-owner`
- 主目标：O6 `software_proof_docker_credential_rotation_gate`
- 非目标：真实云部署、真实 4G/SIM、真实 OSS upload、真实 STS issuance、CDN origin fetch、production-ready、HIL 或真实送达

## 1. 用户价值和产品北极星

普通用户只通过手机看状态、发命令和处理异常。对于远程控制面来说，凭证轮换和 STS/受限 AK 边界如果不可见，用户会在高风险配置下误以为系统 ready；如果直接显示 token、AK/SK 或内部错误，又会产生安全泄露和售后风险。

本轮用户价值是把“生产凭证 rotate/STS 边界是否满足”变成一个 Docker/local 可验证、phone-safe 可展示、preflight 可阻断的 gate。它服务 O6 的北极星：手机经云端 API 控制，小车 outbound polling，不依赖同 WiFi；但本轮不跨越到真实云、真实 4G、真实对象存储或生产账号。

## 2. OKR 映射

- O6 KR1：继续收紧 command/status/ack 控制面上线前 gate，确保 bearer token rotate 未证明时不能显示 production-ready。
- O6 KR3：把 OSS credential mode、STS 临时凭证/受限 AK 边界写入 artifact 和 preflight，不把 manifest artifact 等同真实 OSS upload 或 STS issuance。
- O6 KR5：把 `.env` 不入仓库、凭证通过环境变量注入、密钥泄露有 rotate 流程的 contract 从文档推进到 Docker/local credential rotation gate。
- O6 KR6：凭证或 STS 边界失败时 phone-safe degradation，区分“凭证/账号问题”与“机器人任务问题”。
- O5 支撑：手机/API 只展示安全摘要和 retry hint，不展示 raw JSON、ROS topic、底层硬件字段或密钥。

## 3. KR 拆解或更新

本轮不直接更新 `OKR.md`；实现和验收完成后由 Product Owner 在收口阶段保守判断是否提升 O6。

本轮可验收 KR 拆解：

1. `credential_rotation_artifact`：生成本地 artifact，包含 schema/version、evidence boundary、rotation status、STS/受限 AK status、account/provisioning/audit `not_proven`、checksum 和 phone-safe summary。
2. `preflight_consumption`：`--preflight` 或 `/preflightz` 可消费 artifact；有效 artifact 让 credential rotation check 通过，但真实生产缺口仍使 `production_ready=false`。
3. `phone_safe_redaction`：`/api/status` 或 `/api/diagnostics` 只显示 safe summary、retry hint、状态枚举和 `not_proven`；不得暴露 token、Authorization header、OSS secret、AK/SK、root password、state path、串口、baudrate、WAVE ROVER 参数、ROS topic 或 `/cmd_vel`。
4. `compatibility_fence`：remote bridge 对 auth failure、ACK failure、malformed response 和 cursor persistence 的保守语义不能因为 rotate gate 退化。

## 4. 本轮核心抓手

核心抓手不是增加一批测试，而是新增一个 credential rotation gate artifact 并让 preflight 与 phone-safe diagnostics 实际消费。测试只作为围栏：证明 artifact shape、redaction 和兼容语义，不扩大到全量回归。

## 5. 需要做什么

- 在 independent relay / preflight 体系中新增 credential rotation artifact 的生成或读取入口。
- 在 production preflight 中新增 credential rotation check，并把 artifact 缺失、无效、stale、failed 与 passed 区分为 phone-safe 状态。
- 在 operator/API diagnostics 中新增 credential rotation 摘要，普通用户只看到“凭证轮换检查未完成/凭证边界已通过本地 proof/需要运维重新生成”等文案。
- 在 docs/product/cloud_4g_infrastructure.md 同步记录本轮 gate 的 evidence boundary 和不可声明范围。
- 在 sprint `tech-done.md` 记录实际验证命令、输出片段和剩余风险；收口时更新 `side2side_check.md`、`final.md` 与 `OKR.md`。

## 6. 优先级和验收口径

### P0

- Artifact schema、version、checksum、`evidence_boundary=software_proof_docker_credential_rotation_gate`、`not_proven` 字段可被本地 CLI 或 preflight 消费。
- Preflight 输出 credential rotation check，并在真实生产缺口存在时保持 `production_ready=false`、`overall_status=blocked` 或等效阻断。
- Phone-safe 输出不得包含任何凭证、内部路径、ROS topic 或硬件字段。

### P1

- Operator/API diagnostics 能展示 credential rotation 摘要和 retry hint。
- Remote bridge compatibility fence 证明 auth/ACK/cursor 保守语义不退化。

### P2

- 后续真实云前可扩展到 HTTPS/TLS、公网入口、真实 4G/SIM outbound polling、真实 OSS upload/STS issuance/CDN origin fetch。

## 7. 对应责任 Engineer

- `full-stack-software-engineer`：主责 artifact/preflight/phone-safe diagnostics 实现与 docs/product 同步。
- `robot-software-engineer`：主责 remote bridge compatibility fence，确保 credential rotate gate 不改变 ACK/cursor/action 触发边界。
- `product-okr-owner`：主责验收口径、sprint 收口和 OKR 保守更新。
- `hardware-engineer`：本轮不主责；没有真实硬件，不做 HIL 或 WAVE ROVER 结论。
- `autonomy-engineer`：本轮不主责；没有 Nav2/fixed-route 实跑范围。

## 8. 风险、阻塞和证据链

- 风险：artifact pass 被误读为真实生产凭证安全。控制方式：preflight 必须继续列出真实云、HTTPS/TLS、公网入口、真实 STS issuance、真实 OSS upload、CDN origin fetch、生产 DB/queue 和 4G/SIM 未证明。
- 风险：phone-safe redaction 不完整。控制方式：围栏测试必须包含 token、Authorization、OSS secret、AK/SK、root password、state path、串口、baudrate、WAVE ROVER、ROS topic、`/cmd_vel` 等 hostile sample。
- 阻塞：本机没有真实硬件和真实云账号，本轮不能完成真实 4G、OSS/CDN、STS、HIL 或送达。
- 证据链：`OKR.md` O6 低于 O5 且 Docker-only 可推进；14-15 final 指向 bearer rotate/STS；15-16 final 说明 O5 已闭合本地浏览器 proof；cloud infrastructure doc 明确 rotate/STS 是后续范围。

## 9. 需要创建或更新的 sprint 文档

本轮启动阶段创建：

- `sprints/2026.05.12_16-17_remote-credential-rotation-gate/pre_start.md`
- `sprints/2026.05.12_16-17_remote-credential-rotation-gate/prd.md`
- `sprints/2026.05.12_16-17_remote-credential-rotation-gate/tech-plan.md`

实现完成后必须更新：

- `sprints/2026.05.12_16-17_remote-credential-rotation-gate/tech-done.md`
- `sprints/2026.05.12_16-17_remote-credential-rotation-gate/side2side_check.md`
- `sprints/2026.05.12_16-17_remote-credential-rotation-gate/final.md`
- `OKR.md`
- `docs/product/cloud_4g_infrastructure.md`

## 10. 明确不声明

本轮即使全部通过，也不得声明真实云、真实 4G/SIM、真实 OSS upload、真实 STS issuance、CDN origin fetch、生产账号 ready、production-ready、Nav2/fixed-route、WAVE ROVER、HIL、真实送达或垃圾投递完成。
