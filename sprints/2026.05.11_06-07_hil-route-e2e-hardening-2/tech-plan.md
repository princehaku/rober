# Sprint 2026.05.11 06-07 HIL + Route E2E Hardening-2 - Tech Plan

## 状态

- 阶段：tech-plan started
- 时间：2026-05-11 06:10 Asia/Shanghai
- Owner：`product-okr-owner`
- 目标：只围绕 O1/O2/O3 低完成度主线推进，不将 full-stack 作为主线执行内容。

## 本轮技术目标（与 evidence 对齐）

- O1：把软硬件证据分层从当前离线说明推进到可复现 HIL 跑法（含 run 级 evidence_ref）。
  - 证据来源：`OKR.md`、`05-06 tech-done.md`、`21-22 review`
- O2：任务失败恢复字段完整可追溯，包含 `failure_code/state_transition_history/human_intervention_required/evidence_ref/source`。
  - 证据来源：`OKR.md`、`05-06 tech-done.md`、`21-22 review`
- O3：固定路线复盘字段一致，路由中断可复现归因。
  - 证据来源：`OKR.md`、`05-06 tech-done.md`、`21-22 review`

## 任务分工与文件范围

### 1) `hardware-engineer`（主责：O1）

#### 文件范围

- `scripts/hardware_smoke_wave_rover.py`
- `docs/acceptance/wave_rover_hil_evidence.md`
- `docs/acceptance/robot_bringup_checklist.md`
- `docs/hardware/wave_rover_json_bridge.md`

#### 目标

- 产出可执行的 HIL 参数模板与采样约定（串口、波特率、T=1/T=13、采样时长）。
- `evidence_ref` 与 `source=hil_pass`/`software_proof` 分离。
- 若受阻，明确在文档记录 blocked 原因（而非伪造通过）。

#### 验收命令（最小围栏）

- `python3 scripts/hardware_smoke_wave_rover.py --help`
- `python3 scripts/hardware_smoke_wave_rover.py --status`
- `PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile scripts/hardware_smoke_wave_rover.py`
- 上机可运行（环境满足时）：`python3 scripts/hardware_smoke_wave_rover.py --move-test --test-speed 0.05 --test-duration-s 0.3 --serial-port /dev/ttyUSB0 --baudrate 115200`

#### 证据来源映射

- O1 仅做到可复现实机证据级别，不覆盖 O2/O3 逻辑实现。
- 证据来源：`OKR.md`（O1 实测缺口）、`05-06 tech-done.md`（软件证据已补但实机阻塞）、`21-22 review`（验收围栏问题）。

### 2) `robot-software-engineer`（主责：O2）

#### 文件范围

- `src/ros2_trashbot_behavior/ros2_trashbot_behavior/task_orchestrator.py`
- `src/ros2_trashbot_behavior/ros2_trashbot_behavior/task_record.py`
- `src/ros2_trashbot_behavior/ros2_trashbot_behavior/delivery_state_machine.py`
- `src/ros2_trashbot_behavior/test/test_task_orchestrator_collection_execution.py`
- `src/ros2_trashbot_behavior/test/test_task_record.py`

#### 目标

- 让失败恢复路径（超时/取消/导航失败）完整持久化 `failure_code` 与 `state_transition_history`。
- 强制记录 `human_intervention_required` 与 `result_path/source/evidence_ref`。
- 统一与 diagnostics/上次任务回放字段边界。

#### 验收命令（最小）

- `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest src/ros2_trashbot_behavior/test/test_task_orchestrator_collection_execution.py src/ros2_trashbot_behavior/test/test_task_record.py`
- `PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile src/ros2_trashbot_behavior/ros2_trashbot_behavior/task_orchestrator.py src/ros2_trashbot_behavior/ros2_trashbot_behavior/task_record.py src/ros2_trashbot_behavior/ros2_trashbot_behavior/delivery_state_machine.py`

#### 证据来源映射

- `OKR.md` 的任务闭环缺口 + `05-06 tech-done.md` 的任务记录能力 + `21-22 review` 验收可执行性要求。

### 3) `autonomy-engineer`（主责：O3）

#### 文件范围

- `src/ros2_trashbot_nav/ros2_trashbot_nav/fixed_route_autonomy.py`
- `src/ros2_trashbot_nav/ros2_trashbot_nav/route_utils.py`
- `src/ros2_trashbot_nav/test/test_fixed_route_dry_run_offline.py`
- `src/ros2_trashbot_nav/test/test_fixed_route_status_static.py`

#### 目标

- 对齐 fixed-route 的 `checkpoint/current_index/target/evidence_ref/failure_code` 与任务复盘字段。
- 提供路线缺失、中断、导航终止的可复现归因。
- 保持现有 dry-run 回放能力不回退。

#### 验收命令（最小）

- `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest src/ros2_trashbot_nav/test/test_fixed_route_dry_run_offline.py src/ros2_trashbot_nav/test/test_fixed_route_status_static.py`
- `PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile src/ros2_trashbot_nav/ros2_trashbot_nav/fixed_route_autonomy.py src/ros2_trashbot_nav/ros2_trashbot_nav/route_utils.py`

#### 证据来源映射

- `OKR.md` O3 缺口、`05-06 tech-done.md` fixed-route 字段增强、`21-22 review`（验证命令摩擦）。

### 4) `full-stack-software-engineer`（只做支援）

#### 文件范围

- 仅在本轮文档层面约束接口展示；不做主线闭环编码扩展。

#### 目标

- 确认 O1/O2/O3 证据与失败码展示仅为一致性消费，不改变行为/导航/硬件主线。
- 证据来源：本轮优先级与范围限定。

## review 围栏收敛（最小化测试体量）

- 不新增测试文件。
- 继续保留 `test_*review*py` 命名风险修复为最小措施：本轮采用可执行替代命令，不让 `NO TESTS RAN` 成为阻塞项。
- 证据来源：`21-22 review-progress-metrics/final.md`。

## 风险与阻塞

- HIL 受外设与依赖限制导致 O1 可能先 blocked，需在 `tech-done` 标注 residual risk 后推进 O2/O3 软件闭环。
- `evidence_ref` 命名若三角色不一致，O2/O3 复盘链路断裂。
- O1/O2/O3 都有验收门槛，但不可用 full-stack 代码改动替代硬件或导航主线交付。
- 上述风控均需引用：`OKR.md` 当前快照、`05-06 tech-done.md` 风险项、`21-22 review` 验收命令记录。

## 本轮不做

- 不改动 `sprints/2026.05.11_06-07_hil-route-e2e-hardening-2/` 以外的业务代码。
- 不改接口契约本体，不重构用户界面。
- 不新增或扩展测试矩阵。
