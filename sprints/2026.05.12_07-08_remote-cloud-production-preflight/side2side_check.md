# Sprint 2026.05.12_07-08 Remote Cloud Production Preflight - Side2Side Check

## 状态

- 阶段：side2side_check
- 时间：2026-05-12 Asia/Shanghai
- Product Owner：`product-okr-owner`
- 主责 Engineer：`full-stack-software-engineer`
- 支撑 Engineer：`robot-software-engineer`
- 结论：DONE_WITH_CONCERNS
- 证据边界：`software_proof_docker_preflight_gate`

## 用户价值和产品北极星

本轮验收的用户价值是把“未来真实云上线前不能带病进入生产路径”变成可执行 gate。普通手机用户还没有拿到正式手机 UI 或真实 4G 云服务，但后续上线前可以通过 preflight 输出提前发现凭证、TLS、公网入口、OSS/CDN、state store 和 phone-safe 输出缺口。

产品北极星不变：普通用户只用手机，通过 4G 云中转完成 trash delivery。本轮只证明 Docker/local production preflight gate，不证明真实送达或真实云生产链路。

## OKR 映射

| Objective/KR | 验收结论 |
| --- | --- |
| O6 KR1 云中转最小契约 | `/preflightz` 与 `--preflight` 是旁路 gate，未改变 commands/status/ack 契约。 |
| O6 KR2 云服务端基线 | Gate 能识别 HTTPS/public ingress 缺口；当前仍 blocked。 |
| O6 KR3 OSS 写入策略 | Gate 能识别 OSS/CDN 未达生产条件；无真实上传证据。 |
| O6 KR4 CDN 只读入口 | Gate 检查 CDN 目标配置口径；无 CDN 实流量证据。 |
| O6 KR5 凭证管理 contract | Gate 覆盖 missing/placeholder credential 和敏感输出过滤。 |
| O6 KR6 graceful degradation | blocked/warning/pass 与 `safe_summary` / `retry_hint` 可支撑后续手机提示。 |
| O5 支撑项 | 只有 phone-safe readiness 文案和状态支撑，不提升 O5。 |

## KR 拆解或更新

- O6 当前从约 27% 小幅上调到约 30%，依据是本轮形成 `software_proof_docker_preflight_gate`。
- O5 保持约 33%，因为本轮没有正式手机 UI、普通用户实机验收或真实手机远程流程。
- O1/O2/O3/O4 保持不变，因为本轮没有硬件、导航、感知或任务实跑新增证据。

## 本轮核心抓手

核心抓手是 production preflight gate，而不是生产部署。验收重点是：

- Docker/local 环境可运行 gate。
- Gate 输出 machine-readable blocked/warning/pass。
- Gate 明确暴露 credential、TLS/public ingress、OSS/CDN、state store、phone-safe 输出缺口。
- Robot command/status/ack 主路径不被 gate 改 shape 或改语义。
- 输出不泄露 secret、底层 ROS topic、串口、baudrate、WAVE ROVER 参数或 `/cmd_vel`。

## 做什么 / 不做什么

做：

- 接受本轮 `software_proof_docker_preflight_gate` 为 O6 的小幅进展。
- 将 blocked preflight 解释为云端生产配置未就绪，而不是机器人失败。
- 将 `safe_summary` / `retry_hint` 视为后续手机 UI 可消费素材。

不做：

- 不声明真实云部署完成。
- 不声明真实 4G/SIM、HTTPS/TLS 公网入口、防火墙或公网可达完成。
- 不声明 OSS/CDN 上传、回源、实流量、STS 或 rotate 完成。
- 不声明生产 DB/queue、多实例一致性、备份或灾备完成。
- 不声明正式手机 UI、Nav2/fixed-route、WAVE ROVER、HIL 或真实垃圾送达完成。

## 优先级和验收口径

| 优先级 | 验收项 | 结果 |
| --- | --- | --- |
| P0 Config gate | Docker/local 可以运行 preflight 并返回 blocked/warning/pass | 通过 |
| P0 Secret gate | missing/placeholder credential 可识别，输出不泄露敏感字段 | 通过 |
| P0 TLS/public gate | local-only / HTTPS public ingress missing 被标记 blocked | 通过 |
| P0 OSS/CDN gate | OSS/CDN 未实证被标记 blocked | 通过 |
| P0 State gate | file-backed store 仅为 proof，unwritable store 可 blocked | 通过 |
| P0 Robot compatibility | command/status/ack 与 cursor/ACK 保守语义不退化 | 通过 |
| P0 Evidence boundary | 所有结论保持 `software_proof_docker_preflight_gate` | 通过 |

## 对应责任 Engineer

- `full-stack-software-engineer`：production preflight gate、secret/TLS/public/OSS-CDN/state/phone-safe checks、Docker smoke、相关 docs/product 同步。
- `robot-software-engineer`：remote bridge compatibility fence，确认 preflight gate 不改变 robot polling 主路径。
- `product-okr-owner`：本文件、`final.md` 和 `OKR.md` 保守进度快照。

## 风险、阻塞和证据链缺口

- 真实云：无真实云主机、域名、HTTPS/TLS 证书、公网入口、防火墙实证。
- 真实网络：无真实 4G/SIM、carrier 弱网/断网恢复证据。
- 对象链路：无 OSS 上传、CDN 回源、CDN 实流量、STS 或受限 AK 实证。
- 生产状态：无生产 DB/queue、多实例一致性、备份、灾备或 rotate 证据。
- 机器人链路：无 Nav2/fixed-route、WAVE ROVER、真实串口、HIL 或真实垃圾送达证据。
- 手机体验：只有 phone-safe readiness 支撑，没有正式 UI 美观验收或普通用户实机验收。

## 需要创建或更新的 sprint 文档

- 已创建：`side2side_check.md`
- 待本轮收口创建：`final.md`
- 已更新：`OKR.md`
- 不需要修正：`tech-done.md` 当前事实与验收边界一致。
