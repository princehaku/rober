# Sprint 2026.05.13_07-08 Mobile Operation Log Gate - Tech Done

## Sprint Type

- `sprint_type: epic`
- evidence_boundary：`software_proof_docker_mobile_operation_log_gate`
- 收口时间：2026-05-13 07:14 Asia/Shanghai

## 用户价值和产品北极星

用户价值：普通手机用户在等待、阻塞、离线恢复、人工接管或需要售后交接时，可以在手机端看到最近发生了什么、当前卡在哪里、下一步如何安全处理，不需要理解 ROS2、云队列、串口、WAVE ROVER 或 raw diagnostics。

产品北极星：手机端必须成为普通用户唯一可理解入口；operation log 只解释状态、异常和支持交接，不能把内部 `trashbot.remote.v1` command/status/ACK、cursor、机器人动作或硬件细节暴露给用户。

## OKR 映射

- Objective 4 KR1：补齐"查看状态 -> 处理异常"的手机最小流程。
- Objective 4 KR4：把最近状态、失败/阻塞原因和支持交接摘要转成 phone-safe 操作日志。
- Objective 4 KR5：普通用户不接触命令行、ROS2、串口或硬件调试，也能理解失败状态和下一步。
- Objective 4 KR7：继续完善中文优先、按钮 fail-closed、支持入口可见的手机端体验。
- Objective 2/5 guardrail：operation-log metadata 只作为 phone/support metadata，不触发 robot action、ACK 或 cursor 进展。

## 实际改动

Task A `full-stack-software-engineer`：

- `mobile/web/index.html`
- `mobile/web/styles.css`
- `mobile/web/app.js`
- `mobile/fixtures/mobile_web_status.fixture.json`
- `mobile/test_mobile_web_entrypoint.py`
- `mobile/README.md`
- `docs/product/mobile_user_flow.md`

交付内容：

- 手机端新增只读"操作日志"面板，优先展示后端/fixture `operation_log` / `phone_operation_log`。
- 当 operation-log 字段缺失时，仅从 `phone_readiness`、`command_safety`、`phone_task_flow_readiness`、`phone_offline_resume_readiness`、`phone_support_bundle`、`voice_prompt_readiness` 派生 phone-safe 安全事件。
- 面板展示最近事件、恢复提示和支持交接入口；不启用、不触发、不绕过 Start/Confirm/Cancel。
- `mobile/README.md` 与 `docs/product/mobile_user_flow.md` 已同步 `software_proof_docker_mobile_operation_log_gate` 和非证明边界。

Task B `robot-software-engineer`：

- `onboard/src/ros2_trashbot_behavior/test/test_remote_bridge.py`
- `onboard/src/ros2_trashbot_behavior/test/test_remote_bridge_protocol.py`
- `docs/interfaces/ros_contracts.md`
- `docs/product/remote_4g_mvp.md`

交付内容：

- 增加 operation-log compatibility fence。
- valid command response 中 operation metadata 不污染 command/status/ACK envelope，不把 ACK 升级为 delivery success。
- metadata-only operation-log response 不触发 backend action、不 POST ACK、不推进内存 cursor、不持久化 cursor。
- protocol normalization 剥离 command envelope 外的 `operation_log` / `phone_operation_log`。
- 接口与远程 MVP 文档已同步 metadata-only fence 与 ACK 边界。

Task C `product-okr-owner`：

- `sprints/2026.05.13_07-08_mobile-operation-log-gate/tech-done.md`
- `sprints/2026.05.13_07-08_mobile-operation-log-gate/side2side_check.md`
- `sprints/2026.05.13_07-08_mobile-operation-log-gate/final.md`
- `OKR.md`
- `docs/process/okr_progress_log.md`

交付内容：

- 完成本 sprint Product closeout。
- 更新 Objective 4 从约 58% 到约 60%。
- 最新 sprint 更新为 `2026.05.13_07-08_mobile-operation-log-gate`。
- Objective 1/2/3/5 不调整。

## 验证结果

Task A 验证：

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest mobile.test_mobile_web_entrypoint
```

结果：

```text
Ran 7 tests in 0.002s
OK
```

```bash
git diff --check -- mobile/web mobile/fixtures mobile/test_mobile_web_entrypoint.py mobile/README.md docs/product/mobile_user_flow.md
```

结果：无输出。

Task A 首轮失败定位：

- 新增测试存在正则转义错误。
- 已由 worker 修复并复跑通过。

Task B 验证：

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_remote_bridge.py onboard/src/ros2_trashbot_behavior/test/test_remote_bridge_protocol.py
```

结果：

```text
Ran 69 tests in 34.102s
OK
```

备注：出现一个 closed test socket `ResourceWarning`，命令 exit 0；本轮不把该 warning 计为产品阻塞。

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_bridge.py onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_bridge_protocol.py
```

结果：无输出。

```bash
git diff --check -- onboard/src/ros2_trashbot_behavior/test/test_remote_bridge.py onboard/src/ros2_trashbot_behavior/test/test_remote_bridge_protocol.py docs/interfaces/ros_contracts.md docs/product/remote_4g_mvp.md
```

结果：无输出。

Product closeout 验证：

```bash
test -f docs/product/mobile_user_flow.md && test -f docs/product/remote_4g_mvp.md && test -f docs/interfaces/ros_contracts.md && test -f docs/process/okr_progress_log.md
git diff --check -- OKR.md docs/process/okr_progress_log.md sprints/2026.05.13_07-08_mobile-operation-log-gate
```

执行结果见本轮最终输出；预期为 docs path 存在且 scoped diff check 无输出。

## 偏差与失败定位

- Task A 首轮测试失败已定位为测试正则转义错误，修复后通过。
- Task B 有一个 closed test socket `ResourceWarning`，但 targeted unittest exit 0，未影响 compatibility fence 结论。
- 本轮未发现需要扩大文件范围的产品问题。

## 剩余风险

- 仍没有真实手机设备/browser 验收。
- 仍没有 production app 或真实 PWA install prompt 证据。
- 仍没有真实云/4G、OSS/CDN live traffic、production DB/queue 证据。
- 仍没有 Nav2/fixed-route、WAVE ROVER、HIL 或真实送达证据。
- ACK 仍只表示 accepted/processing evidence，不是 delivery success。

## OKR 更新摘要

- Objective 4：约 58% -> 约 60%。
- Objective 1/2/3/5：不调整。
- evidence_boundary：`software_proof_docker_mobile_operation_log_gate`。
