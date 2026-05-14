# Sprint 2026.05.14_17-18 Mobile PWA Install Prompt Event Capture - Tech Done

sprint_type: epic

## 实际改动

Task A `full-stack-software-engineer` 已完成手机端 PWA install prompt event capture：

- 更新 `mobile/web/app.js`、`mobile/web/index.html`、`mobile/fixtures/mobile_web_status.fixture.json`、`mobile/test_mobile_web_entrypoint.py`、`mobile/README.md`、`docs/product/mobile_user_flow.md`。
- 新增 `mobile_pwa_install_prompt_event_capture*` schema、运行时事件监听、whitelist-only copy package 和敏感字段围栏。
- 监听 `beforeinstallprompt`、`beforeinstallprompt.userChoice`、`appinstalled`；缺事件时保持 blocked-by-design / `not_proven`；事件出现也不启用 Start/Confirm/Cancel。
- 产出 `sprints/2026.05.14_17-18_mobile-pwa-install-prompt-event-capture/evidence/task_a_mobile_pwa_install_prompt_event_capture_summary.json`。

Task B `robot-software-engineer` 已完成 Robot metadata-only fence：

- 更新 `onboard/src/ros2_trashbot_behavior/test/test_remote_bridge.py`、`onboard/src/ros2_trashbot_behavior/test/test_remote_bridge_protocol.py`、`docs/interfaces/ros_contracts.md`。
- 新增 `mobile_pwa_install_prompt_event_capture*` metadata-only fence。
- 覆盖纯 metadata response 不触发 collect/dropoff/cancel、ACK POST、cursor 持久化、terminal ACK、production readiness、HIL、dropoff/cancel completion 或 delivery success。
- 覆盖 mixed valid-command 场景，确认实际 action/ACK/cursor 仍只由合法 `trashbot.remote.v1` collect envelope 决定。

Task C `product-okr-owner` 已完成 closeout：

- 创建 `tech-done.md`、`side2side_check.md`、`final.md`。
- 更新 `OKR.md` 4.1 快照。
- 更新 `docs/process/okr_progress_log.md`。

## 验证结果

Task A 验证：

```text
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest mobile.test_mobile_web_entrypoint
Ran 35 tests OK

PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile mobile/test_mobile_web_entrypoint.py
pass

node --check mobile/web/app.js
pass

required rg
pass

scoped git diff --check
pass

fixture/evidence JSON parse
pass
```

Task B 验证：

```text
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest \
  onboard/src/ros2_trashbot_behavior/test/test_remote_bridge.py \
  onboard/src/ros2_trashbot_behavior/test/test_remote_bridge_protocol.py
Ran 187 tests in 96.024s OK

PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile \
  onboard/src/ros2_trashbot_behavior/test/test_remote_bridge.py \
  onboard/src/ros2_trashbot_behavior/test/test_remote_bridge_protocol.py
pass

required rg
pass

scoped git diff --check
pass
```

Task C 验证命令在 closeout 后执行，结果记录在最终回复和 `final.md`。

## 偏差和失败定位

- Task A/B 未报告最终失败；已报告的命令均通过。
- 本轮没有真实 iPhone/Android device behavior、production app、真实 PWA prompt/user choice 现场验收、O5 external proof、公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、production worker/migration、Nav2/fixed-route、WAVE ROVER、HIL、dropoff/cancel completion 或 delivery success。
- 因此本轮证据边界只能写为 `software_proof_docker_mobile_pwa_install_prompt_event_capture_gate`，不能写成真实设备验收或云端生产验收。

## 剩余风险

- `beforeinstallprompt` 和 `appinstalled` 受浏览器、安装状态、manifest、service worker、HTTPS 和用户行为影响；未触发时必须继续输出 `not_proven`。
- `safe_to_control=false`、`accepted_processing_only_not_delivery_success`、whitelist-only copy、Start/Confirm/Cancel fail closed 必须保持，后续不能被 event observed 状态放宽。
- Objective 5 仍缺真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue connectivity 或 production worker/migration；本轮不应提升 O5。
