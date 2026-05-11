# Sprint 2026.05.11 08-09 HIL pass and route replay - Tech Done

## 状态

- 阶段：tech-done in-progress
- 时间：2026-05-11 16:35 Asia/Shanghai
- Owner：`autonomy-engineer`
- 范围：O3 run-level 复现对齐与复盘证据收口

## 任务目标

- O3：将 fixed-route replay 与 task/task_record 的 `evidence_ref` 对齐，补齐可复盘的 run-level route replay 读数。
- 本轮为闭环最小化改动：不新增测试文件、不改行为状态机、不改硬件链路。

## 本轮实际执行

### 1) 固定路线复盘契约核验

- `src/ros2_trashbot_nav/ros2_trashbot_nav/fixed_route_autonomy.py`
  - route 状态主键已包含：`checkpoint`、`current_index`、`target`、`failure_code`、`evidence_ref`。
  - `software_proof` 输出中已带 `artifact_path` 与 `evidence_ref`，并按 JSONL 行写入 `route_progress` 的 replay 字段。
  - `route_progress` 与顶层状态字段的索引/目标一致性在 dry-run 与错误分支中均保持。

- `src/ros2_trashbot_nav/ros2_trashbot_nav/route_utils.py`
  - `build_route_checkpoint_payload()` 与 `build_route_replay_entry()` 已提供 run-level 对齐字段；`evidence_ref` 会透传到 replay 行。

### 2) 证据可复用/复盘脚本化描述

- `docs/navigation/fixed_route_workflow.md`
  - 补充并保留同一 `evidence_ref` 的 route replay 可复盘命令输出说明。
  - 复盘检查点明确为：
    - `route_progress.checkpoint == payload.current_index == payload.checkpoint`
    - `route_progress.target == payload.target`
    - `route_progress.current_index == payload.current_index`
    - `route_progress.failure_code == payload.failure_code`
    - `route_progress.evidence_ref == payload.evidence_ref`

### 3) 回归验证

- 命令 1（静态复测 + dry-run）：
  - `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest src/ros2_trashbot_nav/test/test_fixed_route_dry_run_offline.py src/ros2_trashbot_nav/test/test_fixed_route_status_static.py`
  - 输出：`Ran 13 tests in 0.020s` `OK`

- 命令 2（语法编译）：
  - `PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile src/ros2_trashbot_nav/ros2_trashbot_nav/fixed_route_autonomy.py src/ros2_trashbot_nav/ros2_trashbot_nav/route_utils.py`
  - 输出：exit code 0

## 结果判定

- O3 软件层：`route_progress` 与 `route replay` 字段已对齐，可用于同一 `evidence_ref` 的复盘消费。
- O3 run-level 真机复盘：未在本轮产生；受限于当前运行环境。

## 下轮建议

- 在有串口/上机环境时，用同一 `evidence_ref` 发起 `fixed_route_autonomy` fixed-route run 和行为 task run，验证 task_record 与 route replay 在单 run 内联动。
- 建议把 `route_progress` 与 task_record 的 `current_index/target/failure_code` 做一条端到端自动脚本核对。
