# Side By Side Check

sprint_type: epic

Sprint: `2026.05.22_22-23_field-evidence-rerun-acceptance-backfill-review-decision`

Capability: `field_evidence_rerun_execution_result_acceptance_backfill_review_decision`

Evidence boundary: `software_proof_docker_field_evidence_rerun_execution_result_acceptance_backfill_review_decision_gate`

## 用户价值和产品北极星

产品北极星仍是低成本 ROS2 垃圾投递机器人：普通用户通过手机触发和理解送垃圾任务，系统把路线、电梯、手机状态和现场证据链做成可复盘、可交接、可阻断的闭环。

本轮用户价值不是证明真实送达，而是把 `field_evidence_rerun_execution_result_acceptance_backfill` 的回填结果转成可复核决策，方便 field owner / support / reviewer 判断下一步是 handoff、补材料、修正 evidence_ref、拒绝 unsafe 材料，还是等待 backfill。

## OKR 映射

- Objective 2：补 route/elevator field rerun result acceptance 的 review-decision 链路，但不证明真实 delivery。
- Objective 3：补现场复跑结果证据链的 PC gate 和 evidence contract，但不证明真实 Nav2/fixed-route runtime。
- Objective 4：补手机端只读 panel，让普通用户/支持人员能看到复核决策和 blocked reason，但不证明 true phone/browser。
- Objective 5：当前仍最低，约 68%；本轮没有外部云、OSS/CDN、4G 或 production proof，不提升。
- Objective 1：约 81%；PR #5 `PRRT_kwDOSWB9286CJ3tX` 仍 unresolved / `hardware_material_pending`，不提升。

## KR 拆解或更新

- PC gate：Autonomy owner 已交付 `field_evidence_rerun_execution_result_acceptance_backfill_review_decision`，输出 review decision 分类。
- Robot safe alias：Robot owner 已交付 `robot_diagnostics_field_evidence_rerun_execution_result_acceptance_backfill_review_decision_summary`。
- Mobile read-only panel：Full-Stack owner 已交付“现场证据复跑执行结果验收回填复核决策”面板。
- Product closeout：本文件、`tech-done.md`、`final.md`、`OKR.md`、`docs/process/okr_progress_log.md` 已按 no-lift 边界收口。

## 核心抓手和验收口径

验收只接受 software proof：

- `source=software_proof`
- `not_proven`
- `delivery_success=false`
- `primary_actions_enabled=false`
- `safe_to_control=false`
- `software_proof_docker_field_evidence_rerun_execution_result_acceptance_backfill_review_decision_gate`

主操作必须 fail-closed；Start Delivery / Confirm Dropoff / Cancel 不能因本轮 review-decision metadata 启用。

## Side By Side 对照

| 项目 | 预期 | 本轮结果 |
| --- | --- | --- |
| PC review-decision gate | 从 acceptance backfill safe metadata 输出 handoff / more material / mismatch / unsafe / blocked 分类 | A Autonomy 已实现并通过 `Ran 5 tests in 0.096s OK` |
| Robot safe summary | 只暴露 safe alias、safe source、safe decision 和 disabled flags | B Robot 已实现并通过 `Ran 293 tests in 2.345s OK` |
| Mobile read-only panel | 展示 review decision 和缺口，主操作保持 disabled | C Full-Stack 已实现并通过 `Ran 272 tests in 2.310s OK` |
| OKR 证据边界 | no OKR percentage lift；不写成真实手机、真实送达、O5 external proof 或 O1 HIL | Product closeout 已保守更新 |
| PR #5 live state | `PRRT_kwDOSWB9286CJ3tQ` / `PRRT_kwDOSWB9286CJ3tU` resolved；`PRRT_kwDOSWB9286CJ3tX` unresolved | 已按 unresolved / `hardware_material_pending` 写入 closeout |

## 风险、阻塞和证据链缺口

- `PRRT_kwDOSWB9286CJ3tX` remains `is_resolved=false` / unresolved / `hardware_material_pending`。
- 本轮不是 true phone/browser proof，不是 route/elevator field pass，不是 Nav2/fixed-route runtime pass，不是 verified terminal result，不是 dropoff/cancel completion，不是 delivery success，不是 Objective 5 external proof，不是 Objective 1 HIL。
- 仍需同一 safe `evidence_ref` 的真实 field rerun result、真实 task record、真实 route/elevator pass、真实 Nav2/fixed-route runtime log、真实 dropoff/cancel completion、真实手机/browser 证据、真实 O5 external proof 或真实 WAVE ROVER/HIL material 才能推动对应 OKR 百分比。
