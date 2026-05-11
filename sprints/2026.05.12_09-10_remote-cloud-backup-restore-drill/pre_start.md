# Sprint 2026.05.12_09-10 Remote Cloud Backup Restore Drill - Pre Start

## 状态

- 阶段：pre_start
- 创建时间：2026-05-12 Asia/Shanghai
- Product Owner：`product-okr-owner`
- 主责 Engineer：`full-stack-software-engineer`
- 支撑 Engineer：`robot-software-engineer`
- 证据目标：`software_proof_docker_backup_restore_drill`
- 环境边界：本机只有 Docker；没有真实云主机、域名、公网 HTTPS/TLS、真实 4G/SIM、OSS/CDN 实流量、生产 DB/queue、真实硬件或 HIL。

## 用户价值和产品北极星

本轮用户价值是把 O6 从“SQLite 单实例状态可恢复”继续推进到“状态文件可以被备份、恢复，并在恢复后保留 commands/status/acks 的可复盘语义”。对普通手机用户的间接价值是：未来云中转节点发生本地数据损坏、容器重建或人工恢复时，用户命令和机器人状态不会被静默丢弃，系统也能用普通用户可理解的方式说明当前是否只能执行软件级恢复。

产品北极星保持不变：普通手机用户只用手机，通过 4G 云中转控制小车完成 trash delivery，不接触 ROS2、SSH、串口、硬件参数或 raw JSON。本轮只推进 O6 的 backup/restore/disaster-recovery drill 软件闭环，不声明真实云、真实 4G、OSS/CDN、正式手机 UI、Nav2/fixed-route、WAVE ROVER 或 HIL 完成。

## 当前仓库证据

- `OKR.md` 最新快照显示 O6 约 32%，O5 约 33%，O2 约 74%，O1/O4 约 75%，O3 约 76%；按“优先推进 OKR 完成度低的部分”，最低完成度是 O6。
- `sprints/2026.05.12_08-09_remote-cloud-sqlite-state-proof/final.md` 结论为 SQLite 单实例 state proof 完成，证据边界是 `software_proof_docker_sqlite_state_store`。
- 上轮 final 明确 production DB/queue、多实例一致性、backup/restore、disaster recovery、真实云/4G/OSS/CDN 仍缺。
- 近期评审反复要求证据边界必须写清：Docker/local proof 不能写成真实云、真实 4G、HIL 或正式手机 UI。

## OKR 映射

| Objective | 本轮处理 |
| --- | --- |
| O6 4G 云中转 + OSS/CDN | 主线推进。基于 SQLite state proof 增加 backup/restore/drill 的可执行闭环和 preflight gate，为 O6 KR2/KR6 增加软件证据。 |
| O5 手机体验与量产边界 | 只作为 phone-safe restore status/retry hint 支撑；不交付正式手机 UI。 |
| O1/O2/O3/O4 | 不作为本轮主线。当前主机没有真实硬件、真实路线、真实相机、Nav2/fixed-route 实跑或 HIL，不能提升这些目标完成度。 |

## 上轮未完成项和本轮继承

- 08-09 已证明 SQLite backend 下 command/status/ack 可跨 store reopen 或 relay/container restart 恢复。
- 本轮继承并收窄 backup/restore、disaster recovery 缺口：先做 Docker-only 可执行演练，不进入真实云灾备。
- Production DB/queue、多实例一致性、secret rotate、真实公网 TLS、4G/SIM 和 OSS/CDN 实流量仍不在本轮完成范围。
- Backup/restore pass 只能说明单实例、本地 Docker/software proof 的恢复演练，不等于生产备份策略、跨可用区灾备或真实云运维完成。

## 本轮核心抓手

核心抓手是 O6 `remote_cloud_backup_restore_drill`：

1. 为 SQLite-backed relay state 提供可执行 backup artifact 生成入口。
2. 提供 restore drill：从备份恢复到新 state path，恢复后 commands/status/acks 仍符合既有 API shape。
3. 为 preflight 增加 backup/restore/DR drill gate，明确 `software_proof_docker_backup_restore_drill`。
4. 输出 phone-safe backup/restore 状态、失败原因和 retry hint，不泄露 token、路径、硬件或 ROS 底层细节。
5. Robot compatibility 只验收 status-command-ack 与 cursor/ACK 语义未变。

## 做什么 / 不做什么

做：

- 创建 backup/restore/drill 的产品和技术边界。
- 要求 `full-stack-software-engineer` 实现或接入 SQLite state backup、restore drill、preflight gate 和 targeted validation。
- 要求 restore 后验证 commands/status/acks 的 HTTP shape、terminal ACK/cursor 语义和 phone-safe output。
- 要求 `robot-software-engineer` 只做 remote bridge compatibility acceptance，确认 robot polling、status、ACK 和 cursor 语义未退化。
- 要求后续验收在 `tech-done.md` 记录命令、输出摘要、失败定位和剩余风险；收口时再更新 `side2side_check.md`、`final.md` 和必要 OKR。

不做：

- 不部署真实云主机，不配置域名、公网 HTTPS/TLS、防火墙或真实 4G/SIM。
- 不接入生产 DB/queue，不做多实例一致性、跨可用区灾备或容量压测。
- 不完成 OSS/CDN 上传、STS 发放、CDN 回源、生命周期或 rotate 实流量。
- 不做正式手机 UI、美观验收或普通用户实机验收。
- 不修改硬件、Nav2、fixed-route、WAVE ROVER、串口或 HIL 相关实现。

## 优先级和验收口径

| 优先级 | 验收口径 |
| --- | --- |
| P0 backup artifact | SQLite state 可生成可复用 backup artifact，并保留必要 metadata 和 evidence boundary。 |
| P0 restore drill | 从 backup 恢复到新 state path 后，commands/status/acks 可按既有语义读取。 |
| P0 DR gate | preflight 或 CLI gate 能输出 backup/restore/DR drill 状态，并保持 production DR 未完成边界。 |
| P0 phone-safe output | restore 失败、backup 缺失、checksum/metadata 不匹配时输出安全摘要和 retry hint。 |
| P0 robot compatibility | `RemoteCloudClient` 的 post_status、get_next_command、post_ack 语义不变，失败不推进 cursor。 |
| P1 sprint evidence | 后续 `tech-done.md` 必须记录实际命令、输出片段、失败定位和剩余风险。 |

## 责任 Engineer

- `full-stack-software-engineer`：主责 backup artifact、restore drill、preflight DR gate、targeted relay tests/smoke 和必要 `docs/product/` 同步。
- `robot-software-engineer`：支撑 remote bridge compatibility acceptance，确认 status-command-ack 与 cursor/ACK 语义不退化。
- `product-okr-owner`：负责 O6/O5/O1-O4 边界、side-by-side acceptance、final 和必要 OKR 保守更新。

## 风险、阻塞和证据链缺口

- Backup/restore drill 仍是单实例 local/Docker proof；它不替代生产 DB/queue、多实例一致性或真实灾备。
- 如果 restore drill 需要真实云资源才能运行，说明设计过重，必须退回 Docker-only 可验证闭环。
- 如果 backup artifact 暴露 bearer token、Authorization header、OSS secret、root password、原始 state path、ROS topic、串口、baudrate、WAVE ROVER 参数或 `/cmd_vel`，必须先修脱敏。
- 如果 ACK 恢复被写成真实送达成功，说明证据语义越界，必须纠正为 command envelope 处理证明。
- 本轮不能补真实云、真实 4G/SIM、OSS/CDN 实流量、正式手机 UI、Nav2/fixed-route、WAVE ROVER 或 HIL。

## 需要创建或更新的 sprint 文档

- 本轮已创建：`pre_start.md`
- 本轮前置必须创建：`prd.md`、`tech-plan.md`
- 实现后必须更新：`tech-done.md`
- 验收后必须更新：`side2side_check.md`、`final.md`
- 验收后按证据保守更新：`OKR.md`
