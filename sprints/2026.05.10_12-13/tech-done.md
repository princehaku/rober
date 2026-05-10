# Sprint 2026.05.10 12-13 Tech Done

## 实际改动

- Robot Platform Engineer 将 `legacy_trash_collection_server` 从 sleep-demo action server 改为 quarantine 兼容入口。
- `trash_collection_server.py` 收到 `/trashbot/collect_trash` goal 后发布一次失败反馈，调用 `goal_handle.abort()`，并返回：
  - `success=false`
  - `error_code=legacy_server_quarantined`
  - `error_message` 指向使用 `task_orchestrator`
  - `final_state=error`
- 移除了旧 demo pipeline：`_navigate_to_trash()`、`_collect_trash()`、`_deliver_to_bin()`、`_sleep()`。
- 保留 `setup.py` 中 `legacy_trash_collection_server = ros2_trashbot_behavior.trash_collection_server:main`，避免兼容入口消失。
- 新增静态测试覆盖 legacy quarantine、无 `asyncio.sleep`、无 `goal_handle.succeed()`、无 `result.success = True`，并验证 `setup.py` / `docs/interfaces/ros_contracts.md` 仍声明 `task_orchestrator` 是默认 product entry point。
- 更新 `docs/interfaces/ros_contracts.md`，明确 legacy server 只为兼容保留，调用会以 `legacy_server_quarantined` abort。
- 更新 `OKR.md` 当前快照和第 22 轮进度：Objective 2 从约 72% 推进到约 74%。

## 验证结果

- `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest src/ros2_trashbot_behavior/test/test_legacy_trash_collection_server_static.py src/ros2_trashbot_behavior/test/test_behavior_package_contract_static.py` 通过，5 tests OK。
- `python3 -m py_compile src/ros2_trashbot_behavior/ros2_trashbot_behavior/trash_collection_server.py src/ros2_trashbot_behavior/test/test_legacy_trash_collection_server_static.py` 通过。
- `PYTHONDONTWRITEBYTECODE=1 bash scripts/run_smoke_tests.sh` 通过，覆盖 interfaces 6、hardware 14、nav 27、bringup 9、behavior 110、vision 8。
- `git diff --check` 通过，退出码 0。
- `bash scripts/docker_humble_build.sh` 已尝试，但当前 WSL 2 distro 没有 `docker` 命令，输出提示需要开启 Docker Desktop WSL integration；未完成 Docker/Humble colcon build。

## 偏差与风险

- 本轮没有修改 `task_orchestrator` 主路径，也没有新增 action/msg contract。
- 本轮不涉及硬件、vendor 文件、串口、波特率、底盘协议或电气假设。
- 没有真实 ROS2/Humble action runtime、fixed-route/Nav2 行驶、真实 SLAM/Nav2 学习到巡逻 E2E 或 WAVE ROVER HIL。
- `AGENTS.md` 是既有 unrelated 修改，本轮保持未改、未提交。
