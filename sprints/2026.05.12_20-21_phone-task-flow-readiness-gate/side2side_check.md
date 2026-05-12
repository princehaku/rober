# Sprint 2026.05.12_20-21 Phone Task Flow Readiness Gate - Side2Side Check

## 状态

- 阶段：side2side_check
- Product Owner：`product-okr-owner`
- 验收时间：2026-05-12 20:55 Asia/Shanghai
- 目标 Objective：Objective 5 手机体验与量产边界
- 目标 evidence boundary：`software_proof_docker_phone_task_flow_readiness_gate`

## 用户价值和产品北极星

北极星仍是普通用户只用手机，把垃圾交给小车，并能理解下一步、阻塞原因和人工接管路径。

本轮验收聚焦一个产品问题：本地/Docker 手机入口是否已经从“可安装壳层”推进到“普通用户任务流程 readiness gate”。验收结果是通过，但证据仅限 local/Docker software proof。

## OKR 映射

- O5 / KR7：首屏围绕连接/就绪、目的地、装载确认、发车、状态解释、求助/诊断组织，满足本轮 task-flow readiness gate。
- O5 / 普通用户入口：ACK 文案保持为 command accepted/processing evidence，不写成 delivery success。
- O6：只作为 `trashbot.remote.v1` command/status/ack envelope 兼容性围栏，本轮不提升。
- O1/O2/O3/O4：没有新增真实硬件、Nav2/fixed-route、感知实景或 HIL 证据，不提升。

## PRD / Tech Plan 对照检查

| 验收项 | 责任 Engineer | 结果 | 证据 |
| --- | --- | --- | --- |
| 新增 `trashbot.phone_task_flow_readiness.v1` 或等价 phone-safe metadata | `full-stack-software-engineer` | 通过 | `/api/status` 顶层、`phone_readiness.phone_task_flow_readiness` 和 `/api/diagnostics` 已暴露 task-flow metadata。 |
| 首屏覆盖连接/就绪、目的地、装载确认、发车、状态解释、求助/诊断 | `full-stack-software-engineer` | 通过 | Task A 记录首屏已围绕普通用户任务步骤组织，并同步 `docs/product/mobile_user_flow.md`。 |
| 用户可见 copy phone-safe，不暴露 raw ROS/topic/串口/JSON/token/硬件参数 | `full-stack-software-engineer` | 通过 | Task A 验证覆盖 operator gateway HTTP/static 路径；本轮产品验收未发现 PRD 禁止字段被新增为用户主流程。 |
| Start/Confirm/Cancel 继续受 action permissions 与 command safety gate 控制 | `full-stack-software-engineer` | 通过 | Task A 记录保留 `command_safety` gate；Diagnostics 可访问但不代表主任务 ready。 |
| ACK 不等于送达成功 | `full-stack-software-engineer`、`robot-software-engineer` | 通过 | Task A 首屏 copy 和 Task B compatibility fence 均确认 ACK 只代表 command accepted/processing evidence。 |
| 新 metadata 不改变 `trashbot.remote.v1` command/status/ack envelope | `robot-software-engineer` | 通过 | Task B 新增 `test_remote_bridge.py` 兼容性围栏，`remote_bridge.py` 未改生产行为。 |
| 新 metadata 不触发额外 robot action、不推进或持久化 cursor | `robot-software-engineer` | 通过 | Task B metadata-only response 围栏确认不触发 action、不 ACK、不推进 `last_ack_id`、不持久化 cursor。 |
| 文档同步更新 | `full-stack-software-engineer`、`product-okr-owner` | 通过 | `docs/product/mobile_user_flow.md` 已同步 task-flow readiness gate；本文件与 `final.md` 完成 Product acceptance 留档。 |

## 验收证据

Task A validation：

- `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest src/ros2_trashbot_behavior/test/test_operator_gateway_http.py src/ros2_trashbot_behavior/test/test_operator_gateway_static.py`
  - `Ran 46 tests in 20.115s`
  - `OK`
- `PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_http.py`
  - exit 0
- scoped `git diff --check`
  - exit 0

Task B validation：

- `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest src/ros2_trashbot_behavior/test/test_remote_bridge.py`
  - `Ran 33 tests in 16.314s`
  - `OK`
- `PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_bridge.py`
  - exit 0
- scoped `git diff --check`
  - exit 0

## Product Acceptance 结论

本轮满足 PRD 与 tech-plan 的 P0/P1 验收口径，可以作为 O5 的 `software_proof_docker_phone_task_flow_readiness_gate` 收口证据。

O5 可从约 46% 保守上调到约 48%。O6 保持约 47%。O1/O2/O3/O4 不提升。

## 剩余风险和证据缺口

- 没有真实手机设备 Safari/Chrome 验收，也没有 production app。
- 没有真实云、真实 4G/SIM、HTTPS/TLS 公网入口、生产账号、生产 DB/queue 或 OSS/CDN 实流量。
- 没有 Nav2/fixed-route 实跑、WAVE ROVER、真实串口、HIL 或真实送达。
- ACK 仍只是 command accepted/processing evidence；送达成功必须以后续任务状态、Nav2/fixed-route 或实机证据证明。
