# Sprint 2026.05.10 11-12 Tech Done

## 实际改动

- Robot Platform Engineer 扩展 `NavigationResult`，新增 `evidence` 字段。
- `task_orchestrator._navigate_fixed_route_status()` 现在会从 fixed-route status JSON 提取结构化证据，并保留到 `nav_results`，最终进入 `TrashCollection` task record。
- 证据字段覆盖 fixed-route contract、route file、keyframe dir、checkpoint/index、visual gate、preflight、failure reason、last nav result 和更新时间。
- 新增回归测试覆盖 fixed-route status evidence 和 `TrashCollection` fixed-route 成功 task record 证据。
- 测试 fixture 已对齐导航契约 `fixed_route.v1`。
- Autonomy Algorithm Engineer 只读确认 fixed-route status contract，建议优先保留 `state`、`route_contract_version`、`current_index`、`visual_gate_status`、`last_nav_result` 等字段。
- `OKR.md` 更新当前快照和第 21 轮进度，Objective 2 从约 69% 推进到约 72%，Objective 5 从约 68% 推进到约 69%。

## 验证结果

- `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest src/ros2_trashbot_behavior/test/test_task_orchestrator_fixed_route_status.py src/ros2_trashbot_behavior/test/test_task_orchestrator_collection_execution.py` 通过，9 tests OK。
- `python3 -m py_compile src/ros2_trashbot_behavior/ros2_trashbot_behavior/task_orchestrator.py src/ros2_trashbot_behavior/test/test_task_orchestrator_fixed_route_status.py src/ros2_trashbot_behavior/test/test_task_orchestrator_collection_execution.py` 通过。
- `PYTHONDONTWRITEBYTECODE=1 bash scripts/run_smoke_tests.sh` 通过，覆盖 interfaces 6、hardware 14、nav 27、bringup 9、behavior 107、vision 8。
- `git diff --check` 通过。

## 偏差与风险

- 本轮是行为层 fixed-route status 消费与记录证明，不替代真实 fixed-route/Nav2 行驶。
- Docker/Humble colcon build 未在本轮重跑；当前环境历史上持续受 WSL Docker integration 缺失影响。
- WAVE ROVER HIL、真实手机浏览器、真实 speaker/TTS 仍未完成。
- `AGENTS.md` 存在 unrelated 修改，本轮未纳入提交。
