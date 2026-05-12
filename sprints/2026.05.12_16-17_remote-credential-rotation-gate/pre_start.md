# Sprint 2026.05.12_16-17 Remote Credential Rotation Gate - Pre Start

## 状态

- 阶段：pre_start
- 启动时间：2026-05-12 16:17 Asia/Shanghai
- Product Owner：`product-okr-owner`
- 主目标：O6 `software_proof_docker_credential_rotation_gate`
- 本轮环境：macOS + Docker/local；本机没有真实硬件、真实 4G/SIM 或真实云生产账号

## 用户价值和产品北极星

用户价值：普通手机用户不应因为服务端 token、OSS/STS 凭证或生产账号配置即将轮换而看到误导性的 ready；operator 应能在 phone-safe 状态里看到“凭证轮换未完成/STS 边界未证明/请联系运维”等可行动提示，同时不会暴露 bearer token、Authorization header、OSS AK/SK、root password、raw state path、串口、baudrate、WAVE ROVER 参数、ROS topic 或 `/cmd_vel`。

产品北极星：手机通过云端 API 控制小车，小车通过 4G outbound polling 消费命令和回传状态；本轮只在 Docker/local 环境推进生产凭证 rotate/STS 边界的可验证 artifact、preflight consumption 和 phone-safe redaction，不声明真实云、真实 4G、真实 OSS upload、真实 STS issuance、CDN origin fetch 或 production-ready。

## Evidence-First 选择依据

- `OKR.md` 当前快照显示 O6 约 41%、O5 约 43%，O1-O4 均约 70%+；本机没有真实硬件，O1/HIL 本轮不能补成真实 `hil_pass`。
- `sprints/2026.05.12_15-16_phone-browser-acceptance-gate/final.md` 已把 O5 推进到 local Chrome browser proof，但明确没有真实云、真实 4G、OSS/CDN 实流量、HIL 或真实送达。
- `sprints/2026.05.12_14-15_remote-network-recovery-drill/final.md` 明确建议 O6 下一步优先补 HTTPS/TLS + 公网入口 + bearer rotate/STS 边界，再做真实 4G/SIM outbound polling 与真实 OSS upload/CDN origin fetch。
- `docs/product/cloud_4g_infrastructure.md` 已写明 token rotate、账号分级、robot provisioning、审计日志，以及 STS/受限 AK 仍是后续范围；OSS/CDN manifest 仍不等于真实 upload、STS 或 CDN origin fetch。

## 上轮未完成项和阻塞

- O6 已有 Docker/local relay、preflight、SQLite store、backup/restore、OSS/CDN manifest、phone/API consumption、command safety 和 network recovery drill proof，但仍缺生产凭证 rotate/STS 边界 proof。
- 真实云部署、HTTPS/TLS、公网入口、真实 4G/SIM、生产鉴权 rotate、STS/受限 AK、真实 OSS upload、CDN origin fetch、生产 DB/queue、多实例一致性仍未完成或未验证。
- O1/HIL 仍受本机无真实串口和 WAVE ROVER 硬件限制；本轮不得把 Docker/local O6 proof 写成 `hil_pass` 或真实送达。

## 本轮核心抓手

用一个 Docker/local credential rotation artifact 作为本轮抓手：

- artifact 表达当前 bearer token rotate、OSS credential mode、STS/受限 AK 边界、账号分级/provisioning/audit 的未证明项。
- production preflight 能消费 artifact，并在 artifact valid 时输出 `credential_rotation=pass` 或同等 check，同时整体仍保持 `production_ready=false`。
- phone/API diagnostics 只消费脱敏摘要和 retry hint，不显示任何密钥、token、URL credential、内部路径或底层 ROS/硬件字段。

## 初始范围

本轮进入实现阶段前，先由 Product Owner 创建：

- `pre_start.md`
- `prd.md`
- `tech-plan.md`

实现阶段主责建议：

- `full-stack-software-engineer`：relay artifact、preflight consumption、phone/API diagnostics redaction。
- `robot-software-engineer`：remote bridge compatibility fence，确认 auth/ACK/cursor 保守语义不因 rotate gate 退化。
- `product-okr-owner`：验收口径、sprint 收口、OKR 保守更新。

## 验收边界

- 目标证据边界：`software_proof_docker_credential_rotation_gate`。
- 允许证明：Docker/local artifact schema、checksum、preflight consumption、phone-safe summary、redaction、ACK 语义未扩大。
- 禁止声明：真实云、真实 4G/SIM、真实 OSS upload、真实 STS issuance、CDN origin fetch、production-ready、HIL、WAVE ROVER feedback、Nav2/fixed-route 送达或真实垃圾投递。

## 风险

- 凭证 rotate 语义容易被误写成“生产账号已安全上线”；本轮必须用 `not_proven` 和 `production_ready=false` 固化边界。
- artifact 如果包含原始 env、token、AK/SK、state path 或内部 topic，会直接破坏 phone-safe contract。
- 如果实现阶段只新增测试不推动 artifact/preflight/diagnostics 功能，则不满足“功能往前走”。
