# Sprint 2026.05.11 05-06 HIL + Route E2E Hardening - Tech Done

## 状态
- 阶段：tech-done completed
- 时间：2026-05-11
- Owner：`product-okr-owner`（汇总）
- 录入人：团队执行成员（robot/hardware/autonomy/full-stack）

## 本轮实际交付（按 O1/O2/O3 优先级）

### O1 硬件协议与 HIL 证据闭环
- 完成 `scripts/hardware_smoke_wave_rover.py` 的可复用参数、`--status` 与反馈采样输出增强。
- 在 `docs/acceptance/wave_rover_hil_evidence.md`、`docs/acceptance/robot_bringup_checklist.md`、`docs/hardware/wave_rover_json_bridge.md` 明确 `software_proof` 与 `hil_pass` 边界。
- 新增 `docs/acceptance/hil_runbook.md`，把 HIL 运行步骤、采样条件、pass criteria 与 evidence_ref 记录模板写入。
- 更新 `src/ros2_trashbot_hardware/ros2_trashbot_hardware/hardware_diagnostics_proof.py` 元数据 source 标注。

### O2 送达任务闭环与可恢复性
- 在行为侧补齐失败可追溯路径：
  - `src/ros2_trashbot_behavior/ros2_trashbot_behavior/task_orchestrator.py`
  - `src/ros2_trashbot_behavior/ros2_trashbot_behavior/task_record.py`
  - `src/ros2_trashbot_behavior/ros2_trashbot_behavior/delivery_state_machine.py`
- task record 新字段：`source`、`state_transition_history`、`result_path`、`failure_code`、`human_intervention_required`。
- `operator_gateway.py` 补齐任务终态与状态透传。
- 测试：行为链条 `test_task_orchestrator_collection_execution` + `test_task_record` 已通过。

### O3 固定路线复盘与字段可复用
- `src/ros2_trashbot_nav/ros2_trashbot_nav/fixed_route_autonomy.py` 与 `route_utils.py` 增加 O3 对齐失败码（`NO_ROUTE`、`CHECKPOINT_MISSING`、`NAVIGATION_ABORT`）。
- fixed-route status 增加 `checkpoint`、`target`、`failure_code` 与 `state` 一致口径。
- `docs/navigation/fixed_route_workflow.md` 更新字段含义。
- 测试：`test_fixed_route_dry_run_offline` + `test_fixed_route_status_static` 已通过。

### 用户触点可读性（O5 最小同步）
- 全栈侧完成 `/api` 与 Operator UI 的可追溯字段透传。
- 文件：`operator_gateway.py`、`operator_gateway_diagnostics.py`、`operator_gateway_http.py` 及对应 tests。
- 失败任务支持 `source`（`hil_pass|software_proof|simulated`）、`evidence_ref`、`failure_code`、`human_intervention_required`、`state_transition_history`。

## 验收命令执行与结果

- 行为链：
  - `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest src/ros2_trashbot_behavior/test/test_task_orchestrator_collection_execution.py src/ros2_trashbot_behavior/test/test_task_record.py`
  - `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest src/ros2_trashbot_bringup/test/test_launch_contract_static.py`
  - 结果：通过

- 导航链：
  - `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest src/ros2_trashbot_nav/test/test_fixed_route_dry_run_offline.py src/ros2_trashbot_nav/test/test_fixed_route_status_static.py`
  - 结果：通过

- 全栈链：
  - `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest src/ros2_trashbot_behavior/test/test_operator_gateway_static.py src/ros2_trashbot_behavior/test/test_operator_gateway_http.py src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`
  - `PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway.py src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_http.py`
  - 结果：通过

- 硬件 smoke：
  - `python3 scripts/hardware_smoke_wave_rover.py --help`
  - `python3 scripts/hardware_smoke_wave_rover.py --status`
  - `python3 scripts/hardware_smoke_wave_rover.py --move-test --test-speed 0.05 --test-duration-s 0.3 --serial-port /dev/ttyUSB0 --baudrate 115200`
  - 结果：受环境限制阻塞（`ModuleNotFoundError: No module named 'serial'`）

## 风险与剩余任务

1. 环境阻塞：当前 Python 运行环境为外部管理（PEP 668），无法直接 `pip install pyserial`，建议在 Docker 或虚拟环境内重跑 HIL 命令并补 `hil_pass` evidence。
2. 实机验证仍待：`hil_pass` 需真实串口执行后回填到 `wave_rover_hil_evidence.md` 与 `robot_bringup_checklist.md`。
3. full-stack 与 robot 字段对齐依赖 task_record 来源字段持续写入（`source/failure_code/evidence_ref/human_intervention_required/state_transition_history`）
