# Sprint 2026.05.09_22-23 Tech Plan

## 文档阶段门禁

- 前置文档：`prd.md`。
- 前置 gate：PRD 已明确 fixed route 主路径、Docker P0、HIL 准入、消费者终态字段和范围边界。
- 当前阶段：TECH PLAN。
- 本阶段完成条件：Engineer 执行范围、验证命令、风险边界明确。
- 下一文档：只有本阶段完成并进入 DEV/TEST 后，才允许创建或生效 `tech-done.md`。

## 总体技术方案

用最小补强关闭软件证据缺口：

1. 保持 `TrashCollection.Result` 现有 `error_code`、`error_message`、`final_state`、`task_record_path` 契约。
2. 将 task record 持久化补齐到同一终态契约，方便手机/远程和维护者复盘。
3. 用 fixed route status reader 的 completed/failed/timeout 结果驱动行为层结果测试。
4. 跑本地 smoke、行为/导航定向测试、Docker Humble build gate。
5. HIL 只检查准入清单与 vendor 来源，不写实机通过。

## Engineer 执行拆分

| 模块 | Owner | 执行范围 |
| --- | --- | --- |
| 行为层 | `robot-software-engineer` | 补 task record 终态字段和 action result 静态/离线测试 |
| 导航/fixed route | `autonomy-engineer` | 验证 status reader 识别 completed、failed、timeout |
| 接口契约 | `robot-software-engineer` | 确认 `TrashCollection.action` result/feedback 字段仍兼容 |
| Bringup | `robot-software-engineer` | 运行 Docker Humble build；失败则记录 P0 blocked 根因 |
| 硬件准入 | `hardware-engineer` | 复核 `docs/vendor/VENDOR_INDEX.md` 和 HIL checklist，实机验证 deferred |
| 手机/远程消费者 | `full-stack-software-engineer` | 确认终态字段可被手机/远程消费 |
| 阶段收口 | `product-okr-owner` | 对照 OKR/KR、P0 状态和剩余风险 |

## 具体改动

- `src/ros2_trashbot_behavior/ros2_trashbot_behavior/task_record.py`
  - 增加可选 `error_code`、`final_state` 字段。
  - 默认值从 `machine.events[-1].event.value` 和 `machine.state.value` 推导，保持旧调用兼容。
- `src/ros2_trashbot_behavior/ros2_trashbot_behavior/task_orchestrator.py`
  - 写 collection record 时传入 action result 对应的 `error_code` 和 `final_state`。
- `src/ros2_trashbot_behavior/test/test_task_record.py`
  - 验证 success/failure 记录包含终态字段、导航结果和 fixed route 配置。
- `src/ros2_trashbot_behavior/test/test_task_orchestrator_static.py`
  - 验证 collection record 写入终态字段。

## 验证命令

| 层级 | 命令 | 预期 |
| --- | --- | --- |
| 行为定向 | `python3 -m unittest discover -s src/ros2_trashbot_behavior/test -p "test*.py"` | 行为测试通过 |
| 导航定向 | `python3 -m unittest discover -s src/ros2_trashbot_nav/test -p "test*.py"` | fixed route 测试通过 |
| 本地 smoke | `bash scripts/run_smoke_tests.sh` | 本地 compileall + package unittest 通过，interfaces 可被记录为 skipped |
| Docker gate | `ROBOT_DAILY_DOCKER_BUILD=1 bash scripts/run_smoke_tests.sh` | Docker Humble build 通过；若 Docker 不可用则 P0 blocked |
| 直接 Docker | `bash scripts/docker_humble_build.sh` | 等价 Docker Humble build 证据 |

## 风险边界

- 本地测试不等于 ROS2 Humble 构建。
- Docker build 不等于实机 HIL。
- HIL 准入清单 ready 不等于串口、低速方向、反馈流已验证。
- `AGENTS.md` 和 `.codex/agents/turnover_2026.05.09_22-23_325.md` 当前已有未提交改动，本轮不得回滚或覆盖。

## 本文件 Gate

- Engineer 实现范围、文件、验证命令和风险边界已明确。
- 允许进入 DEV/TEST，并在实际执行后创建 `tech-done.md`。
