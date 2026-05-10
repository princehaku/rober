# Sprint 2026.05.11 05-06 HIL + Route E2E Hardening - Tech Plan

## 状态

- 阶段：tech-plan started
- 时间：2026-05-11 05:06 Asia/Shanghai
- Owner：`product-okr-owner`
- 主目标：让 O1/O2/O3 从 dry-run 软件证据闭环转换为可复现实机证据闭环，且不重写既有 dry-run 兼容边界。

## 任务分工与验收边界

### 1. `hardware-engineer`（主责：O1）

- 改动文件范围：
  - `scripts/hardware_smoke_wave_rover.py`
  - `docs/acceptance/wave_rover_hil_evidence.md`
  - `docs/acceptance/robot_bringup_checklist.md`
  - `docs/hardware/wave_rover_json_bridge.md`
  - （如需）`docs/vendor/VENDOR_INDEX.md` 引用核对，仅只读
- 交付要求：
  - 产出一次可复现的 WAVE ROVER HIL run，包含 `serial`、`baudrate`、T=1/T=13 指令与反馈样本。
  - 明确 `source=hil_pass` 与 `source=software_proof` 的边界，不混淆。
  - 证据文件必须能回指回 `evidence_ref`。
- 验收命令：
  - `python3 scripts/hardware_smoke_wave_rover.py --help`
  - `python3 scripts/hardware_smoke_wave_rover.py --status`
  - `PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile scripts/hardware_smoke_wave_rover.py`

### 2. `robot-software-engineer`（主责：O2）

- 改动文件范围：
  - `src/ros2_trashbot_behavior/ros2_trashbot_behavior/task_orchestrator.py`
  - `src/ros2_trashbot_behavior/ros2_trashbot_behavior/task_record.py`
  - `src/ros2_trashbot_behavior/ros2_trashbot_behavior/delivery_state_machine.py`
  - `src/ros2_trashbot_bringup/launch/autonomous.launch.py`
  - 相关测试文件（behavior test 路径）
- 交付要求：
  - 完成 O2 失败恢复链路的证据字段覆盖，状态迁移和 `failure_code` 不漏。
  - task_record 写入 `source`, `result_path`, `state_transition_history`, `human_intervention_required`, `evidence_ref`。
  - 保持 dry-run/soft proof 可回放能力不退化。
- 验收命令：
  - `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest src/ros2_trashbot_behavior/test/test_task_orchestrator_collection_execution.py src/ros2_trashbot_behavior/test/test_task_record.py`
  - `PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile src/ros2_trashbot_behavior/ros2_trashbot_behavior/task_orchestrator.py src/ros2_trashbot_behavior/ros2_trashbot_behavior/task_record.py src/ros2_trashbot_behavior/ros2_trashbot_behavior/delivery_state_machine.py`

### 3. `autonomy-engineer`（主责：O3）

- 改动文件范围：
  - `src/ros2_trashbot_nav/ros2_trashbot_nav/fixed_route_autonomy.py`
  - `src/ros2_trashbot_nav/ros2_trashbot_nav/route_utils.py`
  - `src/ros2_trashbot_nav/test/test_fixed_route_status_static.py`
  - `src/ros2_trashbot_nav/test/test_fixed_route_dry_run_offline.py`
- 交付要求：
  - 固定路线状态字段与任务复盘字段对齐（checkpoint/current_index/target/evidence_ref）。
  - 路线缺失与导航失败产生可复现错误码。
- 验收命令：
  - `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest src/ros2_trashbot_nav/test/test_fixed_route_dry_run_offline.py src/ros2_trashbot_nav/test/test_fixed_route_status_static.py`
  - `PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile src/ros2_trashbot_nav/ros2_trashbot_nav/fixed_route_autonomy.py src/ros2_trashbot_nav/ros2_trashbot_nav/route_utils.py`

### 4. `full-stack-software-engineer`（支持：O1/O2/O3）

- 改动文件范围：
  - `src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py`
  - `src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_http.py`
- 交付要求：
  - operator/diagnostics 统一展示 `source=hil_pass|software_proof|simulated`。
  - 展示 `evidence_ref`、失败码和人工接管建议。
- 验收命令：
  - `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest src/ros2_trashbot_behavior/test/test_operator_gateway_static.py src/ros2_trashbot_behavior/test/test_operator_gateway_http.py src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`
  - `PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_http.py`

## 评审与验收收敛

- review 命名问题为 P3：
  - 目标是确保技术计划所列 review 命令可执行，避免重复出现 `NO TESTS RAN`。
- diff 与格式验证边界：
  - 在 scoped 范围内先清洁 `git diff --check`；`README.md` 尾空格仅在外层 P3 中跟踪，不阻塞 O1/O2/O3 主线。

## 本轮不做

- 不新增电梯现实机控制能力。
- 不扩展视觉/detection 模型。
- 不引入大规模参数或场景矩阵。

## 风险与依赖

- O1 的实机证据依赖上机时序与实际串口参数确认。
- O2/O3 回放证据依赖工程师在同一 run 内保持 `evidence_ref` 唯一且不丢失。
- dry-run 与 HIL 数据必须分源标注，否则会再次触发验收边界争议。
