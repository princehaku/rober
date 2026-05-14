# Sprint 2026.05.14_19-20 Route Task Rehearsal Artifact - Tech Done

sprint_type: epic

## 实际改动

Task A `autonomy-engineer` 已完成 route/task rehearsal artifact gate：

- `pc-tools/evidence/evidence_crosscheck.py`
- `onboard/src/ros2_trashbot_behavior/test/test_task_record.py`
- `pc-tools/README.md`
- `docs/navigation/fixed_route_workflow.md`

Task A 交付内容：

- 新增 `--rehearsal-artifact`，可写出 schema/version、`evidence_boundary=software_proof_docker_route_task_rehearsal_artifact_gate`、`evidence_ref`、route/task summary、crosscheck status、HIL alignment status 和 `not_proven`。
- blocked HIL 或缺 HIL gate 时仍可保存 artifact，但 artifact 明确只表示 status/replay/task_record 软件对账，不表示真实 HIL。
- fenced test 覆盖 blocked HIL 仍可保存 artifact，并验证串口、波特率等材料被脱敏。

Task B `robot-software-engineer` 已完成 task record / behavior fixed-route evidence compatibility：

- `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/task_record.py`
- `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/task_orchestrator.py`
- `onboard/src/ros2_trashbot_behavior/test/test_task_orchestrator_collection_execution.py`
- `onboard/src/ros2_trashbot_behavior/test/test_task_orchestrator_fixed_route_status.py`
- `docs/interfaces/ros_contracts.md`

Task B 交付内容：

- `task_record.py` 忽略空 `route_progress`，必要时把 `route_progress.evidence_ref` 提升到 top-level `evidence_ref`，显式保留 evidence anchor。
- `task_orchestrator.py` 优先使用 fixed-route evidence 或 nested `route_progress` 的真实 `evidence_ref`，再回退到 status/route file。
- targeted tests 覆盖 task record、collection execution 和 fixed-route status，证明兼容逻辑不把软件状态升级为真实 delivery success。

Task C `product-okr-owner` 收口改动：

- `OKR.md`
- `docs/process/okr_progress_log.md`
- `sprints/2026.05.14_19-20_route-task-rehearsal-artifact/tech-done.md`
- `sprints/2026.05.14_19-20_route-task-rehearsal-artifact/side2side_check.md`
- `sprints/2026.05.14_19-20_route-task-rehearsal-artifact/final.md`

## 验证结果

Task A 验证：

```text
python3 -m py_compile pc-tools/evidence/evidence_crosscheck.py
pass

python3 onboard/src/ros2_trashbot_behavior/test/test_task_record.py
Ran 8 tests OK

required rg
pass

scoped git diff --check
pass
```

Task B 验证：

```text
py_compile task_record.py task_orchestrator.py
pass

python3 onboard/src/ros2_trashbot_behavior/test/test_task_record.py
Ran 8 tests OK

python3 onboard/src/ros2_trashbot_behavior/test/test_task_orchestrator_collection_execution.py
Ran 10 tests OK

python3 onboard/src/ros2_trashbot_behavior/test/test_task_orchestrator_fixed_route_status.py
Ran 6 tests OK

required rg
pass

scoped git diff --check
pass
```

Task C 收口验证：

```text
rg -n "software_proof_docker_route_task_rehearsal_artifact_gate|Objective 2|Objective 3|Objective 5|Nav2/fixed-route|WAVE ROVER|HIL|delivery success|autonomy-engineer|robot-software-engineer|product-okr-owner" OKR.md docs/process/okr_progress_log.md sprints/2026.05.14_19-20_route-task-rehearsal-artifact

git diff --check -- OKR.md docs/process/okr_progress_log.md sprints/2026.05.14_19-20_route-task-rehearsal-artifact
```

Task C 命令输出以最终聊天汇总为准。

## 偏差与边界

- 本轮证据边界统一为 `software_proof_docker_route_task_rehearsal_artifact_gate`。
- artifact pass 只证明 fixed-route status、software proof replay、task record 和 evidence crosscheck 的软件对账通过。
- `final_status=success`、artifact pass、ACK 或 HTTP accepted 均不得写成真实 delivery success。
- 本轮不是真实 Nav2/fixed-route、真实路线采集、WAVE ROVER、真实串口、HIL、同一 `evidence_ref` 的上车复账、dropoff/cancel completion 或 delivery success。
- Objective 2 和 Objective 3 可各从约 77% 谨慎上调到约 78%；Objective 5 因没有真实外部证据，保持约 68%。

## 剩余风险

- 真实 Nav2/fixed-route 实跑、真实路线采集、关键帧实景证据仍未完成。
- WAVE ROVER、真实串口、真实 HIL 与同一 `evidence_ref` 的上车复账仍未完成。
- dropoff/cancel completion、真实失败恢复和真实 delivery success 仍未完成。
- Objective 5 仍缺真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue connectivity 和 production worker/migration。
