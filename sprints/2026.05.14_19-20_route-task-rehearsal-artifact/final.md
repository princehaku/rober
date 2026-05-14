# Sprint 2026.05.14_19-20 Route Task Rehearsal Artifact - Final

sprint_type: epic

## 收口结论

本 sprint 完成 `software_proof_docker_route_task_rehearsal_artifact_gate`。Task A 已让 `evidence_crosscheck.py` 保存 route/task rehearsal artifact；Task B 已让 task record / behavior fixed-route evidence anchor 更稳定；Task C 已按软件证据边界更新 OKR、进度日志和 closeout 文档。

Objective 2 和 Objective 3 各从约 77% 谨慎上调到约 78%。Objective 5 保持约 68%，因为本轮没有真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue connectivity、production worker/migration 或其他真实外部 O5 证据。

## 实际改动

Task A `autonomy-engineer`：

- `pc-tools/evidence/evidence_crosscheck.py`
- `onboard/src/ros2_trashbot_behavior/test/test_task_record.py`
- `pc-tools/README.md`
- `docs/navigation/fixed_route_workflow.md`

Task B `robot-software-engineer`：

- `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/task_record.py`
- `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/task_orchestrator.py`
- `onboard/src/ros2_trashbot_behavior/test/test_task_orchestrator_collection_execution.py`
- `onboard/src/ros2_trashbot_behavior/test/test_task_orchestrator_fixed_route_status.py`
- `docs/interfaces/ros_contracts.md`

Task C `product-okr-owner`：

- `OKR.md`
- `docs/process/okr_progress_log.md`
- `sprints/2026.05.14_19-20_route-task-rehearsal-artifact/tech-done.md`
- `sprints/2026.05.14_19-20_route-task-rehearsal-artifact/side2side_check.md`
- `sprints/2026.05.14_19-20_route-task-rehearsal-artifact/final.md`

## 验证结果

- Task A：`python3 -m py_compile pc-tools/evidence/evidence_crosscheck.py` pass；`python3 onboard/src/ros2_trashbot_behavior/test/test_task_record.py` Ran 8 tests OK；required `rg` pass；scoped `git diff --check` pass。
- Task B：behavior py_compile pass；`test_task_record.py` Ran 8 tests OK；`test_task_orchestrator_collection_execution.py` Ran 10 tests OK；`test_task_orchestrator_fixed_route_status.py` Ran 6 tests OK；required `rg` pass；scoped `git diff --check` pass。
- Task C：required `rg` 与 scoped `git diff --check` 已执行，输出见最终聊天汇总。

## 阶段验收

通过。P0 验收项均满足：

- artifact 可保存，并包含 schema/version、`evidence_ref`、route/task summary、crosscheck status、HIL alignment status 和 `not_proven`。
- artifact 明确输出 `software_proof_docker_route_task_rehearsal_artifact_gate`。
- blocked HIL 或缺 HIL gate 时，artifact 仍只作为软件排练证据保存。
- task record / behavior evidence anchor 与 fixed-route status/replay 对账路径对齐。
- 文档已同步 route/task rehearsal artifact、`route_progress`、`evidence_ref` 和非 HIL 边界。

## OKR 最低优先级回顾

tech-plan 中的 OKR 最低优先级核对理由仍成立：Objective 5 仍是数字最低（约 68%），但本轮期间没有真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/migration 或其他真实外部材料出现。继续推进本地 O5 metadata depth 不会移动 O5 completion，因此本轮切到 Objective 2/3 的 route/task rehearsal artifact 合理。

下一轮如果真实 O5 外部材料出现，应优先回到 Objective 5；如果仍没有外部材料，O2/O3 的下一步应从本轮 software proof 走向真实 Nav2/fixed-route、真实路线采集和同一 `evidence_ref` 的上车复账，而不是继续扩大 artifact 文档。

## OKR 与风险

本轮直接服务 Objective 2 KR5 和 Objective 3 KR2/KR3/KR5：任务复盘、固定路线软件对账和 PC evidence 保存链路变得可复核。上调幅度限制为各约 1pp，因为证据仍是 Docker/local software proof。

剩余风险：

- 真实 Nav2/fixed-route、真实路线采集、关键帧实景证据未完成。
- WAVE ROVER、真实串口、HIL 与同一 `evidence_ref` 的上车复账未完成。
- dropoff/cancel completion、真实失败恢复和 delivery success 未完成。
- Objective 5 external proof 仍缺：公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue connectivity、production worker/migration 均未出现。
