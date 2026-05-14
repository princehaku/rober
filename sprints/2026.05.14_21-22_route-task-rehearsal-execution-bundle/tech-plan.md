# Sprint 2026.05.14_21-22 Route Task Rehearsal Execution Bundle - Tech Plan

sprint_type: epic

## OKR 最低优先级核对

当前 `OKR.md` 4.1 最低 Objective 是 Objective 5，约 68%。本 sprint 不直接推进 Objective 5，理由是本机只有 Docker，且当前缺真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue connectivity、production worker/migration 等外部材料；继续本地 O5 metadata depth 不会移动 O5 completion。

本 sprint 选择 Objective 2/3，因为二者约 79%，低于 Objective 4 的约 95%，且可以在 Docker-only 环境中从上轮 diagnostics consumption 继续推进到可重复 execution bundle。该结果仍只能计为 software proof。

## 方案

### Task A - Autonomy

Owner：`autonomy-engineer`

文件范围：

- `pc-tools/evidence/route_task_rehearsal_bundle.py`
- `pc-tools/README.md`
- `docs/navigation/fixed_route_workflow.md`

实现：

- 新增 dependency-free CLI，接收 route status、task record 或 task_record_dir、可选 hil gate output 和 output dir。
- 调用/复用 `pc-tools/evidence/evidence_crosscheck.py`，生成 route/task rehearsal artifact。
- 写出 execution bundle manifest，schema 使用 `trashbot.route_task_rehearsal_execution_bundle`，evidence_boundary 使用 `software_proof_docker_route_task_rehearsal_execution_bundle_gate`。
- manifest 只记录脱敏 path/ref、artifact status、crosscheck status、HIL alignment、`not_proven` 和 next_step。

验收命令：

```bash
python3 -m py_compile pc-tools/evidence/route_task_rehearsal_bundle.py
python3 pc-tools/evidence/route_task_rehearsal_bundle.py --help
python3 pc-tools/evidence/route_task_rehearsal_bundle.py <临时 route_status.json> --task-record <临时 task_record.json> --output-dir <临时输出目录>
rg -n "route_task_rehearsal_execution_bundle|software_proof_docker_route_task_rehearsal_execution_bundle_gate" pc-tools/README.md docs/navigation/fixed_route_workflow.md pc-tools/evidence/route_task_rehearsal_bundle.py
git diff --check -- pc-tools/evidence/route_task_rehearsal_bundle.py pc-tools/README.md docs/navigation/fixed_route_workflow.md
```

### Task B - Robot

Owner：`robot-software-engineer`

文件范围：

- `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py`
- `onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`
- `docs/interfaces/ros_contracts.md`

实现：

- 新增 diagnostics 只读 summary：读取 execution bundle manifest，支持 explicit ref 或环境变量。
- 保留 artifact summary 兼容，不改变 command/status/ACK envelope。
- missing/invalid/crosscheck-fail 时保守输出 blocked/read_error，不启用 primary actions，不声称 HIL 或 delivery success。
- 用现有 diagnostics unittest 加 metadata-only 围栏，不新增测试文件。

验收命令：

```bash
python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest onboard.src.ros2_trashbot_behavior.test.test_operator_gateway_diagnostics
rg -n "route_task_rehearsal_execution_bundle|software_proof_docker_route_task_rehearsal_execution_bundle_gate|delivery success|primary_actions_enabled" onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py docs/interfaces/ros_contracts.md
git diff --check -- onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py docs/interfaces/ros_contracts.md
```

### Task C - Product Closeout

Owner：`product-okr-owner`

文件范围：

- `OKR.md`
- `docs/process/okr_progress_log.md`
- `sprints/2026.05.14_21-22_route-task-rehearsal-execution-bundle/tech-done.md`
- `sprints/2026.05.14_21-22_route-task-rehearsal-execution-bundle/side2side_check.md`
- `sprints/2026.05.14_21-22_route-task-rehearsal-execution-bundle/final.md`

验收命令：

```bash
rg -n "2026.05.14_21-22_route-task-rehearsal-execution-bundle|software_proof_docker_route_task_rehearsal_execution_bundle_gate|Objective 2|Objective 3|Objective 5|not_proven|delivery success|HIL" OKR.md docs/process/okr_progress_log.md sprints/2026.05.14_21-22_route-task-rehearsal-execution-bundle
git diff --check -- OKR.md docs/process/okr_progress_log.md sprints/2026.05.14_21-22_route-task-rehearsal-execution-bundle/tech-done.md sprints/2026.05.14_21-22_route-task-rehearsal-execution-bundle/side2side_check.md sprints/2026.05.14_21-22_route-task-rehearsal-execution-bundle/final.md
```

## 风险边界

- 本轮不读取或修改 WAVE ROVER、UART、Orange Pi、launch 硬件参数；不需要 vendor 硬件资料。
- 本轮产物是 `software_proof_docker_route_task_rehearsal_execution_bundle_gate`。
- 不把 bundle manifest、artifact pass、diagnostics summary 写成真实 fixed-route/Nav2、HIL、dropoff/cancel completion 或 delivery success。
