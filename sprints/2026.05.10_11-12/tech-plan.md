# Sprint 2026.05.10 11-12 Tech Plan

## 技术方案

- 扩展 `NavigationResult`，让 fixed-route 轮询结果携带 `evidence`。
- 从 fixed-route status JSON 中白名单提取复盘字段：`route_contract_version`、`state`、`mode`、`route_file`、`current_index`、`current_target`、`total`、`visual_gate_status`、`visual_gate_detail`、`keyframe_preflight`、`last_nav_result`、`updated_at` 等。
- 保持原有终态判断：`completed/success/succeeded` 仍映射为 `fixed_route_completed`，`failed/error` 仍映射为 `fixed_route_failed`。
- 通过现有 `write_task_record()` 的 `nav_results` 序列化路径自然落盘，不新增任务记录格式分叉。

## 文件范围

- `src/ros2_trashbot_behavior/ros2_trashbot_behavior/task_orchestrator.py`
- `src/ros2_trashbot_behavior/test/test_task_orchestrator_fixed_route_status.py`
- `src/ros2_trashbot_behavior/test/test_task_orchestrator_collection_execution.py`

## 验收命令

- `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest src/ros2_trashbot_behavior/test/test_task_orchestrator_fixed_route_status.py src/ros2_trashbot_behavior/test/test_task_orchestrator_collection_execution.py`
- `python3 -m py_compile src/ros2_trashbot_behavior/ros2_trashbot_behavior/task_orchestrator.py src/ros2_trashbot_behavior/test/test_task_orchestrator_fixed_route_status.py src/ros2_trashbot_behavior/test/test_task_orchestrator_collection_execution.py`
- `PYTHONDONTWRITEBYTECODE=1 bash scripts/run_smoke_tests.sh`
- `git diff --check`
