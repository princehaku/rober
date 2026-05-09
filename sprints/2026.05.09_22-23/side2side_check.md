# Sprint 2026.05.09_22-23 Side To Side Check

## 文档阶段门禁

- 前置文档：`tech-done.md`。
- 前置 gate：实际改动、验证输出、失败定位和剩余风险已记录。
- 当前阶段：SIDE TO SIDE CHECK。
- 本阶段完成条件：完成 PRD vs 实现、OKR/KR、接口、文档、测试和 P0 风险对照。
- 下一文档：只有本阶段 P0 全部 closed 后，才允许创建或生效 `final.md`。

## PRD vs 实现

| PRD 项 | 实现状态 | 证据 | 结论 |
| --- | --- | --- | --- |
| fixed route delivery dry-run 结果路径验收 | implemented | `_navigate_fixed_route_status` completed/error/timeout/cancel tests；`_execute_collection` fixed-route timeout test | software closed |
| action result 覆盖 success、failure、timeout、cancel | implemented for software paths | dry-run success、fixed-route timeout、状态机 failure/cancel/dropoff tests | software closed |
| task record 写入机器可判定终态 | implemented | `error_code`、`final_state`、`nav_results`、`dropoff_result` tests | closed |
| Docker Humble build P0 | blocked | `ROBOT_DAILY_DOCKER_BUILD=1 bash scripts/run_smoke_tests.sh` exit 1: `docker` not found | blocked |
| HIL 准入，不声明实机通过 | documented | `docs/vendor/VENDOR_INDEX.md` 已复核；`docs/acceptance/wave_rover_hil_evidence.md` 作为准入清单 | deferred |

## OKR/KR 对照

| OKR | 本轮检查点 | 状态 |
| --- | --- | --- |
| Objective 1 | HIL 只做准入；不把静态测试写成硬件通过 | deferred to real robot |
| Objective 2 | 送垃圾 action result 和 task record 可判定 | software closed |
| Objective 3 | fixed route status/dry-run 作为主路径证据 | software closed |
| Objective 4 | 视觉不作为送达成功前提 | unchanged |
| Objective 5 | 手机/远程可读 `final_state`、`error_code`、`error_message`、`task_record_path` | closed |

## 接口与记录契约

| 契约 | Producer | Consumer | 状态 |
| --- | --- | --- | --- |
| `TrashCollection.Result.error_code` | behavior | 手机/远程/测试 | success 为空；failed/canceled/timeout 为机器码 |
| `TrashCollection.Result.final_state` | behavior | 手机/远程/测试 | 使用状态机最终状态 |
| `TrashCollection.Result.task_record_path` | behavior | debug/远程诊断/维护者 | 指向 JSON 任务记录 |
| task record `error_code`/`final_state` | behavior | debug/远程诊断/维护者 | 已持久化 |
| fixed route status JSON | nav | behavior | 支持 completed/error/timeout/cancel 结果路径 |

## 验证证据

| 命令 | 状态 | 摘要 |
| --- | --- | --- |
| `python3 -m unittest discover -s src/ros2_trashbot_behavior/test -p "test*.py"` | passed | 88 tests OK |
| `python3 -m unittest discover -s src/ros2_trashbot_nav/test -p "test*.py"` | passed | 18 tests OK |
| `bash -n scripts/run_smoke_tests.sh && bash -n scripts/docker_humble_build.sh` | passed | shell syntax OK |
| `bash scripts/run_smoke_tests.sh` | passed | interfaces skipped；13 + 18 + 7 + 88 + 1 tests OK |
| `ROBOT_DAILY_DOCKER_BUILD=1 bash scripts/run_smoke_tests.sh` | blocked | local smoke passed；Docker gate failed because current WSL 2 distro cannot find `docker` |

## 硬件事实与 HIL 边界

已采用硬件事实入口：

- `docs/vendor/VENDOR_INDEX.md`

本轮不新增串口设备名、波特率、速度映射、反馈字段、引脚、电压或机械尺寸结论。

HIL 本轮状态：

- 准入清单存在：`docs/acceptance/wave_rover_hil_evidence.md`。
- 实机未跑：串口、停止命令、`T=1001` 反馈、低速前进/后退/转向、急停均未填真实证据。
- 结论：HIL real-robot validation deferred，不作为本轮 closed 项。

## P0 清零表

| P0 | Owner | Gate | 状态 |
| --- | --- | --- | --- |
| action result 不能机器判定 success/failure/timeout/cancel | `robot-software-engineer` | 行为测试 + action execution 轻量测试 | closed |
| fixed route delivery 没有离线结果路径证据 | `autonomy-engineer` | fixed-route status reader + nav dry-run tests | closed |
| task record 不记录终态诊断 | `robot-software-engineer` | JSON record 字段测试 | closed |
| Docker Humble build 不能证明接口/action/msg 生成 | `robot-software-engineer` | Docker build 通过 | blocked: `docker` command not found |
| HIL 准入资料不完整却宣称硬件完成 | `hardware-engineer` | 准入清单 ready，实机 deferred | closed for documentation boundary only |
| P0 未清零就 final | `product-okr-owner` | 本表全部 closed | open because Docker P0 blocked |

## 本阶段结论

软件验收 P0 已关闭；Docker Humble build P0 阻塞，原因是当前 WSL 2 distro 找不到 `docker` 命令。因此本轮不能创建有效 `final.md` 收口。下一步必须启用 Docker Desktop WSL integration 或提供可用 Docker/Humble 环境后重跑 Docker gate。
