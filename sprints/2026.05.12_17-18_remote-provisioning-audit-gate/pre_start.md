# Sprint 2026.05.12_17-18 Remote Provisioning Audit Gate - Pre Start

## 状态

- Sprint 状态：planning
- 当前主机：macOS + Docker/local，无真实硬件、无真实 4G/SIM、无真实云账号实证
- 目标边界：只推进 Docker/local software proof，不声明 production-ready、真实云、真实 OSS upload、真实 STS issuance、真实 audit log、WAVE ROVER、HIL 或真实送达
- 允许文件范围：本 sprint 的 `pre_start.md`、`prd.md`、`tech-plan.md`

## 触发背景

上一轮 `2026.05.12_16-17_remote-credential-rotation-gate` 已把 O6 credential rotation 从风险项推进到 artifact、preflight 和 phone-safe 摘要 gate：

- Evidence boundary：`software_proof_docker_credential_rotation_gate`
- O6：约 41% -> 约 43%
- O5：保持约 43%
- 仍明确 blocked：真实云、真实 4G/SIM、真实 OSS upload、真实 STS issuance、生产账号 provisioning、真实 audit log、production-ready、Nav2/fixed-route、WAVE ROVER、HIL、真实送达

当前 OKR 快照中 O5 与 O6 都约 43%。O5 已有本地 Chrome browser acceptance gate；O6 虽达到 43%，但上一轮 final 明确建议下一轮优先推进 production credential provisioning / STS issuance / audit log 的外部 proof。由于本机仍无真实硬件，本轮继续选择 O6 作为可在 Docker/local 前进的最低完成度主线。

## 用户价值和产品北极星

用户价值：

- 普通手机用户不需要理解云账号、STS、OSS AK/SK 或审计日志，也能看到“远程控制为什么还不能生产上线”的脱敏原因。
- 支持/运维可以用本地 artifact、preflight 和 phone-safe 摘要判断 robot provisioning、STS issuance、audit log 三类生产前置项是否具备可执行证据，而不是只看到泛化 blocked。

产品北极星：

- 继续服务“普通手机用户通过 4G 云中转控制小车”的北极星。
- 本轮只把生产账号和审计前置口径推进到可执行 gate，不把本地 gate 包装成真实云或真实 4G。

## OKR 映射

- 主目标：Objective 6 - 4G 云中转 + OSS/CDN 数据通路产品化。
- 关联 KR：
  - KR1：保持 `trashbot.remote.v1` command/status/ack 兼容，不暴露 `/cmd_vel` 或 inbound 直连小车。
  - KR3：继续收敛 OSS 写入策略与 STS/受限 AK 边界，但本轮不做真实 OSS upload。
  - KR5：把凭证管理 contract 从 credential rotation gate 继续推进到 robot provisioning、STS issuance、audit log 的 artifact/preflight/phone-safe gate。
  - KR6：让 graceful degradation 和远程诊断能区分 provisioning/STS/audit-log blocked，而不是把全部生产缺口混成 cloud blocked。
- 旁路支撑：Objective 5 只获得 phone-safe 摘要素材支撑，不提升 O5 进度。

## 上轮未完成项

- 缺真实 production account provisioning。
- 缺真实 STS issuance。
- 缺真实 audit log。
- 缺真实 OSS upload、CDN origin fetch、生命周期策略。
- 缺真实云部署、HTTPS/TLS、公网入口、真实 4G/SIM、生产 DB/queue、多实例一致性、生产备份策略。
- 缺正式手机 app/真实手机设备验收。
- 缺 Nav2/fixed-route、WAVE ROVER、HIL 或真实送达。

## 本轮核心抓手

把上轮 `credential_rotation` gate 中仍是 blocked reason 的三类生产前置项拆成独立、可执行、可脱敏展示的 Docker/local artifact：

1. Robot provisioning gate：证明 robot identity/provisioning request 的 schema、state、safe summary、retry hint 和 redaction 规则可执行。
2. STS issuance gate：证明 STS issuance request/result 的本地 artifact 形态、到期时间、权限边界和 blocked/non-production 口径可校验。
3. Audit log gate：证明 provisioning/STS/preflight 的审计事件 shape、checksum、redaction 和 phone-safe 摘要可执行。

## Owner 分工

- Full-stack owner：负责 relay/preflight/operator phone-safe 摘要和 `docs/product/` 同步；主责本轮实现。
- Robot owner：负责 `remote_bridge` 兼容围栏，确认新增 provisioning/STS/audit metadata 不改变 command/status/ack、ACK、cursor 和本地 action 语义。
- Product owner：本轮计划阶段负责 PRD/tech-plan；后续验收阶段负责 `tech-done.md`、`side2side_check.md`、`final.md` 和 `OKR.md` 收口。

## 验收口径

本轮成功只允许声明：

- `software_proof_docker_provisioning_audit_gate`
- Robot provisioning / STS issuance / audit log 已从泛化 blocked reason 推进到 Docker/local artifact、preflight 和 phone-safe 摘要 gate
- Robot bridge 对新增 metadata 仍保持保守兼容

本轮禁止声明：

- 真实云、真实 4G/SIM、真实 OSS upload、真实 STS issuance、真实 audit log
- production-ready、生产账号已开通、生产凭证已签发
- CDN origin fetch、生命周期策略、生产 DB/queue、多实例一致性
- WAVE ROVER、HIL、Nav2/fixed-route 或真实送达

## 需要创建或更新的 sprint 文档

- 当前阶段创建：`pre_start.md`、`prd.md`、`tech-plan.md`
- 实现完成后必须更新：`tech-done.md`
- 验收完成后必须更新：`side2side_check.md`、`final.md`
- OKR 收口时必须更新：`OKR.md`
