# Sprint 2026.05.19_00-01 Elevator Assist Action Feedback Mainline - Tech Done

## sprint_type

epic

## Robot Platform Engineer

### 实际改动

- `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/task_orchestrator.py`
  - `_execute_collection` 现在把 `goal_handle` 和 `start_time` 传入电梯 assisted delivery 路径。
  - 新增 `_publish_elevator_assist_feedback`，在默认 dry-run 和 rehearsal artifact 两条路径逐阶段发布 `TrashCollection.Feedback`。
  - `current_step` 使用 `elevator:<phase>`，覆盖 `elevator:waiting_elevator_open`、`elevator:requesting_floor_help`、`elevator:resume_delivery` 等阶段。
  - `status=3`、`percent_complete=30-55`，`event` 来自 `elevator_phase` 或 `elevator_completed`，不改变 action definition、result、task record schema 或送达成功边界。
- `onboard/src/ros2_trashbot_behavior/test/test_task_orchestrator_collection_execution.py`
  - 补充默认 dry-run 和 rehearsal artifact 路径的 action feedback 断言，锁定 `elevator:<phase>` 顺序、event、state、status、progress 和 phone-safe message。
- `docs/product/elevator_assisted_delivery.md`
  - 补充手机/API 可实时消费 `elevator:<phase>` feedback 的产品边界，明确仍属 software proof。
- `docs/interfaces/ros_contracts.md`
  - 补充 `/trashbot/collect_trash` feedback contract，明确电梯阶段 feedback 不改变 ROS action schema，不放开 Start/Confirm/Cancel，不声明 delivery success。

### 验证结果

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/task_orchestrator.py
# pass

PYTHONDONTWRITEBYTECODE=1 python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_task_orchestrator_collection_execution.py
# Ran 15 tests in 0.015s
# OK

rg -n "elevator:waiting_elevator_open|elevator:requesting_floor_help|software_proof_docker_elevator_evidence_driven_mainline_gate|delivery_success=false|primary_actions_enabled=false" onboard/src/ros2_trashbot_behavior docs/product/elevator_assisted_delivery.md docs/interfaces/ros_contracts.md sprints/2026.05.19_00-01_elevator-assist-action-feedback-mainline
# pass; matched elevator feedback docs/tests and software_proof boundaries.

git diff --check -- onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/task_orchestrator.py onboard/src/ros2_trashbot_behavior/test/test_task_orchestrator_collection_execution.py docs/product/elevator_assisted_delivery.md docs/interfaces/ros_contracts.md
# pass
```

### 失败定位

- 本轮指定围栏未出现失败。

### 剩余风险

- 当前证据仍是 Docker/local software proof：`software_proof_docker_elevator_assist_default_mainline_gate` / `software_proof_docker_elevator_evidence_driven_mainline_gate`。
- 不证明真实电梯门状态、真实目标楼层确认、真实人工协助、真实 Nav2/fixed-route、WAVE ROVER/UART/HIL、真实手机或 O5 external proof。
- `delivery_success=false`、`primary_actions_enabled=false` 保持不变。

### 协同需求

- Full-Stack 后续可消费 `TrashCollection.Feedback.current_step=elevator:<phase>` 做实时手机展示。
- Product 后续可在 sprint `side2side_check.md` / `final.md` 复核 Objective 2 / Objective 4 的证据边界。

## Product Closeout

### 用户价值和产品北极星

- 用户价值：手机用户和现场 operator 可以在任务执行中看到电梯 assisted delivery 的阶段反馈，而不是等任务结束后只读 task record。
- 产品北极星：送垃圾主流程必须可解释、可恢复、可复盘；本轮推进“电梯阶段可解释”，不把 software proof 包装成真实现场通过。

### OKR 映射和 KR 拆解

- Objective 2：映射 KR6 / KR7。`TrashCollection` action feedback 现在可表达电梯 assisted delivery 的等待开门、进入电梯、请求按楼层、等待目标楼层、驶出电梯和恢复送达阶段。
- Objective 4：映射 KR6 / KR7。`current_step=elevator:<phase>` 给手机/API 后续展示提供 phone-safe 消费点。
- Objective 1：不调整。没有新增 WAVE ROVER、UART、HIL packet、`feedback_T1001.log`、`/odom`、`/imu/data`、`/battery` 或 operator HIL report。
- Objective 5：不调整。没有真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/cutover 或真实 external proof。

### 本轮核心抓手和验收口径

- 核心抓手：把电梯 assisted delivery 的 dry-run / rehearsal artifact 子阶段实时暴露为 action feedback，`current_step=elevator:<phase>`。
- 验收口径：只能记录为 `software_proof_docker_elevator_assist_default_mainline_gate` / `software_proof_docker_elevator_evidence_driven_mainline_gate`；必须保持 `not_proven`、`delivery_success=false`、`primary_actions_enabled=false`。
- 百分比：Objective 2 保守保持约 99%，Objective 4 保守保持约 99%，Objective 1 保持约 81%，Objective 5 保持约 68%。

### 责任 Engineer 和后续协同

- 已完成 owner：Robot Platform Engineer。
- 后续 owner：Full-Stack 可消费 `TrashCollection.Feedback.current_step=elevator:<phase>` 做只读实时手机展示。
- 后续边界：Full-Stack 不应改变 Start Delivery、Confirm Dropoff、Cancel gating，不应声明真实手机通过或 delivery success。

### 风险、阻塞和证据链缺口

- 仍缺真实电梯、真实门状态、真实楼层确认、人工协助现场记录、真实喇叭/TTS、真实 Nav2/fixed-route、WAVE ROVER/UART/HIL、真实手机、O5 external proof、真实 dropoff/cancel completion 和 delivery success。
- PR #4 仍需真实 route/elevator field materials 回填；PR #5 仍需真实 2D LiDAR / ToF SKU/source/receipt/procurement/installation/wiring/power/calibration/HIL-entry 材料。
- 已更新 sprint `side2side_check.md` / `final.md`、`OKR.md` 4.1 / 第 6 / 第 7 节，以及 `docs/process/okr_progress_log.md`。
