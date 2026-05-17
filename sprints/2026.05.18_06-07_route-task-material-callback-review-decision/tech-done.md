# Sprint 2026.05.18_06-07 Route Task Material Callback Review Decision - Tech Done

sprint_type: epic

## 1. 实际改动

本轮按 A/B/C worker 分工完成 `software_proof_docker_route_task_field_retest_material_callback_review_decision_gate`，把上一轮 `route_task_field_retest_material_callback_packet` 推进为“现场材料回执复核决策”。

- A / Autonomy：新增 `pc-tools/evidence/route_task_field_retest_material_callback_review_decision.py`、focused test，并更新 `docs/interfaces/evidence_contracts.md`。PC gate 读取 material callback packet artifact / summary / wrapper / nested diagnostics，输出 `trashbot.route_task_field_retest_material_callback_review_decision.v1` 与 `trashbot.route_task_field_retest_material_callback_review_decision_summary.v1`。
- B / Robot：新增 diagnostics metadata-only consumer 和 aliases：`route_task_field_retest_material_callback_review_decision`、`route_task_field_retest_material_callback_review_decision_summary`、`robot_diagnostics_route_task_field_retest_material_callback_review_decision_summary`。Robot 只读透传 safe summary，不触发 Start、Confirm Dropoff、Cancel、ACK、Nav2、HIL 或 primary actions。
- C / Full-stack：新增 mobile/web 只读“现场材料回执复核决策”panel，展示 review decision、safe `evidence_ref`、accepted/missing/rejected materials、owner acknowledgement、next required evidence、rerun commands 和 evidence boundary；copy/export whitelist-only。
- Product closeout：更新 `OKR.md`、`docs/process/okr_progress_log.md`、本 `tech-done.md`、`side2side_check.md` 与 `final.md`。

## 2. 用户价值和产品北极星

用户价值：现场 owner 不再把 material callback packet 误读为“现场已经通过”，而是能看到回执材料是否足够进入受控现场复跑、是否需要材料补齐，或是否被安全边界阻断。

产品北极星：继续服务“普通手机用户交付垃圾后，小车沿固定路线、必要时借助电梯，可靠完成投递”的证据链；本轮只补证据复核层，不把本地软件证明包装成真实送达。

## 3. OKR 映射和 KR 拆解

- Objective 2：补齐 route/elevator assisted delivery 的现场材料复核层；保守保持约 99%，不升级为 real route/elevator field pass。
- Objective 3：把 Nav2/fixed-route runtime log、route completion signal、task record、dropoff/cancel completion、delivery result 的回执材料复核结构化；保守保持约 99%，不升级为 Nav2/fixed-route proof。
- Objective 4：在 mobile/web 只读解释 review decision 和下一步材料动作；保守保持约 99%，不升级为真实手机/browser proof。
- Objective 1：保持约 81%，本轮没有 WAVE ROVER、UART、HIL、`feedback_T1001.log`、`/odom`、`/imu/data`、`/battery` 或 PR #5 真实 2D LiDAR / ToF 材料。
- Objective 5：保持约 68%，本轮没有公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue connectivity、production worker/migration/cutover 或真实 external proof。

## 4. 验证结果

A/B/C worker 已报告：

- A / Autonomy focused unittest：`Ran 5 tests OK`。
- B / Robot diagnostics unittest：`Ran 175 tests OK`。
- C / Full-stack mobile unittest：`Ran 72 tests OK`。

Product closeout 验收：

```text
rg -n "route_task_field_retest_material_callback_review_decision|software_proof_docker_route_task_field_retest_material_callback_review_decision_gate|Objective 5|Objective 1|PR #4|PR #5|not_proven|delivery_success=false|primary_actions_enabled=false" OKR.md docs/process/okr_progress_log.md sprints/2026.05.18_06-07_route-task-material-callback-review-decision
git diff --check -- OKR.md docs/process/okr_progress_log.md sprints/2026.05.18_06-07_route-task-material-callback-review-decision
```

## 5. 剩余风险

本轮不是 real route/elevator field pass、Nav2/fixed-route proof、task record/completion signal、dropoff/cancel completion、delivery success、HIL、WAVE ROVER/UART、真实手机/browser 或 Objective 5 external proof。仍需真实 PR #4 现场材料、PR #5 硬件材料、真实手机设备/browser 和真实外部云证据回填。
