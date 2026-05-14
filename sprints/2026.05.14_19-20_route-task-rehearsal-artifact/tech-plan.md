# Sprint 2026.05.14_19-20 Route Task Rehearsal Artifact - Tech Plan

## 技术目标

新增一个 Docker-only route/task rehearsal artifact gate：把 fixed-route status、software proof replay、task record 和 `pc-tools/evidence/evidence_crosscheck.py` 对账结果保存成可复核材料，并把证据边界固定为 `software_proof_docker_route_task_rehearsal_artifact_gate`。

本轮只做软件排练证据。任何输出、文档和 OKR 更新都不得声明真实 Nav2/fixed-route 实跑、WAVE ROVER、真实串口、HIL、dropoff/cancel completion 或 delivery success。

## 任务分工

### Task A - `autonomy-engineer`

目标：让 PC evidence 工具能产出 route/task rehearsal summary/artifact，并更新 fixed-route 使用文档。

允许改动文件范围：

- `pc-tools/evidence/evidence_crosscheck.py`
- `pc-tools/evidence/` 下相邻 helper 或 fixture 文件，仅限 artifact 输出所需的最小新增文件。
- `pc-tools/README.md`
- `docs/navigation/fixed_route_workflow.md`
- 必要的既有 fenced test 文件，优先复用 `onboard/src/ros2_trashbot_behavior/test/test_task_record.py` 中的 evidence crosscheck fixture，不新增大测试堆。

实现要求：

- artifact 必须包含 schema/version、`evidence_boundary=software_proof_docker_route_task_rehearsal_artifact_gate`、`evidence_ref`、route status summary、task record summary、crosscheck status、HIL alignment status、`not_proven`。
- artifact pass 只能表示 status/replay/task_record 软件对账通过。
- HIL gate 未提供、缺失、`software_proof` 或 `blocked` 时，artifact 仍可保存，但必须输出 not real HIL / not proven。
- summary 输出不得包含 bearer token、Authorization header、OSS secret、AK/SK、root password、DB URL、queue URL、串口设备、波特率或 raw traceback。

验收命令：

```bash
python3 -m py_compile pc-tools/evidence/evidence_crosscheck.py
python3 onboard/src/ros2_trashbot_behavior/test/test_task_record.py
rg -n "software_proof_docker_route_task_rehearsal_artifact_gate|route/task rehearsal|not_proven|evidence_ref" pc-tools/README.md docs/navigation/fixed_route_workflow.md pc-tools/evidence/evidence_crosscheck.py onboard/src/ros2_trashbot_behavior/test/test_task_record.py
git diff --check -- pc-tools/evidence/evidence_crosscheck.py pc-tools/README.md docs/navigation/fixed_route_workflow.md onboard/src/ros2_trashbot_behavior/test/test_task_record.py
```

### Task B - `robot-software-engineer`

目标：保证 task record / behavior fixed-route evidence compatibility 与 rehearsal artifact 对齐，不触发 HIL 或 delivery success claim。

允许改动文件范围：

- `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/task_record.py`
- `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/task_orchestrator.py`
- `onboard/src/ros2_trashbot_behavior/test/test_task_record.py`
- `onboard/src/ros2_trashbot_behavior/test/test_task_orchestrator_collection_execution.py`
- `onboard/src/ros2_trashbot_behavior/test/test_task_orchestrator_fixed_route_status.py`
- `docs/interfaces/ros_contracts.md`

实现要求：

- task record 中 `route_progress`、`nav_results[-1].evidence.route_progress` 和 `evidence_ref` 的来源要能被 Task A artifact 稳定消费。
- 如果补字段或兼容逻辑，只能补软件证据追踪字段；不得改变 ROS2 action/topic/service contract。
- `final_status=success` 只能表示当前 dry-run / software proof 任务状态机结果，不能被文档或代码输出升级为真实 delivery success。
- 所有新增技术注释必须使用中文，且复杂逻辑要解释为什么这样保护证据边界。

验收命令：

```bash
python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/task_record.py onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/task_orchestrator.py
python3 onboard/src/ros2_trashbot_behavior/test/test_task_record.py
python3 onboard/src/ros2_trashbot_behavior/test/test_task_orchestrator_collection_execution.py
python3 onboard/src/ros2_trashbot_behavior/test/test_task_orchestrator_fixed_route_status.py
rg -n "route_progress|evidence_ref|software_proof_docker_route_task_rehearsal_artifact_gate|delivery success|HIL|Nav2/fixed-route" docs/interfaces/ros_contracts.md onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/task_record.py onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/task_orchestrator.py onboard/src/ros2_trashbot_behavior/test/test_task_record.py
git diff --check -- onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/task_record.py onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/task_orchestrator.py onboard/src/ros2_trashbot_behavior/test/test_task_record.py onboard/src/ros2_trashbot_behavior/test/test_task_orchestrator_collection_execution.py onboard/src/ros2_trashbot_behavior/test/test_task_orchestrator_fixed_route_status.py docs/interfaces/ros_contracts.md
```

### Task C - `product-okr-owner`

目标：实现完成后按软件证据边界更新 OKR、进度日志和 sprint closeout。

允许改动文件范围：

- `OKR.md`
- `docs/process/okr_progress_log.md`
- `sprints/2026.05.14_19-20_route-task-rehearsal-artifact/tech-done.md`
- `sprints/2026.05.14_19-20_route-task-rehearsal-artifact/side2side_check.md`
- `sprints/2026.05.14_19-20_route-task-rehearsal-artifact/final.md`

实现要求：

- 只有 Task A/B 均完成并提供验证证据后，才更新 OKR 完成度。
- O2/O3 如上调，只能因 `software_proof_docker_route_task_rehearsal_artifact_gate` 谨慎上调；不得写成真实路线实跑或真实任务闭环。
- `final.md` 必须回顾本 tech-plan 的 OKR 最低优先级核对理由是否仍成立。
- `docs/process/okr_progress_log.md` 必须记录剩余缺口：真实 Nav2/fixed-route、真实路线采集、WAVE ROVER/HIL、同一 `evidence_ref` 的上车复账和真实送达。

验收命令：

```bash
rg -n "software_proof_docker_route_task_rehearsal_artifact_gate|Objective 2|Objective 3|Objective 5|Nav2/fixed-route|WAVE ROVER|HIL|delivery success|autonomy-engineer|robot-software-engineer|product-okr-owner" OKR.md docs/process/okr_progress_log.md sprints/2026.05.14_19-20_route-task-rehearsal-artifact
git diff --check -- OKR.md docs/process/okr_progress_log.md sprints/2026.05.14_19-20_route-task-rehearsal-artifact
```

## 接口影响

- ROS2 action/topic/service contract：预期不变。
- fixed-route status contract：预期只新增或复用 artifact summary 字段，不破坏现有 `route_progress`、`software_proof`、`failure_code`、`evidence_ref`。
- task record contract：允许补齐 route/task evidence traceability 字段，但必须兼容既有消费者。
- PC tool CLI：可新增 summary/artifact 输出参数；默认只读，不修改输入 status、replay 或 task record。
- 文档：必须同步更新 `pc-tools/README.md`、`docs/navigation/fixed_route_workflow.md`、`docs/interfaces/ros_contracts.md` 中的证据边界。

## 风险边界

- 当前主机没有真实硬件、串口、WAVE ROVER、Nav2 实跑或 HIL；所有验证只能是 Docker/local software proof。
- `evidence_crosscheck.py` 对账通过只证明字段一致，不证明小车真实运动。
- task record success 不等于真实 delivery success；如果 dry-run 成功，artifact 仍必须保留非声明字段。
- 如果实现中发现需要变更共享 contract，必须先让 `robot-software-engineer` 主责集成，`autonomy-engineer` 只做 PC tool 对接，避免两个 owner 同时改同一语义。

## 并行启动策略

本 sprint 为 Epic，且 Task A/B/C 文件范围互不重叠，后续进入实现时应并行派发 3 个 worker：

- `autonomy-engineer`：PC evidence artifact 与 navigation 文档。
- `robot-software-engineer`：task record compatibility 与 ROS contract 文档。
- `product-okr-owner`：等 A/B 结果后收口 OKR 与 sprint 文档。若运行时不能让 Product 等待 A/B，则 Product 先做只读 closeout 模板，不得提前上调 OKR。

## OKR 最低优先级核对

- 当前 `OKR.md` 4.1 节完成度最低的 Objective：Objective 5（约 68%）。
- 本 sprint 是否针对该 Objective：否。
- 不针对理由：Objective 5 当前下一步有效进展需要真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/migration 或真实外部材料；当前 Docker-only 主机无法提供这些证据。继续堆本地 O5 metadata depth 不会提高 O5 completion。Objective 1 也缺真实硬件/串口，无法产出 `hil_pass`。Objective 2/3 虽然不是最低，但仍有可执行的软件证据缺口，可通过 route/task rehearsal artifact 推进任务复盘与固定路线软件证明。
- final.md 收口时需复核：O5 外部材料是否在本轮期间出现；如果仍未出现，本轮切到 O2/O3 的理由继续成立。如果出现真实 O5 外部材料，下一轮应优先回到 Objective 5。

## 本规划阶段验收命令

规划文档创建后，Product worker 必须运行：

```bash
test -f sprints/2026.05.14_19-20_route-task-rehearsal-artifact/pre_start.md && test -f sprints/2026.05.14_19-20_route-task-rehearsal-artifact/prd.md && test -f sprints/2026.05.14_19-20_route-task-rehearsal-artifact/tech-plan.md
rg -n "sprint_type: epic|OKR 最低优先级核对|Objective 5|Objective 1|Objective 2|Objective 3|software_proof_docker_route_task_rehearsal_artifact_gate|autonomy-engineer|robot-software-engineer|product-okr-owner" sprints/2026.05.14_19-20_route-task-rehearsal-artifact
git diff --check -- sprints/2026.05.14_19-20_route-task-rehearsal-artifact
```
