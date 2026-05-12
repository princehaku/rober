# Sprint 2026.05.12_14-15 Remote Network Recovery Drill - Pre Start

## 状态

- 阶段：pre_start
- 创建时间：2026-05-12 14:00 Asia/Shanghai
- Product Owner：`product-okr-owner`
- 主目标：Objective 6 `software_proof_docker_network_recovery_drill`
- 支撑目标：Objective 5 phone-safe 恢复摘要，只做支撑，不作为本轮主目标
- 执行边界：本机只有 Docker/local 环境，无真实云、真实 4G/SIM、真实手机设备、WAVE ROVER 或 HIL

## 用户价值和产品北极星

用户价值：普通手机用户在远程链路断网、恢复、ACK 失败或云端状态异常时，不应该看到一个误导性的“已发送/已完成”。系统必须保守地告诉用户当前是网络问题还是机器人问题，并且在 ACK 未可靠落云前不推进命令 cursor、不隐藏 pending command、不触发本地 action。

产品北极星：手机是普通用户唯一入口，4G 场景必须通过云端中转完成 command/status/ack。当前阶段的关键不是继续补按钮文案，而是证明远程控制面在断网/恢复场景下不会把不可确认的命令误报为已处理。

## OKR 映射

- O6 当前约 39%，是当前最低且 Docker-only 可推进的 Objective。
- O5 当前约 40%，已完成本地 command safety browser/API gate，本轮只消费 O6 恢复摘要，避免把 UI 支撑当成主目标。
- O1/O2/O3/O4 当前约 74%-76%，本机无真实硬件或路线实跑证据，本轮不推进、不上调。

## 近期证据

- `OKR.md` 当前快照显示 O6 仍缺真实云、HTTPS/TLS、公网入口、真实 4G/SIM、弱网/断网恢复、生产鉴权/rotate、STS/受限 AK、真实 OSS upload、CDN origin fetch、生产 DB/queue 和多实例一致性。
- `sprints/2026.05.12_13-14_phone-command-safety-browser-gate/final.md` 已完成 phone command safety browser/API gate，但明确证据边界只是 `software_proof_docker_phone_command_safety_browser_gate`，没有真实浏览器/手机设备、真实云或真实 4G。
- `docs/product/remote_4g_mvp.md` 明确 remote bridge 在 cloud unreachable、auth failed、malformed command/status/ACK response 或 ACK post failure 时，必须不推进 cursor、不持久化 terminal cursor、不触发本地 action。
- `docs/product/cloud_4g_infrastructure.md` 已有 Docker deploy、SQLite state proof、backup/restore drill、OSS/CDN manifest proof 和 phone consumption gate；下一步应把断网/恢复/ACK cursor 保守语义变成可执行 Docker/local drill 和 phone-safe 摘要。

## 上轮未完成项

- `13-14` 仅证明手机按钮级 gate 可消费 remote degradation，不证明网络恢复后的 command/status/ack 一致性。
- 仍缺一个可复现的 Docker/local drill，能制造 relay unreachable、ACK post failure、status stale、恢复后重试，并输出 artifact。
- 仍缺 preflight/diagnostics 对 network recovery drill artifact 的消费口径。
- 仍缺 robot 侧 compatibility fence，证明 remote_bridge 在上述错误场景不会推进 terminal cursor 或触发本地 action。

## 本轮核心抓手

把 O6 从“有 relay、状态存储、备份、manifest、phone gate”推进到“有断网/恢复/ACK cursor 保守语义的软件演练”。

目标证据边界：

```text
software_proof_docker_network_recovery_drill
```

该边界只允许说明 Docker/local 网络恢复语义、artifact schema、preflight/diagnostics 消费和 robot compatibility fence 通过；不得宣称真实云、真实 4G、生产网络或真实送达完成。

## 责任分工

- `full-stack-software-engineer`：主责 relay 侧 network recovery drill、artifact、preflight 消费、diagnostics/phone-safe summary。
- `robot-software-engineer`：主责 remote_bridge command/status/ack/cursor compatibility fence，确认失败时不推进 cursor、不触发本地 action。
- `product-okr-owner`：维护本 sprint PRD、验收口径、证据边界和最终 OKR 更新建议。
- `hardware-engineer`：本轮不参与执行；无真实硬件，不产生 HIL 证据。
- `autonomy-engineer`：本轮不参与执行；无真实 fixed-route/Nav2 实跑，不产生路线闭环证据。

## 初始优先级

P0：

- 可执行 Docker/local network recovery drill。
- Drill artifact 能记录断网、恢复、ACK cursor 未推进/恢复后重试、phone-safe summary 和 `not_proven`。
- Preflight/diagnostics 能消费 artifact，并在 missing/invalid/stale/failed 时保守阻断 readiness。
- Robot remote bridge compatibility fence 覆盖 cloud unreachable、auth failed、malformed response、ACK post failure。

P1：

- Operator/phone readiness 摘要消费 drill summary，解释“网络恢复演练未通过/已过期/需要重新执行”。
- 继续保持 sensitive field redaction，不暴露 token、Authorization、state path、OSS secret、串口、ROS topic 或 `/cmd_vel`。

P2：

- 真实云、HTTPS/TLS、公网入口、真实 4G/SIM、真实 OSS upload、CDN origin fetch、生产 DB/queue、多实例一致性。上述均不在本轮 Docker-only 范围内。

## 风险和阻塞

- Docker/local drill 不能代表真实 4G carrier 弱网、真实公网 TLS、真实云防火墙或生产多实例一致性。
- ACK cursor 语义必须以 remote_bridge 行为为准，不能只在 relay artifact 里自证。
- Phone-safe 摘要只能做恢复提示，不能把 ACK 解释成 delivery success。
- 若 implementation 发现现有接口无法无侵入接入 artifact，需要由 `full-stack-software-engineer` 和 `robot-software-engineer` 收敛接口，不能扩大到硬件或导航主线。

## 本轮需创建或更新的 sprint 文档

- 已创建：`pre_start.md`
- 本阶段创建：`prd.md`
- 本阶段创建：`tech-plan.md`
- 执行完成后必须更新：`tech-done.md`
- 验收完成后必须更新：`side2side_check.md`
- 收口完成后必须更新：`final.md`，并由 Product Owner 决定是否更新 `OKR.md`
