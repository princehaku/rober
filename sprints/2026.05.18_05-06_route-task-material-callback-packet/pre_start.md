# Sprint 2026.05.18_05-06 Route Task Material Callback Packet - Pre Start

sprint_type: epic

## 1. 启动结论

本轮启动新 sprint：`2026.05.18_05-06_route-task-material-callback-packet`。

本轮目标是把上一 sprint `2026.05.18_04-05_route-task-field-retest-material-pack` 留下的 callback skeleton 推进为可填写、可校验、可回传、可被 Robot diagnostics 和 mobile/web 只读消费的 `route_task_field_retest_material_callback_packet`。上一轮已经完成 `software_proof_docker_route_task_field_retest_material_pack_gate`，但 skeleton 只是字段列表；现场 owner 仍缺一份能够承载真实回填材料、同一 safe `evidence_ref`、owner 签收、缺口原因、复跑命令和只读摘要的 packet。

证据边界固定为：`software_proof_docker_route_task_field_retest_material_callback_packet_gate`。

Schema 固定为：

- `trashbot.route_task_field_retest_material_callback_packet.v1`
- `trashbot.route_task_field_retest_material_callback_packet_summary.v1`

本轮不是 real route/elevator field pass，不是 Nav2/fixed-route proof，不是 task record/completion signal，不是 dropoff/cancel completion，不是 delivery success，不是 HIL，不是 WAVE ROVER/UART，不是真实手机/browser，不是 Objective 5 external proof。

## 2. 用户价值和产品北极星

用户价值：现场复测同学拿到的不再是“应该填哪些字段”的 skeleton，而是一份可以按项填写、回传、被系统 fail-closed 校验并在手机端解释的 callback packet。它降低真实 route/elevator 现场材料回填时漏采、错填、跨 `evidence_ref`、误写成功结论和误触发主操作的风险。

产品北极星：低成本 ROS2 垃圾投递机器人要把“用户交垃圾后能跨路线/电梯可靠送达”推进到可验证证据链，而不是堆本地 metadata。当前主机只有 Docker，所以本轮只交付 software proof 的 callback packet，不把它写成真实送达、真实电梯、真实手机、真实硬件或真实云证据。

## 3. Live Evidence 与切换理由

当前 `OKR.md` 4.1 显示：

- Objective 5 约 68%，数值最低；但没有真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/cutover 或真实手机/browser external proof。继续做本地 O5 metadata depth 不能推动真实 completion。
- Objective 1 约 81%；但最近三轮已围绕 WAVE ROVER HIL packet 做 intake、review decision、execution pack。剩余 blocker 是真实 WAVE ROVER、UART、串口/topic samples 和 operator HIL report。本机没有真实硬件，继续包装同一 blocker 会重复消费。
- Objective 2 / Objective 3 已接近 99%，但缺口是 PR #4 要求的真实 route/elevator field materials：真实门状态、真实楼层确认、人工协助记录、Nav2/fixed-route runtime log、同一 `evidence_ref` 的 task record/completion signal、dropoff/cancel completion 和 delivery result。

上一 sprint `2026.05.18_04-05_route-task-field-retest-material-pack/final.md` 已完成 `software_proof_docker_route_task_field_retest_material_pack_gate`，明确 material pack 只是 checklist / callback skeleton / owner work orders / rerun commands；下一步应该把 skeleton 变成可交付 packet，而不是继续停留在字段列表。

## 4. PR / Review 证据

- PR #4 证据：elevator-assisted delivery 已被写入必达能力，路线/电梯材料链必须覆盖门状态、目标楼层确认、人工协助、继续送达、投放或取消结果，不能把电梯流程当可选 demo。
- PR #5 证据：hardware baseline 与 2D LiDAR / ToF / source material 风险仍存在。当前本轮不新增 SKU、串口、波特率、ToF 通道数、WAVE ROVER 指令或硬件假设；只把这些真实材料缺口保留为 callback packet 中的待回填证据类型。
- 上一轮 final 证据：`route_task_field_retest_material_pack` 已把 field capture checklist 和 callback skeleton 打包，但没有生成可回传 packet，也没有 Robot/mobile 可读的 callback packet summary。

## 5. 本轮核心抓手

本轮核心抓手：`route_task_field_retest_material_callback_packet`。

必须具备：

- 可从上一轮 material pack artifact/summary/wrapper/nested diagnostics 中读取来源。
- 固定同一 safe `evidence_ref`，并在 mismatch、missing、unsafe raw field、success claim、action enablement、unsupported schema 时 fail closed。
- 允许现场 owner 填写材料回传状态、采集结果引用、缺失原因、下一次补采动作、owner 签收和 rerun commands。
- 输出 PC artifact 与 summary v1，Robot diagnostics 只读消费，mobile/web 只读展示。
- 保持 `not_proven`、`delivery_success=false`、`primary_actions_enabled=false`。

## 6. Owner 与执行边界

Task A / Autonomy Algorithm Engineer：

- 文件范围：`pc-tools/evidence/route_task_field_retest_material_callback_packet.py`、对应 focused test、`docs/interfaces/evidence_contracts.md`。
- 目标：生成和校验 callback packet artifact / summary。

Task B / Robot Platform Engineer：

- 文件范围：`onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py`、对应 diagnostics test、`docs/interfaces/ros_contracts.md`。
- 目标：metadata-only 消费 callback packet summary，并输出 fail-closed diagnostics alias。

Task C / User Touchpoint Full-Stack Engineer：

- 文件范围：`mobile/web/app.js`、mobile fixture/test、`docs/product/mobile_user_flow.md`。
- 目标：在手机端只读展示 callback packet 状态，不改变 Start Delivery、Confirm Dropoff、Cancel 或任何 robot command gating。

Product closeout：

- 文件范围：`OKR.md`、`docs/process/okr_progress_log.md`、本 sprint `tech-done.md`、`side2side_check.md`、`final.md`。
- 目标：只在 worker 完成后记录证据、边界和 OKR 进展；不得把本轮写成真实 field pass 或 O5 external proof。

## 7. 风险、阻塞与证据链

- O5 blocker：缺真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/cutover、真实手机/browser external proof。
- O1 blocker：缺真实 WAVE ROVER、UART、串口/topic samples、operator HIL report、`feedback_T1001.log`、`/odom`、`/imu/data`、`/battery`。
- O2/O3 blocker：缺真实 route/elevator field pass、Nav2/fixed-route proof、task record/completion signal、dropoff/cancel completion、delivery success。
- O4 blocker：缺真实手机/browser、production app、真实 PWA prompt/user choice。
- PR #5 hardware blocker：缺真实 2D LiDAR / ToF SKU/source/receipt/procurement/installation/wiring/power/calibration/HIL-entry。

本轮只能补齐 callback packet 的 software proof。后续只有真实 field callback 材料回填后，才可进入 result acceptance 或 field pass 复账。
