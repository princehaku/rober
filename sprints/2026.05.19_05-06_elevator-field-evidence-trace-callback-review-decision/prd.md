# Sprint 2026.05.19_05-06 Elevator Field Evidence Trace Callback Review Decision - PRD

## 1. 用户价值和产品北极星

现场 owner 回填 route/elevator 材料后，不能只靠聊天结论判断“可以继续跑”。本轮把上一轮 callback intake 结果升级成明确 review decision：告诉现场、Robot、mobile 下一步是继续补材料、重新回执，还是可以进入下一段 owner handoff。

北极星仍是普通手机用户能理解机器人为什么不能继续、缺什么现场材料、下一步谁处理；本轮不做真实电梯运行、不做实机送达、不做云端生产验收。

## 2. OKR 映射

- Objective 2：推进 elevator-assisted delivery 现场证据链的复核决策层，避免把 intake ready 当作实机通过。
- Objective 3：把 Nav2/fixed-route runtime log、route completion signal、field task record 等缺口继续作为 review decision 的 hard requirement。
- Objective 4：手机端只读展示 review decision、缺口和 owner handoff，帮助用户/现场人员理解下一步，不启用控制。
- Objective 1：不推进。缺真实 WAVE ROVER/UART/HIL 和 PR #5 sensor material。
- Objective 5：不推进。缺真实 external proof。

## 3. 本轮范围

### In Scope

- 新增 PC evidence gate：`elevator_field_evidence_trace_callback_review_decision`。
- 新增 Robot diagnostics safe alias：`robot_diagnostics_elevator_field_evidence_trace_callback_review_decision_summary`。
- 新增 mobile/web 只读 panel，展示 review decision、reasons、missing/rejected materials、next required evidence 和 owner handoff。
- 更新接口文档、产品流程文档、sprint closeout、OKR 和 progress log。

### Out of Scope

- 不新增真实 route/elevator 控制 API。
- 不修改 `TrashCollection` action schema。
- 不修改 serial/UART、WAVE ROVER、2D LiDAR、ToF、firmware、launch hardware 参数。
- 不读取或上传真实材料文件。
- 不提升 O5 external proof 或 O1 HIL/hardware completion。

## 4. 验收口径

- review decision schema 和 diagnostics/mobile summary 均必须是 `software_proof` / `not_proven`。
- `delivery_success` 和 `primary_actions_enabled` 必须为布尔 false。
- same safe `evidence_ref` 不匹配、缺 required material、存在 rejected material、unsafe copy、unsupported schema 都要进入 fail-closed 或 backfill 决策。
- mobile/web 只能只读展示，Start Delivery、Confirm Dropoff、Cancel gating 不因本轮变更而放开。
- 验证只跑围栏命令：focused unittest、`py_compile`、`node --check`、required `rg`、scoped `git diff --check`。

## 5. 输出物

- `trashbot.elevator_field_evidence_trace_callback_review_decision.v1`
- `trashbot.elevator_field_evidence_trace_callback_review_decision_summary.v1`
- `robot_diagnostics_elevator_field_evidence_trace_callback_review_decision_summary`
- mobile/web read-only `elevator_field_evidence_trace_callback_review_decision` panel

## 6. 剩余风险

即使本轮全部围栏验证通过，仍缺真实电梯、真实 Nav2/fixed-route、真实 route completion signal、真实现场 task record、dropoff/cancel completion、delivery success、WAVE ROVER/UART/HIL、真实手机/browser、O5 external proof 和 PR #5 真实 sensor material。
