# Sprint 2026.05.11 07-08 HIL proof and route replay - PRD

## 用户价值与北极星

把“普通手机用户一键发起送垃圾任务”从离线逻辑说明升级为“可复现、可交付、可追溯”的实机闭环能力：同一任务 run 必须能在证据链中回答“是否真实到达、为何失败、如何恢复”。

## 本轮目标（仅 O1/O3 主线）

1. 完成一次真实 `hil_pass` 采集与 run 级证据归档，不将 `software_proof` 冒充为 HIL 通过。
2. 用同一 run 链路补齐一次固定路线复现证据（route replay）并可回放到 task 复盘。
3. 以最小围栏命令清理验收阻塞，不新增测试文件。

## OKR 映射（本轮下沉）

### Objective 1：打通官方硬件协议，建立可信底盘控制层

- KR1：补齐一次可复现的 WAVE ROVER 实机 run（`serial_port/baudrate/feedback_interval_ms/evidence_ref` 全量留存）。
  - 证据来源：`docs/acceptance/hil_runbook.md`, `docs/acceptance/wave_rover_hil_evidence.md`
- KR2：明确 `hil_pass` 证据与 `software_proof` 的边界，不混淆。
  - 证据来源：`sprints/2026.05.11_06-07_hil-route-e2e-hardening-2/tech-done.md`, `docs/acceptance/robot_bringup_checklist.md`

### Objective 3：建立可验证导航与固定路线能力

- KR1：一次 route replay 产生 `checkpoint/current_index/target/evidence_ref/failure_code`。
  - 证据来源：`docs/navigation/fixed_route_workflow.md`, `src/ros2_trashbot_nav/ros2_trashbot_nav/fixed_route_autonomy.py`
- KR2：复盘 run 与固定路线状态字段一一对应。
  - 证据来源：`sprints/2026.05.11_06-07_hil-route-e2e-hardening-2/tech-done.md`, `src/ros2_trashbot_behavior/ros2_trashbot_behavior/task_record.py`

## 本轮不做

- 不做：O2 复杂新逻辑开发、O4/O5 扩展、full-stack 主链路改造。
- 不做：新增测试文件，仅做围栏命令和现有测试命名修复。

## 优先级

- P0：O1 一次成功 `hil_pass` + 证据链完整。
- P1：O3 route replay + 复盘字段一致。
- P2：清理验收围栏风险（`NO TESTS RAN`）。

## 验收口径

1. 产出至少一条 `hil_pass` evidence 记录，并填入
   - `source=hil_pass`
   - `evidence_ref`
   - `command.txt` / `serial.log` / `feedback_T1001.log`
   - `odom_once.jsonl` / `imu_once.jsonl` / `battery_once.jsonl`
2. route replay 可复现一次任务状态转移并回放到 task record 的 `route_progress`。
3. `evidence_ref` 在 hardware/route/diagnostics/task 之间一致。
4. 验收命令可执行且无新增测试文件。

## 对应主责

- `hardware-engineer`（O1）
- `autonomy-engineer`（O3）
- `robot-software-engineer`（O2 维持复盘一致性，不新增功能）
