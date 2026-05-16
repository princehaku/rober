# Sprint 2026.05.17_04-05 Route Task Field Retest Drill Console - Pre Start

sprint_type: epic

## 1. 启动背景

本轮创建 fresh sprint folder，目标为 `route_task_field_retest_drill_console`。产品北极星仍是让普通手机用户把垃圾交给低成本 ROS2 小车后，可以通过固定路线和电梯 assisted delivery 获得可验证、可解释、可复盘的送达体验。

当前 `OKR.md` 4.1 快照更新时间为 2026-05-17 03:44 Asia/Shanghai：

- Objective 1：约 77%
- Objective 2：约 86%
- Objective 3：约 86%
- Objective 4：约 97%
- Objective 5：约 66%

Objective 5 数值最低，但本机是 Docker-only，缺真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/migration。继续堆 O5 local metadata 不能形成 Objective 5 external proof，本轮不继续消费该 blocker。

最新 `sprints/2026.05.17_03-04_hardware-sensor-hil-entry-execution-pack/final.md` 表明 O1 真硬件、2D LiDAR、ToF 和 HIL-entry 下一步需要真实 SKU/source/receipt/procurement/installation/wiring/power/calibration/HIL-entry 材料。继续本地包装会重复消费硬件 blocker，因此本轮不走硬件材料链。

`sprints/2026.05.17_01-02_route-task-field-retest-operator-drill/final.md` 明确建议：若没有 O5 外部材料，下一步把 operator drill 用于真实现场材料回填，按同一 `evidence_ref` 执行 material pack、result intake、result reconciliation，并补 route/elevator field materials。

## 2. 近期 PR / 评审证据

- PR #5 review 指出 `production_hardware_boundary.md` 中 2D LiDAR / ToF / source baseline 曾存在矛盾，推动了硬件材料链。
- 硬件材料链当前已推进到 `hardware_sensor_hil_entry_execution_pack`，下一步需要真实材料，不适合继续在 Docker-only 主机上做本地 wrapper。
- `route_task_field_retest_operator_drill` 已把 material pack -> result intake -> result reconciliation 的命令顺序、缺失材料和回调动作固化；本轮应把它变成现场复测演练控制台，让 PC、Robot diagnostics、mobile/web 三个消费面用同一 safe summary 解释下一步。

## 3. 本轮目标

新增 `route_task_field_retest_drill_console`，证据边界为 `software_proof_docker_route_task_field_retest_drill_console_gate`。

本轮必须保持：

- `trashbot.route_task_field_retest_drill_console.v1`
- `trashbot.route_task_field_retest_drill_console_summary.v1`
- `not_proven`
- `delivery_success=false`
- `primary_actions_enabled=false`

本轮不读取真实材料目录，不访问 ROS graph、Nav2 runtime、serial/UART、WAVE ROVER、真实电梯、外部云、OSS/CDN、DB/queue 或 4G；不声明 route/elevator field pass、HIL、真实投放、真实 cancel/dropoff completion 或 delivery success。

## 4. 用户价值和产品北极星

用户价值是把“现场人员知道要跑哪些命令”进一步推进为“现场人员能在一个只读控制台里理解同一 `evidence_ref` 的演练状态、下一步清单、缺失材料和安全边界”。这降低现场复测材料回填时的操作断裂，也让手机端和 Robot diagnostics 不会把本地演练误读成真实送达。

产品北极星不变：普通用户不需要 SSH、ROS2、串口或硬件调试知识，也能看懂机器人当前是否可以安全进入下一步；工程侧则必须保留可复盘证据链。

## 5. Owner 与并行策略

本轮是 3 owner Epic sprint，文件范围互不重叠，按 AGENTS.md 并行启动强制规则执行：

- Task A Autonomy Algorithm Engineer：新增 dependency-free PC drill console gate，消费 `route_task_field_retest_operator_drill` artifact / summary，输出 console artifact / summary。
- Task B Robot Platform Engineer：新增 diagnostics metadata-only consumer，fail closed，不触发 collect、dropoff、cancel、ACK、Nav2、HIL 或 delivery success。
- Task C User Touchpoint Full-Stack Engineer：新增 mobile/web 只读“现场复测演练控制台” panel，只展示 safe checklist/copy，Start Delivery、Confirm Dropoff、Cancel gating 不变。

Product closeout 后续由主会话处理，届时再更新 `tech-done.md`、`side2side_check.md`、`final.md`、`OKR.md` 和 `docs/process/okr_progress_log.md`。

## 6. 风险、阻塞和证据链缺口

- Objective 5 external proof 仍缺：真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/migration。
- Objective 1 / 硬件材料仍缺：真实 2D LiDAR / ToF SKU、source、receipt、procurement、installation、wiring、power、calibration、HIL-entry 和 WAVE ROVER / UART / `T=1001` feedback。
- Objective 2 / Objective 3 仍缺：真实 Nav2/fixed-route runtime log、route completion signal、task record、真实电梯门状态、目标楼层确认、人工协助记录、dropoff/cancel completion、delivery result 和同一 `evidence_ref` 的实机复账。
- Objective 4 仍缺：真实 iPhone/Android browser、production app、真实 PWA prompt/user choice 和真实现场 phone behavior。

## 7. 本轮需要创建或更新的 sprint 文档

Planning 阶段创建：

- `sprints/2026.05.17_04-05_route-task-field-retest-drill-console/pre_start.md`
- `sprints/2026.05.17_04-05_route-task-field-retest-drill-console/prd.md`
- `sprints/2026.05.17_04-05_route-task-field-retest-drill-console/tech-plan.md`

实现完成后必须继续补齐：

- `sprints/2026.05.17_04-05_route-task-field-retest-drill-console/tech-done.md`
- `sprints/2026.05.17_04-05_route-task-field-retest-drill-console/side2side_check.md`
- `sprints/2026.05.17_04-05_route-task-field-retest-drill-console/final.md`
