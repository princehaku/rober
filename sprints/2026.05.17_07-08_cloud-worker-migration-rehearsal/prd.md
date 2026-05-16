# Sprint 2026.05.17_07-08 Cloud Worker Migration Rehearsal - PRD

sprint_type: epic

## 1. 用户价值和产品北极星

用户价值：当手机通过云端下发任务时，用户需要任务“不丢、可恢复、失败可解释”。虽然当前没有真实 production DB/queue，本轮仍要把 migration 与 queue worker 变成本地可执行 rehearsal，减少未来接入真实云服务时的未知风险。

产品北极星：`rober` 要成为普通手机用户可用的低成本 ROS2 自主垃圾投递机器人。云中转链路必须支撑手机控制、机器人 outbound polling、状态回传和 ACK 对账，但不能把 Docker-only software proof 说成真实云、真实 4G 或真实送达。

## 2. 问题定义

Objective 5 过去已经覆盖 cloud deployment readiness、external probe bundle、public ingress/TLS、DB/queue config、DB/queue external probe、OSS/CDN live probe 和 external evidence intake。当前缺口不是“再列一遍 production DB/queue 不可用”，而是：

- migration 仍停留在配置或外部探测枚举，没有本地 SQLite relay 可执行 rehearsal。
- queue worker 仍缺本地执行 artifact，无法证明 worker 如何处理 command/status/ack invariant。
- preflight / diagnostics / phone-safe summary 还不能区分“缺真实生产 DB/queue”和“本地 worker/migration rehearsal 已可执行”。
- Docker-only host 不能生成真实外部材料，因此必须把本轮产物命名和 copy 明确限定为 `software_proof_docker_cloud_worker_migration_rehearsal_gate`。

## 3. OKR 映射

Objective 5：云中转 + OSS/CDN 数据通路产品化，当前约 66%，本轮主攻。

- KR1：保持 `trashbot.remote.v1` commands/status/ack 控制面语义，新增 worker/migration rehearsal 不暴露 `/cmd_vel`，不接受 inbound 直连小车。
- KR2：同步 cloud infrastructure 文档，明确 4C 8G 云端基线仍缺真实公网、DB/queue 和 worker 外部证据。
- KR5：凭证管理保持 `.env` 不入仓库，artifact / summary 不输出 DB URL、queue URL、token、Authorization、root password 或 credential-bearing URL。
- KR6：对 production DB/queue 缺失、worker/migration 未外部证明、rehearsal stale/invalid 提供 graceful degradation 和 phone-safe retry hint。

非目标：

- 不提升 Objective 1，不新增真实 WAVE ROVER、UART、HIL、2D LiDAR / ToF 材料。
- 不提升 Objective 2/3，不新增真实 route/elevator field pass、Nav2/fixed-route、task record 或 delivery result。
- 不提升 Objective 4 的真实手机/browser 证明。

## 4. KR 拆解或更新

本轮新增 Objective 5 子 KR 口径：

1. 生成 `trashbot.cloud_worker_migration_rehearsal.v1` artifact，包含 schema、schema_version、evidence_boundary、migration rehearsal result、worker rehearsal result、safe summary、retry hint、not_proven 和 checksum。
2. 本地 SQLite relay state 能执行 migration rehearsal，至少覆盖初始化、重复运行幂等、schema version 标记、坏 schema fail closed。
3. 本地 queue worker rehearsal 能执行一次或多次 command/status/ack 处理，证明 ACK 仍只是 accepted/processing evidence，不等于 delivery success。
4. Preflight / diagnostics / phone-safe summary 能消费 artifact，并在 valid 时仍保持 `production_ready=false`、`delivery_success=false`、`primary_actions_enabled=false`。
5. Artifact 与 summary 不包含 raw DB path、DB URL、queue URL、credential-bearing URL、Authorization、bearer token、OSS AK/SK、root password、serial/UART、WAVE ROVER、ROS topic 或 `/cmd_vel`。

## 5. 本轮核心抓手

`cloud_worker_migration_rehearsal` 是本轮唯一核心抓手：

- 从“配置存在/缺失”推进到“Docker-only SQLite relay 可执行 rehearsal”。
- 通过 artifact 把 migration、worker、ACK/cursor invariant 和 production gaps 固化。
- 通过 Robot compatibility fence 确保 cloud rehearsal metadata 不会触发机器人动作。
- 通过 Product closeout 保守更新 OKR，避免将 rehearsal 误报为真实 production worker/migration。

## 6. 需要做什么

### Must Have

- 新增本地可运行的 migration rehearsal 入口或 CLI。
- 新增本地可运行的 queue worker rehearsal 入口或 CLI。
- 生成 `software_proof_docker_cloud_worker_migration_rehearsal_gate` artifact 和 safe summary。
- 接入 preflight 或等价 readiness check，valid artifact 也必须保持 blocked-by-design production 状态。
- 新增或更新 focused tests，覆盖 valid、missing、invalid、stale、unsafe copy、credential leak、delivery success wording 和 metadata-only isolation。
- 同步更新 `docs/product/cloud_4g_infrastructure.md`、cloud relay README 或接口文档中与本轮实现相关的段落。

### Should Have

- 本地 Docker smoke 可消费 rehearsal artifact。
- `/api/status` 或 diagnostics 可只读展示 worker/migration rehearsal summary。
- `.env.example` 只新增 placeholder artifact env var，不出现真实连接信息。

### Won't Have

- 真实公网 HTTPS/TLS。
- 真实 4G/SIM。
- OSS/CDN live traffic。
- production DB/queue connectivity。
- 真实 production migration。
- 真实 production worker。
- 多实例一致性或生产 transaction isolation。
- HIL、真实送达或 delivery success。

## 7. 优先级和验收口径

P0：Artifact gate 和核心 rehearsal 必须可执行。

- `cloud_worker_migration_rehearsal` 能在 Docker/local Python 环境生成 artifact。
- Artifact 包含 `software_proof_docker_cloud_worker_migration_rehearsal_gate`。
- Artifact 和 summary 固定 `production_ready=false`、`delivery_success=false`、`primary_actions_enabled=false`。

P1：Robot compatibility fence 必须证明 metadata-only。

- Rehearsal summary 不进入 robot command payload。
- 不触发 collect/dropoff/cancel/ACK action。
- 不推进或持久化 command cursor。
- ACK 不等于 delivery success。

P2：文档和 Product closeout 必须真实同步。

- `tech-done.md` 汇总 Engineer 实际改动和验证输出。
- `side2side_check.md` 对照本 PRD 的 Must Have / Won't Have。
- `final.md` 与 `OKR.md` 只做保守更新，明确不是真实 external proof。

## 8. 对应责任 Engineer

- `full-stack-software-engineer`：cloud relay migration/worker rehearsal、artifact、preflight、Docker smoke、cloud docs。
- `robot-software-engineer`：remote bridge / protocol / diagnostics compatibility fence，必要时更新接口文档。
- `product-okr-owner`：规划、验收、OKR 更新和 sprint closeout。

## 9. 风险、阻塞和需要补齐的证据链

- O5 真实完成度仍受外部材料阻塞：公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、真实 worker/migration、生产账号和凭证。
- 本轮 rehearsal 只能证明本地软件 invariant，不证明生产 DB/queue、多实例一致性、真实事务隔离、真实备份/灾备或云端上线许可。
- PR #5 硬件材料缺口仍存在，不能由本轮云 rehearsal 替代。
- 近期 route/elevator wrapper 已消耗到 evidence dispatch，当前没有真实现场材料；本轮不继续 O2/O3 wrapper。

## 10. 需要创建或更新的 sprint 文档

Planning 阶段：

- `pre_start.md`
- `prd.md`
- `tech-plan.md`

实现和收口阶段：

- `tech-done.md`
- `side2side_check.md`
- `final.md`
