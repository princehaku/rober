# Sprint 2026.05.14_20-21 Route Task Rehearsal Diagnostics - Tech Plan

sprint_type: epic

## 总方案

在上一轮 route/task rehearsal artifact 基础上补一层 diagnostics consumption：

- `autonomy-engineer` 负责 PC 工具 artifact 字段/文档，让 artifact 能被诊断面稳定消费。
- `robot-software-engineer` 负责 operator diagnostics 只读 summary builder 和最小测试。
- `product-okr-owner` 负责收口、OKR 和进度日志。

## 文件范围

### Task A - autonomy-engineer

允许改动：

- `pc-tools/evidence/evidence_crosscheck.py`
- `pc-tools/README.md`
- `docs/navigation/fixed_route_workflow.md`
- 必要时可改 `onboard/src/ros2_trashbot_behavior/test/test_task_record.py` 中已有围栏断言，不新增大测试套件。

验收命令：

```bash
python3 -m py_compile pc-tools/evidence/evidence_crosscheck.py
python3 onboard/src/ros2_trashbot_behavior/test/test_task_record.py
rg -n "software_proof_docker_route_task_rehearsal_diagnostics_gate|route_task_rehearsal|not_proven|evidence_ref" pc-tools/README.md docs/navigation/fixed_route_workflow.md pc-tools/evidence/evidence_crosscheck.py
git diff --check -- pc-tools/evidence/evidence_crosscheck.py pc-tools/README.md docs/navigation/fixed_route_workflow.md onboard/src/ros2_trashbot_behavior/test/test_task_record.py
```

### Task B - robot-software-engineer

允许改动：

- `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py`
- `onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`
- `docs/interfaces/ros_contracts.md`

验收命令：

```bash
python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest onboard.src.ros2_trashbot_behavior.test.test_operator_gateway_diagnostics
rg -n "route_task_rehearsal|software_proof_docker_route_task_rehearsal_diagnostics_gate|not delivery success|not_proven" onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py docs/interfaces/ros_contracts.md
git diff --check -- onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py docs/interfaces/ros_contracts.md
```

### Task C - product-okr-owner

允许改动：

- `OKR.md`
- `docs/process/okr_progress_log.md`
- `sprints/2026.05.14_20-21_route-task-rehearsal-diagnostics/tech-done.md`
- `sprints/2026.05.14_20-21_route-task-rehearsal-diagnostics/side2side_check.md`
- `sprints/2026.05.14_20-21_route-task-rehearsal-diagnostics/final.md`

验收命令：

```bash
rg -n "2026.05.14_20-21_route-task-rehearsal-diagnostics|software_proof_docker_route_task_rehearsal_diagnostics_gate|Objective 2|Objective 3|Objective 5|not_proven" OKR.md docs/process/okr_progress_log.md sprints/2026.05.14_20-21_route-task-rehearsal-diagnostics
git diff --check -- OKR.md docs/process/okr_progress_log.md sprints/2026.05.14_20-21_route-task-rehearsal-diagnostics
```

## 接口边界

- 新增/消费的 `route_task_rehearsal` 是 diagnostics metadata-only，不是 ROS2 action/topic/service，不是 `trashbot.remote.v1` command/status/ACK。
- `software_proof_docker_route_task_rehearsal_diagnostics_gate` 只证明 Docker/local route/task artifact 可被诊断面安全消费。
- 不改变 Start/Confirm/Cancel、ACK、cursor、terminal ACK、Nav2、WAVE ROVER、HIL 或 delivery result。

## OKR 最低优先级核对

- 当前 `OKR.md` 4.1 节完成度最低的 Objective：Objective 5，约 68%。
- 本 sprint 是否针对该 Objective：否。
- 理由：Objective 5 的真实完成度需要公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue connectivity 或 production worker/migration 等外部材料；本机只有 Docker，没有这些材料。近期多轮已经重复完成 O5/O4 本地 metadata gate，继续堆本地 O5 metadata 不会移动 O5 completion。
- 本轮改攻 Objective 2/3：上一轮 final 的明确剩余风险是 route/task artifact 尚未进入诊断消费链路，且这一步不依赖真实硬件或外部云。
- final.md 收口时需复核：本轮期间是否出现真实 O5 外部材料；若没有，保持该理由成立。
