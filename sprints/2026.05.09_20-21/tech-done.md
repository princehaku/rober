# Sprint 2026.05.09_20-21 Tech Done

## 文档阶段门禁

- 前置文档：`tech-plan.md`。
- 前置 gate：模块方案、P7 DEV handoff、验证计划、风险边界已明确。
- 当前阶段：DEV DONE。
- 本阶段完成条件：记录 DEV completion、实际改动、验证输出、失败定位和剩余风险。
- 下一文档：只有本阶段完成后，才允许创建或生效 `side2side_check.md`。
- 如果本文件早于 tech-plan gate 被预创建，则在 gate 完成前只能视为 invalid draft。

## 当前状态

本文件用于记录本轮实际执行结果。启动阶段已完成 sprint 留档骨架；本轮 P7 已进入接口/行为可判定终态实现。仓库在本轮开始前已经存在 delivery state machine、delivery navigation、task record、fixed-route dry-run 与相关测试，因此状态记录拆成“既有实现已存在”和“本轮验收/补强仍在进行”，不把既有代码误写成尚未实现。

## 实际改动

| 时间 | Owner | 改动 | 路径 | 需求映射 | 证据 |
| --- | --- | --- | --- | --- | --- |
| 2026-05-09 20:32 | `p8-project-lead` | 建立本轮 sprint 留档 | `sprints/2026.05.09_20-21/` | 迭代强制留档 | `bash scripts/run_smoke_tests.sh` passed |
| 2026-05-09 20:32 | `p7-tech-test-engineer` | 修复 bash 验证脚本 CRLF 行尾，未改脚本逻辑 | `scripts/run_smoke_tests.sh`, `scripts/docker_humble_build.sh` | 验证优先 | `file` 显示二者已是 shell script，无 CRLF |
| 2026-05-09 20:50 | `p7-tech-implementation-worker` | 将 delivery timeout 作为一等状态机事件，不再混入普通 navigation_failed | `delivery_state_machine.py`, `task_orchestrator.py` | A2 成功/失败/取消/超时明确 | red-green 单测通过 |
| 2026-05-09 20:55 | `p7-tech-implementation-worker` | 为 `TrashCollection.Result` 增加 `error_code`、`final_state`，并透传到 operator gateway / remote bridge | `TrashCollection.action`, `task_orchestrator.py`, `operator_gateway.py`, `remote_bridge.py` | A2/A4 机器可判定终态 | contract/static tests passed |
| 2026-05-09 21:00 | `p7-tech-docs-acceptance` | 修正 README 与硬件 docs 的 vendor/HIL 边界，避免编码器/超声波/蜂鸣器/看门狗无证据声明 | `README.md`, `docs/hardware/wave_rover_json_bridge.md`, `docs/interfaces/ros_contracts.md` | 硬件事实可追溯 | 待 smoke |

## 验证记录

| 命令 | Owner | 结果 | 摘要 | 后续 |
| --- | --- | --- | --- | --- |
| `git status --short` | `p7-tech-test-engineer` | done | baseline: `M AGENTS.md`, `?? sprints/`; 修复后新增 `M scripts/docker_humble_build.sh`, `M scripts/run_smoke_tests.sh` | `AGENTS.md` 为既有未提交改动，不回滚 |
| `bash scripts/run_smoke_tests.sh` | `p7-tech-test-engineer` | passed | 首轮因 CRLF 行尾失败；修复 LF 后通过。P7 实现前基线为 13 + 18 + 7 + 74 + 1 tests OK；P7 timeout 实现后为 13 + 18 + 7 + 76 + 1 tests OK；interfaces 无 Python test 目录被跳过 | 文档/接口补强后需最终重跑 |
| `docker --version` | `p7-tech-test-engineer` | blocked | 当前 WSL 2 distro 找不到 `docker` 命令，提示需开启 Docker Desktop WSL integration | Docker Humble build 暂不能本地执行 |
| `ROBOT_DAILY_DOCKER_BUILD=1 bash scripts/run_smoke_tests.sh` | `p7-tech-test-engineer` | blocked | Docker 不可用，未运行 | 开启 Docker Desktop WSL integration 后执行 |
| Docker Humble `colcon build --symlink-install` | `p8-bringup-integration-lead` | blocked | Docker 不可用 | 可用时执行 |
| WAVE ROVER HIL | `p8-hardware-lead` | pending | 需要实机 | 不作为本地静态完成结论 |

## 失败定位与二次验证

已记录：

- `bash scripts/run_smoke_tests.sh` 首轮失败：`scripts/run_smoke_tests.sh: line 3: set: pipefail\r: invalid option name`。
- 根因：`scripts/run_smoke_tests.sh` 和 `scripts/docker_humble_build.sh` 为 CRLF 行尾，bash 将回车读入 `pipefail` 参数。
- 修复：机械转换为 LF 行尾，未改变脚本逻辑。
- 重跑：`bash scripts/run_smoke_tests.sh` exit 0。
- Docker 检查：`docker --version` exit 1，当前 WSL 2 distro 未安装/未集成 Docker。

本轮后续任何测试失败必须记录：

- 首次失败命令。
- 关键错误。
- 根因判断。
- 修复路径。
- 重跑命令与结果。

## 未完成项

- P0-1：行为层送垃圾状态机既有实现存在；本轮已补 timeout 一等事件和 action terminal diagnostics，仍需更深 action execution result tests。
- P0-2：route/waypoint delivery 输入和 fixed-route dry-run 既有实现存在；仍需行为级结果路径测试和 Docker/ROS2 build。
- P0-3：硬件桥 vendor 事实源已部分审查；HIL 待验证项仍 open。
- P0-4：side2side P0 清零。
