# Sprint 2026.05.13_05-06 Mobile Task Start Confirmation Gate - Final

## 收口结论

本轮完成 `software_proof_docker_mobile_task_start_confirmation_gate`，Objective 4 可从约 56% 保守上调到约 58%。Objective 1/2/3/5 不调整。

阶段验收通过，但证据边界必须保持为 Docker/local 软件证明：本轮没有真实手机设备/浏览器、production app、真实云/4G、OSS/CDN live traffic、Nav2/fixed-route、WAVE ROVER、HIL 或真实送达。

## 用户价值和产品北极星

用户价值：手机发车前现在必须确认目的垃圾站和"已放入垃圾"，把误发车、空车发车、发错站点这些普通用户高频风险前置拦住。

产品北极星：普通用户继续只通过手机理解任务状态和下一步动作，不需要接触 ROS2、SSH、串口、raw JSON、云队列或硬件细节。ACK 仍只代表 command accepted/processing evidence。

## OKR 映射

- Objective 4 KR1：完成手机最小任务主路径中的目标确认、装载确认和一键发车 gate。
- Objective 4 KR5：普通用户在未满足条件时看到阻塞原因，Start fail closed。
- Objective 4 KR7：本地手机入口继续围绕中文主路径、按钮 gate 和 phone-safe payload 推进。
- Objective 2 guardrail：Robot fence 确认 phone metadata 不触发 action、不 ACK、不推进 cursor。
- Objective 5 guardrail：collect payload 可服务未来云中转，但本轮不证明真实云、4G、OSS/CDN 或 production queue。

## 实际改动

Worker 已完成并记录在 `tech-done.md`：

- Full-stack：`mobile/web` 增加发车确认区、destination + loaded confirmation + `command_safety` + `can_collect` 四重 gate，`POST /api/collect` 改为 phone-safe JSON body，payload 同时包含 `destination` 和同值 `target` 以兼容现有 collect 入口，并更新 mobile smoke 与 `docs/product/mobile_user_flow.md`。
- Robot：增加 remote bridge/protocol compatibility fence，证明 metadata-only phone confirmation 不触发 backend action/ACK/cursor，protocol normalization 剥离 metadata，并更新 `docs/interfaces/ros_contracts.md`、`docs/product/remote_4g_mvp.md`。
- Product：完成 `side2side_check.md`、本 `final.md`、`OKR.md` 4.1 和 `docs/process/okr_progress_log.md` 收口。

## 验证结果

- `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest mobile.test_mobile_web_entrypoint`：`Ran 6 tests in 0.001s`，`OK`。
- `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_remote_bridge.py onboard/src/ros2_trashbot_behavior/test/test_remote_bridge_protocol.py`：`Ran 64 tests in 32.606s`，`OK`。
- `PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_bridge.py onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_bridge_protocol.py`：通过，无输出。
- `test -f docs/product/mobile_user_flow.md && test -f docs/product/remote_4g_mvp.md && test -f docs/interfaces/ros_contracts.md && test -f docs/process/okr_progress_log.md`：通过。
- 收口文件 scoped `git diff --check`：通过。

## OKR 更新

- `OKR.md` 最新 sprint 更新为 `2026.05.13_05-06_mobile-task-start-confirmation-gate`。
- Objective 4 从约 56% 保守上调到约 58%。
- Objective 1/2/3/5 不调整。
- `docs/process/okr_progress_log.md` 已追加本轮记录。

## 剩余风险

- 仍无真实手机设备/浏览器验收、production app、真实 PWA install prompt。
- 仍无真实云/4G、OSS/CDN live traffic、production DB/queue。
- 仍无 Nav2/fixed-route、WAVE ROVER、HIL 或真实送达。
- "已放入垃圾"是用户确认，不是传感器自动检测。
