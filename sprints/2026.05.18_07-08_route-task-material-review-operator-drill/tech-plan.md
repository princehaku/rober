# Sprint 2026.05.18_07-08 Route Task Material Review Operator Drill - Tech Plan

sprint_type: epic

## 1. 技术目标

让 `route_task_field_retest_operator_drill` 从上一轮 `route_task_field_retest_material_callback_review_decision` 继续推进，而不是回退到 material pack-only drill。

固定 literal：

- `route_task_field_retest_material_callback_review_decision`
- `route_task_field_retest_operator_drill`
- `trashbot.route_task_field_retest_operator_drill.v1`
- `trashbot.route_task_field_retest_operator_drill_summary.v1`
- `software_proof_docker_route_task_field_retest_operator_drill_gate`
- `not_proven`
- `delivery_success=false`
- `primary_actions_enabled=false`

新增或补强能力：

1. PC gate：读取 `route_task_field_retest_material_callback_review_decision` artifact / summary / wrapper / nested diagnostics，生成同一 schema 的 operator drill artifact / summary。
2. Robot diagnostics：验证或小补 `route_task_field_retest_operator_drill` summary 的 metadata-only consumer。
3. mobile/web：验证或小补 first-screen “现场操作演练” panel，只读展示 operator drill summary。
4. Product closeout：工程完成后更新 OKR/progress/sprint docs，保持证据边界。

## 2. OKR 最低优先级核对

- 当前 `OKR.md` 4.1 节完成度最低的 Objective：Objective 5，约 68%。
- 本 sprint 是否针对该最低 Objective：否。
- 理由：Objective 5 继续推进必须有真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue connectivity、production worker/migration/cutover 或真实手机/browser external proof；当前本机只有 Docker，无法产生这类 evidence。O5 stop rule 继续成立，继续增加本地 O5 metadata depth 会重复消费 blocker。
- 下一低项 Objective 1 约 81%，本轮也不针对。原因是剩余进展必须依赖真实 WAVE ROVER、UART、串口/topic samples、`feedback_T1001.log`、`/odom`、`/imu/data`、`/battery` 或 operator HIL report；当前没有真实硬件。PR #5 review 暴露的 hardware baseline / vendor source 风险保留为真实材料缺口，不用本地文档包装成完成。
- 本 sprint 选择 Objective 2 / 3 / 4：PR #4 把 elevator-assisted delivery 写成必达能力，上一轮已经完成 `route_task_field_retest_material_callback_review_decision`；下一步最小有效功能是把 review decision 接入 `route_task_field_retest_operator_drill`，让现场执行从最新复核结论继续。
- final.md 收口时需复核：上述 O5/O1 blocker 是否仍成立，是否拿到真实外部云、真实硬件或真实手机/browser 材料。

## 3. 文件范围和 owner

Task A / Autonomy Algorithm Engineer 可改：

- `pc-tools/evidence/route_task_field_retest_operator_drill.py`
- `pc-tools/evidence/test_route_task_field_retest_operator_drill.py`
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
- `sprints/2026.05.18_07-08_route-task-material-review-operator-drill/tech-done.md`
- `sprints/2026.05.18_07-08_route-task-material-review-operator-drill/side2side_check.md`
- `sprints/2026.05.18_07-08_route-task-material-review-operator-drill/final.md`

范围外文件不得改动。A/B/C 文件范围互不重叠，必须并行派 3 个 worker；Product closeout 等 A/B/C 验证完成后执行。

## 4. 接口契约

PC gate 必须新增支持的 source：

- `schema=trashbot.route_task_field_retest_material_callback_review_decision.v1`
- `schema=trashbot.route_task_field_retest_material_callback_review_decision_summary.v1`
- `evidence_boundary=software_proof_docker_route_task_field_retest_material_callback_review_decision_gate`
- safe `evidence_ref`
- `same_evidence_ref_required=true`
- `review_decision`
- `material_callback_review_summary`
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

PC gate 输出必须保持：

- `schema=trashbot.route_task_field_retest_operator_drill.v1`
- `schema_version=1`
- `summary_schema=trashbot.route_task_field_retest_operator_drill_summary.v1`
- `evidence_boundary=software_proof_docker_route_task_field_retest_operator_drill_gate`
- `source_schema` 指向 review decision artifact 或 summary。
- `source_boundary=software_proof_docker_route_task_field_retest_material_callback_review_decision_gate`
- `safe_evidence_ref`
- `same_evidence_ref_required=true`
- `operator_drill_status`
- `next_operator_commands`
- `callback_checklist`
- `required_outputs`
- `rerun_commands`
- `safe_copy`
- `not_proven`
- `delivery_success=false`
- `primary_actions_enabled=false`

建议状态：

- `ready_for_route_task_field_retest_operator_drill_not_proven`
- `needs_material_callback_backfill_before_operator_drill_not_proven`
- `evidence_ref_mismatch_rerun_operator_drill_not_proven`
- `blocked_missing_route_task_field_retest_operator_drill_not_proven`
- `unsupported_material_callback_review_decision_schema_not_proven`
- `unsafe_success_claim_rejected_not_proven`

## 5. Worker A / Autonomy 任务

目标：修改 PC gate 和 focused test，让 operator drill 消费 material callback review decision。

必须实现：

- 支持从 `route_task_field_retest_material_callback_review_decision` artifact、summary、wrapper、nested diagnostics 中读取来源。
- 保留对旧 material pack 输入的兼容性，但优先选择 review decision source；测试必须覆盖不回退到 material pack-only drill。
- 校验 source schema、source boundary、safe `evidence_ref`、same-evidence-ref、disabled action flags。
- 根据 `review_decision`、accepted / missing / rejected materials、owner acknowledgement、next required evidence 输出 operator commands、callback checklist 和 rerun commands。
- 拒绝 unsupported schema、bad boundary、weak evidence ref、evidence ref mismatch、unsafe raw path、credentials、OSS/DB/queue/token material、success claim、`delivery_success=true`、`primary_actions_enabled=true`。
- 更新 `docs/interfaces/evidence_contracts.md`，说明 operator drill 可消费 material callback review decision，但不是真实 route/elevator field pass、Nav2/fixed-route proof、task record/completion signal、dropoff/cancel completion、delivery success、HIL、WAVE ROVER/UART、真实手机/browser 或 Objective 5 external proof。

验收命令：

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile pc-tools/evidence/route_task_field_retest_operator_drill.py
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest pc-tools/evidence/test_route_task_field_retest_operator_drill.py
rg -n "route_task_field_retest_material_callback_review_decision|route_task_field_retest_operator_drill|software_proof_docker_route_task_field_retest_operator_drill_gate|trashbot.route_task_field_retest_operator_drill.v1|trashbot.route_task_field_retest_operator_drill_summary.v1|not_proven|delivery_success=false|primary_actions_enabled=false" pc-tools/evidence docs/interfaces/evidence_contracts.md
git diff --check -- pc-tools/evidence/route_task_field_retest_operator_drill.py pc-tools/evidence/test_route_task_field_retest_operator_drill.py docs/interfaces/evidence_contracts.md
```

## 6. Worker B / Robot 任务

目标：验证或小补 Robot diagnostics 对 operator drill summary 的只读支持。

必须实现或确认：

- `operator_gateway_diagnostics.py` 能消费 `route_task_field_retest_operator_drill`、`route_task_field_retest_operator_drill_summary`、wrapper 或 nested diagnostics summary。
- 输出 alias：`route_task_field_retest_operator_drill`、`route_task_field_retest_operator_drill_summary`、`robot_diagnostics_route_task_field_retest_operator_drill_summary`。
- 若 Autonomy 新增 review-decision-derived 字段，Robot 只输出 whitelist metadata，不输出 raw artifact、raw command、local path、credentials、ROS topic、serial/UART、Nav2/HIL claim 或 success wording。
- fail closed on missing summary、unsupported schema、bad boundary、weak evidence ref、unsafe raw fields、success claim、enabled action。
- 不输出 collect/dropoff/cancel/ACK/cursor/Nav2/HIL/field pass/Start enablement/Confirm enablement/Cancel enablement。
- 更新 `docs/interfaces/ros_contracts.md`。

验收命令：

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py
rg -n "route_task_field_retest_material_callback_review_decision|route_task_field_retest_operator_drill|software_proof_docker_route_task_field_retest_operator_drill_gate|trashbot.route_task_field_retest_operator_drill_summary.v1|not_proven|delivery_success=false|primary_actions_enabled=false" onboard/src/ros2_trashbot_behavior docs/interfaces/ros_contracts.md
git diff --check -- onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py docs/interfaces/ros_contracts.md
```

## 7. Worker C / Full-Stack 任务

目标：验证或小补 mobile/web first-screen “现场操作演练” panel。

必须实现或确认：

- 从 status/readiness/diagnostics 多入口读取 `route_task_field_retest_operator_drill_summary`，并支持 compatible Robot diagnostics summary。
- panel 顺序保留在 `route_task_field_retest_material_callback_review_decision` 之后；有 review decision 时不把用户导回 material pack-only drill。
- 展示 operator drill status、safe `evidence_ref`、next operator commands、callback checklist、required outputs、rerun commands、evidence boundary。
- copy/export whitelist-only；没有 backend `safe_copy` 时显示 blocked copy unavailable。
- 保持 Start Delivery、Confirm Dropoff、Cancel、dispatch、callback、ACK、cursor、robot command gating 不变。
- 文案必须明确 `not_proven`、`delivery_success=false`、`primary_actions_enabled=false`。
- 更新 `docs/product/mobile_user_flow.md`。

验收命令：

```bash
node --check mobile/web/app.js
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest mobile.web.test_mobile_web_entrypoint
rg -n "route_task_field_retest_material_callback_review_decision|route_task_field_retest_operator_drill|software_proof_docker_route_task_field_retest_operator_drill_gate|not_proven|delivery_success=false|primary_actions_enabled=false|现场操作演练" mobile docs/product/mobile_user_flow.md
git diff --check -- mobile/web/app.js mobile/fixtures/mobile_web_status.fixture.json mobile/web/test_mobile_web_entrypoint.py docs/product/mobile_user_flow.md
```

## 8. Product Closeout 任务

Product closeout 必须在 A/B/C 完成后执行：

- 更新 `OKR.md`：记录 O2/O3/O4 software proof 是否可保守推进；Objective 5 保持约 68%，Objective 1 不因本轮上调。
- 更新 `docs/process/okr_progress_log.md`。
- 创建/更新本 sprint `tech-done.md`、`side2side_check.md`、`final.md`。
- 明确本轮不是 real route/elevator field pass、Nav2/fixed-route proof、task record/completion signal、dropoff/cancel completion、delivery success、HIL、WAVE ROVER/UART、真实手机/browser 或 Objective 5 external proof。

验收命令：

```bash
rg -n "route_task_field_retest_material_callback_review_decision|route_task_field_retest_operator_drill|software_proof_docker_route_task_field_retest_operator_drill_gate|Objective 5|Objective 1|PR #4|PR #5|not_proven|delivery_success=false|primary_actions_enabled=false" OKR.md docs/process/okr_progress_log.md sprints/2026.05.18_07-08_route-task-material-review-operator-drill
git diff --check -- OKR.md docs/process/okr_progress_log.md sprints/2026.05.18_07-08_route-task-material-review-operator-drill
```

## 9. 并行启动要求

A/B/C 文件范围互不重叠，且接口通过 schema literal、summary 字段、boundary 和 fail-closed flags 对齐。实现阶段必须在同一轮并行发起 3 个 worker：

- A `autonomy-engineer`：PC gate、focused test、evidence docs。
- B `robot-software-engineer`：diagnostics contract 验证/小补、ROS contract docs。
- C `full-stack-software-engineer`：mobile first-screen panel 验证/小补、mobile flow docs。

Product Owner 不写产品代码、测试代码或硬件配置，只做 closeout 和 OKR/sprint 文档收口。

## 10. 风险与阻塞

- 如果 operator drill 被写成 real route/elevator field pass，则验收失败。
- 如果 operator drill 被写成 Nav2/fixed-route proof、task record/completion signal、dropoff/cancel completion、delivery success、HIL、真实手机/browser 或 Objective 5 external proof，则验收失败。
- 如果 diagnostics 或 mobile/web 因 operator drill 存在而启用 Start / Confirm / Cancel / dispatch / callback / ACK / cursor / robot command，则验收失败。
- 如果 implementation 回退到只消费 material pack，且不消费 `route_task_field_retest_material_callback_review_decision`，则验收失败。
- 如果 worker 需要新增 WAVE ROVER、UART、波特率、JSON 指令、速度映射、反馈协议、引脚、电压、固件、2D LiDAR、ToF 或机械尺寸事实，必须先读 `docs/vendor/VENDOR_INDEX.md`，否则验收失败。
- 本轮没有真实现场材料，因此不会证明 real route/elevator field pass、Nav2/fixed-route proof、task record/completion signal、dropoff/cancel completion、delivery success、HIL、WAVE ROVER/UART、真实手机/browser 或 Objective 5 external proof。
