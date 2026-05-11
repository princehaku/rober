# Sprint 2026.05.12_08-09 Remote Cloud SQLite State Proof - Pre Start

## 状态

- 阶段：pre_start
- 创建时间：2026-05-12 Asia/Shanghai
- Product Owner：`product-okr-owner`
- 主责 Engineer：`full-stack-software-engineer`
- 支撑 Engineer：`robot-software-engineer`
- 证据目标：`software_proof_docker_sqlite_state_store`
- 环境边界：本机只有 Docker；没有真实云主机、域名、公网 HTTPS/TLS、真实 4G/SIM、OSS/CDN 实流量、生产 DB/queue、真实硬件或 HIL。

## 用户价值和产品北极星

本轮用户价值是把 O6 从 file-backed relay proof 推进到“状态可恢复的最小数据库形态”。对普通手机用户的价值是间接但必要的：未来手机发出的命令、机器人回传的状态和 ACK 不应因为 relay 进程重启就丢失或错乱；同时，系统必须能用 phone-safe 方式说明当前只是 SQLite 软件证明，还没有达到生产 DB/queue、多实例一致性或真实云完成。

产品北极星保持不变：普通手机用户只用手机，通过 4G 云中转控制小车完成 trash delivery，不接触 ROS2、SSH、串口、硬件参数或 raw JSON。本轮只推进 O6 的 state store recovery proof，不声明真实云、真实 4G、OSS/CDN、正式手机 UI、Nav2/fixed-route、WAVE ROVER 或 HIL 完成。

## 当前仓库证据

- `OKR.md` 2026-05-12 08:00 快照显示 O6 约 30%，O5 约 33%，O1/O2/O3/O4 约 74%-76%；按“优先推进 OKR 完成度低的部分”，且本机 Docker-only 可推进的最低方向是 O6。
- `sprints/2026.05.12_07-08_remote-cloud-production-preflight/final.md` 明确上一轮形成 `software_proof_docker_preflight_gate`，并指出下一轮 O6 应优先补真实云最小 staging 条件，其中 state store 仍是 file-backed proof，生产 DB/queue 缺口明确。
- 近期 O6 链路已经具备 independent relay service、bearer auth、phone-safe errors、Docker deploy/readiness、`/preflightz` 和 robot compatibility fence；下一步应集中证明 state store backend 可恢复，而不是扩大到真实云部署。
- 当前主机没有真实云、4G/SIM、OSS/CDN、生产 DB/queue 或机器人硬件；本轮所有证据必须标注为 Docker/local `software_proof`。

## OKR 映射

| Objective | 本轮处理 |
| --- | --- |
| O6 4G 云中转 + OSS/CDN | 主线推进。为 independent relay 增加 SQLite-backed state store proof，覆盖 commands/status/acks 可恢复，并让 preflight 对 `TRASHBOT_REMOTE_CLOUD_STATE_BACKEND=sqlite` 输出软件证明边界。 |
| O5 手机体验与量产边界 | 只作为 phone-safe readiness 支撑：未来手机端可以理解 state backend、恢复状态和生产缺口；不交付正式手机 UI。 |
| O1/O2/O3/O4 | 不作为本轮主线。无真实硬件、真实路线、真实相机、Nav2/fixed-route 实跑或 HIL，不能提升这些目标完成度。 |

## 上轮未完成项和本轮继承

- 07-08 preflight gate 已能识别 file-backed store only；本轮继承该缺口，把 state backend 从 file-backed proof 推进到 SQLite-backed proof。
- 生产 DB/queue、多实例一致性、备份、灾备、secret rotate、真实公网 TLS、4G/SIM 和 OSS/CDN 实流量仍不在本轮完成范围。
- commands/status/acks 的 HTTP API shape 已有 robot compatibility fence；本轮必须保持兼容，不以 state backend 改造破坏 remote bridge。
- SQLite pass 只能说明单实例、本地 Docker/software proof 的持久化恢复，不等于生产数据库、队列、云服务或手机流程完成。

## 本轮核心抓手

核心抓手是 O6 `remote_cloud_sqlite_state_store_proof`：

1. 为 independent relay 增加 `TRASHBOT_REMOTE_CLOUD_STATE_BACKEND=sqlite` 入口。
2. 在 SQLite backend 下覆盖 commands、status、acks 的重启后恢复。
3. 不改变 `trashbot.remote.v1` HTTP API shape，不改变 command/status/ack envelope 语义。
4. Preflight 对 SQLite backend 输出 pass/warning/block 边界，明确 `software_proof_docker_sqlite_state_store`，不得宣称生产 DB/queue 或真实云 ready。
5. Robot compatibility 只验收 status-command-ack 和 cursor/ACK 语义未变。

## 做什么 / 不做什么

做：

- 创建 SQLite-backed state store proof 的产品和技术边界。
- 要求 `full-stack-software-engineer` 实现或接入 SQLite backend，并用 targeted validation 证明 commands/status/acks 可恢复。
- 要求 preflight 在 `TRASHBOT_REMOTE_CLOUD_STATE_BACKEND=sqlite` 下输出清晰 evidence boundary、production DB/queue 缺口和 phone-safe retry/status 文案。
- 要求 `robot-software-engineer` 只做 remote bridge compatibility acceptance，确认 status-command-ack 和 cursor/ACK 语义未变。
- 要求验收后由 `product-okr-owner` 更新 `OKR.md` 和 sprint 收口文档，O6 只能保守小幅提升，O5/O1/O2/O3/O4 不提升。

不做：

- 不部署真实云主机，不配置域名、公网 HTTPS/TLS、防火墙或真实 4G/SIM。
- 不接入生产 DB/queue，不做多实例一致性、备份、灾备或容量压测。
- 不完成 OSS/CDN 上传、STS 发放、CDN 回源、生命周期或 rotate 实流量。
- 不做正式手机 UI、美观验收或普通用户实机验收。
- 不修改硬件、Nav2、fixed-route、WAVE ROVER、串口或 HIL 相关实现。

## 优先级和验收口径

| 优先级 | 验收口径 |
| --- | --- |
| P0 SQLite backend | `TRASHBOT_REMOTE_CLOUD_STATE_BACKEND=sqlite` 可选择 SQLite state store，且默认 HTTP API shape 不变。 |
| P0 commands recovery | 已入队 commands 在 relay 重启后仍可按既有语义被 robot poll 到。 |
| P0 status recovery | robot status 写入后，relay 重启仍能返回最近状态或既有 status shape。 |
| P0 ack recovery | ACK 写入后，relay 重启仍能保留 terminal ACK/cursor 相关状态，不伪造 delivery result。 |
| P0 preflight boundary | preflight 对 SQLite backend 输出 `software_proof_docker_sqlite_state_store` 或等价边界，并明确不等于 production DB/queue。 |
| P0 robot compatibility | `RemoteCloudClient` 的 post_status、get_next_command、post_ack 语义不变，auth/cloud malformed 失败不推进 cursor。 |
| P1 sprint evidence | 后续 `tech-done.md` 必须记录命令、输出摘要、失败定位和剩余风险；验收后更新 `side2side_check.md`、`final.md`、`OKR.md`。 |

## 责任 Engineer

- `full-stack-software-engineer`：主责 SQLite-backed state store proof、preflight backend boundary、targeted relay tests 和必要 docs/product 同步。
- `robot-software-engineer`：支撑 remote bridge compatibility acceptance，确认 status-command-ack 与 cursor/ACK 语义不退化。
- `product-okr-owner`：负责 O6/O5/O1-O4 边界、side-by-side acceptance、final 和必要 OKR 保守更新。

## 风险、阻塞和证据链缺口

- SQLite proof 仍是单实例 local/Docker proof；它降低 file-backed proof 缺口，但不替代生产 DB/queue。
- 如果 SQLite backend 需要改变 HTTP API shape，说明实现越界，必须回退到兼容设计。
- 如果 ACK 恢复被写成真实送达成功，说明证据语义越界，必须纠正为 command envelope 处理证明。
- 本轮不能补真实云、真实 4G/SIM、OSS/CDN 实流量、正式手机 UI、Nav2/fixed-route、WAVE ROVER 或 HIL。

## 需要创建或更新的 sprint 文档

- 本轮创建：`pre_start.md`
- 本轮前置必须创建：`prd.md`、`tech-plan.md`
- 实现后必须更新：`tech-done.md`
- 验收后必须更新：`side2side_check.md`、`final.md`
- 验收后按证据保守更新：`OKR.md`
