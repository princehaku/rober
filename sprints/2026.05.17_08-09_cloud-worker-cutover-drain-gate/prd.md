# Sprint 2026.05.17_08-09 Cloud Worker Cutover Drain Gate - PRD

sprint_type: epic

## 1. 用户价值和产品北极星

用户价值：云端中转进入 worker cutover 或重启恢复时，手机用户最怕的是任务丢失、重复执行、状态变成“看似成功但其实未送达”。本轮用 Docker-only drain gate 先把 pending command 的一次性 drain、幂等重跑、cursor 和 ACK 边界做成可执行合同，降低未来接入真实 production worker / DB / queue 时的产品风险。

产品北极星：`rober` 要成为普通手机用户可用的低成本 ROS2 自主垃圾投递机器人。云中转链路必须让手机控制、机器人 outbound polling、状态回传、ACK 对账和恢复策略可解释；本轮只证明本地软件功能，不证明真实云、真实 4G、真实 production DB/queue、真实手机、HIL、Nav2/fixed-route 或 delivery success。

## 2. 问题定义

上一轮 `cloud_worker_migration_rehearsal` 已经把 Objective 5 的 migration / worker rehearsal 变成 Docker-only 可执行 gate，但还没有覆盖 cutover 时最关键的一次性 drain 场景：

- pending command 从旧 worker / 本地 relay state 切到新 worker 时，必须能 drain 且可审计。
- drain 需要幂等，失败重跑不能重复推进 cursor 或重复触发机器人动作。
- terminal ACK 只能表示云端控制面看到了终态 ACK，不等于真实送达或 dropoff/cancel completion。
- Artifact / summary 必须脱敏，不能泄露 DB path、DB URL、queue URL、credential-bearing URL、Authorization、bearer token、OSS AK/SK、root password、serial/UART、WAVE ROVER、ROS topic 或 `/cmd_vel`。
- Robot diagnostics 可以读 summary，但 summary 不能进入 command payload，不能触发 collect/dropoff/cancel/ACK，不能推进 cursor。

## 3. OKR 映射

Objective 5：云中转 + OSS/CDN 数据通路产品化，当前约 67%，本轮主攻。

- KR1：继续保持 `trashbot.remote.v1` commands/status/ack 控制面，不暴露 `/cmd_vel`，不接受 inbound 直连小车；新增 drain gate 只作用于 relay state / worker readiness。
- KR2：cloud docs 说明 cutover / drain 的 4C 8G 云端演进边界，仍缺真实 production DB/queue 和公网材料。
- KR5：凭证管理保持 `.env` 不入仓库，artifact / summary 只输出脱敏字段和 safe summary。
- KR6：4G 中断、worker 重启、pending command drain 失败、artifact stale/invalid 时必须有 graceful degradation、retry hint 和 fail-closed preflight。

非目标：

- 不提升 Objective 1：不新增真实 WAVE ROVER、UART、HIL、2D LiDAR / ToF 材料。
- 不提升 Objective 2 / 3：不新增真实 route/elevator field pass、Nav2/fixed-route、task record、dropoff/cancel completion 或 delivery result。
- 不提升 Objective 4 的真实手机/browser/production app proof。

## 4. KR 拆解或更新

本轮新增 Objective 5 子 KR 口径：

1. `cloud_worker_cutover_drain` 能读取本地 SQLite / File relay state，并 drain pending command 到安全 summary。
2. Artifact schema 为 `trashbot.cloud_worker_cutover_drain.v1`，summary schema 为 `trashbot.cloud_worker_cutover_drain_summary.v1`。
3. Drain 必须证明 idempotency：重复运行不会重复推进 cursor，不会重复产生 robot action，不会把 ACK 当成 delivery success。
4. Drain 必须证明 failure rerun：失败后重跑能给出 bounded retry result，invalid / stale / unsafe artifact fail closed。
5. Preflight 和 Docker smoke 能消费 cutover drain artifact，但整体保持 `production_ready=false`。
6. Robot diagnostics 只能 metadata-only 消费 summary，固定 `delivery_success=false`、`primary_actions_enabled=false`。

## 5. 本轮核心抓手

`cloud_worker_cutover_drain` 是唯一核心抓手：

- 从上一轮 migration / worker rehearsal 继续向“切换时 pending command 怎么处理”推进。
- 把 drain、cursor、ACK、retry、redaction 和 Robot isolation 串成一个可执行 gate。
- 避免再做 O5 external-blocked metadata wrapper；本轮必须有 CLI/env/artifact/preflight/Docker smoke 的可运行闭环。
- 避免继续 O2/O3 route/elevator wrapper 或 PR #5 hardware wrapper，除非拿到真实现场/硬件材料。

## 6. 需要做什么

### Must Have

- Cloud relay / onboard relay 新增 `cloud_worker_cutover_drain` CLI 或等价入口。
- 支持通过 env / CLI 指定 cutover drain artifact 输入输出和 relay state。
- 生成 `software_proof_docker_cloud_worker_cutover_drain_gate` artifact 与 safe summary。
- 覆盖 pending command drain、idempotency、cursor、terminal ACK 不等于 delivery success、失败重跑和脱敏。
- Preflight / Docker smoke 能消费 artifact；valid artifact 也必须保持 `production_ready=false`。
- Robot diagnostics metadata-only consumption / fence 覆盖 summary 不进 command payload、不触发 collect/dropoff/cancel/ACK、不推进 cursor。
- 同步 `docs/product/cloud_4g_infrastructure.md`、cloud relay README 或 `docs/interfaces/ros_contracts.md` 中与本轮实现相关的段落。

### Should Have

- Artifact 包含 bounded retry hint、pending count summary、drained count summary、cursor summary、terminal ACK summary 和 redaction self-check result。
- Tests 覆盖 valid、missing、invalid schema、unsupported boundary、stale artifact、unsafe copy、credential leak、success wording、`production_ready=true`、`delivery_success=true`、`primary_actions_enabled=true`。
- Docker smoke 覆盖 build/start、artifact generation、preflight consumption、status/command/ACK、cutover drain rerun。

### Won't Have

- 真实 production worker/migration。
- 真实 production DB/queue。
- 真实公网 HTTPS/TLS。
- 真实 4G/SIM。
- OSS/CDN live traffic。
- 真实手机设备/browser 或 production app。
- HIL、WAVE ROVER、Nav2/fixed-route、真实投放、真实 delivery success。

## 7. 优先级和验收口径

P0：Cloud cutover drain gate 可执行。

- `cloud_worker_cutover_drain` 能生成 artifact。
- Artifact / summary 包含 `software_proof_docker_cloud_worker_cutover_drain_gate`。
- `production_ready=false`、`delivery_success=false`、`primary_actions_enabled=false` 固定出现。

P1：Robot action isolation 可证明。

- Summary 不进入 command payload。
- 不触发 collect/dropoff/cancel/ACK。
- 不推进 cursor。
- terminal ACK 不等于 delivery success。

P2：文档和 Product closeout 保守同步。

- `tech-done.md` 汇总 A/B 实际改动和验证输出。
- `side2side_check.md` 对照 Must Have / Won't Have。
- `final.md`、`OKR.md`、`docs/process/okr_progress_log.md` 只在 A/B 验证通过后保守更新 Objective 5，且必须明确不是 real external proof。

## 8. 对应责任 Engineer

- `full-stack-software-engineer`：Task A，负责 cloud relay / onboard relay CLI、env、artifact、preflight、Docker smoke 和 cloud docs。
- `robot-software-engineer`：Task B，负责 Robot diagnostics metadata-only consumption / fence 和接口文档。
- `product-okr-owner`：Task C，负责阶段验收、OKR 更新、progress log 和 sprint closeout。

## 9. 风险、阻塞和证据链

- 本轮只能证明 Docker-only software proof。它不能证明真实 production worker/migration、production DB/queue connectivity、公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、真实手机或 production app。
- 如果 drain gate 没有覆盖 idempotency、cursor、terminal ACK、失败重跑和脱敏，则不能视为 O5 功能前进。
- PR #4 的真实电梯现场材料和 PR #5 的真实 2D LiDAR / ToF / HIL-entry 材料仍然独立缺失。
- O2/O3 最新 evidence dispatch 已经把现场材料回填路径固定；没有真实现场材料时继续 wrapper 不应计入 OKR 前进。

## 10. 需要创建或更新的 sprint 文档

Planning 阶段：

- `pre_start.md`
- `prd.md`
- `tech-plan.md`

实现和收口阶段：

- `tech-done.md`
- `side2side_check.md`
- `final.md`
