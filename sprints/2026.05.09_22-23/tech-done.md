# Sprint 2026.05.09_22-23 Tech Done

## 文档阶段门禁

- 前置文档：`tech-plan.md`。
- 前置 gate：Engineer 执行范围、验证命令和风险边界已明确。
- 当前阶段：DEV/TEST DONE。
- 本阶段完成条件：记录实际改动、验证输出、失败定位和剩余风险。
- 下一文档：只有本阶段完成后，才允许创建或生效 `side2side_check.md`。

## 实际改动

| Owner | 改动 | 路径 | 需求映射 |
| --- | --- | --- | --- |
| `robot-software-engineer` | task record 增加 `error_code`、`final_state` 持久化字段，默认从状态机推导 | `src/ros2_trashbot_behavior/ros2_trashbot_behavior/task_record.py` | 手机/远程和维护者可判定终态 |
| `robot-software-engineer` | collection record 写入与 action result 一致的终态诊断；success 保持空 `error_code` | `src/ros2_trashbot_behavior/ros2_trashbot_behavior/task_orchestrator.py` | action result 与 task record 一致 |
| `robot-software-engineer` | 补 task record success/failure 终态字段测试 | `src/ros2_trashbot_behavior/test/test_task_record.py` | A1/A2 |
| `autonomy-engineer` | 补 fixed-route status reader completed/error/timeout/cancel 轻量执行测试 | `src/ros2_trashbot_behavior/test/test_task_orchestrator_fixed_route_status.py` | A1/A3 |
| `robot-software-engineer` | 补 `_execute_collection` dry-run success 与 fixed-route timeout action result/task record 轻量执行测试 | `src/ros2_trashbot_behavior/test/test_task_orchestrator_collection_execution.py` | A1/A2/A3 |
| `robot-software-engineer` | 补 dropoff cancel 结果测试 | `src/ros2_trashbot_behavior/test/test_dropoff_confirmation.py` | A1 |
| `robot-software-engineer` | 补 collection record 写入终态字段静态测试 | `src/ros2_trashbot_behavior/test/test_task_orchestrator_static.py` | A2 |

## 验证记录

| 命令 | 结果 | 摘要 |
| --- | --- | --- |
| `python3 -m unittest discover -s src/ros2_trashbot_behavior/test -p "test*.py"` | first run failed | 81 tests run，1 failure：success 记录的 `error_code` 断言错误 |
| `python3 -m unittest discover -s src/ros2_trashbot_behavior/test -p "test*.py"` | passed | 88 tests OK |
| `python3 -m unittest discover -s src/ros2_trashbot_nav/test -p "test*.py"` | passed | 18 tests OK |
| `bash -n scripts/run_smoke_tests.sh && bash -n scripts/docker_humble_build.sh` | passed | shell syntax OK |
| `bash scripts/run_smoke_tests.sh` | passed | interfaces skipped；13 + 18 + 7 + 88 + 1 tests OK |
| `ROBOT_DAILY_DOCKER_BUILD=1 bash scripts/run_smoke_tests.sh` | blocked | local smoke passed；Docker gate failed because `docker` command not found in current WSL 2 distro |

## 失败定位

- 首次失败：`test_write_task_record_persists_state_transitions` 断言 success record 的 `error_code` 为 `return_succeeded`。
- 根因：成功 action result 的 `error_code` 应为空字符串，task record 也应保持一致；不能把成功终态事件写成错误码。
- 修复：`write_task_record()` 将 `error_code=None` 作为自动推导，显式空字符串作为成功无错误码保留；orchestrator 在 `final_status == "success"` 时传空错误码。
- 重跑：行为包 88 tests OK。

## 当前剩余验证

- 本地全局 smoke 已通过：`bash scripts/run_smoke_tests.sh`。
- Docker Humble build P0 blocked：当前 WSL 2 distro 找不到 `docker` 命令。
- HIL 本轮只做准入，不做实机通过声明。

## 本文件 Gate

- DEV/TEST 实际改动和初次失败已记录。
- 行为/导航定向测试和本地 smoke 已通过。
- Docker P0 blocked，允许进入 `side2side_check.md` 记录阻塞，但不允许有效 final 收口。
