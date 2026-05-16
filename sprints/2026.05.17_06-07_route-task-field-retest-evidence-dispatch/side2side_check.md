# Sprint 2026.05.17_06-07 Route Task Field Retest Evidence Dispatch - Side2Side Check

sprint_type: epic

## 1. 验收对象

本次验收对象是 `route_task_field_retest_evidence_dispatch` 从 PC gate 到 Robot diagnostics 再到 mobile/web 只读 panel 的 software-proof closeout 链路，以及 Product 对 sprint closeout、OKR 和进度日志的收口。

## 2. 对照检查

| 检查项 | 结果 | 说明 |
| --- | --- | --- |
| 用户价值 | pass | 已把 acceptance brief 的证据要求推进为 owner/file/backfill/callback dispatch，方便现场支持补齐真实 route/elevator 材料。 |
| OKR 映射 | pass | Objective 2 / Objective 3 保守上调，Objective 4 / Objective 1 / Objective 5 不上调。 |
| 证据边界 | pass | 文档保持 `software_proof_docker_route_task_field_retest_evidence_dispatch_gate`、Docker-only、`not_proven`、`delivery_success=false`、`primary_actions_enabled=false`。 |
| A/B/C worker 汇总 | pass | Task A Autonomy、Task B Robot、Task C Full-stack 的文件、验证、失败定位和风险已写入 `tech-done.md`。 |
| 手机主操作 gating | pass | Task C 结果确认 Start Delivery / Confirm Dropoff / Cancel gating 不变。 |
| Robot action 语义 | pass | Task B 结果确认 collect/dropoff/cancel/ACK/Nav2/HIL/cursor/delivery success 不变。 |
| Objective 5 stop rule | pass | Objective 5 仍约 66%，没有把本地 metadata depth 写成 external proof。 |
| PR #4 / PR #5 边界 | pass | 明确电梯材料与 2D LiDAR / ToF 硬件材料仍需真实补齐。 |

## 3. 验收命令

```bash
rg -n "route_task_field_retest_evidence_dispatch|software_proof_docker_route_task_field_retest_evidence_dispatch_gate|Objective 2|Objective 3|Objective 4|Objective 5|Docker-only|not_proven|delivery_success=false|primary_actions_enabled=false|PR #4|PR #5" sprints/2026.05.17_06-07_route-task-field-retest-evidence-dispatch OKR.md docs/process/okr_progress_log.md

git diff --check -- sprints/2026.05.17_06-07_route-task-field-retest-evidence-dispatch/tech-done.md sprints/2026.05.17_06-07_route-task-field-retest-evidence-dispatch/side2side_check.md sprints/2026.05.17_06-07_route-task-field-retest-evidence-dispatch/final.md OKR.md docs/process/okr_progress_log.md

git status --short
```

## 4. 验收结果

```text
rg -n "route_task_field_retest_evidence_dispatch|software_proof_docker_route_task_field_retest_evidence_dispatch_gate|Objective 2|Objective 3|Objective 4|Objective 5|Docker-only|not_proven|delivery_success=false|primary_actions_enabled=false|PR #4|PR #5" sprints/2026.05.17_06-07_route-task-field-retest-evidence-dispatch OKR.md docs/process/okr_progress_log.md
exit 0
Representative matches:
OKR.md:161 Objective 2 约 89% with software_proof_docker_route_task_field_retest_evidence_dispatch_gate.
OKR.md:162 Objective 3 约 89% with route_task_field_retest_evidence_dispatch.
OKR.md:163 Objective 4 保持约 99% with not_proven, delivery_success=false, primary_actions_enabled=false.
OKR.md:164 Objective 5 保持约 66% and not real Objective 5 external proof.
docs/process/okr_progress_log.md:21 records PR #4 / PR #5 boundaries, Docker-only, not_proven, delivery_success=false, primary_actions_enabled=false.

git diff --check -- sprints/2026.05.17_06-07_route-task-field-retest-evidence-dispatch/tech-done.md sprints/2026.05.17_06-07_route-task-field-retest-evidence-dispatch/side2side_check.md sprints/2026.05.17_06-07_route-task-field-retest-evidence-dispatch/final.md OKR.md docs/process/okr_progress_log.md
exit 0; no output.

git status --short
M OKR.md
M docs/interfaces/ros_contracts.md
M docs/navigation/fixed_route_workflow.md
M docs/process/okr_progress_log.md
M docs/product/mobile_user_flow.md
M mobile/web/app.js
M mobile/web/fixtures/status.json
M mobile/web/styles.css
M mobile/web/test_mobile_web_entrypoint.py
M onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py
M onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py
M pc-tools/README.md
?? pc-tools/evidence/route_task_field_retest_evidence_dispatch.py
?? pc-tools/evidence/test_route_task_field_retest_evidence_dispatch.py
?? sprints/2026.05.17_06-07_route-task-field-retest-evidence-dispatch/
```

## 5. 剩余风险

- 该链路只证明当前 repo 的本地 software proof / metadata-only fail-closed 证据包派发能力。
- 不证明真实 route/elevator field pass、真实 Nav2/fixed-route、真实 task record、真实 route completion signal、真实 dropoff/cancel completion、delivery success、真实手机/browser、production app、WAVE ROVER、真实串口/UART、HIL 或 Objective 5 external proof。
- 下一步需要真实现场材料按同一 `evidence_ref` 回填，否则 Objective 2 / Objective 3 不应继续因本地 wrapper 上调。
