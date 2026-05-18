# Sprint 2026.05.19_04-05 Elevator Field Evidence Trace Callback Intake - Side2Side Check

## sprint_type: epic

Check time: 2026-05-19 04:22 Asia/Shanghai.

## 用户价值和产品北极星

验收目标不是证明小车真实进出电梯或完成送达，而是确认本轮新增链路是否能把未来现场 owner 回填的 callback packet、`elevator_action_feedback_trace`、Robot diagnostics/mobile summary 和 route/elevator required materials 放到同一 safe `evidence_ref` 下做只读 intake 判定。

产品北极星保持：送垃圾机器人必须能面向普通手机用户解释当前阶段、缺失材料和下一步人工补证动作。本轮只补可判定回填入口，证据边界是 `software_proof`、`not_proven`。

## Side-by-Side 验收

| 计划验收口径 | 实际结果 | 判定 |
| --- | --- | --- |
| P0：same safe `evidence_ref` 是主键；缺失、不安全或不一致必须 blocked。 | Autonomy gate 覆盖 same ref、mismatch、weak/unsafe ref，Robot diagnostics/mobile 只读消费 summary。 | 通过，软件围栏内成立。 |
| P0：`source=software_proof`、`overall_status=not_proven`、`delivery_success=false`、`primary_actions_enabled=false`。 | Autonomy artifact/summary、Robot alias、mobile fixture/panel 均保留这些边界。 | 通过，未放宽控制边界。 |
| P0：不得启用 Start Delivery、Confirm Dropoff、Cancel、ACK、cursor、command 或任何 primary action。 | Full-Stack 保持按钮 gating 不变；Robot unsafe/control fields fail closed。 | 通过，仍是只读 panel。 |
| P1：callback packet 只能接受 phone-safe / redacted / metadata-only 字段。 | Autonomy/Robot 均对 raw ROS topic、本机路径、凭证、traceback、success/control claims fail closed；docs 明确 phone-safe 边界。 | 通过，仍需后续真实 packet 现场验证。 |
| P1：缺真实材料必须列出 `missing_required_materials`，不得补默认成功值。 | Summary 和 mobile panel 展示 missing materials / owner handoff；callback ready 仍保持 `not_proven`。 | 通过。 |
| P2：Robot/mobile 展示只读摘要，帮助现场 owner 复盘下一步材料回填动作。 | 新增 `robot_diagnostics_elevator_field_evidence_trace_callback_intake_summary` 和 mobile/web 只读 panel。 | 通过。 |

## OKR 映射验收

- Objective 2：记录为电梯 assisted delivery 现场材料回填入口的 `software_proof` 可判定性进展，仍约 99%，不写成真实 field pass。
- Objective 3：记录为 route/fixed-route required materials intake 进展，仍约 99%，不写成真实 Nav2/fixed-route runtime。
- Objective 4：记录为手机端只读展示和 owner handoff 进展，仍约 99%，不写成真实手机/browser 验收。
- Objective 1：无真实 WAVE ROVER/UART/HIL 或 PR #5 2D LiDAR / ToF 材料，保持约 81%。
- Objective 5：无真实外部云/4G/OSS/CDN/DB/queue/phone external proof，保持约 68%。

## 风险、阻塞和需要补齐的证据链

- 仍缺真实电梯门状态、目标楼层确认、人工协助记录、Nav2/fixed-route runtime log、route completion signal、现场 task record、dropoff/cancel completion、delivery result。
- 仍缺真实 WAVE ROVER/UART/HIL、真实 phone/browser 和 PR #5 真实 2D LiDAR / ToF SKU/source/receipt/procurement/installation/wiring/power/calibration/HIL-entry。
- 本轮 `callback_packet_intake_ready_for_review_not_proven` 只能进入后续 review decision；不得在 OKR、PR 或用户汇报中写成 `delivery_success`、`field_pass`、`hil_pass` 或 production proof。

## 文档同步检查

- Sprint closeout 文档已补齐：`tech-done.md`、`side2side_check.md`、`final.md`。
- 相关工程文档由 worker 更新：`docs/interfaces/elevator_field_evidence_trace_callback_intake.md`、`docs/interfaces/operator_gateway_diagnostics.md`、`docs/product/mobile_user_flow.md`。
- Product closeout 同步更新：`OKR.md`、`docs/process/okr_progress_log.md`。
