# Sprint 2026.05.11 02-03 Elevator Assisted Delivery Dry Run - Tech Done

## 状态

- 阶段：engineering implementation completed，Product 收口中。
- 时间：2026-05-11 Asia/Shanghai。
- Owner：`robot-software-engineer` 主责集成；`full-stack-software-engineer`、`autonomy-engineer` 协作。
- 范围：默认关闭的 elevator assisted delivery dry-run 行为骨架、任务记录、operator status/diagnostics、nav evidence schema 和 targeted 围栏测试。

## Robot Platform 实际改动

- `delivery_state_machine.py`
  - 新增 `elevator_phase`、`elevator_completed`、`elevator_failed` 事件。
  - 电梯 dry-run 阶段保持主状态为 `delivering`，细粒度阶段写入 transition message，避免改变未启用时的 delivery 主链路。
- `task_orchestrator.py`
  - 新增参数：`elevator_assist_enabled=false`、`elevator_assist_mode=dry_run`、`elevator_assist_target_floor=1`、`elevator_assist_dry_run_failure=""`。
  - 默认关闭时写入稳定 disabled contract，不插入电梯子流程。
  - 启用 dry-run 时记录阶段序列：`approaching_elevator`、`waiting_elevator_open`、`entering_elevator`、`requesting_floor_help`、`waiting_target_floor`、`exiting_elevator`、`resume_delivery`。
  - 进入求助阶段的 speaker prompt 固定为：`你好,好心人,.我要去1楼扔垃圾,请帮我按一下电梯,`。
  - dry-run 失败注入覆盖 `door_timeout`、`target_floor_unconfirmed`、`unsafe_to_exit`。
- `task_record.py`
  - task record 顶层新增 `elevator_assist`，包含 `enabled`、`mode`、`state`、`phase`、`requires_human_help`、`reason`、`target_floor`、`speaker_prompt`、`evidence`、`events`。
- `autonomous.launch.py`、`bringup.launch.py`
  - 新增电梯 assist launch 参数，默认关闭并传给 `task_orchestrator`。
- Targeted tests
  - 覆盖状态机电梯阶段/失败、collection dry-run happy path、collection 电梯失败 task record、task record 字段持久化、launch 默认关闭参数传递。

## 验证结果

### Robot Platform

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest \
  src/ros2_trashbot_behavior/test/test_delivery_state_machine.py \
  src/ros2_trashbot_behavior/test/test_task_orchestrator_collection_execution.py \
  src/ros2_trashbot_behavior/test/test_task_record.py \
  src/ros2_trashbot_bringup/test/test_launch_contract_static.py
```

结果：`Ran 29 tests in 0.013s - OK`。

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile \
  src/ros2_trashbot_behavior/ros2_trashbot_behavior/delivery_state_machine.py \
  src/ros2_trashbot_behavior/ros2_trashbot_behavior/task_orchestrator.py \
  src/ros2_trashbot_behavior/ros2_trashbot_behavior/task_record.py
```

结果：通过，无输出。

```bash
git diff --check -- \
  src/ros2_trashbot_behavior \
  src/ros2_trashbot_bringup \
  sprints/2026.05.11_02-03_elevator-assisted-delivery-dry-run
```

结果：通过，无输出。

### User Touchpoint Full-Stack

工程 agent 汇总结果：

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest \
  src/ros2_trashbot_behavior/test/test_operator_gateway_static.py \
  src/ros2_trashbot_behavior/test/test_operator_gateway_http.py \
  src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py
```

结果：`Ran 53 tests ... OK`。

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile \
  src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway.py \
  src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py \
  src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_http.py
```

结果：通过，无输出。

```bash
git diff --check -- \
  src/ros2_trashbot_behavior \
  docs/product/mobile_user_flow.md \
  sprints/2026.05.11_02-03_elevator-assisted-delivery-dry-run
```

结果：通过，无输出。

### Autonomy Evidence Schema

工程 agent 汇总结果：

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest \
  src/ros2_trashbot_nav/test/test_fixed_route_dry_run_offline.py \
  src/ros2_trashbot_nav/test/test_visual_gate_proof.py \
  src/ros2_trashbot_nav/test/test_fixed_route_status_static.py
```

结果：`Ran 19 tests ... OK`。

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile \
  src/ros2_trashbot_nav/ros2_trashbot_nav/route_utils.py \
  src/ros2_trashbot_nav/ros2_trashbot_nav/fixed_route_autonomy.py \
  src/ros2_trashbot_nav/ros2_trashbot_nav/visual_gate_proof.py
```

结果：通过，无输出。

```bash
git diff --check -- \
  src/ros2_trashbot_nav \
  docs/product/elevator_assisted_delivery.md \
  sprints/2026.05.11_02-03_elevator-assisted-delivery-dry-run
```

结果：通过，无输出。

## 偏差与协作风险

- 本轮未改 ROS2 action/msg/srv 定义，所有新增信息走 task record/status JSON 兼容扩展。
- 本轮未做真实电梯、真实 TTS、相机门识别、楼层 OCR、Nav2/固定路线实跑或硬件在环验证；dry-run 通过不等于实机电梯能力完成。
- Full-stack 结果已补入本文件：operator status/diagnostics 已按本轮 `elevator_assist` contract 暴露机器可读状态、用户可读 phone copy 和 speaker prompt contract；未做真实 TTS 播放。
- Autonomy 结果已补入本文件：nav/visual gate 只输出保守离线 evidence schema；即使 visual gate passed，也不声明已识别电梯门、楼层 OCR 或目标楼层真实到达。
- 当前工作区中 `.codex/config.toml` 有无关未提交改动，不属于本轮成果，Product 收口不记录为 OKR 证据。
