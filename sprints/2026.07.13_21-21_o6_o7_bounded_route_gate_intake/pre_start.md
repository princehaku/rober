# Pre Start - O6/O7 Bounded Route Gate Intake

## Sprint Metadata

- sprint_type: epic
- Sprint: `sprints/2026.07.13_21-21_o6_o7_bounded_route_gate_intake/`
- started_at: 2026-07-13 21:21 CST
- Product owner: `product-okr-owner`
- Primary implementation owner: `robot-software-engineer`
- Supporting implementation owner: `full-stack-software-engineer`
- Target Objective: O6/O7 same-task mission evidence consumption, with O5 blocker explicitly skipped
- Direction judgment: adjust away from repeated O5 CDN/TLS 4xx blocker and consume the accepted O3 bounded route gate material into O6/O7

## User Value And Product North Star

普通手机用户最终需要看到一条任务从路线材料、执行前安全 gate、bounded command plan、现场执行、送达结果到验收材料的完整证据链。本 sprint 不执行路线、不发控制命令，只把 07:07 fail-closed controlled route execution gate 和 08:09 no-motion bounded route command plan 变成 O6/O7 selected-task 可接收、可回读、可解释的任务材料。

本 sprint 必须固定安全边界：不发送 `/cmd_vel`、不调用 `/api/base/manual`、不触发 NavigateToPose、不访问 WAVE ROVER UART。所有成功和失败输出都必须固定 `safe_to_control=false`、`delivery_success=false`、`route_execution_success=false`、`hil_pass=false`、`robot_control_executed=false`。

## Recent Evidence Reviewed

- `sprints/2026.07.13_19-19_o5_cdn_tls_readiness_packet_consumption/final.md`：O5 仍 blocked 在 `blocked_http_status_not_success_class`，源 artifact 为 `http_status_class=4xx` / `accepted_claim=none`，O5 继续约 `85%`，KR `不归档`。
- `sprints/2026.07.13_20-20_o6_o7_phone_browser_proof_intake/final.md`：O6/O7 phone-browser terminal material intake 已接受为 support-only；下一轮不得继续堆 wrapper/readback-only，必须消费 distinct mission material。
- `sprints/2026.07.13_07-07_o3_controlled_route_execution_gate_record/final.md`：已接受同一 `packet_id` 的 fail-closed execution gate record，明确 `route_csv_row_count=28`、`packet_jsonl_event_count=28`、`route_execution_success=false`。
- `sprints/2026.07.13_08-09_o3_bounded_route_command_plan/final.md`：已接受 bounded route command plan，明确 `execution_plan_status=blocked_pending_live_safety_gate`、`segment_count=27`、`global_abort_criteria` 有 11 项。

## Non-Repeating Blocker Reason

本轮不继续 O5 同一 blocker，原因：

- 最近两轮 O5 都围绕同一 CDN/TLS 4xx artifact 消费，继续探测或包装会第三次消费 `blocked_http_status_not_success_class`。
- 当前没有 success-class HTTPS/TLS endpoint、production DB/queue、worker cutover、OSS/CDN origin fetch/upload、4G/SIM 或真实 phone/browser production evidence。
- O1/O3 live HIL / route execution 需要 explicit operator approval，本自动化不能默认发 motion/control。
- O6/O7 是下一个低进度可推进项；本轮消费的是已存在但尚未进入 O6/O7 主证据链的 bounded route gate material，不重复 20:20 phone/browser intake。

## Needed Work

`robot-software-engineer` 需要补 O6 archive/consumer contract：

- 新增 `bounded_route_execution_gate_material` section，schema 建议为 `trashbot.o6.bounded_route_execution_gate_material.v1`。
- 接收 selected task 的 07:07 controlled gate 与 08:09 bounded plan 安全摘要：`packet_id`、`task_id`、`route_intent_id`、28/28/28 counts、`execution_plan_status`、`segment_count`、`global_abort_criteria_count`、safe refs 和 missing prerequisites。
- 回读只允许 safe basename/ref/count/status/blocked reasons/next evidence，不回显 raw path payload、控制命令、UART、完整 local path、traceback 或危险 true field。

`full-stack-software-engineer` 需要补 O7 selected-task intake/readback：

- 新增 `POST /api/o7/consumer-read/tasks/:taskId/bounded-route-gate/intake?baseUrl=<local-loopback-url>`。
- Adapter 只允许 local-loopback O6 baseUrl，并只转发 bounded route gate 安全摘要。
- Receipt 显示 `bounded_route_execution_gate_material_written/readback`、`same_task_id_consumed`、`packet_id`、`segment_count`、`execution_plan_status`、fixed false fields 和 next required evidence。
- 非回环 URL、task mismatch、dangerous true、unsafe refs/text、route execution success true 或 control/HIL true 必须 fail closed。

## Acceptance Boundary

接受为：

- O6/O7 bounded route gate material local/mock intake/readback software proof。
- 同一 `task_id` 的 07:07/08:09 execution-gate material 进入 O6 archive，并能被 O7 selected-task 主路径回读。
- fixed false fields 明确存在：`safe_to_control=false`、`delivery_success=false`、`route_execution_success=false`、`hil_pass=false`、`robot_control_executed=false`。

拒绝为：

- real route execution、fixed-route movement、NavigateToPose、controller/BT、`/cmd_vel`、`/api/base/manual` 或 WAVE ROVER UART。
- delivery/operator acceptance、真实 delivery success、current live HIL 或 safe-to-control。
- production cloud、production DB/queue、OSS/CDN live traffic、4G/SIM 或 O5 external evidence success。

## KR And History Decision

- O5 继续约 `85%`，本轮不推进同一 CDN/TLS blocker。
- O1 继续约 `94%`，本轮没有 explicit operator-approved live HIL 或 route execution。
- O6/O7 继续约 `93%`，本 sprint 预计只形成 distinct software proof，不归档 KR。
- 已完成 KR 不移动；本轮只在后续 closeout 有真实 route/delivery/HIL/production evidence 时再判断历史归档。
