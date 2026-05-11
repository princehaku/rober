# Sprint 2026.05.11 09-10 HIL pass and route replay crosscheck - Tech Done

## 状态

- 阶段：tech-done in-progress
- 时间：2026-05-11 16:47 Asia/Shanghai
- Owner：`autonomy-engineer`
- 范围：O3 fixed-route run-level 复核对齐与跨层核对辅助工具

## 任务目标

- 以同一 `evidence_ref` 为主线补齐 fixed-route run-level 复盘闭环。
- 让 `route_progress` 与 route replay、task_record/diagnostics 可对齐核验。
- 缺 run-level 样本时给出可复验的只读对账脚本与重试路径。

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

### 4) 验证命令

- `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest src/ros2_trashbot_nav/test/test_fixed_route_dry_run_offline.py src/ros2_trashbot_nav/test/test_fixed_route_status_static.py`
  - `Ran 13 tests in 0.032s`
  - `OK`
- `PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile src/ros2_trashbot_nav/ros2_trashbot_nav/fixed_route_autonomy.py src/ros2_trashbot_nav/ros2_trashbot_nav/route_utils.py`
  - pass
- `PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile scripts/evidence_crosscheck.py`
  - pass
- `python3 scripts/evidence_crosscheck.py /tmp/rober_evidence_crosscheck/route_status.json --task-record /tmp/rober_evidence_crosscheck/task_record.json --evidence-ref /tmp/rober_evidence_crosscheck/route_evidence.ref.json`
  - `mismatches=0`
