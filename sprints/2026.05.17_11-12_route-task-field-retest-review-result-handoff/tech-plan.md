# Sprint 2026.05.17_11-12 Route Task Field Retest Review Result Handoff - Tech Plan

sprint_type: epic

## 1. 技术目标

新增 `route_task_field_retest_review_result_handoff` planning baseline，让下一步实现可以把 `route_task_field_retest_callback_review_decision` 安全转成 result-intake 前交接包。该交接包只做 read-only、metadata-only、software proof，不触发真实动作、不生成真实送达结论。

固定 gate 和边界：

- `software_proof_docker_route_task_field_retest_review_result_handoff_gate`
- `not_proven`
- `delivery_success=false`
- `primary_actions_enabled=false`

## 2. 架构和接口方案

### 输入

输入来自上一轮：

- `trashbot.route_task_field_retest_callback_review_decision.v1`
- `trashbot.route_task_field_retest_callback_review_decision_summary.v1`

必须兼容 artifact、summary、wrapper、nested diagnostics summary，但不需要读取真实硬件、真实 Nav2、真实手机或云端材料。

### 输出

计划新增：

- `trashbot.route_task_field_retest_review_result_handoff.v1`
- `trashbot.route_task_field_retest_review_result_handoff_summary.v1`

核心字段建议：

- `schema`
- `gate`
- `source_schema`
- `safe_evidence_ref`
- `source_review_decision`
- `handoff_status`
- `result_intake_readiness`
- `required_result_materials`
- `owner_handoff`
- `blocked_reasons`
- `next_operator_action`
- `same_evidence_ref_required=true`
- `not_proven=true`
- `delivery_success=false`
- `primary_actions_enabled=false`
- `boundary`

### Decision mapping

| source review decision | handoff_status | result_intake_readiness |
| --- | --- | --- |
| `ready_for_result_intake` | `ready_for_result_intake_handoff` | `ready_for_result_material_intake` |
| `needs_material_backfill` | `blocked_until_material_backfill` | `not_ready` |
| `evidence_ref_mismatch_rerun` | `blocked_until_same_evidence_ref_rerun` | `not_ready` |
| `unsupported_callback_schema` | `blocked_unsupported_source_schema` | `not_ready` |
| `blocked_unsafe_callback` | `blocked_unsafe_source_review` | `not_ready` |
| `blocked_success_claim` | `blocked_unsafe_source_review` | `not_ready` |

## 3. Owner 拆分和文件范围

### Task A - Autonomy PC gate

Owner：`autonomy-engineer`

允许改动：

- `pc-tools/evidence/route_task_field_retest_review_result_handoff.py`
- `pc-tools/evidence/test_route_task_field_retest_review_result_handoff.py`
- `pc-tools/README.md`
- `docs/navigation/fixed_route_workflow.md`

实现要求：

- 新增 dependency-free CLI。
- 支持 `--callback-review-json`、`--evidence-ref`、`--output`、`--summary-output`、`--once-json`。
- 对 unsupported source schema、missing safe evidence ref、success/control claim、`delivery_success=true`、`primary_actions_enabled=true` fail closed。
- 输出 artifact 和 summary 都必须包含 `software_proof_docker_route_task_field_retest_review_result_handoff_gate`、`not_proven`、`delivery_success=false`、`primary_actions_enabled=false`。

验收命令：

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile pc-tools/evidence/route_task_field_retest_review_result_handoff.py
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest pc-tools/evidence/test_route_task_field_retest_review_result_handoff.py
python3 pc-tools/evidence/route_task_field_retest_review_result_handoff.py --help
rg -n "route_task_field_retest_review_result_handoff|software_proof_docker_route_task_field_retest_review_result_handoff_gate|not_proven|delivery_success=false|primary_actions_enabled=false|ready_for_result_intake|needs_material_backfill|evidence_ref_mismatch_rerun" pc-tools/evidence docs/navigation/fixed_route_workflow.md
git diff --check -- pc-tools/evidence/route_task_field_retest_review_result_handoff.py pc-tools/evidence/test_route_task_field_retest_review_result_handoff.py pc-tools/README.md docs/navigation/fixed_route_workflow.md
```

### Task B - Robot diagnostics consumer

Owner：`robot-software-engineer`

允许改动：

- `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py`
- `onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`
- `docs/interfaces/ros_contracts.md`

实现要求：

- 新增 `route_task_field_retest_review_result_handoff` / `_summary` metadata-only diagnostics consumer。
- 只暴露 sanitized summary、safe `evidence_ref`、handoff status、result-intake readiness、required materials、owner handoff、blocked reasons、boundary。
- 不新增 ACK、cursor、Nav2 command、dropoff/cancel result、delivery result 或 primary action。
- 对 missing、unsupported、unsafe、success phrasing、`delivery_success=true`、`primary_actions_enabled=true` fail closed。

验收命令：

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py
rg -n "route_task_field_retest_review_result_handoff|software_proof_docker_route_task_field_retest_review_result_handoff_gate|metadata-only|not_proven|delivery_success=false|primary_actions_enabled=false" onboard/src/ros2_trashbot_behavior docs/interfaces/ros_contracts.md
git diff --check -- onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py docs/interfaces/ros_contracts.md
```

### Task C - Full-stack mobile/web read-only panel

Owner：`full-stack-software-engineer`

允许改动：

- `mobile/web/app.js`
- `mobile/web/styles.css`
- `mobile/web/fixtures/status.json`
- `mobile/web/test_mobile_web_entrypoint.py`
- `docs/product/mobile_user_flow.md`

实现要求：

- 新增只读“现场复测结果交接” panel。
- 消费 `route_task_field_retest_review_result_handoff`、`route_task_field_retest_review_result_handoff_summary` 和 Robot diagnostics summary。
- 展示 safe `evidence_ref`、handoff status、source review decision、result-intake readiness、required materials、owner handoff、blocked reasons 和 boundary。
- copy/export whitelist-only。
- 不改变 Start Delivery、Confirm Dropoff、Cancel gating，不新增 result-intake 请求，不显示真实完成或真实送达语义。

验收命令：

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest mobile/web/test_mobile_web_entrypoint.py
node --check mobile/web/app.js
rg -n "route_task_field_retest_review_result_handoff|software_proof_docker_route_task_field_retest_review_result_handoff_gate|not_proven|delivery_success=false|primary_actions_enabled=false|现场复测结果交接" mobile/web docs/product/mobile_user_flow.md
git diff --check -- mobile/web/app.js mobile/web/styles.css mobile/web/fixtures/status.json mobile/web/test_mobile_web_entrypoint.py docs/product/mobile_user_flow.md
```

### Task D - Product closeout

Owner：`product-okr-owner`

允许改动：

- `sprints/2026.05.17_11-12_route-task-field-retest-review-result-handoff/tech-done.md`
- `sprints/2026.05.17_11-12_route-task-field-retest-review-result-handoff/side2side_check.md`
- `sprints/2026.05.17_11-12_route-task-field-retest-review-result-handoff/final.md`
- `OKR.md`
- `docs/process/okr_progress_log.md`

实现要求：

- 汇总 Task A/B/C 真实验证输出。
- 只在实现完成并有验证证据后更新 OKR 进度。
- 明确本轮不是真实 route/elevator field pass、HIL、真实手机/browser、Objective 5 external proof、真实投放、dropoff/cancel completion 或 delivery success。

验收命令：

```bash
rg -n "route_task_field_retest_review_result_handoff|software_proof_docker_route_task_field_retest_review_result_handoff_gate|Objective 2|Objective 3|Objective 5|PR #4|PR #5|not_proven|delivery_success=false|primary_actions_enabled=false" sprints/2026.05.17_11-12_route-task-field-retest-review-result-handoff OKR.md docs/process/okr_progress_log.md
git diff --check -- sprints/2026.05.17_11-12_route-task-field-retest-review-result-handoff OKR.md docs/process/okr_progress_log.md
```

## 4. 接口影响

- PC 侧新增 result-handoff artifact / summary contract。
- Robot diagnostics 只新增 metadata-only read path，不影响 ROS2 action/topic/service。
- mobile/web 只新增 read-only panel，不影响 command API、Start、Confirm Dropoff、Cancel 或 recovery gating。
- 不引入硬件参数、串口、WAVE ROVER、2D LiDAR、ToF、电压、引脚或机械尺寸假设。

## 5. 验证围栏

本 sprint 实现阶段只运行 scoped commands：

- Autonomy：`py_compile`、focused unittest、CLI help、required `rg`、scoped `git diff --check`。
- Robot：`py_compile`、focused unittest、required `rg`、scoped `git diff --check`。
- Full-stack：mobile unittest、`node --check`、required `rg`、scoped `git diff --check`。
- Product：required `rg` 和 scoped `git diff --check`。

不运行 broad regression，也不把 Docker-only software proof 写成 HIL 或真实现场结果。

## 6. OKR 最低优先级核对

当前 `OKR.md` 4.1 中完成度最低的 Objective 是 Objective 5，约 68%。

本 sprint 不针对 Objective 5，原因如下：

- Objective 5 的有效提升需要真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue connectivity、production worker/migration/cutover 或真实手机/browser 证据。
- 当前本机只有 Docker，无法提供真实 external proof。
- 近期已多次消费 O5 外部环境 blocker；继续新增本地 metadata wrapper 不会形成真实 Objective 5 进展。
- PR #5 硬件 source/config blocker 也已多次消费，当前缺真实 SKU/source/receipt/install/wiring/calibration/HIL-entry 材料，不适合作为本轮主线继续重复包装。

本 sprint 针对 Objective 2 和 Objective 3，因为最新 PR #4 route/elevator callback review decision 已到 `ready_for_result_intake` / backfill / mismatch / blocked 层，下一步最可行动作是补 result-intake 前交接包。

## 7. 完成前反思清单

- 是否仍然只在 `software_proof_docker_route_task_field_retest_review_result_handoff_gate` 边界内。
- 是否没有启用真实 Start、Confirm Dropoff、Cancel、ACK、cursor、Nav2 command 或 result-intake 请求。
- 是否没有把 `ready_for_result_intake` 写成真实结果完成。
- 是否所有 owner 都保留 `not_proven`、`delivery_success=false`、`primary_actions_enabled=false`。
- 是否实现后同步更新相关 `docs/` 和 sprint closeout。
- 是否没有修改本计划文件范围外的无关文件。
