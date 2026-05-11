# Sprint 2026.05.11 09-10 HIL pass and route replay crosscheck - Tech Done

## 状态

- 阶段：tech-done in-progress
- 时间：2026-05-11 16:47 Asia/Shanghai
- Owner：`hardware-engineer`
- 范围：O1 WAVE ROVER 真实串口 move-test 上车前准入与 evidence_ref 闭环准备

## 任务目标

- 以同一 `evidence_ref` 为主线补齐 fixed-route run-level 复盘闭环。
- 让 `route_progress` 与 route replay、task_record/diagnostics 可对齐核验。
- 缺 run-level 样本时给出可复验的只读对账脚本与重试路径。
- 以 `source=software_proof` 验证后尝试单次 `hil_pass` run-level 产物（本轮目标：`run_20260511T094018Z_hil_pass_speed0p050_dur0p30`）。

## 本轮实际执行

### 1) 固定路线字段复用与持久化

- `src/ros2_trashbot_nav/ros2_trashbot_nav/fixed_route_autonomy.py`
  - `build_route_checkpoint_payload()` 参数传入 `source` 与 `route_contract_version`。
  - `route_progress` 与 replay 写入字段链路固定为：
    - `checkpoint`
    - `current_index`
    - `target`
    - `failure_code`
    - `evidence_ref`

- `src/ros2_trashbot_nav/ros2_trashbot_nav/route_utils.py`
  - `build_route_checkpoint_payload()` 明确默认补齐 `route_contract_version` 与 `source`。
  - 契约字段在 `route_progress` 与 `build_route_replay_entry()` 侧可持续复用。

### 2) run-level 对账脚本（read-only helper）

- `scripts/evidence_crosscheck.py`
  - 新增命令：
    - 检查 fixed-route status 与其 `route_progress` 主字段。
    - 检查 latest route_replay 行与 status 字段一致性。
    - 可选对齐 task_record（显式路径或目录按 evidence_ref 自动查找）。
  - 对齐项：`checkpoint/current_index/target/failure_code/evidence_ref`。

### 3) 文档

- `docs/navigation/fixed_route_workflow.md`
  - 补充脚本调用方式、缺样本说明和 `evidence_ref` 对账期望。

### 4) O1 硬件 smoke 阻塞准入（本轮关键）

- 依据命令：
  - `python3 scripts/hardware_smoke_wave_rover.py --help`
  - `python3 scripts/hardware_smoke_wave_rover.py --status`
  - `python3 scripts/hardware_smoke_wave_rover.py --move-test --test-speed 0.05 --test-duration-s 0.3 --serial-port /dev/ttyUSB0 --baudrate 115200 --evidence-ref run_20260511T094018Z_hil_pass_speed0p050_dur0p30`
  - `PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile scripts/hardware_smoke_wave_rover.py`
- 结果：
  - `--help`/`--status`/`py_compile` 均返回 `0`（software proof）
  - `--move-test` 因 `serial` 不存在返回 `1`
- 严格根因：
  - `ls -l /dev/ttyUSB0`：`No such file or directory`
  - `/dev/ttyUSB*`：`[]`
- 已输出 run-level 证据占位（阻塞）：
  - `evidence/run_20260511T094018Z_hil_pass_speed0p050_dur0p30/command.txt`
  - `.../serial.log`
  - `.../feedback_T1001.log`
  - `.../odom_once.jsonl`
  - `.../imu_once.jsonl`
  - `.../battery_once.jsonl`
- O2/O3 串联说明：
  - 本轮未形成 `source=hil_pass` 的真实 `feedback`/`odom`/`imu`/`battery` 样本，`O2/O3` 的 `fixed-route` run-level 复核链路仍待上车补齐。

### 5) O2 任务证据链一致性补齐（robot behavior ↔ diagnostics）

- `src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py`
  - 新增 `coalesce_traceability_fields()`，统一 `result_path/evidence_ref/failure_code/human_intervention_required/state_transition_history` 的回溯规则。
  - 优先级统一为：`task_record -> latest_status -> last_task`，并补齐 `state_transition_history` 的 list 回退链（`state_transition_history` -> `state_transitions` -> `last_task/latest`）以保证 task_record 缺失时优先复用 last_task 历史。
- `src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway.py`
  - `_task_record_support_fields()` 改为复用同一 traceability 抽取语义，避免网关端状态与 diagnostics 对账字段漂移。
- `test_operator_gateway_diagnostics.py`
  - 新增 regression case 覆盖 task_record 为权威来源、task_record 不可读时回退到 last_task history 的行为。
- `src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py`
  - 小修复：当 `last_task` 不含 `evidence_ref` 且有 `result_path` 时，保留 `last_task.evidence_ref` 的兼容值回退为 `result_path`；保留有值时则与主 traceability 对齐。

### 4) 验证命令

- `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest src/ros2_trashbot_nav/test/test_fixed_route_dry_run_offline.py src/ros2_trashbot_nav/test/test_fixed_route_status_static.py`
  - `Ran 13 tests in 0.032s`
  - `OK`
- `PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile src/ros2_trashbot_nav/ros2_trashbot_nav/fixed_route_autonomy.py src/ros2_trashbot_nav/ros2_trashbot_nav/route_utils.py`
  - pass
- `PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile scripts/evidence_crosscheck.py`
  - pass
- `PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile src/ros2_trashbot_behavior/ros2_trashbot_behavior/task_orchestrator.py src/ros2_trashbot_behavior/ros2_trashbot_behavior/task_record.py src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway.py src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py`
  - pass
- `python3 scripts/evidence_crosscheck.py /tmp/rober_evidence_crosscheck/route_status.json --task-record /tmp/rober_evidence_crosscheck/task_record.json --evidence-ref /tmp/rober_evidence_crosscheck/route_evidence.ref.json`
  - `mismatches=0`
- `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest src/ros2_trashbot_behavior/test/test_task_orchestrator_collection_execution.py src/ros2_trashbot_behavior/test/test_task_record.py src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`
  - `Ran 39 tests in 0.014s`
  - `OK`

## 验收命令结果（本轮）

- `python3 scripts/hardware_smoke_wave_rover.py --help`
  - 通过（退出码 `0`，help 内容输出）
- `python3 scripts/hardware_smoke_wave_rover.py --status`
  - 通过（退出码 `0`，包含 startup 命令与参数默认值）
- `python3 scripts/hardware_smoke_wave_rover.py --move-test --test-speed 0.05 --test-duration-s 0.3 --serial-port /dev/ttyUSB0 --baudrate 115200 --evidence-ref run_20260511T094018Z_hil_pass_speed0p050_dur0p30`
  - 失败（退出码 `1`，`FileNotFoundError: /dev/ttyUSB0`）
- `PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile scripts/hardware_smoke_wave_rover.py`
  - 通过（退出码 `0`）
