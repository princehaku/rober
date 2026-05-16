# Sprint 2026.05.17_07-08 Cloud Worker Migration Rehearsal - Pre Start

## 1. Sprint 声明

sprint_type: epic

目标：启动 Objective 5 的 Docker-only 功能前进 sprint，新增 `cloud_worker_migration_rehearsal`。本轮把 production DB/queue 的 migration 与 queue worker 从配置/外部探测枚举推进到本地 SQLite relay 可执行 rehearsal artifact，但证据边界固定为 `software_proof_docker_cloud_worker_migration_rehearsal_gate`。

本轮必须保持：

- `production_ready=false`
- `delivery_success=false`
- `primary_actions_enabled=false`
- Docker-only / software proof / not real external cloud proof

## 2. 背景证据

- `OKR.md` 4.1 显示 Objective 5 仍为最低，约 66%。主要缺口是真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、production worker/migration 和外部云证据。
- 本机是 Docker-only，不能生成真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、真实 worker、真实 migration、真实外部云、HIL 或 delivery success。
- GitHub PR #5 review 指向 `docs/product/production_hardware_boundary.md` 的 P1 默认硬件集与 mandatory sensor baseline 矛盾，以及 P2 mandatory sensor assumptions 缺 `docs/vendor/` citation。近期硬件 ladder 已把这些问题消化为 source alignment、procurement、HIL-entry readiness/execution pack，状态仍是 `hardware_material_pending` / `not_proven`，不能虚增真实硬件。
- 最新 sprint `2026.05.17_06-07_route-task-field-retest-evidence-dispatch/final.md` 明确下一步不要继续堆 route/elevator 本地 wrapper；若无 O5 外部材料，应优先真实现场材料或 PR #5 真实 2D LiDAR / ToF 材料。但 CEO 明确当前本机没有真实硬件，只有 Docker，并要求“重新在功能往前走”。

## 3. 用户价值和产品北极星

用户价值：云端中转不是只列出“生产 DB/queue 未配置”，而是能在 Docker-only relay 上演练 migration 与 worker 的最小执行闭环。后续拿到真实 DB/queue 时，Engineer 有可复用的 schema、artifact、worker invariant 和验收口径，不需要从配置清单重新摸索。

产品北极星：普通手机用户不关心云端 queue 细节，但他们需要“手机下发任务后，小车稳定收到、状态可恢复、失败可解释”。本轮只推进这条产品链路的云 worker/migration 软件可执行性，不宣称真实云、真实 4G、真实生产队列或真实送达。

## 4. OKR 映射

- Objective 5：主目标。推进 KR1/KR2/KR5/KR6 的本地可执行 cloud relay 证据，尤其是 commands/status/ack 控制面、生产 DB/queue 缺口、凭证边界和 graceful degradation 的 worker/migration rehearsal。
- Objective 4：只作为手机/用户安全边界的旁路约束。若后续实现暴露 phone-safe summary，必须保持只读，不启用 Start / Confirm / Cancel。
- Objective 1/2/3：本轮不新增真实硬件、真实 route/elevator field pass、Nav2/fixed-route、WAVE ROVER、UART、HIL 或 delivery success。

## 5. 本轮核心抓手

新增 `cloud_worker_migration_rehearsal` artifact gate：

- 使用本地 SQLite relay state 执行 migration rehearsal。
- 使用本地 queue worker rehearsal 校验 command/status/ack invariant。
- 输出 phone-safe / diagnostics-safe summary。
- 接入 preflight 或等价 readiness 消费面。
- 保持 `production_ready=false`、`delivery_success=false`、`primary_actions_enabled=false`。

## 6. 责任分工

- `full-stack-software-engineer`：主责实现 cloud relay worker/migration rehearsal、artifact、preflight 和文档同步。
- `robot-software-engineer`：主责 Robot compatibility fence，证明 rehearsal metadata 不触发 robot action、不推进 command cursor、不改变 ACK 语义。
- `product-okr-owner`：主责阶段收口、OKR 保守更新、sprint 留档和边界复核。
- `hardware-engineer`：本轮不改硬件文件；只在 final 中确认没有真实硬件证据被误写。
- `autonomy-engineer`：本轮不改 route/elevator/导航文件；避免重复 O2/O3 wrapper。

## 7. 风险、阻塞和证据链缺口

- 缺真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue connectivity、真实 worker、真实 migration、多实例一致性、生产队列顺序、生产 transaction isolation、真实备份/恢复、真实云和真实手机设备证据。
- 缺真实 WAVE ROVER、UART、HIL、Nav2/fixed-route、route/elevator field pass、真实 task record、真实 dropoff/cancel completion 和 delivery success。
- PR #5 相关真实 2D LiDAR / ToF SKU/source/receipt/procurement/installation/wiring/power/calibration/HIL-entry 材料仍缺，本轮不能替代。
- 本轮如果只产出 planning 文档，不更新 `OKR.md` 进度；实现和验证完成后才允许 Product closeout 保守更新。

## 8. 需要创建或更新的 sprint 文档

Planning 阶段创建：

- `sprints/2026.05.17_07-08_cloud-worker-migration-rehearsal/pre_start.md`
- `sprints/2026.05.17_07-08_cloud-worker-migration-rehearsal/prd.md`
- `sprints/2026.05.17_07-08_cloud-worker-migration-rehearsal/tech-plan.md`

实现和验收阶段后续必须补齐：

- `sprints/2026.05.17_07-08_cloud-worker-migration-rehearsal/tech-done.md`
- `sprints/2026.05.17_07-08_cloud-worker-migration-rehearsal/side2side_check.md`
- `sprints/2026.05.17_07-08_cloud-worker-migration-rehearsal/final.md`
