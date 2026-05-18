# Sprint 2026.05.19_00-01 Elevator Assist Action Feedback Mainline - Tech Plan

## 1. 技术方案

在 `TaskOrchestrator._execute_collection` 中把 `goal_handle` 和 `start_time` 传给电梯 assist 执行路径。`_perform_elevator_assist` / `_perform_rehearsal_artifact_elevator_assist` 在每个电梯子阶段调用一个新的内部 helper，发布 `TrashCollection.Feedback`：

- `status`: 保持 delivery 阶段内的非成功状态码，不改变 action result。
- `percent_complete`: 在 30-55% 之间递增，避免和 dropoff/return/done 冲突。
- `current_step`: 使用 `elevator:<phase>`，便于 mobile/API 消费方稳定识别。
- `event`: 仍来自 state machine 的 `elevator_phase` 或 `elevator_completed`。
- `message`: 中文优先 phone-safe 文案，不包含 raw artifact、路径、串口、ROS topic 或底层控制参数。

实现不改变 action/service/msg 定义，不改变 task record schema，不改变已有 dry-run/rehearsal evidence validation 边界。

## 2. 文件范围

Robot worker 允许改：

- `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/task_orchestrator.py`
- `onboard/src/ros2_trashbot_behavior/test/test_task_orchestrator_collection_execution.py`
- `docs/product/elevator_assisted_delivery.md`
- `docs/interfaces/ros_contracts.md`

Product worker 允许改：

- `OKR.md`
- `docs/process/okr_progress_log.md`
- `sprints/2026.05.19_00-01_elevator-assist-action-feedback-mainline/tech-done.md`
- `sprints/2026.05.19_00-01_elevator-assist-action-feedback-mainline/side2side_check.md`
- `sprints/2026.05.19_00-01_elevator-assist-action-feedback-mainline/final.md`

## 3. 接口影响

- ROS action definition 不变。
- `TrashCollection.Feedback` 现有字段复用：`current_step`、`state`、`event`、`message`、`percent_complete`。
- 兼容性：旧消费者继续看到原 loaded/delivering/dropoff/returning/done feedback；新消费者可以额外识别 `current_step=elevator:<phase>`。

## 4. 验收命令

Robot worker 必须运行：

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/task_orchestrator.py
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_task_orchestrator_collection_execution.py
rg -n "elevator:waiting_elevator_open|elevator:requesting_floor_help|software_proof_docker_elevator_evidence_driven_mainline_gate|delivery_success=false|primary_actions_enabled=false" onboard/src/ros2_trashbot_behavior docs/product/elevator_assisted_delivery.md docs/interfaces/ros_contracts.md sprints/2026.05.19_00-01_elevator-assist-action-feedback-mainline
git diff --check -- onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/task_orchestrator.py onboard/src/ros2_trashbot_behavior/test/test_task_orchestrator_collection_execution.py docs/product/elevator_assisted_delivery.md docs/interfaces/ros_contracts.md
```

Product worker 必须运行：

```bash
test -f sprints/2026.05.19_00-01_elevator-assist-action-feedback-mainline/tech-done.md && test -f sprints/2026.05.19_00-01_elevator-assist-action-feedback-mainline/side2side_check.md && test -f sprints/2026.05.19_00-01_elevator-assist-action-feedback-mainline/final.md
rg -n "Objective 5|Objective 1|Objective 2|Objective 4|PR #4|PR #5|software_proof|not_proven|delivery_success=false|primary_actions_enabled=false|elevator action feedback" OKR.md docs/process/okr_progress_log.md sprints/2026.05.19_00-01_elevator-assist-action-feedback-mainline
git diff --check -- OKR.md docs/process/okr_progress_log.md sprints/2026.05.19_00-01_elevator-assist-action-feedback-mainline
```

## 5. OKR 最低优先级核对

- 当前 `OKR.md` 4.1 节完成度最低的 Objective：Objective 5，约 68%。
- 本 sprint 是否针对该 Objective：否。
- 不针对理由：Objective 5 下一步需要真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/cutover 或真实手机/browser external proof；当前主机只有 Docker/local software proof，继续本地 O5 metadata 会违反 stop rule。
- 次低 Objective：Objective 1，约 81%。本轮也不针对，原因是真实 WAVE ROVER/UART/HIL 和 PR #5 真实 2D LiDAR / ToF 材料均缺失，且已有多轮本地硬件材料 gate。
- 本轮目标：在不消费真实材料 blocker 的前提下，推进 PR #4 要求的 Objective 2 电梯主链路和 Objective 4 用户触点可观测性。
- final.md 收口时需复核：O5/O1 blocker 是否仍成立；本轮是否只证明 software-proof action feedback，而非真实电梯或送达成功。

## 6. 风险边界

- 这是 Docker/local 行为层 software proof。
- 不证明真实电梯门状态、目标楼层确认、人工协助、真实 Nav2/fixed-route、WAVE ROVER/UART/HIL、真实 dropoff/cancel completion、真实手机或 O5 external proof。
- 若 feedback helper 引入重复或顺序漂移，必须用现有 collection execution unittest 锁住关键阶段顺序。
