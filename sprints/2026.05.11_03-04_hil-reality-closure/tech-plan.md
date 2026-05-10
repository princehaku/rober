# Sprint 2026.05.11 03-04 HIL Reality Closure - Tech Plan

## 状态

- 阶段：tech-plan in progress
- 时间：2026-05-11 03:01 Asia/Shanghai
- Owner：`product-okr-owner`
- 主线目标：把软件 dry-run 迁移到“可复现实机 evidence”前置闭环。

## 任务分工与文件范围

### 1. `robot-software-engineer`（主责）

允许改动范围：

- `src/ros2_trashbot_behavior/ros2_trashbot_behavior/task_orchestrator.py`
- `src/ros2_trashbot_behavior/ros2_trashbot_behavior/task_record.py`
- `src/ros2_trashbot_behavior/ros2_trashbot_behavior/delivery_state_machine.py`
- `src/ros2_trashbot_behavior/test/test_task_orchestrator_collection_execution.py`
- `src/ros2_trashbot_behavior/test/test_task_record.py`
- `src/ros2_trashbot_bringup/launch/autonomous.launch.py`
- `src/ros2_trashbot_bringup/launch/bringup.launch.py`

实现要求：

- 保持 `elevator_assist` 默认关闭；任务主链继续 fixed-route/waypoint 主路径优先。
- 明确 `DELIVERING` 与失败/人工接管路径下的状态转移，`task_record` 写入 `result_path`（成功/失败/返回/超时）。
- 失败恢复要补齐 `task record` 可复盘字段：`source`, `state_transition_history`, `failure_code`, `human_intervention_required`。

验收命令：

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest \
  src/ros2_trashbot_behavior/test/test_task_orchestrator_collection_execution.py \
  src/ros2_trashbot_behavior/test/test_task_record.py
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest \
  src/ros2_trashbot_bringup/test/test_launch_contract_static.py
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile \
  src/ros2_trashbot_behavior/ros2_trashbot_behavior/task_orchestrator.py \
  src/ros2_trashbot_behavior/ros2_trashbot_behavior/task_record.py \
  src/ros2_trashbot_behavior/ros2_trashbot_behavior/delivery_state_machine.py
git diff --check -- \
  src/ros2_trashbot_behavior \
  src/ros2_trashbot_bringup \
  scripts/hardware_smoke_wave_rover.py \
  sprints/2026.05.11_03-04_hil-reality-closure
```

### 2. `hardware-engineer`（并行）

允许改动范围：

- `scripts/hardware_smoke_wave_rover.py`
- `docs/acceptance/wave_rover_hil_evidence.md`
- `docs/hardware/wave_rover_json_bridge.md`
- `docs/acceptance/robot_bringup_checklist.md`
- `docs/vendor/VENDOR_INDEX.md`（只读核对）

实现要求：

- 补齐可执行 HIL 参数模板：串口设备名、波特率、T=1/T=13 运动 smoke、feedback 校验。
- 明确产出文件中的 `source` 字段（`software_proof` vs `hil_pass`）
- 在接受文档记录真实反馈频率、轮向一致性和 IMU/电压解析结果的缺失与假设。

验收命令：

```bash
python3 scripts/hardware_smoke_wave_rover.py --help
python3 scripts/hardware_smoke_wave_rover.py --move-test --test-speed 0.05 --test-duration-s 0.3
# 上机时加 --serial-port /dev/ttyUSB0，或用实际设备参数
```

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile scripts/hardware_smoke_wave_rover.py
```

```bash
git diff --check -- scripts/hardware_smoke_wave_rover.py docs/acceptance/wave_rover_hil_evidence.md docs/hardware/wave_rover_json_bridge.md docs/acceptance/robot_bringup_checklist.md
```

### 3. `autonomy-engineer`（并行）

允许改动范围：

- `src/ros2_trashbot_nav/ros2_trashbot_nav/fixed_route_autonomy.py`
- `src/ros2_trashbot_nav/ros2_trashbot_nav/route_utils.py`
- `src/ros2_trashbot_nav/test/test_fixed_route_status_static.py`
- `src/ros2_trashbot_nav/test/test_fixed_route_dry_run_offline.py`

实现要求：

- 强化 fixed-route 状态与 task_record 的字段对齐（checkpoint、current_index、target、evidence_ref）。
- 保持现有 dry-run 行为兼容的前提下，补齐 real route 状态入口。

验收命令：

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest \
  src/ros2_trashbot_nav/test/test_fixed_route_dry_run_offline.py \
  src/ros2_trashbot_nav/test/test_fixed_route_status_static.py
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile \
  src/ros2_trashbot_nav/ros2_trashbot_nav/fixed_route_autonomy.py \
  src/ros2_trashbot_nav/ros2_trashbot_nav/route_utils.py
git diff --check -- src/ros2_trashbot_nav sprints/2026.05.11_03-04_hil-reality-closure
```

### 4. `full-stack-software-engineer`（协同）

允许改动范围：

- `src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway.py`
- `src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py`
- `src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_http.py`

实现要求：

- operator/diagnostics 增加“source=hil|dry_run|simulated”与最近一次任务 run 的 evidence_ref。
- 页面或 API 显示 “模拟/实机差异提示”，避免用户误读。

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
```

## 跨角色协作边界

- 若硬件实测失败阻塞，行为/导航改动必须先补偿回 fallback，不影响既有离线 dry-run。
- `docs/interfaces/ros_contracts.md` 与 operator contract 需保持兼容。
- 所有新证据字段需带 `source` 字段，避免“软件证据冒充 HIL”。

## 测试围栏原则

- 本轮仅执行围栏：上述目标命令、`py_compile`、scoped `git diff --check`。
- 不新增大面积新测试。

## 验收要求（启动前）

```bash
test -f sprints/2026.05.11_03-04_hil-reality-closure/pre_start.md && \
test -f sprints/2026.05.11_03-04_hil-reality-closure/prd.md && \
test -f sprints/2026.05.11_03-04_hil-reality-closure/tech-plan.md
```
