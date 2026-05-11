# Sprint 2026.05.11 07-08 HIL proof and route replay - Tech Done

## 状态

- 阶段：tech-done completed
- 时间：2026-05-11 22:30 Asia/Shanghai
- Owner：`product-okr-owner`
- 结论：本轮未形成可交付 `hil_pass` 实机证据包；已完成 O3 route replay 复盘字段修补并可执行静态复现，进入 Blocked 收口。

## 本轮实际变更与执行结果

### O1 `hardware-engineer`

- 约束文件保持原样读取并核对：`docs/acceptance/hil_runbook.md`、`docs/acceptance/robot_bringup_checklist.md`、`docs/acceptance/wave_rover_hil_evidence.md`。
- 未新增/修改产品代码，仅执行验收命令确认当前阻塞：
  - `python3 scripts/hardware_smoke_wave_rover.py --help`
  - `python3 scripts/hardware_smoke_wave_rover.py --status`
  - `PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile scripts/hardware_smoke_wave_rover.py`
  - `python3 scripts/hardware_smoke_wave_rover.py --move-test --test-speed 0.05 --test-duration-s 0.3 --serial-port /dev/ttyUSB0 --baudrate 115200`
- 结果：`--move-test` 因真实串口缺失阻塞，未产出 `command.txt / serial.log / feedback_T1001.log / odom_once.jsonl / imu_once.jsonl / battery_once.jsonl`。
- 结论：O1 不满足本轮“真实一次 `hil_pass` + 完整 evidence packet”验收，Blocked。

### O3 `autonomy-engineer`

- 在既有文档与代码边界内补齐 route replay 一致性并执行 dry-run 与静态校验：
  - `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest src/ros2_trashbot_nav/test/test_fixed_route_dry_run_offline.py src/ros2_trashbot_nav/test/test_fixed_route_status_static.py`
  - `PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile src/ros2_trashbot_nav/ros2_trashbot_nav/fixed_route_autonomy.py src/ros2_trashbot_nav/ros2_trashbot_nav/route_utils.py`
- 结果：13 tests OK；py_compile pass。
- 结论：软件层 route_progress 已对齐 `checkpoint/current_index/target/failure_code/evidence_ref` 到 task 复盘字段口径，并新增可配置 `evidence_ref` 覆盖；未产生新的 route replay 实车 run 产物，故不构成 O3 全链路验收通过。

### O2 `robot-software-engineer`

- 执行一致性核验围栏：
  - `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest src/ros2_trashbot_behavior/test/test_task_orchestrator_collection_execution.py src/ros2_trashbot_behavior/test/test_task_record.py`
  - `PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile src/ros2_trashbot_behavior/ros2_trashbot_behavior/task_orchestrator.py src/ros2_trashbot_behavior/ros2_trashbot_behavior/task_record.py`
- 结果：10 tests OK；py_compile pass。
- 结论：字段契约仍可解析，但本轮未新增 run-level 任务复盘样本（失败/超时/取消）与 `evidence_ref` run 复现记录。

## 证据对齐与失败定位

- `scripts/hardware_smoke_wave_rover.py --status` 输出包含 `source=software_proof` 与 `source=hil_pass` 边界、`dependency_note: pyserial required`、`required_args_for_hil`。
- `--move-test` 输出已打印 `evidence_ref` 为 `run_20260511T063354Z_-dev-ttyUSB0_hil_pass_speed0p050_dur0p30`，但因 `could not open port /dev/ttyUSB0` 未写盘。
- 当前 `hardware`、`route`、`task_record` 三端没有共享到同一个已落盘 `evidence_ref`。
- `NO TESTS RAN` 在本轮未出现；本轮验收仅使用已执行命令。

## 剩余风险与阻塞

1. O1：无真实串口设备导致 `hil_pass` 无法完成，`/odom/imu/battery` 以及 `feedback_T1001` 采样证据无法补齐。
2. O3：未形成新 run replay 记录，无法给 O3 的 route replay 验收加码。
3. O2：缺 run-level 失败/超时/取消样本，`failure_code/state_transition_history/human_intervention_required` 的 run 交叉复盘未闭环。
4. 运行后续动作：在可用硬件环境（支持 `/dev/ttyUSB0`）下重跑 `hil_pass`，并与 route replay 使用同一 `evidence_ref`。
