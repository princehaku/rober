# Sprint 2026.05.10 12-13 Tech Plan

## 文件范围

- `src/ros2_trashbot_behavior/ros2_trashbot_behavior/trash_collection_server.py`
- `src/ros2_trashbot_behavior/test/`
- `docs/interfaces/ros_contracts.md`
- `OKR.md`
- `sprints/2026.05.10_12-13/`

## 实现计划

1. 将 legacy action server 改为 quarantine 入口：收到目标后发布一次失败反馈，调用 `goal_handle.abort()`，返回 `TrashCollection.Result`，其中 `success=false`、`error_code=legacy_server_quarantined`、`final_state=error`，并提示使用 `task_orchestrator`。
2. 移除 `_navigate_to_trash()`、`_collect_trash()`、`_deliver_to_bin()`、`_sleep()` 等 demo pipeline，避免静态上继续出现 sleep 成功链路。
3. 保留 `legacy_trash_collection_server = ros2_trashbot_behavior.trash_collection_server:main`，避免兼容入口消失。
4. 增加静态测试覆盖：
   - legacy 文件不再包含 sleep-demo pipeline、`asyncio.sleep` 或 `goal_handle.succeed()`。
   - legacy quarantine result/error code/message 存在。
   - `setup.py` 和 `docs/interfaces/ros_contracts.md` 仍声明默认入口是 `task_orchestrator`，legacy 只作为 legacy。
5. 更新 OKR 当前快照和本轮进度，Objective 2 只做 modest 提升，不声称真实 Nav2/HIL 完成。

## 验证命令

- `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest src/ros2_trashbot_behavior/test/test_legacy_trash_collection_server_static.py src/ros2_trashbot_behavior/test/test_behavior_package_contract_static.py`
- `python3 -m py_compile src/ros2_trashbot_behavior/ros2_trashbot_behavior/trash_collection_server.py src/ros2_trashbot_behavior/test/test_legacy_trash_collection_server_static.py`
- `PYTHONDONTWRITEBYTECODE=1 bash scripts/run_smoke_tests.sh`
- `git diff --check`

## 风险边界

- 不改 action/msg contract。
- 不改 `task_orchestrator` 主路径。
- 不改硬件/vendor 文件。
- 不提交，由 coordinator review 后提交。
