# Sprint 2026.05.18_16-17 Route Task Acceptance Execution Rerun Queue - Pre Start

## 1. Sprint 声明

- sprint_type: epic
- 启动时间: 2026-05-18 16:17 Asia/Shanghai
- 主题: `route_task_field_retest_acceptance_execution_rerun_queue`
- 证据边界: `software_proof_docker_route_task_field_retest_acceptance_execution_rerun_queue_gate`
- 本轮只启动计划阶段，后续由 Autonomy / Robot / Full-stack workers 按 `tech-plan.md` 并行执行。

## 2. 用户价值和产品北极星

北极星仍是面向普通手机用户的低成本 ROS2 自主垃圾投递机器人：用户把垃圾交给小车后，小车能沿固定路线和电梯 assisted delivery 流程完成送达，并在失败时给出可理解、可复盘、可接管的状态。

本轮用户价值不是宣称真实复跑已经发生，而是把上一轮 owner handoff intake 的状态转成受控现场复跑队列包。现场 owner、Robot diagnostics 和手机支持界面可以围绕同一 safe `evidence_ref` 判断：是否已具备 owner ack、是否还缺现场材料、是否需要同一证据号重跑、是否必须继续阻断。

## 3. Live 证据核对

- `OKR.md` 4.1 显示 Objective 5 约 68% 为数字最低，但真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/cutover 和真实手机/browser 仍不可用；继续本地 O5 metadata depth 不应提升 O5。
- `OKR.md` 4.1 显示 Objective 1 约 81%，但真实 WAVE ROVER/UART/HIL、`feedback_T1001.log`、`/odom`、`/imu/data`、`/battery`、operator HIL report 和 PR #5 2D LiDAR / ToF 真实材料仍缺；本机没有真实硬件，不能把软件包装写成 HIL。
- Objective 2 / 3 / 4 约 99%，仍缺真实 route/elevator field pass、真实电梯门状态、真实楼层确认、人工协助记录、Nav2/fixed-route runtime log、task record/completion signal、dropoff/cancel completion、delivery result 和真实手机设备验收。
- 上一轮 `sprints/2026.05.18_15-16_route-task-acceptance-execution-handoff-intake/final.md` 完成 `software_proof_docker_route_task_field_retest_acceptance_execution_handoff_intake_gate`，并建议下一步用 handoff intake gate 判定 owner ack、材料补齐或同一 `evidence_ref` 重跑。
- GitHub PR #4 已 merged，证据为它把 elevator-assisted delivery 写成行为链、Autonomy、Robot、Full-stack 共同责任。
- GitHub PR #5 已 merged，证据为它把 mandatory navigation/sensing baseline 扩展为单目 + 2D LiDAR + ToF safety ring，并由 review 暴露 default hardware set、vendor/source attribution、2D LiDAR / ToF 材料缺口。
- `docs/product/elevator_assisted_delivery.md` 明确受控实景材料必须包括门状态、目标楼层确认、人工协助、Nav2/fixed-route runtime log、task record、completion signal 和 diagnostics/mobile safe summary。
- `docs/product/mobile_user_flow.md` 明确手机端只能只读展示 route/elevator support metadata，Start / Confirm Dropoff / Cancel gating 不因材料 gate 放开。
- `docs/product/production_hardware_boundary.md` 明确当前 2D LiDAR / ToF 仍是 `hardware_material_pending`、`not_proven`，不是已采购、安装、接线、标定或 HIL-proven 硬件。

## 4. OKR 映射

- Objective 2: 主要目标。把可送垃圾任务和电梯 assisted delivery 的现场回填链推进到受控复跑队列，而不是停在 handoff intake。
- Objective 3: 主要目标。复跑队列必须继续要求 Nav2/fixed-route runtime log、task record、completion signal 和同一 `evidence_ref`，否则不能进入现场复跑准备。
- Objective 4: 次级目标。手机/diagnostics 只读展示复跑队列状态和下一步材料要求，不暴露 raw JSON、ROS topic、串口、路径、凭证或控制按钮。
- Objective 5: 明确不作为本轮主线。Objective 5 数字最低，但缺真实外部材料；本轮不得写成 O5 production proof。
- Objective 1: 明确不作为本轮主线。Objective 1 仍缺真实硬件/HIL；本轮不得写成 WAVE ROVER/UART/HIL proof。

## 5. KR 拆解和本轮核心抓手

核心抓手是新增 metadata-only `route_task_field_retest_acceptance_execution_rerun_queue`：

- 消费上一轮 `route_task_field_retest_acceptance_execution_handoff_intake` artifact、summary、wrapper 或 nested JSON。
- 可选消费 queue request JSON，但只作为队列意图和 owner 材料补充，不触发现场复跑。
- 输出 artifact schema `trashbot.route_task_field_retest_acceptance_execution_rerun_queue.v1` 和 summary schema `trashbot.route_task_field_retest_acceptance_execution_rerun_queue_summary.v1`。
- 固定 evidence boundary 为 `software_proof_docker_route_task_field_retest_acceptance_execution_rerun_queue_gate`。
- 状态必须区分 ready / blocked / backfill / mismatch / unsafe，但所有状态都必须保留 `not_proven`、`delivery_success=false`、`primary_actions_enabled=false`。
- 队列包只能表达“可以交给人类 owner 准备受控现场复跑”或“缺材料需修复”，不能表达真实现场复跑、真实送达、dropoff/cancel completion、HIL、真实手机/browser 或 Objective 5 proof。

## 6. 优先级和验收口径

P0:

- Autonomy worker 实现 PC gate 和 focused unittest，确保 source handoff intake 未 ready、owner ack 缺失、queue request mismatch、unsafe copy、success/control claim 都 fail closed。
- Robot worker 增加 diagnostics safe alias，只读消费 rerun queue summary，不触发 collect/dropoff/cancel、ACK、cursor、Nav2、serial/UART 或 HIL。
- Full-stack worker 增加 mobile/web 只读“受控复跑队列” panel，只展示 phone-safe queue status、safe `evidence_ref`、owner handoff、next required evidence、rerun hint 和 boundary flags。
- Product closeout 更新 `tech-done.md`、`side2side_check.md`、`final.md`、`OKR.md` 和相关 docs，严格说明本轮是 software proof。

P1:

- 在 README / product docs / ROS contract 中同步新增 schema、boundary、not-proven language。
- 复核新增代码中文技术注释比例超过 20%，并避免硬编码硬件 SKU、串口、波特率或真实传感器阈值。

验收口径:

- 所有 worker 必须运行 `tech-plan.md` 中自己的围栏命令。
- 集成验收必须覆盖 `route_task_field_retest_acceptance_execution_rerun_queue`、`robot_diagnostics_route_task_field_retest_acceptance_execution_rerun_queue_summary`、`software_proof_docker_route_task_field_retest_acceptance_execution_rerun_queue_gate`、`PR #4`、`PR #5`、`Objective 5`、`Objective 1`、`not_proven`、`delivery_success=false`、`primary_actions_enabled=false`。
- 最终不能因为本地 Docker/local proof 上调真实 field pass、HIL、O5 external proof 或 delivery success。

## 7. 对应责任 Engineer

- `autonomy-engineer`: 主责 PC evidence gate、artifact/summary schema、queue decision mapping、focused unittest、PC/docs 同步。
- `robot-software-engineer`: 主责 operator diagnostics safe alias、metadata-only fence、diagnostics tests、ROS/diagnostics docs 同步。
- `full-stack-software-engineer`: 主责 mobile/web 只读 panel、fixture/tests、手机用户流程 docs 同步。
- `product-okr-owner`: 主责计划、PRD、验收口径、OKR 映射、最终 sprint closeout 和 OKR 边界更新。
- `hardware-engineer`: 本轮只读咨询。除非后续触碰 WAVE ROVER、UART、2D LiDAR、ToF、电气、接线或真实硬件材料，否则不改硬件配置；若触碰，必须先读 `docs/vendor/VENDOR_INDEX.md`。

## 8. 风险、阻塞和证据链缺口

- 真实外部 O5 材料缺失: HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/cutover、真实手机/browser。
- 真实 O1 硬件材料缺失: WAVE ROVER、UART、HIL、`feedback_T1001.log`、`/odom`、`/imu/data`、`/battery`。
- PR #5 2D LiDAR / ToF 仍缺真实 SKU/source、receipt、procurement、installation、wiring、power、calibration、HIL-entry。
- PR #4 route/elevator 仍缺真实现场材料：电梯门状态、目标楼层确认、人工协助记录、Nav2/fixed-route runtime log、task record、completion signal、dropoff/cancel completion、delivery result。
- 本轮如果只产出 queue metadata，OKR 只能记录软件证明层推进，不能写成真实完成度闭环。

## 9. 需要创建或更新的 sprint 文档

本计划阶段创建：

- `sprints/2026.05.18_16-17_route-task-acceptance-execution-rerun-queue/pre_start.md`
- `sprints/2026.05.18_16-17_route-task-acceptance-execution-rerun-queue/prd.md`
- `sprints/2026.05.18_16-17_route-task-acceptance-execution-rerun-queue/tech-plan.md`

后续实现阶段必须更新：

- `tech-done.md`
- `side2side_check.md`
- `final.md`

