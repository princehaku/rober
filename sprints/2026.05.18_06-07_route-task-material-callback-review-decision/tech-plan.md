# Sprint 2026.05.18_06-07 Route Task Material Callback Review Decision - Tech Plan

sprint_type: epic

## 1. 技术目标

新增 `route_task_field_retest_material_callback_review_decision` 三面契约：

1. PC gate：读取上一轮 `route_task_field_retest_material_callback_packet` artifact/summary/wrapper/nested diagnostics，生成复核决策 artifact 和 summary。
2. Robot diagnostics：只读消费复核决策 summary，输出 metadata-only alias，缺失或不安全时 fail closed。
3. mobile/web：只读展示复核决策状态、safe `evidence_ref`、accepted/missing/rejected materials、next required evidence、rerun commands 和安全边界，不改变任何主操作 gating。

固定 literal：

- `route_task_field_retest_material_callback_review_decision`
- `trashbot.route_task_field_retest_material_callback_review_decision.v1`
- `trashbot.route_task_field_retest_material_callback_review_decision_summary.v1`
- `software_proof_docker_route_task_field_retest_material_callback_review_decision_gate`
- `not_proven`
- `delivery_success=false`
- `primary_actions_enabled=false`

## 2. OKR 最低优先级核对

- 当前 `OKR.md` 4.1 节完成度最低的 Objective：Objective 5，约 68%。
- 本 sprint 是否针对该最低 Objective：否。
- 理由：Objective 5 继续推进必须有真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue connectivity、production worker/migration/cutover 或真实手机/browser external proof；当前本机只有 Docker，无法产生这类 evidence。继续增加本地 O5 metadata depth 会重复消费 blocker。
- 下一低项 Objective 1 约 81%，本轮也不针对。原因是最近多轮已经围绕 WAVE ROVER/HIL packet 做 replay、intake、review decision、execution pack；剩余需要真实 WAVE ROVER、UART、串口/topic samples 和 operator HIL report，本机没有真实硬件。
- 本 sprint 选择 Objective 2 / 3 / 4：PR #4 要求电梯 assisted delivery 必达，PR #5 review 要求硬件 baseline/source 材料可追溯；上一轮 callback packet 已经存在，下一步最小有效功能是 material callback review decision。
- final.md 收口时需复核：上述 O5/O1 blocker 是否仍成立，是否拿到了真实外部云或真实硬件材料。

## 3. 文件范围和 owner

Task A / Autonomy Algorithm Engineer 可改：

- `pc-tools/evidence/route_task_field_retest_material_callback_review_decision.py`
- `pc-tools/evidence/test_route_task_field_retest_material_callback_review_decision.py`
- `docs/interfaces/evidence_contracts.md`

Task B / Robot Platform Engineer 可改：

- `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py`
- `onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`
- `docs/interfaces/ros_contracts.md`

Task C / User Touchpoint Full-Stack Engineer 可改：

- `mobile/web/app.js`
- `mobile/fixtures/mobile_web_status.fixture.json`
- `mobile/web/test_mobile_web_entrypoint.py`
- `docs/product/mobile_user_flow.md`

Product closeout 可改：

- `OKR.md`
- `docs/process/okr_progress_log.md`
- `sprints/2026.05.18_06-07_route-task-material-callback-review-decision/tech-done.md`
- `sprints/2026.05.18_06-07_route-task-material-callback-review-decision/side2side_check.md`
- `sprints/2026.05.18_06-07_route-task-material-callback-review-decision/final.md`

范围外文件不得改动。A/B/C 文件范围互不重叠，必须并行派 3 个 worker；Product closeout 等 A/B/C 验证完成后执行。

## 4. 接口契约

PC artifact 必须包含：

- `schema=trashbot.route_task_field_retest_material_callback_review_decision.v1`
- `schema_version=1`
- `evidence_boundary=software_proof_docker_route_task_field_retest_material_callback_review_decision_gate`
- `source_schema=trashbot.route_task_field_retest_material_callback_packet.v1`
- `source_boundary=software_proof_docker_route_task_field_retest_material_callback_packet_gate`
- `safe_evidence_ref`
- `same_evidence_ref_required=true`
- `review_decision`
- `accepted_materials`
- `missing_materials`
- `rejected_materials`
- `owner_acknowledgement`
- `next_required_evidence`
- `rerun_commands`
- `safe_copy`
- `not_proven`
- `delivery_success=false`
- `primary_actions_enabled=false`

PC summary 必须包含：

- `schema=trashbot.route_task_field_retest_material_callback_review_decision_summary.v1`
- `source_schema=trashbot.route_task_field_retest_material_callback_review_decision.v1`
- `evidence_boundary=software_proof_docker_route_task_field_retest_material_callback_review_decision_gate`
- `review_decision`
- `safe_evidence_ref`
- `material_callback_review_summary`
- `owner_next_steps`
- `safe_copy`
- `not_proven`
- `delivery_success=false`
- `primary_actions_enabled=false`

建议状态：

- `ready_for_controlled_field_rerun_not_proven`
- `needs_material_callback_backfill_not_proven`
- `evidence_ref_mismatch_rerun_not_proven`
- `blocked_material_callback_review_not_proven`
- `unsupported_material_callback_packet_schema_not_proven`
- `unsafe_success_claim_rejected_not_proven`

## 5. Worker A / Autonomy 任务

目标：新增 PC gate 和 focused test，把 callback packet 转成复核决策。

必须实现：

- 支持从 material callback packet artifact、summary、wrapper、nested diagnostics 中读取来源。
- 校验 source schema、source boundary、safe `evidence_ref`、same-evidence-ref、disabled action flags。
- 根据 accepted / missing / rejected materials 和 owner acknowledgement 输出 review decision。
- 拒绝 unsupported schema、bad boundary、weak evidence ref、evidence ref mismatch、unsafe raw path、credentials、OSS/DB/queue/token material、success claim、action enablement。
- 更新 `docs/interfaces/evidence_contracts.md`，说明本 gate 不是真实 route/elevator field pass、Nav2/fixed-route proof、task record/completion signal、dropoff/cancel completion、delivery success、HIL、WAVE ROVER/UART、真实手机/browser 或 Objective 5 external proof。

验收命令：

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile pc-tools/evidence/route_task_field_retest_material_callback_review_decision.py
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest pc-tools/evidence/test_route_task_field_retest_material_callback_review_decision.py
rg -n "route_task_field_retest_material_callback_review_decision|software_proof_docker_route_task_field_retest_material_callback_review_decision_gate|trashbot.route_task_field_retest_material_callback_review_decision.v1|trashbot.route_task_field_retest_material_callback_review_decision_summary.v1|not_proven|delivery_success=false|primary_actions_enabled=false" pc-tools/evidence docs/interfaces/evidence_contracts.md
git diff --check -- pc-tools/evidence/route_task_field_retest_material_callback_review_decision.py pc-tools/evidence/test_route_task_field_retest_material_callback_review_decision.py docs/interfaces/evidence_contracts.md
```

## 6. Worker B / Robot 任务

目标：Robot diagnostics 只读消费 material callback review decision。

必须实现：

- 在 `operator_gateway_diagnostics.py` 中新增 metadata-only consumer。
- 支持直接 summary、artifact 派生 summary、wrapper、nested diagnostics summary。
- 输出 alias：`route_task_field_retest_material_callback_review_decision`、`route_task_field_retest_material_callback_review_decision_summary`、`robot_diagnostics_route_task_field_retest_material_callback_review_decision_summary`。
- fail closed on missing summary、unsupported schema、bad boundary、weak evidence ref、unsafe raw fields、success claim、enabled action。
- 不输出 collect/dropoff/cancel/ACK/cursor/Nav2/HIL/field pass/Start enablement/Confirm enablement/Cancel enablement。
- 更新 `docs/interfaces/ros_contracts.md`。

验收命令：

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py
rg -n "route_task_field_retest_material_callback_review_decision|software_proof_docker_route_task_field_retest_material_callback_review_decision_gate|trashbot.route_task_field_retest_material_callback_review_decision_summary.v1|not_proven|delivery_success=false|primary_actions_enabled=false" onboard/src/ros2_trashbot_behavior docs/interfaces/ros_contracts.md
git diff --check -- onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py docs/interfaces/ros_contracts.md
```

## 7. Worker C / Full-Stack 任务

目标：mobile/web 只读展示 material callback review decision。

必须实现：

- 从 status/readiness/diagnostics 多入口读取 `route_task_field_retest_material_callback_review_decision_summary`。
- 展示 review decision、safe `evidence_ref`、accepted/missing/rejected materials、owner acknowledgement、next required evidence、rerun commands、evidence boundary。
- 保持 copy/export whitelist-only。
- 保持 Start Delivery、Confirm Dropoff、Cancel、dispatch、callback、robot command gating 不变。
- 文案必须明确 `not_proven`、`delivery_success=false`、`primary_actions_enabled=false`。
- 更新 `docs/product/mobile_user_flow.md`。

验收命令：

```bash
node --check mobile/web/app.js
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest mobile.web.test_mobile_web_entrypoint
rg -n "route_task_field_retest_material_callback_review_decision|software_proof_docker_route_task_field_retest_material_callback_review_decision_gate|not_proven|delivery_success=false|primary_actions_enabled=false|现场材料回执复核决策" mobile docs/product/mobile_user_flow.md
git diff --check -- mobile/web/app.js mobile/fixtures/mobile_web_status.fixture.json mobile/web/test_mobile_web_entrypoint.py docs/product/mobile_user_flow.md
```

## 8. Product Closeout 任务

Product closeout 必须在 A/B/C 完成后执行：

- 更新 `OKR.md`：记录 O2/O3/O4 software proof 是否可保守推进；Objective 5 保持约 68%，Objective 1 不因本轮上调。
- 更新 `docs/process/okr_progress_log.md`。
- 创建/更新本 sprint `tech-done.md`、`side2side_check.md`、`final.md`。
- 明确本轮不是 real route/elevator field pass，不是 Nav2/fixed-route proof，不是 task record/completion signal，不是 dropoff/cancel completion，不是 delivery success，不是 HIL，不是 WAVE ROVER/UART，不是真实手机/browser，不是 Objective 5 external proof。

验收命令：

```bash
rg -n "route_task_field_retest_material_callback_review_decision|software_proof_docker_route_task_field_retest_material_callback_review_decision_gate|Objective 5|Objective 1|PR #4|PR #5|not_proven|delivery_success=false|primary_actions_enabled=false" OKR.md docs/process/okr_progress_log.md sprints/2026.05.18_06-07_route-task-material-callback-review-decision
git diff --check -- OKR.md docs/process/okr_progress_log.md sprints/2026.05.18_06-07_route-task-material-callback-review-decision
```

## 9. 并行启动要求

A/B/C 文件范围互不重叠，且接口通过 schema literal 与 summary 字段约束对齐。实现阶段必须在同一轮并行发起 3 个 worker：

- `autonomy-engineer` 负责 PC gate 和 evidence contract。
- `robot-software-engineer` 负责 diagnostics 和 ROS contract。
- `full-stack-software-engineer` 负责 mobile/web 和 product flow。

Product Owner 不写产品代码、测试代码或硬件配置，只做 closeout 和 OKR/sprint 文档收口。

## 10. 风险与阻塞

- 如果 review decision 被写成 route/elevator field pass，则验收失败。
- 如果 diagnostics 或 mobile/web 因 review decision 存在而启用 Start / Confirm / Cancel，则验收失败。
- 如果 review decision 接收 raw local paths、credentials、OSS/DB/queue token、serial/UART raw paths 或 success claim，则验收失败。
- 如果 worker 需要新增 WAVE ROVER、UART、波特率、JSON 指令、速度映射、反馈协议、引脚、电压、固件、2D LiDAR、ToF 或机械尺寸事实，必须先读 `docs/vendor/VENDOR_INDEX.md`，否则验收失败。
- 本轮没有真实现场材料，因此不会证明 real route/elevator field pass、Nav2/fixed-route proof、task record/completion signal、dropoff/cancel completion、delivery success、HIL、WAVE ROVER/UART、真实手机/browser 或 Objective 5 external proof。
