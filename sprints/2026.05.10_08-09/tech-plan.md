# Sprint 2026.05.10 08-09 Tech Plan

## 文件范围

- `src/ros2_trashbot_behavior/ros2_trashbot_behavior/task_orchestrator.py`
- `src/ros2_trashbot_behavior/test/test_task_orchestrator_patrol_execution.py`
- `OKR.md`
- `sprints/2026.05.10_08-09/tech-done.md`
- `sprints/2026.05.10_08-09/final.md`

## 技术方案

1. 在 patrol action 中移除 `use_saved_map=false` 的 fake learning drive。
2. 新增内部 helper，统一加载 patrol waypoint，并在 learning proof 模式下要求 `waypoints` 非空。
3. learning proof 缺失时 action abort，状态进入 `ERROR`，不递增 `learn_count`。
4. learning proof 存在时，递增 `learn_count` 并继续走已有 waypoint 导航路径。
5. 增加回归测试覆盖 proof 缺失和 proof 存在两个分支，并加入静态断言避免 fake learning 文案回流。

## 验收命令

- `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest src/ros2_trashbot_behavior/test/test_task_orchestrator_patrol_execution.py`
- `PYTHONDONTWRITEBYTECODE=1 bash scripts/run_smoke_tests.sh`
- `git diff --check`

## 风险边界

- 不修改硬件协议、UART、WAVE ROVER 参数，不需要 vendor 二次确认。
- 不修改 `Patrol.action` 字段，避免扩大接口变更。
- 不把本轮纯软件 proof-gate 表述为真实 SLAM 或 Nav2 已验证。
