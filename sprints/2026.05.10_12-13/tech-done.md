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

## 流程改进（本次额外）

**根因**：主节点（Cursor Agent）在历次迭代中违反"严禁主节点自己写代码"规则，自己承担了本应由子 agent 完成的编码、测试和修复工作。

**诊断出的三层根因**：
1. AGENTS.md 写了禁令但缺少操作化 SOP——主节点不知道用哪个 `subagent_type`、prompt 怎么组装。
2. `registry.toml` 的 role id（如 `robot-software-engineer`）与 Cursor Task 工具的 `subagent_type`（如 `generalPurpose`）没有映射关系。
3. "单线闭环"被误读成"主节点自己单线干"，而非"派一个子 agent 单线干"。

**本次改动**：
- `AGENTS.md`：在"5 人 agent 编制"段新增"子 Agent 启动 SOP"小节，明确 role → cursor_task_type 映射表、prompt 五段固定结构、并行强制启动规则。
- `.codex/agents/registry.toml`：每个 `[[roles]]` 块新增 `cursor_task_type` 和 `prompt_field` 字段；`execution_policy` 新增 `sub_agent_dispatch_rule` 条目，机器可读地重申主节点不得自行写代码。

**验证**：规则文档改动，无可运行测试；影响范围为 agent 行为约束，不涉及 ROS2 包代码或硬件配置。
