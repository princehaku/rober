# Sprint 2026.05.11 02-03 Elevator Assisted Delivery Dry Run - Tech Plan

## 状态

- 阶段：tech-plan completed。
- 时间：2026-05-11 02:03 Asia/Shanghai。
- Owner：`product-okr-owner`。
- 执行类型：多 Engineer 工程实现计划；本文件完成后进入 implementation，由子 agent 执行。

## 产品目标

把 `docs/product/elevator_assisted_delivery.md` 里的电梯状态链路推进到默认关闭的软件 dry-run 骨架。工程结果必须能证明行为状态、任务记录、operator 手机状态和 diagnostics contract 可以贯通；不能宣称实机电梯能力完成。

## 任务分工

### 1. Robot Platform Engineer - 主责集成

角色 id：`robot-software-engineer`。

允许改动范围：

- `src/ros2_trashbot_behavior/ros2_trashbot_behavior/delivery_state_machine.py`
- `src/ros2_trashbot_behavior/ros2_trashbot_behavior/task_orchestrator.py`
- `src/ros2_trashbot_behavior/ros2_trashbot_behavior/task_record.py`
- `src/ros2_trashbot_bringup/launch/autonomous.launch.py`
- `src/ros2_trashbot_bringup/launch/bringup.launch.py`
- 行为/bringup targeted tests：
  - `src/ros2_trashbot_behavior/test/test_delivery_state_machine.py`
  - `src/ros2_trashbot_behavior/test/test_task_orchestrator_collection_execution.py`
  - `src/ros2_trashbot_behavior/test/test_task_record.py`
  - `src/ros2_trashbot_bringup/test/test_launch_contract_static.py`
- 本 sprint 后续记录：
  - `sprints/2026.05.11_02-03_elevator-assisted-delivery-dry-run/tech-done.md`

实现要求：

- 增加默认关闭的电梯 dry-run 子流程参数：建议 `elevator_assist_enabled=false`、`elevator_assist_mode=dry_run`，命名可按现有代码风格调整。
- dry-run 状态序列覆盖：`approaching_elevator`、`waiting_elevator_open`、`entering_elevator`、`requesting_floor_help`、`waiting_target_floor`、`exiting_elevator`、`resume_delivery`。
- 失败路径覆盖：`door_timeout`、`target_floor_unconfirmed`、`unsafe_to_exit` 或等价错误。
- 任务结果和 task record 必须写入 elevator 状态转移、模拟证据、失败原因、是否需要人工接管。
- 未启用时不得改变当前 waypoint/fixed-route delivery 行为。

验收命令：

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest \
  src/ros2_trashbot_behavior/test/test_delivery_state_machine.py \
  src/ros2_trashbot_behavior/test/test_task_orchestrator_collection_execution.py \
  src/ros2_trashbot_behavior/test/test_task_record.py \
  src/ros2_trashbot_bringup/test/test_launch_contract_static.py
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile \
  src/ros2_trashbot_behavior/ros2_trashbot_behavior/delivery_state_machine.py \
  src/ros2_trashbot_behavior/ros2_trashbot_behavior/task_orchestrator.py \
  src/ros2_trashbot_behavior/ros2_trashbot_behavior/task_record.py
git diff --check -- \
  src/ros2_trashbot_behavior \
  src/ros2_trashbot_bringup \
  sprints/2026.05.11_02-03_elevator-assisted-delivery-dry-run
```

### 2. User Touchpoint Full-Stack Engineer - 状态契约协作

角色 id：`full-stack-software-engineer`。

允许改动范围：

- `src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway.py`
- `src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py`
- `src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_http.py`
- operator targeted tests：
  - `src/ros2_trashbot_behavior/test/test_operator_gateway_static.py`
  - `src/ros2_trashbot_behavior/test/test_operator_gateway_http.py`
  - `src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`
- 如需同步用户触点文档，只允许：
  - `docs/product/mobile_user_flow.md`
- 本 sprint 后续记录：
  - `sprints/2026.05.11_02-03_elevator-assisted-delivery-dry-run/tech-done.md`

实现要求：

- 在 status/diagnostics payload 中暴露机器可读 `elevator_assist` 状态，字段命名需稳定且不破坏现有客户端。
- 对电梯状态输出普通用户可读 `phone_copy`，进入电梯后输出 speaker prompt：`你好,好心人,.我要去1楼扔垃圾,请帮我按一下电梯,`。
- diagnostics 必须能显示门未开、等待目标楼层、目标楼层证据不可靠、需要人工接管等状态。
- 不做生产账号系统、不做远程云改造、不做真实 TTS 播放。

验收命令：

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest \
  src/ros2_trashbot_behavior/test/test_operator_gateway_static.py \
  src/ros2_trashbot_behavior/test/test_operator_gateway_http.py \
  src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile \
  src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway.py \
  src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py \
  src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_http.py
git diff --check -- \
  src/ros2_trashbot_behavior \
  docs/product/mobile_user_flow.md \
  sprints/2026.05.11_02-03_elevator-assisted-delivery-dry-run
```

### 3. Autonomy Algorithm Engineer - Evidence Schema 协作

角色 id：`autonomy-engineer`。

允许改动范围：

- `src/ros2_trashbot_nav/ros2_trashbot_nav/route_utils.py`
- `src/ros2_trashbot_nav/ros2_trashbot_nav/fixed_route_autonomy.py`
- `src/ros2_trashbot_nav/ros2_trashbot_nav/visual_gate_proof.py`
- nav targeted tests：
  - `src/ros2_trashbot_nav/test/test_fixed_route_dry_run_offline.py`
  - `src/ros2_trashbot_nav/test/test_visual_gate_proof.py`
  - `src/ros2_trashbot_nav/test/test_fixed_route_status_static.py`
- 如需同步产品 contract，只允许：
  - `docs/product/elevator_assisted_delivery.md`
- 本 sprint 后续记录：
  - `sprints/2026.05.11_02-03_elevator-assisted-delivery-dry-run/tech-done.md`

实现要求：

- 定义电梯 dry-run evidence schema，至少覆盖：`door_open`、`door_closed_or_unknown`、`inside_elevator`、`target_floor_confirmed`、`target_floor_unconfirmed`、`safe_to_exit`、`unsafe_to_exit`。
- 只做离线/dry-run 证据结构，不做真实相机识别、楼层 OCR 或电梯实景验证。
- evidence 应能被 Robot Platform 写入 task record，并能被 operator diagnostics 展示。
- 不新增硬件依赖，不改变 fixed-route 默认行为。

验收命令：

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest \
  src/ros2_trashbot_nav/test/test_fixed_route_dry_run_offline.py \
  src/ros2_trashbot_nav/test/test_visual_gate_proof.py \
  src/ros2_trashbot_nav/test/test_fixed_route_status_static.py
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile \
  src/ros2_trashbot_nav/ros2_trashbot_nav/route_utils.py \
  src/ros2_trashbot_nav/ros2_trashbot_nav/fixed_route_autonomy.py \
  src/ros2_trashbot_nav/ros2_trashbot_nav/visual_gate_proof.py
git diff --check -- \
  src/ros2_trashbot_nav \
  docs/product/elevator_assisted_delivery.md \
  sprints/2026.05.11_02-03_elevator-assisted-delivery-dry-run
```

## 并行策略

- `robot-software-engineer` 是主责，负责最终接口收敛和集成验收。
- `full-stack-software-engineer` 和 `autonomy-engineer` 的文件范围互不重叠，可以与主责并行启动，但必须避免改同一份 behavior 核心文件。
- 若接口耦合导致冲突，以 Robot Platform 的 task record / status contract 为集成真相，其他 agent 调整自己的输出字段。

## 接口影响

- ROS2 action/srv/msg：本轮默认不改接口定义；优先在现有 action result、task record、status JSON 和 diagnostics JSON 中增加向后兼容字段。
- Launch：只新增默认关闭参数，不改变现有默认行为。
- Operator API：`GET /api/status` 和 `GET /api/diagnostics` 可增加 `elevator_assist` 字段；不得移除既有字段。
- 硬件：无硬件接口影响。本轮不涉及 WAVE ROVER、ESP32、Orange Pi UART、波特率、引脚、电压、固件或机械尺寸。

## 验证围栏

本轮响应用户“测试只围栏”的要求，验证只做：

- targeted behavior tests。
- targeted operator gateway/diagnostics tests。
- targeted nav/evidence schema tests。
- touched Python 文件 `py_compile`。
- scoped `git diff --check`。
- 如多个 agent 集成后风险较高，Robot Platform 最终可运行一次 `PYTHONDONTWRITEBYTECODE=1 bash scripts/run_smoke_tests.sh`，但不要求为了本功能新增大面积测试。

## 风险边界

- dry-run 通过不等于实机电梯通过。
- 不得把固定等待时间写成目标楼层确认。
- 不得让电梯功能默认开启。
- 不得新增硬件假设；如果后续工程触及硬件事实，必须先查 `docs/vendor/VENDOR_INDEX.md`。
- 不得为了电梯状态破坏现有 Objective 2 送垃圾主链路。

## 本 Product 子任务验收命令

```bash
test -f sprints/2026.05.11_02-03_elevator-assisted-delivery-dry-run/pre_start.md && test -f sprints/2026.05.11_02-03_elevator-assisted-delivery-dry-run/prd.md && test -f sprints/2026.05.11_02-03_elevator-assisted-delivery-dry-run/tech-plan.md
git diff --check -- sprints/2026.05.11_02-03_elevator-assisted-delivery-dry-run
```

## 后续留档要求

- 工程实现完成后，主责 agent 必须更新 `tech-done.md`，写明实际改动、验证结果、偏差和剩余风险。
- 用户验收或对照检查后，再更新 `side2side_check.md`。
- 阶段收口后，再更新 `final.md` 和必要的 OKR 进度说明。
