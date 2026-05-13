# Sprint 2026.05.13_22-23 Mobile Terminal Action Confirmation Gate - Tech Done

## Sprint 类型

sprint_type: epic

本轮按 `tech-plan.md` 拆为 Task A Full-stack、Task B Robot、Task C Product closeout。A/B 已完成并返回验证证据；本文件记录合并后的产品收口。

## 用户价值和产品北极星

本轮把手机端 Confirm Dropoff / Cancel 从“点击即提交”推进到“先看见终端动作风险、ACK 语义和 `not_proven`，再显式确认”。用户价值是降低普通手机用户把 ACK、HTTP accepted 或 receipt 误读成真实投放完成、真实取消完成或 delivery success 的风险。

北极星保持不变：让不会电脑和硬件的普通用户能通过手机理解并操作低成本 ROS2 垃圾投递机器人，同时每个关键动作都保守、可解释、可复盘。

## OKR 映射

- Objective 4 KR1：手机最小流程补齐 Confirm Dropoff / Cancel 的终端动作二次确认。
- Objective 4 KR5：用户不需要理解 ROS2、ACK、remote bridge 或 cursor，也能知道这只是 accepted/processing/support evidence。
- Objective 4 KR7：手机 UI 主路径更接近可直接使用，但仍限定为 Docker/local mobile software proof。
- Objective 5：本轮没有真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue connectivity 或 production worker/migration 证据，因此不提升。

## 实际改动

Task A Full-stack 改动：

- `mobile/web/index.html`
- `mobile/web/app.js`
- `mobile/web/styles.css`
- `mobile/fixtures/mobile_web_status.fixture.json`
- `mobile/test_mobile_web_entrypoint.py`
- `mobile/README.md`
- `docs/product/mobile_user_flow.md`

Task A 行为结果：

- Confirm Dropoff / Cancel 首次点击只打开“终端动作二次确认”panel，不调用 endpoint。
- 用户显式确认后才提交现有 endpoint。
- 提交继续使用 `trashbot.mobile_action_confirmation.v1` compatible payload。
- fixture 首轮因为 `not_proven` 文案包含英文 `WAVE ROVER` 触发 phone-safe 禁词围栏，已改为中文“真实底盘运动”并重跑通过。

Task B Robot 改动：

- `onboard/src/ros2_trashbot_behavior/test/test_remote_bridge.py`
- `onboard/src/ros2_trashbot_behavior/test/test_remote_bridge_protocol.py`
- `docs/interfaces/ros_contracts.md`

Task B 行为结果：

- 新增 `mobile_terminal_action_confirmation_gate` / `mobile_terminal_action_confirmation_summary` metadata-only fence。
- metadata-only response 不触发 collect、confirm_dropoff、cancel。
- metadata-only response 不 POST ACK、不推进 `last_ack_id`、不持久化 terminal cursor、不写 cursor override。
- valid `confirm_dropoff` command-envelope mixed metadata 只按 command envelope 执行。
- 未改 `remote_bridge.py`、`cloud-relay/` 或 production robot runtime。

Task C Product closeout 改动：

- `OKR.md`
- `docs/process/okr_progress_log.md`
- `sprints/2026.05.13_22-23_mobile-terminal-action-confirmation-gate/tech-done.md`
- `sprints/2026.05.13_22-23_mobile-terminal-action-confirmation-gate/side2side_check.md`
- `sprints/2026.05.13_22-23_mobile-terminal-action-confirmation-gate/final.md`

## 验证结果

Task A Full-stack 验证：

```text
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest mobile.test_mobile_web_entrypoint
Ran 19 tests in 0.010s
OK

PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile mobile/test_mobile_web_entrypoint.py
exit 0

node --check mobile/web/app.js
exit 0

git diff --check -- mobile/web/index.html mobile/web/app.js mobile/web/styles.css mobile/fixtures/mobile_web_status.fixture.json mobile/test_mobile_web_entrypoint.py mobile/README.md docs/product/mobile_user_flow.md
exit 0
```

Task B Robot 验证：

```text
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_remote_bridge.py onboard/src/ros2_trashbot_behavior/test/test_remote_bridge_protocol.py
Ran 113 tests in 57.141s
OK

PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile onboard/src/ros2_trashbot_behavior/test/test_remote_bridge.py onboard/src/ros2_trashbot_behavior/test/test_remote_bridge_protocol.py
exit 0

git diff --check -- onboard/src/ros2_trashbot_behavior/test/test_remote_bridge.py onboard/src/ros2_trashbot_behavior/test/test_remote_bridge_protocol.py docs/interfaces/ros_contracts.md
exit 0
```

Task C Product closeout 验证命令见本次最终输出；文件存在性、关键边界检索和 scoped `git diff --check` 均需通过。

## 证据边界

本轮证据边界为 `software_proof_docker_mobile_terminal_action_confirmation_gate`。

它只证明：

- Docker/local `mobile/web/` 终端动作二次确认 gate。
- Confirm Dropoff / Cancel 首次点击不提交，显式确认后才提交。
- `trashbot.mobile_action_confirmation.v1` compatible payload 沿用。
- Robot metadata-only fence 不把 `mobile_terminal_action_confirmation_gate` / summary 当成 command、ACK、cursor 或 delivery result。

它不证明：

- 真实 iPhone/Android device behavior。
- production app。
- 真实 PWA install prompt。
- 真实公网 HTTPS/TLS。
- 4G/SIM。
- OSS/CDN live traffic。
- production DB/queue。
- production worker/migration。
- Nav2/fixed-route。
- 真实底盘运动。
- HIL。
- 真实 dropoff completion。
- 真实 cancel completion。
- 真实 delivery。

ACK、HTTP accepted、receipt、terminal confirmation 仍只是 accepted/processing/support evidence，不是 delivery success。

## 偏差和修正

- Task A 首轮 fixture `not_proven` 使用英文 `WAVE ROVER`，触发 phone-safe 禁词围栏；已改为中文“真实底盘运动”并重跑 targeted mobile unittest 通过。
- 本轮未扩展 production robot runtime，符合 tech-plan 对 robot task 的 metadata-only fence 范围。

## 剩余风险

- Objective 5 仍缺真实外部材料，不能因本轮 O4 手机确认 gate 上调。
- 真实手机浏览器、真实 PWA install prompt、production app 和真实公网链路仍未验证。
- Confirm Dropoff / Cancel 的真实执行结果仍需后续由 robot task result、Nav2/fixed-route、硬件/HIL 或真实交付证据闭环。
