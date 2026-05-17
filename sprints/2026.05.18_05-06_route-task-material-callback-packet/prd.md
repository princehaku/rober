# Sprint 2026.05.18_05-06 Route Task Material Callback Packet - PRD

sprint_type: epic

## 1. 用户价值

现场复测 owner 现在有 `route_task_field_retest_material_pack` 的 checklist 和 callback skeleton，但还没有一个可交付、可回填、可跨 PC/Robot/mobile 解释的 packet。缺少 packet 会导致真实回填时继续靠聊天或临时文档判断：材料是否属于同一 `evidence_ref`、哪些缺失是否可接受、是否误把 ACK / completion signal / delivery result 写成成功、是否错误开启主操作。

本轮交付 `route_task_field_retest_material_callback_packet`，让现场材料回传从“字段提示”升级为“安全 packet”：能填写、能 fail closed、能在 diagnostics 和手机端读出来，并明确当前仍是 `not_proven`、`delivery_success=false`、`primary_actions_enabled=false`。

## 2. 产品北极星

`rober` 的北极星是让普通手机用户把垃圾交给小车后，小车沿固定路线、必要时借助电梯完成可靠投递。当前没有真实硬件、真实路线、真实电梯、真实手机和真实云外部材料，所以本轮不追求完成度表面拉满，而是补齐真实现场回传前必须有的证据承载容器。

## 3. OKR 映射

- Objective 2：服务送垃圾任务和电梯 assisted delivery 必达闭环。callback packet 必须覆盖门状态、目标楼层确认、人工协助记录、dropoff/cancel completion、delivery result 的回填位置和缺失原因。
- Objective 3：服务可验证导航与固定路线。callback packet 必须覆盖 Nav2/fixed-route runtime log、route completion signal、task record、同一 `evidence_ref` 的复账状态。
- Objective 4：服务手机用户体验。mobile/web 只读展示 callback packet，普通用户/现场支持能看懂“还缺什么、为什么不能操作”，但不暴露 raw JSON 或 ROS topic。
- Objective 5：不推进。没有真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/cutover 或真实手机/browser external proof。
- Objective 1：不推进。没有真实 WAVE ROVER、UART、串口/topic samples、operator HIL report 或 HIL packet。

## 4. KR 拆解

KR-A / Packet Contract：

- 产出 `trashbot.route_task_field_retest_material_callback_packet.v1` artifact。
- 产出 `trashbot.route_task_field_retest_material_callback_packet_summary.v1` summary。
- 固定 `evidence_boundary=software_proof_docker_route_task_field_retest_material_callback_packet_gate`。
- packet 必须包含 material pack 来源、safe `evidence_ref`、field callback items、accepted/missing/rejected material summary、owner acknowledgement、next required evidence、rerun commands 和 safe copy。

KR-B / Fail-Closed Safety：

- unsupported schema、missing material pack、bad boundary、weak evidence ref、evidence ref mismatch、unsafe raw path、credential/token/OSS/DB/queue material、success claim、action enablement 均 fail closed。
- 所有输出保留 `not_proven`、`delivery_success=false`、`primary_actions_enabled=false`。

KR-C / Cross Surface Consumption：

- Robot diagnostics 只读消费 packet/summary/wrapper/nested diagnostics，不读真实文件、不触发 ROS command、不输出 ACK/completion signal。
- mobile/web 只读展示 callback packet status、缺失材料、回填动作、owner handoff、rerun commands 和边界说明。

KR-D / Product Closeout：

- worker 完成后更新 `OKR.md` 与 `docs/process/okr_progress_log.md`，只记录 software proof，不把本轮当真实 route/elevator field pass。
- 当前 sprint 补齐 `tech-done.md`、`side2side_check.md`、`final.md`。

## 5. 本轮核心抓手

核心抓手是从上一轮 material pack 的 callback skeleton 进入 `route_task_field_retest_material_callback_packet`：

1. Autonomy 负责 PC gate，把 skeleton 变成 artifact/summary。
2. Robot 负责 diagnostics metadata-only alias。
3. Full-stack 负责手机端只读展示。
4. Product 负责 OKR 与 sprint closeout，不允许证据边界漂移。

## 6. 优先级和验收口径

P0：

- PC gate 能生成 callback packet artifact / summary，并拒绝 unsupported / unsafe / success claim / enabled-action 输入。
- schema、summary schema、boundary literal 固定。
- `not_proven`、`delivery_success=false`、`primary_actions_enabled=false` 贯穿 PC、Robot、mobile、docs。

P1：

- Robot diagnostics 能从 packet/summary/wrapper/nested diagnostics 中提取只读摘要，并在缺失或不安全时 fail closed。
- mobile/web 能展示 packet 状态和下一步，且不改变 Start / Confirm / Cancel gating。

P2：

- docs 同步更新：`docs/interfaces/evidence_contracts.md`、`docs/interfaces/ros_contracts.md`、`docs/product/mobile_user_flow.md`、`docs/process/okr_progress_log.md`。
- Product closeout 明确没有提升 O5/O1，且没有宣称真实 field pass。

## 7. 对应责任 Engineer

- A / Autonomy Algorithm Engineer：`pc-tools/evidence/route_task_field_retest_material_callback_packet.py`、focused test、`docs/interfaces/evidence_contracts.md`。
- B / Robot Platform Engineer：`onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py`、diagnostics test、`docs/interfaces/ros_contracts.md`。
- C / User Touchpoint Full-Stack Engineer：`mobile/web/app.js`、mobile fixture/test、`docs/product/mobile_user_flow.md`。
- Product Manager / OKR Owner：`OKR.md`、`docs/process/okr_progress_log.md`、本 sprint closeout docs。

## 8. 非目标和边界声明

本轮不是 real route/elevator field pass，不是 Nav2/fixed-route proof，不是 task record/completion signal，不是 dropoff/cancel completion，不是 delivery success，不是 HIL，不是 WAVE ROVER/UART，不是真实手机/browser，不是 Objective 5 external proof。

本轮不新增硬件事实；若任何实现碰到 WAVE ROVER、ESP32、Orange Pi、UART、波特率、JSON 指令、速度映射、反馈协议、引脚、电压、固件、2D LiDAR、ToF 或机械尺寸，必须先读 `docs/vendor/VENDOR_INDEX.md` 及其指向资料，并在输出中写明来源。

## 9. 需要创建或更新的 sprint 文档

本轮启动阶段创建：

- `sprints/2026.05.18_05-06_route-task-material-callback-packet/pre_start.md`
- `sprints/2026.05.18_05-06_route-task-material-callback-packet/prd.md`
- `sprints/2026.05.18_05-06_route-task-material-callback-packet/tech-plan.md`

实现完成后由 Product closeout 更新：

- `sprints/2026.05.18_05-06_route-task-material-callback-packet/tech-done.md`
- `sprints/2026.05.18_05-06_route-task-material-callback-packet/side2side_check.md`
- `sprints/2026.05.18_05-06_route-task-material-callback-packet/final.md`
