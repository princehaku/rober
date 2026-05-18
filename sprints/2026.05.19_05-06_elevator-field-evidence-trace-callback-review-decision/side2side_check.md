# Sprint 2026.05.19_05-06 Elevator Field Evidence Trace Callback Review Decision - Side2Side Check

## sprint_type: epic

Check time: 2026-05-19 05:23 Asia/Shanghai.

## 用户价值和产品北极星

验收目标不是证明小车真实进出电梯或完成送达，而是确认本轮新增链路是否能把上一轮 callback intake 结果复核成明确 review decision，并把缺失材料、拒收材料、下一步 owner handoff 只读展示给 Robot diagnostics 和 mobile/web。

## Side-by-Side 验收

| 计划验收口径 | 实际结果 | 判定 |
| --- | --- | --- |
| P0：只读消费上一轮 callback intake artifact/summary，不读取真实材料目录。 | Autonomy gate 只读 intake JSON，支持 artifact/summary/wrapper/env source；不访问 ROS graph、Nav2、硬件、云或手机。 | 通过，软件围栏内成立。 |
| P0：same safe `evidence_ref` 是主键；缺失、不安全或不一致必须 blocked。 | PC gate 覆盖 same-ref mismatch/weak ref；Robot alias 校验 safe ref；mobile 只读展示 safe ref。 | 通过。 |
| P0：`source=software_proof`、`overall_status=not_proven`、`delivery_success=false`、`primary_actions_enabled=false`。 | PC artifact/summary、Robot alias、mobile fixture/panel 均保留这些边界。 | 通过。 |
| P0：不得启用 Start Delivery、Confirm Dropoff、Cancel 或任何 primary action。 | Full-Stack 保持 gating 不变；Robot unsafe/control fields fail closed。 | 通过。 |
| P1：缺真实材料必须进入 backfill 或 rerun，不得默认为通过。 | `needs_route_elevator_material_backfill_not_proven`、`needs_callback_packet_rerun_not_proven` 和 rejected material 分支均有测试覆盖。 | 通过。 |
| P2：Robot/mobile 展示只读复核摘要，帮助现场 owner 安排下一步材料回填。 | 新增 Robot diagnostics alias 与 mobile/web “电梯现场证据回调复核决策” panel。 | 通过。 |

## OKR 映射验收

- Objective 2：记录为电梯 assisted delivery callback review decision 的 `software_proof` 可判定性进展，仍约 99%，不写成真实 field pass。
- Objective 3：记录为 route/fixed-route required materials review decision 进展，仍约 99%，不写成真实 Nav2/fixed-route runtime。
- Objective 4：记录为手机端只读展示和 owner handoff 进展，仍约 99%，不写成真实手机/browser 验收。
- Objective 1：无真实 WAVE ROVER/UART/HIL 或 PR #5 2D LiDAR / ToF 材料，保持约 81%。
- Objective 5：无真实外部云/4G/OSS/CDN/DB/queue/phone external proof，保持约 68%。

## 风险、阻塞和需要补齐的证据链

- 仍缺真实电梯门状态、目标楼层确认、人工协助记录、Nav2/fixed-route runtime log、route completion signal、现场 task record、dropoff/cancel completion、delivery result。
- 仍缺真实 WAVE ROVER/UART/HIL、真实 phone/browser 和 PR #5 真实 2D LiDAR / ToF SKU/source/receipt/procurement/installation/wiring/power/calibration/HIL-entry。
- 本轮 `ready_for_elevator_field_owner_handoff_not_proven` 只能进入后续 owner handoff 或现场材料补采；不得在 OKR、PR 或用户汇报中写成 `delivery_success`、`field_pass`、`hil_pass` 或 production proof。

## 文档同步检查

- Sprint closeout 文档已补齐：`tech-done.md`、`side2side_check.md`、`final.md`。
- 相关工程文档由 worker 更新：`docs/interfaces/elevator_field_evidence_trace_callback_review_decision.md`、`docs/interfaces/operator_gateway_diagnostics.md`、`docs/product/mobile_user_flow.md`。
- Product closeout 同步更新：`OKR.md`、`docs/process/okr_progress_log.md`。
