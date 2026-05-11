# Sprint 2026.05.11 06-07 HIL + Route E2E Hardening-2 - Tech Done

## 状态

- 阶段：tech-done completed (acceptance close)
- 时间：2026-05-11 10:18 Asia/Shanghai
- Owner：`product-okr-owner`（汇总）
- 结论：O1/O2/O3 字段契约已复核贯通；本轮关键偏差在于 O1 实机 `hil_pass` 证据包未补齐，O3 未新增 autonomy 验收日志。

## 本轮按角色跟踪结果

### 1) `hardware-engineer`（O1）

- 已交付证据链：
  - `scripts/hardware_smoke_wave_rover.py` 保留并输出 run-level `evidence_ref`，支持 `--evidence-ref` 显式覆盖。
  - `docs/acceptance/hil_runbook.md`、`docs/acceptance/robot_bringup_checklist.md`、`docs/acceptance/wave_rover_hil_evidence.md`、`docs/hardware/wave_rover_json_bridge.md` 一致声明 `source=software_proof` 与 `source=hil_pass` 边界。
- 本轮阻塞：
  - 未见本轮 `hil_pass` evidence packet（`evidence/<evidence_ref>/command.txt`、`serial.log`、`feedback_T1001.log`）落地记录。

### 2) `robot-software-engineer`（O2）

- 已交付证据链：
  - `task_orchestrator.py` 中任务结果归档包含 `result_path/evidence_ref/failure_code/human_intervention_required` 派生与写入。
  - `task_record.py` 包含 `result_path/evidence_ref/failure_code/human_intervention_required/state_transition_history` 持久化字段。
  - `delivery_state_machine.py` 保留 `NAV_FAIL/NAV_TIMEOUT/TASK_CANCEL` 等失败码语义。
- 验收状态：
  - 本轮未收到新的 unittest 日志；沿用上一轮（05-06）行为链测试通过记录作为当前基线。

### 3) `autonomy-engineer`（O3）

- 已交付证据链：
  - `route_utils.py` 固定失败码常量：`NO_ROUTE`、`CHECKPOINT_MISSING`、`NAVIGATION_ABORT`。
  - `fixed_route_autonomy.py` 保留 `checkpoint/current_index/target/evidence_ref/failure_code` 对齐逻辑。
- 验收状态：
  - 本轮未发现新增 autonomy 侧测试输出日志，且主文件最近修改时间早于本轮 sprint 启动时间。

## 验收命令复核结果（tech-plan 指定）

命令：

```bash
rg -n "source=hil_pass|evidence_ref|failure_code|state_transition_history|human_intervention_required|NO_ROUTE|CHECKPOINT_MISSING|NAVIGATION_ABORT" /Users/m4/apps/rober
```

关键命中片段：

- `scripts/hardware_smoke_wave_rover.py:260` -> `evidence_ref = ... build_run_evidence_ref(..., HIL_SOURCE)`
- `src/ros2_trashbot_behavior/ros2_trashbot_behavior/task_orchestrator.py:612-616` -> `failure_code`、`evidence_ref`、`human_intervention_required`
- `src/ros2_trashbot_behavior/ros2_trashbot_behavior/task_record.py:80-82,86` -> `evidence_ref`、`failure_code`、`human_intervention_required`、`state_transition_history`
- `src/ros2_trashbot_nav/ros2_trashbot_nav/route_utils.py:10-12` -> `NO_ROUTE/CHECKPOINT_MISSING/NAVIGATION_ABORT`
- `src/ros2_trashbot_nav/ros2_trashbot_nav/fixed_route_autonomy.py:126,411,431` -> `evidence_ref`、`failure_code` 写入固定路线状态
- `docs/acceptance/robot_bringup_checklist.md:9,15-17` -> `source=software_proof` 与 `source=hil_pass` 边界
- `docs/acceptance/wave_rover_hil_evidence.md:42-46` -> `hil_pass` evidence packet 与 blocked 记录约束

## 测试输出日志映射到 OKR/PRD

### O1（PRD: O1 KR1/KR2）

- 可用日志（继承 05-06）：
  - `python3 scripts/hardware_smoke_wave_rover.py --help`
  - `python3 scripts/hardware_smoke_wave_rover.py --status`
  - move-test 命令受阻：`ModuleNotFoundError: No module named 'serial'`
- 映射结论：
  - 已满足 `software_proof` 模板核验；
  - 未满足本轮 `hil_pass` 实机准入验收（blocked）。

### O2（PRD: O2 KR1/KR2/KR3）

- 可用日志（继承 05-06）：
  - `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest src/ros2_trashbot_behavior/test/test_task_orchestrator_collection_execution.py src/ros2_trashbot_behavior/test/test_task_record.py` -> 通过
- 映射结论：
  - 失败恢复字段契约具备软件验证基线；
  - 本轮缺少新增 run 级任务回放日志，不提升到“实机闭环”。

### O3（PRD: O3 KR1/KR2/KR3）

- 可用日志（继承 05-06）：
  - `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest src/ros2_trashbot_nav/test/test_fixed_route_dry_run_offline.py src/ros2_trashbot_nav/test/test_fixed_route_status_static.py` -> 通过
- 映射结论：
  - 固定路线失败码与复盘字段契约在软件层有效；
  - 本轮无新增 autonomy 测试日志与 route 实跑证据，完成度不变。

## 失败定位（本轮）

1. O1 失败点：缺真实串口/依赖环境下的 `hil_pass` run 产物，当前只有模板与离线约束。
2. O3 失败点：本轮未提交新的 autonomy 验收日志，无法证明 hardening-2 目标中的“新增复验”。
3. 验收链一致性风险：若 O1 后续补跑时 `evidence_ref` 未与 task record/diagnostics 同步，O2/O3 复盘链会断。

## 剩余风险

- `software_proof` 与 `hil_pass` 仍存在实机证据缺口，不能宣称 O1 已完成。
- `/odom` 当前仍为 command integration 语义，缺 encoder/实测闭环。
- Nav2/固定路线真实场景复现证据仍未入档，O2/O3 仍属于“软件契约可用”层。

## 技术建议（下一轮）

- 建议创建新一轮 `sprints/2026.05.11_07-08_hil-proof-and-route-replay`，而非继续复用当前轮。
- 原因：
  1. 当前轮核心目标是收口与偏差定位，文档已闭环；
  2. 下一轮需要明确执行型目标（O1 实机 `hil_pass` 补证据包 + O3 route replay 实跑），便于独立验收与风险隔离。
