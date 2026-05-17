# Sprint 2026.05.17_08-09 Cloud Worker Cutover Drain Gate - Pre Start

## 1. Sprint 声明

sprint_type: epic

目标：启动 Objective 5 的 Docker-only 功能前进 sprint，规划并交付 `cloud_worker_cutover_drain`。本轮把上一轮 `cloud_worker_migration_rehearsal` 推进为一次性 worker drain / cutover gate：在本地 SQLite / File relay state 中 drain pending command，校验 cursor、terminal ACK、失败重跑和脱敏边界。

本轮 evidence boundary 固定为：

- `Docker-only`
- `software_proof_docker_cloud_worker_cutover_drain_gate`
- `trashbot.cloud_worker_cutover_drain.v1`
- `trashbot.cloud_worker_cutover_drain_summary.v1`
- `production_ready=false`
- `delivery_success=false`
- `primary_actions_enabled=false`
- not real external proof

## 2. 背景证据

- `OKR.md` 4.1 当前显示 Objective 5 约 67%，仍是完成度最低的 Objective。上一轮 `sprints/2026.05.17_07-08_cloud-worker-migration-rehearsal/final.md` 只把 O5 从约 66% 保守推进到约 67%，证据边界明确是 `Docker-only`、`software_proof_docker_cloud_worker_migration_rehearsal_gate`、`production_ready=false`、`delivery_success=false`、`primary_actions_enabled=false`，不是真实 production worker / migration 或 real external proof。
- Objective 5 的真实外部缺口仍不可得：真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue connectivity、真实 production worker/migration、多实例一致性、生产 queue ordering、transaction isolation、backup/recovery。
- `sprints/2026.05.17_06-07_route-task-field-retest-evidence-dispatch/final.md` 已明确：没有真实现场材料时不要继续堆 O2/O3 route/elevator wrapper；该轮只是把现场证据包派发到 PC / Robot / mobile，不是真实 field pass、真实 Nav2/fixed-route 或 delivery success。
- PR #5 硬件材料 blocker 已在多轮 hardware wrapper 中消费，仍缺真实 2D LiDAR / ToF SKU/source/receipt/procurement/installation/wiring/power/calibration/HIL-entry 和 field evidence。PR #4 的 elevator-assisted delivery 主线要求仍需要真实门状态、目标楼层确认和人工协助材料；本机没有真实硬件，不能靠本轮补齐。
- CEO 本轮要求“用team继续完成OKR”“重新在功能往前走”“别测试代码一堆，测试只围栏”“优先推进OKR完成度低的部分”“本机没有真实硬件，只有docker”。因此本轮选择 Objective 5 的可执行软件功能，而不是外部材料 wrapper。

## 3. 用户价值和产品北极星

用户价值：手机用户发出的云端任务不能在切换 worker、重启 relay 或补跑 drain 时悄悄丢失，也不能把 terminal ACK 误写成真实送达。即使现在只有 Docker，本轮也要把“待处理命令如何一次性 drain、如何重跑、如何证明没有越权触发机器人动作”变成可执行、可复验的产品约束。

产品北极星：`rober` 是面向普通手机用户的低成本 ROS2 自主垃圾投递机器人。云中转要支撑手机下发、机器人 outbound polling、状态回传、ACK 对账和故障恢复；本轮只推进 worker cutover / drain 的软件可执行性，不宣称真实公网云、真实 4G、真实 production DB/queue、真实手机或真实送达。

## 4. OKR 映射

- Objective 5：主目标。推进 KR1 / KR2 / KR5 / KR6 的 cloud relay 控制面、生产切换准备、凭证边界和 graceful degradation。核心是让 pending command drain、cursor、ACK 和 retry invariant 可执行、可审计。
- Objective 4：只作为用户触点安全边界。若后续实现暴露 summary，必须只读展示，不启用 Start / Confirm / Cancel，不把云 drain 写成手机真实验收。
- Objective 1 / 2 / 3：本轮不新增真实 WAVE ROVER、UART、HIL、Nav2/fixed-route、route/elevator field pass、真实 task record、dropoff/cancel completion 或 delivery success。

## 5. 本轮核心抓手

新增 `cloud_worker_cutover_drain` gate：

- 支持 CLI / env / artifact / preflight / Docker smoke。
- 从本地 SQLite / File relay state drain pending command。
- 校验 idempotency、cursor、terminal ACK 不等于 delivery success、失败重跑和脱敏。
- 生成 `trashbot.cloud_worker_cutover_drain.v1` artifact 与 `trashbot.cloud_worker_cutover_drain_summary.v1` summary。
- Robot diagnostics 只能 metadata-only 消费 summary，不得进入 command payload、触发动作、推进 cursor 或改变 ACK 语义。

## 6. 责任分工

- Task A `full-stack-software-engineer`：cloud relay / onboard relay 的 CLI、env、artifact、preflight、Docker smoke 和 cloud docs。
- Task B `robot-software-engineer`：Robot diagnostics metadata-only consumption / fence，接口文档同步，确保 fail closed。
- Task C `product-okr-owner`：A/B 返回后更新 `tech-done.md`、`side2side_check.md`、`final.md`、`OKR.md` 和 `docs/process/okr_progress_log.md`。
- `hardware-engineer`：本轮不改硬件文件；PR #5 真实硬件材料保持风险项，不继续 wrapper。
- `autonomy-engineer`：本轮不改 route/elevator/导航文件；PR #4 现场材料保持风险项，不继续 O2/O3 wrapper。

## 7. 风险、阻塞和证据链缺口

- 本轮仍缺真实 production DB/queue、真实 production worker/migration、真实公网 HTTPS/TLS、真实 4G/SIM、OSS/CDN live traffic、真实手机设备、真实 PWA prompt/user choice、生产多实例一致性、真实备份恢复和真实云账号外部探测。
- 本轮仍缺 WAVE ROVER、真实串口/UART、HIL、真实 Nav2/fixed-route、真实 route/elevator field pass、真实 task record、真实 dropoff/cancel completion、真实 delivery result 和 delivery success。
- PR #5 的 2D LiDAR / ToF 真实材料、采购、安装、接线、电源、标定、HIL-entry 和 field evidence 不被本轮替代。
- 如果 A/B 只完成 local drain wrapper 但没有真实 idempotency、cursor、ACK、retry、redaction 和 Robot metadata-only fence，本轮不能更新 Objective 5 进度。

## 8. 需要创建或更新的 sprint 文档

Planning 阶段创建：

- `sprints/2026.05.17_08-09_cloud-worker-cutover-drain-gate/pre_start.md`
- `sprints/2026.05.17_08-09_cloud-worker-cutover-drain-gate/prd.md`
- `sprints/2026.05.17_08-09_cloud-worker-cutover-drain-gate/tech-plan.md`

实现和验收阶段后续必须补齐：

- `sprints/2026.05.17_08-09_cloud-worker-cutover-drain-gate/tech-done.md`
- `sprints/2026.05.17_08-09_cloud-worker-cutover-drain-gate/side2side_check.md`
- `sprints/2026.05.17_08-09_cloud-worker-cutover-drain-gate/final.md`
