# Sprint 2026.05.10 08-09 Tech Done

## 实际改动

- `task_orchestrator._execute_patrol()` 移除 `use_saved_map=false` 的 fake learning drive 口径。
- patrol 学习阶段现在必须先从 `waypoint_file` 读取到非空 `waypoints`，才会递增 `learn_count` 并继续进入巡逻导航。
- 缺少、不可解析或空 waypoint proof 时，patrol action 会 `abort()`，状态进入 `ERROR`，不再继续访问旧的模拟成功路径。
- `test_task_orchestrator_patrol_execution.py` 新增无 waypoint proof abort、有 waypoint proof 继续巡逻、fake learning 文案不回流的回归测试。
- `OKR.md` 更新当前快照，Objective 2 从约 66% 推进到约 69%。

## 验证结果

- `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest src/ros2_trashbot_behavior/test/test_task_orchestrator_patrol_execution.py` 先红后绿，最终 4 tests OK。
- `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest src/ros2_trashbot_behavior/test/test_task_orchestrator_patrol_execution.py src/ros2_trashbot_behavior/test/test_patrol_action_contract_static.py` 通过，9 tests OK。
- `python3 -m py_compile src/ros2_trashbot_behavior/ros2_trashbot_behavior/task_orchestrator.py src/ros2_trashbot_behavior/test/test_task_orchestrator_patrol_execution.py` 通过。
- `PYTHONDONTWRITEBYTECODE=1 bash scripts/run_smoke_tests.sh` 通过，覆盖 interfaces 6、hardware 14、nav 26、bringup 9、behavior 104、vision 8。
- `git diff --check` 通过。
- `bash scripts/docker_humble_build.sh` 已尝试，但当前 WSL 2 distro 未启用 Docker Desktop integration，`docker` 命令不可用，无法完成 Docker/Humble colcon build。

## 偏差与风险

- 本轮不修改硬件协议、串口、波特率或电气假设，不需要 vendor 二次确认。
- `Patrol.action` 当前没有 error code/message 字段，proof gate 失败原因主要通过日志、abort 和 `map_save_path` 定位。
- 当前 proof 是 waypoint 文件可读且非空，不等同于真实 SLAM/Nav2 学习已经在本机完成；真实 E2E 仍需 Docker/Humble 和机器人现场验证。
