# Sprint 2026.05.14_20-21 Route Task Rehearsal Diagnostics - Tech Done

sprint_type: epic

## 实际改动

本 sprint 完成 `software_proof_docker_route_task_rehearsal_diagnostics_gate`，把上一轮 route/task rehearsal artifact 从 PC 工具落盘推进到 diagnostics/support 面可消费。

Task A `autonomy-engineer`：

- `pc-tools/evidence/evidence_crosscheck.py`
- `pc-tools/README.md`
- `docs/navigation/fixed_route_workflow.md`

Task A 保持旧 `software_proof_docker_route_task_rehearsal_artifact_gate` artifact，新增 `diagnostics_summary`；summary schema 为 `trashbot.route_task_rehearsal_diagnostics_summary`，证据边界为 `software_proof_docker_route_task_rehearsal_diagnostics_gate`，只脱敏暴露 status、evidence_boundary、`evidence_ref`、crosscheck_status、hil_alignment_status、`not_proven` 和 next_step。

Task B `robot-software-engineer`：

- `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py`
- `onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`
- `docs/interfaces/ros_contracts.md`

Task B 新增 `summarize_route_task_rehearsal_artifact()`，扩展 `build_diagnostics_payload(..., route_task_rehearsal_artifact_ref=...)`，支持 `TRASHBOT_ROUTE_TASK_REHEARSAL_ARTIFACT`，输出 metadata-only 的 `route_task_rehearsal` summary，并用 valid artifact、missing/sensitive path、crosscheck fail 围栏证明它不改变控制语义。

Task C `product-okr-owner`：

- `OKR.md`
- `docs/process/okr_progress_log.md`
- `sprints/2026.05.14_20-21_route-task-rehearsal-diagnostics/tech-done.md`
- `sprints/2026.05.14_20-21_route-task-rehearsal-diagnostics/side2side_check.md`
- `sprints/2026.05.14_20-21_route-task-rehearsal-diagnostics/final.md`

## 验证结果

Task A 验证：

- `python3 -m py_compile pc-tools/evidence/evidence_crosscheck.py` pass。
- `python3 onboard/src/ros2_trashbot_behavior/test/test_task_record.py` Ran 8 tests OK。
- required `rg` pass。
- scoped `git diff --check` pass。

Task B 验证：

- `python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py` pass。
- `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest onboard.src.ros2_trashbot_behavior.test.test_operator_gateway_diagnostics` Ran 45 tests OK。
- required `rg` pass。
- scoped `git diff --check` pass。
- 中间 copy/redaction 问题已由 Task B 修复并重跑通过。

Task C 验证：

- required `rg` pass，覆盖本 sprint 名称、diagnostics gate、Objective 2/3/5、`not_proven`、delivery success 和 HIL 边界。
- scoped `git diff --check` pass。

## 偏差

无范围偏差。Task C 只更新 OKR、进度日志和本 sprint closeout 文档；未改工程 worker 文件，未回滚其他人的改动。

## 剩余风险

- 本轮仍是 Docker/local software proof，不是真实 Nav2/fixed-route、真实路线采集、真实串口、WAVE ROVER 或 HIL。
- `route_task_rehearsal` diagnostics summary 只读消费 artifact，不证明同一 `evidence_ref` 已完成上车复账。
- 本轮不证明 dropoff/cancel completion、失败恢复实测、delivery success、O5 external proof、公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic 或 production DB/queue。
