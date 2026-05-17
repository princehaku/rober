# Sprint 2026.05.17_13-14 Route Task Handoff Result Reconciliation Bridge - Tech Plan

sprint_type: epic

## 1. 技术方案

本轮在既有 `route_task_field_retest_result_reconciliation` gate 上做窄改：当输入 result-intake artifact / summary 的 `source_result` 指向 `route_task_field_retest_review_result_handoff` 时，reconciliation 输出显式携带安全 lineage metadata。Robot diagnostics 和 mobile/web 只读消费这些字段。

所有输出继续保持：

- `trashbot.route_task_field_retest_result_reconciliation.v1`
- `trashbot.route_task_field_retest_result_reconciliation_summary.v1`
- `software_proof_docker_route_task_field_retest_result_reconciliation_gate`
- `not_proven`
- `delivery_success=false`
- `primary_actions_enabled=false`

## 2. 文件范围与分工

### Task A - Autonomy Algorithm Engineer

允许改动：

- `pc-tools/evidence/route_task_field_retest_result_reconciliation.py`
- `pc-tools/evidence/test_route_task_field_retest_result_reconciliation.py`
- `pc-tools/README.md`
- `docs/navigation/fixed_route_workflow.md`
- 本 sprint `tech-done.md` 中 Task A 段落

要求：

- 在 artifact / summary 中添加 handoff-derived result-intake lineage 字段。
- 增加 focused test：输入 wrapper/nested result-intake，且 result-intake 的 `source_result.schema` 为 `trashbot.route_task_field_retest_review_result_handoff.v1` 或 `_summary.v1` 时，reconciliation 输出保留安全 lineage。
- 不读取 raw handoff artifact；不改变 required result materials。

验收命令：

```bash
python3 -m py_compile pc-tools/evidence/route_task_field_retest_result_reconciliation.py
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest pc-tools/evidence/test_route_task_field_retest_result_reconciliation.py
python3 pc-tools/evidence/route_task_field_retest_result_reconciliation.py --help
rg -n "source_review_result_handoff|source_result_intake|software_proof_docker_route_task_field_retest_result_reconciliation_gate|not_proven|delivery_success=false|primary_actions_enabled=false" pc-tools/evidence pc-tools/README.md docs/navigation/fixed_route_workflow.md sprints/2026.05.17_13-14_route-task-handoff-result-reconciliation-bridge
git diff --check -- pc-tools/evidence/route_task_field_retest_result_reconciliation.py pc-tools/evidence/test_route_task_field_retest_result_reconciliation.py pc-tools/README.md docs/navigation/fixed_route_workflow.md sprints/2026.05.17_13-14_route-task-handoff-result-reconciliation-bridge/tech-done.md
```

### Task B - Robot Platform Engineer

允许改动：

- `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py`
- `onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`
- `docs/interfaces/ros_contracts.md`
- 本 sprint `tech-done.md` 中 Task B 段落

要求：

- `summarize_route_task_field_retest_result_reconciliation` 只读透传 safe lineage metadata。
- 继续支持 file/env/top-level/nested summary。
- 缺字段、unsupported schema、unsafe copy、success/control claim 必须 fail closed。

验收命令：

```bash
python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py
rg -n "source_review_result_handoff|source_result_intake|route_task_field_retest_result_reconciliation|software_proof_docker_route_task_field_retest_result_reconciliation_gate|not_proven|delivery_success=false|primary_actions_enabled=false" onboard/src/ros2_trashbot_behavior docs/interfaces sprints/2026.05.17_13-14_route-task-handoff-result-reconciliation-bridge
git diff --check -- onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py docs/interfaces/ros_contracts.md sprints/2026.05.17_13-14_route-task-handoff-result-reconciliation-bridge/tech-done.md
```

### Task C - User Touchpoint Full-Stack Engineer

允许改动：

- `mobile/web/app.js`
- `mobile/web/fixtures/status.json`
- `mobile/web/test_mobile_web_entrypoint.py`
- `docs/product/mobile_user_flow.md`
- 本 sprint `tech-done.md` 中 Task C 段落

要求：

- Result reconciliation panel 展示 handoff-derived result-intake lineage。
- Copy/export payload 只包含白名单安全字段。
- Start Delivery / Confirm Dropoff / Cancel gating 不变。

验收命令：

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest mobile.web.test_mobile_web_entrypoint
node --check mobile/web/app.js
rg -n "source_review_result_handoff|source_result_intake|route_task_field_retest_result_reconciliation|software_proof_docker_route_task_field_retest_result_reconciliation_gate|not_proven|delivery_success=false|primary_actions_enabled=false" mobile/web docs/product sprints/2026.05.17_13-14_route-task-handoff-result-reconciliation-bridge
git diff --check -- mobile/web/app.js mobile/web/fixtures/status.json mobile/web/test_mobile_web_entrypoint.py docs/product/mobile_user_flow.md sprints/2026.05.17_13-14_route-task-handoff-result-reconciliation-bridge/tech-done.md
```

### Task D - Product Manager / OKR Owner

允许改动：

- `OKR.md`
- `docs/process/okr_progress_log.md`
- `sprints/2026.05.17_13-14_route-task-handoff-result-reconciliation-bridge/tech-done.md`
- `sprints/2026.05.17_13-14_route-task-handoff-result-reconciliation-bridge/side2side_check.md`
- `sprints/2026.05.17_13-14_route-task-handoff-result-reconciliation-bridge/final.md`

要求：

- 待 Task A/B/C 返回后收口。
- 若只完成软件 lineage bridge，Objective 2 / 3 最多保守小幅更新；Objective 5 不更新。
- 明确剩余真实材料缺口。

验收命令：

```bash
rg -n "source_review_result_handoff|source_result_intake|route_task_field_retest_result_reconciliation|Objective 2|Objective 3|Objective 5|PR #4|PR #5|not_proven|delivery_success=false|primary_actions_enabled=false" OKR.md docs/process/okr_progress_log.md sprints/2026.05.17_13-14_route-task-handoff-result-reconciliation-bridge
git diff --check -- OKR.md docs/process/okr_progress_log.md sprints/2026.05.17_13-14_route-task-handoff-result-reconciliation-bridge
```

## 3. OKR 最低优先级核对

1. 当前 `OKR.md` 4.1 最低 Objective：Objective 5，约 68%。
2. 本 sprint 不针对 Objective 5。
3. 理由：本机没有真实硬件和真实外部云/4G/OSS/CDN/DB/queue/手机材料；`OKR.md` 第 6 节明确要求只有真实外部材料到位才继续推进 O5 completion。近期 PR #4/#5 与最近 sprint final 表明当前可执行主线是 O2/O3 的 route/elevator field-material 链路；PR #5 的真实 2D LiDAR / ToF 材料仍缺失，不能再把硬件 blocker 包成第三轮本地 metadata。

## 4. 接口边界

- 不新增 schema major version。
- 不改变 existing result reconciliation required materials。
- 新字段只能是安全 summary/lineage metadata。
- Robot/mobile 只能消费 summary 和 safe copy，不消费 raw artifact。
