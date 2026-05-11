# Sprint 2026.05.11 07-08 HIL proof and route replay - Tech Plan

## 状态

- 阶段：tech-plan completed
- 时间：2026-05-11 11:20 Asia/Shanghai
- Owner：`product-okr-owner`
- 目标：本轮只做 O1/O3 路径的执行与收口，沿用 O2 字段消费链路，不扩大面向范围。

## 阶段收口

- 计划项已由 `tech-done.md` 执行结果逐项回填。
- 本轮按既定验收命令口径收口，不追加新实现或新验证任务。

## 技术目标（与 evidence 对齐）

- O1：执行一次 `hil_pass` 实机 run，强制产出 `evidence_ref` 与证据文件。
- O3：完成一次固定路线复现，确保 `route_progress` 与 `task_record` 的 `evidence_ref` 对齐。
- O2：对齐任务复盘字段语义，不再引入新模型/测试。

## 任务分工（Owner）

### 1) hardware-engineer（主责 O1）

#### 文件范围

- `docs/acceptance/hil_runbook.md`
- `docs/acceptance/wave_rover_hil_evidence.md`
- `docs/acceptance/robot_bringup_checklist.md`
- `docs/hardware/wave_rover_json_bridge.md`
- `scripts/hardware_smoke_wave_rover.py`

#### 目标

- 在可用上机环境下执行 `hil_pass` 命令，生成与文档一致的证据 packet。
- 若受阻，完整记录 `Blocked`（缺依赖/串口权限/反馈缺失/轨迹偏差）并不升级完成度。

#### 验收命令

- `python3 scripts/hardware_smoke_wave_rover.py --help`
- `python3 scripts/hardware_smoke_wave_rover.py --status`
- `PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile scripts/hardware_smoke_wave_rover.py`
- `python3 scripts/hardware_smoke_wave_rover.py --move-test --test-speed 0.05 --test-duration-s 0.3 --serial-port /dev/ttyUSB0 --baudrate 115200`

#### 证据对齐

- 与本轮目标一致：`evidence_ref` 必须覆盖 hardware smoke、/odom、/imu、/battery 与 task trace。

### 2) autonomy-engineer（主责 O3）

#### 文件范围

- `src/ros2_trashbot_nav/ros2_trashbot_nav/fixed_route_autonomy.py`
- `src/ros2_trashbot_nav/ros2_trashbot_nav/route_utils.py`
- `src/ros2_trashbot_nav/test/test_fixed_route_dry_run_offline.py`
- `src/ros2_trashbot_nav/test/test_fixed_route_status_static.py`
- `docs/navigation/fixed_route_workflow.md`

#### 目标

- 在同一 `evidence_ref` 下补齐 route replay 实跑/复盘链，输出可回放状态字段。
- 保证异常码口径与 task record 同步。

#### 验收命令

- `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest src/ros2_trashbot_nav/test/test_fixed_route_dry_run_offline.py src/ros2_trashbot_nav/test/test_fixed_route_status_static.py`
- `PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile src/ros2_trashbot_nav/ros2_trashbot_nav/fixed_route_autonomy.py src/ros2_trashbot_nav/ros2_trashbot_nav/route_utils.py`

### 3) robot-software-engineer（协作 O2）

#### 文件范围

- `src/ros2_trashbot_behavior/ros2_trashbot_behavior/task_record.py`
- `src/ros2_trashbot_behavior/ros2_trashbot_behavior/task_orchestrator.py`

#### 目标

- 仅做字段一致性校验：将 O1/O3 的 `evidence_ref` 与 task 复盘字段保持一致。
- 不新增业务状态机支线。

#### 验收命令

- `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest src/ros2_trashbot_behavior/test/test_task_orchestrator_collection_execution.py src/ros2_trashbot_behavior/test/test_task_record.py`
- `PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile src/ros2_trashbot_behavior/ros2_trashbot_behavior/task_orchestrator.py src/ros2_trashbot_behavior/ros2_trashbot_behavior/task_record.py`

## 流程与围栏约束

- 继续不新增测试文件。
- 本轮主要围栏以命令执行 + 输出文件是否有实际 `hil_pass` 与 route replay 产物为准。
- `NO TESTS RAN` 作为验收失败不再作为通过理由：如命名覆盖问题继续发生，需同步替换为可执行命令路径。

## 交付边界

- 只更新本 sprint 文档、HIL evidence 文档族和现有执行链；不改接口契约本体。
- 所有硬件、导航、行为字段都须写明来源（`source=hil_pass|software_proof`）。
