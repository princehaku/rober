# Sprint 2026.05.18_04-05 Route Task Field Retest Material Pack - PRD

sprint_type: epic

## 1. 用户价值

现场 owner 已经能看到上一轮 result review handoff，但还缺一份可执行材料包来指导“下一次真实回填必须采什么、由谁采、用哪个 safe `evidence_ref`、采完后如何回调复核”。本轮把 handoff 转成 `route_task_field_retest_material_pack`，让 route/elevator 现场准备从聊天式交接变成可复核的 checklist 和 callback skeleton。

## 2. 产品北极星

低成本 ROS2 垃圾投递机器人要能在真实路线/电梯现场形成可追责证据链。当前本机只有 Docker，所以本轮只交付 software proof 的材料包和只读消费面，不把材料包写成真实送达、真实电梯、真实 HIL 或真实手机验收。

## 3. OKR 映射

- Objective 2：服务 KR2.4 / KR2.5 / KR2.6 / KR2.7，把失败原因、任务记录、电梯 evidence 和人工接管材料拆成 owner work orders。
- Objective 3：服务 KR3.2 / KR3.3 / KR3.4 / KR3.5，把 Nav2/fixed-route runtime log、route completion signal 和 task record 采集要求固化。
- Objective 4：手机端只读展示材料包，让普通用户/现场支持知道当前不是 delivery success，也不能触发主操作。
- Objective 5：不推进；缺真实外部 proof。
- Objective 1：不推进；缺真实 WAVE ROVER/UART/HIL。

## 4. PR / 评审输入

- PR #4 要求 elevator assisted delivery 成为主链路，材料包必须覆盖电梯门状态、目标楼层确认、人工协助记录和继续送达结果。
- PR #5 review 暴露硬件 baseline / vendor source 风险，本轮材料包不得引入新的硬件参数、SKU、串口、波特率或传感器假设；如出现硬件字段，只能作为“需真实资料回填”的材料类型。
- 最新 `03-04_route-task-result-review-handoff` final 指出下一步必须要真实 callback 回填材料和同一 `evidence_ref` 上车复账；本轮软件产物正是这条回填路径的准备动作。

## 5. 验收口径

本轮完成时必须满足：

- PC gate 输出 `trashbot.route_task_field_retest_material_pack.v1` 和 summary v1，包含 `material_pack_status`、safe `evidence_ref`、field_capture_checklist、callback_payload_skeleton、owner_work_orders、rerun_commands、not_proven、`delivery_success=false`、`primary_actions_enabled=false`。
- Robot diagnostics 可消费 artifact/summary/wrapper/nested JSON，输出 `route_task_field_retest_material_pack`、`route_task_field_retest_material_pack_summary`、`robot_diagnostics_route_task_field_retest_material_pack_summary` 三个兼容 alias。
- mobile/web 只读展示材料包，不新增 Start Delivery、Confirm Dropoff、Cancel、dispatch、callback 或 robot command。
- docs 同步更新：`docs/interfaces/evidence_contracts.md`、`docs/interfaces/ros_contracts.md`、`docs/product/mobile_user_flow.md`、`docs/process/okr_progress_log.md`。
- 所有验证只使用围栏命令：py_compile、focused unittest、node --check、required rg、scoped diff check。

## 6. 非目标

- 不读取真实材料目录。
- 不访问 ROS graph、Nav2 runtime、serial/UART、WAVE ROVER、外部云、4G、OSS/CDN、DB/queue 或真实手机/browser。
- 不生成真实 field pass、HIL pass、delivery success、dropoff/cancel completion 或 Objective 5 production proof。
