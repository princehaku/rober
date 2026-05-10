# Sprint 2026.05.11 04-05 HIL + Route E2E Hardening - Tech Plan

## 状态

- 阶段：tech-plan started
- 时间：2026-05-11 03:20 Asia/Shanghai
- Owner：`product-okr-owner`

## 任务分工与交付边界

### 1. `robot-software-engineer`（主责）

允许改动路径：

- `src/ros2_trashbot_behavior/ros2_trashbot_behavior/task_orchestrator.py`
- `src/ros2_trashbot_behavior/ros2_trashbot_behavior/task_record.py`
- `src/ros2_trashbot_behavior/ros2_trashbot_behavior/delivery_state_machine.py`
- `src/ros2_trashbot_behavior/test/test_task_orchestrator_collection_execution.py`
- `src/ros2_trashbot_behavior/test/test_task_record.py`
- `src/ros2_trashbot_bringup/launch/autonomous.launch.py`
- `src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway.py`

目标要求：

- 强化 mission 主链失败恢复（`NAV_FAIL`, `NAV_TIMEOUT`, `TASK_CANCEL`）。
- `task_record` 写入 `source`, `state_transition_history`, `failure_code`, `human_intervention_required`, `evidence_ref`。
- 确保 `task_record` 支持 `hil_pass` 与 `dry_run` 两条源。

验收命令：

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest \
  src/ros2_trashbot_behavior/test/test_task_orchestrator_collection_execution.py \
  src/ros2_trashbot_behavior/test/test_task_record.py
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile \
  src/ros2_trashbot_behavior/ros2_trashbot_behavior/task_orchestrator.py \
  src/ros2_trashbot_behavior/ros2_trashbot_behavior/task_record.py \
  src/ros2_trashbot_behavior/ros2_trashbot_behavior/delivery_state_machine.py
```

### 2. `hardware-engineer`

允许改动路径：

- `scripts/hardware_smoke_wave_rover.py`
- `docs/acceptance/wave_rover_hil_evidence.md`
- `docs/acceptance/robot_bringup_checklist.md`
- `docs/hardware/wave_rover_json_bridge.md`

目标要求：

- 明确 HIL 入口参数（串口参数、速度命令测试参数、反馈采样时长）。
- 产出并约束一个 `hil_pass` 证据样例模板。
- 在文档显式标注所有硬件协议和参数依据来源：`docs/vendor/VENDOR_INDEX.md`。

验收命令：

```bash
python3 scripts/hardware_smoke_wave_rover.py --help
python3 scripts/hardware_smoke_wave_rover.py --status
# 上机时补充：--serial-port /dev/ttyUSB0 --baudrate 115200
```

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile scripts/hardware_smoke_wave_rover.py
```

### 3. `autonomy-engineer`

允许改动路径：

- `src/ros2_trashbot_nav/ros2_trashbot_nav/fixed_route_autonomy.py`
- `src/ros2_trashbot_nav/ros2_trashbot_nav/route_utils.py`
- `src/ros2_trashbot_nav/test/test_fixed_route_status_static.py`
- `src/ros2_trashbot_nav/test/test_fixed_route_dry_run_offline.py`

目标要求：

- 将 fixed-route 的 `checkpoint / current_index / target` 与 task record 的复盘字段对齐。
- 失败分支 `NO_ROUTE`, `CHECKPOINT_MISSING`, `NAVIGATION_ABORT` 必须产生可读错误码。

验收命令：

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest \
  src/ros2_trashbot_nav/test/test_fixed_route_dry_run_offline.py \
  src/ros2_trashbot_nav/test/test_fixed_route_status_static.py
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile \
  src/ros2_trashbot_nav/ros2_trashbot_nav/fixed_route_autonomy.py \
  src/ros2_trashbot_nav/ros2_trashbot_nav/route_utils.py
```

### 4. `full-stack-software-engineer`

允许改动路径：

- `src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py`
- `src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_http.py`

目标要求：

- 统一显示 `source=hil_pass|software_proof|simulated`。
- 任务失败与人工接管建议与 `evidence_ref` 一并展示。

验收命令：

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest \
  src/ros2_trashbot_behavior/test/test_operator_gateway_static.py \
  src/ros2_trashbot_behavior/test/test_operator_gateway_http.py \
  src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile \
  src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py \
  src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_http.py
```

## 复核约束（review 命名问题）

- 全量围栏：
  - `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest src/ros2_trashbot_behavior/test/test_review_gate.py`（或以本轮技术计划实际覆盖的 review test 命名文件替代）
  - 若项目仍采用现有 `*review*` 命名策略，要求本轮补齐至少一个可执行 review 单测，清除 `NO TESTS RAN`。
- `git diff --check`：
  - `git diff --check -- src/ros2_trashbot_behavior src/ros2_trashbot_nav src/ros2_trashbot_hardware scripts/hardware_smoke_wave_rover.py docs/acceptance docs/hardware`。
  - 全仓 `git diff --check` 的 README whitespace cleanup 作为 P3 外部任务，在本 sprint 只要求 scoped 清洁。

## 跨角色协调

- 代码变更须保留 dry-run 可运行性；没有上机时不将 HIL 结果当作通过。
- 证据字段必须包含 `source`，并统一到 operator 与 diagnostics 同一命名。
- `docs/vendor/VENDOR_INDEX.md` 仅作硬件事实来源，不在本轮引入新硬件约束。
