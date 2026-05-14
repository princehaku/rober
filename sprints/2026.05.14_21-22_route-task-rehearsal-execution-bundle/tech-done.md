# Sprint 2026.05.14_21-22 Route Task Rehearsal Execution Bundle - Tech Done

sprint_type: epic

## 实际改动

Task A `autonomy-engineer` 新增 `pc-tools/evidence/route_task_rehearsal_bundle.py`，复用 `evidence_crosscheck.run_crosscheck()` 生成底层 route/task rehearsal artifact，再输出 schema 为 `trashbot.route_task_rehearsal_execution_bundle` 的 manifest。首轮集成核对发现 generator 与 diagnostics consumer 的 manifest shape 不一致，crosscheck/HIL 摘要只在 `artifact_status` 内；修复后 manifest 顶层直接包含 `route_task_rehearsal_artifact_ref`、`crosscheck_status`、`hil_alignment_status`、`diagnostics_summary`，并保留 `artifact_status` 兼容。

Task B `robot-software-engineer` 新增 diagnostics summary `route_task_rehearsal_execution_bundle`，支持 explicit `route_task_rehearsal_bundle_ref` 和环境变量 `TRASHBOT_ROUTE_TASK_REHEARSAL_BUNDLE`，同时保留旧 artifact summary 兼容。missing、read_error、unsupported schema、crosscheck fail 均保守降级，`primary_actions_enabled=false`，不触发 ACK POST、cursor、Start/Confirm/Cancel enablement、HIL 或 delivery success claim。

Product closeout 更新本文件、`side2side_check.md`、`final.md`、`OKR.md` 和 `docs/process/okr_progress_log.md`。OKR 口径为 Objective 2 与 Objective 3 各从约 79% 保守上调到约 80%；Objective 5 仍最低约 68%，但本轮无真实外部云/4G/OSS/CDN/DB/queue 材料，不上调。

## 验证结果

Autonomy worker 验证：

```text
python3 -m py_compile pc-tools/evidence/route_task_rehearsal_bundle.py
pass

python3 pc-tools/evidence/route_task_rehearsal_bundle.py --help
pass

临时 /tmp drill
CHECK summary: mismatches=0
top_level_artifact_ref_present: True
top_level_crosscheck_status: pass
top_level_hil_alignment_status: not_proven
top_level_diagnostics_summary_present: True

required rg
pass

scoped git diff --check
pass
```

Robot worker 验证：

```text
python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py
pass

PYTHONDONTWRITEBYTECODE=1 python3 -m unittest onboard.src.ros2_trashbot_behavior.test.test_operator_gateway_diagnostics
Ran 48 tests ... OK

required rg
pass

scoped git diff --check
pass
```

Product closeout 验证：

```text
rg -n "2026.05.14_21-22_route-task-rehearsal-execution-bundle|software_proof_docker_route_task_rehearsal_execution_bundle_gate|Objective 2|Objective 3|Objective 5|not_proven|delivery success|HIL" OKR.md docs/process/okr_progress_log.md sprints/2026.05.14_21-22_route-task-rehearsal-execution-bundle
pass: output includes current sprint path, evidence boundary, Objective 2/3/5 updates, `not_proven`, HIL boundary, and delivery success non-claim lines.

git diff --check -- OKR.md docs/process/okr_progress_log.md sprints/2026.05.14_21-22_route-task-rehearsal-execution-bundle/tech-done.md sprints/2026.05.14_21-22_route-task-rehearsal-execution-bundle/side2side_check.md sprints/2026.05.14_21-22_route-task-rehearsal-execution-bundle/final.md
pass: no output, exit code 0.
```

## 偏差与修复

- 首轮 Autonomy manifest 与 Robot diagnostics consumer 的 shape 不一致，crosscheck/HIL 摘要只在 `artifact_status` 内；已退回 Autonomy worker 修复，并重新验证顶层字段存在。
- 本轮没有运行真实硬件、真实串口、真实 Nav2/fixed-route 或真实手机/cloud 验收；证据边界保持为 `software_proof_docker_route_task_rehearsal_execution_bundle_gate`。

## 剩余风险

- `not_proven` 仍包括真实路线采集、Nav2 waypoint/fixed-route 实跑、WAVE ROVER、真实串口、HIL、同一 `evidence_ref` 的上车复账、dropoff/cancel completion 和 delivery success。
- Objective 5 仍最低约 68%，但继续推进需要真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue connectivity 或 production worker/migration 材料；本机 Docker-only 无法提供。
