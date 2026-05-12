# Sprint 2026.05.13_07-08 Mobile Operation Log Gate - Final

## Sprint Type

- `sprint_type: epic`
- evidence_boundary：`software_proof_docker_mobile_operation_log_gate`
- 收口时间：2026-05-13 07:14 Asia/Shanghai

## 最终结论

本 sprint 完成 Objective 4 的手机 operation log gate：手机端能以 phone-safe 方式展示最近事件、恢复提示和支持交接入口；robot compatibility fence 证明 operation-log metadata 不会触发 robot action、ACK 或 cursor 进展，也不会把 ACK 升级为 delivery success。

Objective 4 从约 58% 保守上调到约 60%。Objective 1/2/3/5 不调整。最新 sprint 更新为 `2026.05.13_07-08_mobile-operation-log-gate`。

## 用户价值和产品北极星

用户价值：普通用户在手机上能看懂"刚才发生什么、现在卡在哪里、下一步如何处理或交接支持"，不需要看 raw JSON、ROS topic、串口、硬件参数或云队列细节。

产品北极星：rober 的手机端继续朝普通用户唯一入口推进；内部 robot command/status/ACK 与 support metadata 被清晰隔离，避免把诊断解释误当成真实动作或送达完成。

## OKR 映射与 KR 更新

- Objective 4 KR1：手机最小流程补上"查看状态 -> 处理异常"软件证明。
- Objective 4 KR4：远程诊断最小数据包中的状态、失败原因和支持摘要已进入 phone-safe operation log 表达。
- Objective 4 KR5：用户无需命令行、ROS2、串口或硬件调试即可理解阻塞与恢复提示。
- Objective 4 KR7：手机端新增中文优先操作日志、支持入口和 fail-closed 主操作边界。
- Objective 2/5 guardrail：operation-log metadata 不改变 robot action、ACK、cursor、云中转或 delivery success 语义。

## 本轮核心抓手

核心抓手是"状态可解释 + 异常可恢复 + 支持可交接"。在 Docker-only 环境中，本轮没有继续堆云端后端深度，也没有把本地 fixture/static smoke 夸大为真实手机或真实机器人证据。

## 实际改动摘要

Task A `full-stack-software-engineer`：

- 手机端新增只读 operation log 面板。
- 优先消费 `operation_log` / `phone_operation_log`；缺失时只从既有 phone-safe readiness/support 字段派生安全事件。
- 展示最近事件、恢复提示、支持交接入口；不启用或触发 Start/Confirm/Cancel。
- 同步 `mobile/README.md` 与 `docs/product/mobile_user_flow.md`。

Task B `robot-software-engineer`：

- 增加 operation-log compatibility fence。
- 证明 valid command response 中 metadata 不污染 command/status/ACK envelope。
- 证明 metadata-only operation-log response 不触发 backend action、不 POST ACK、不推进或持久化 cursor。
- 同步 `docs/interfaces/ros_contracts.md` 与 `docs/product/remote_4g_mvp.md`。

Task C `product-okr-owner`：

- 补齐 `tech-done.md`、`side2side_check.md`、`final.md`。
- 更新 `OKR.md` 与 `docs/process/okr_progress_log.md`。

## 验证结果

Task A：

- `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest mobile.test_mobile_web_entrypoint` -> `Ran 7 tests in 0.002s`，`OK`。
- `git diff --check -- mobile/web mobile/fixtures mobile/test_mobile_web_entrypoint.py mobile/README.md docs/product/mobile_user_flow.md` -> 无输出。
- 首轮失败为新增测试正则转义错误，已修复并复跑通过。

Task B：

- `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_remote_bridge.py onboard/src/ros2_trashbot_behavior/test/test_remote_bridge_protocol.py` -> `Ran 69 tests in 34.102s`，`OK`；有一个 closed test socket `ResourceWarning`，exit 0。
- `PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_bridge.py onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_bridge_protocol.py` -> 无输出。
- `git diff --check -- onboard/src/ros2_trashbot_behavior/test/test_remote_bridge.py onboard/src/ros2_trashbot_behavior/test/test_remote_bridge_protocol.py docs/interfaces/ros_contracts.md docs/product/remote_4g_mvp.md` -> 无输出。

Product closeout：

- docs path check 覆盖 `docs/product/mobile_user_flow.md`、`docs/product/remote_4g_mvp.md`、`docs/interfaces/ros_contracts.md`、`docs/process/okr_progress_log.md`。
- scoped `git diff --check -- OKR.md docs/process/okr_progress_log.md sprints/2026.05.13_07-08_mobile-operation-log-gate` 通过后可作为最终 closeout fence。

## 不声明范围

本轮不声明：

- 真实手机设备/browser。
- production app。
- 真实 PWA install prompt。
- 真实云/4G。
- OSS/CDN live traffic。
- production DB/queue。
- Nav2/fixed-route。
- WAVE ROVER。
- HIL。
- 真实送达。

ACK 仍只是 accepted/processing evidence，不是 delivery success。

## 剩余风险

- 真实手机浏览器/设备、PWA install prompt 和触控体验仍需后续设备验收。
- 真实云/4G、OSS/CDN live traffic、production DB/queue 仍需 Objective 5 后续 sprint。
- 真实 Nav2/fixed-route、WAVE ROVER、HIL 和真实送达仍需 O1/O2/O3 后续证据。
- Task B 的 closed test socket `ResourceWarning` 不影响本轮 exit 0，但可后续单独清理。

## 下一步建议

下一轮继续按 live `OKR.md` 最低 Objective 选择。若 O4 仍最低，优先补真实手机浏览器/设备验收或 operation-log 弱网/恢复路径的浏览器证据；若 O5 再次低于 O4，则切回真实云/4G 或 production DB/queue 的可验证证据链。
