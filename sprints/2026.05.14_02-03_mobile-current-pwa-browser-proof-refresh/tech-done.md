# Sprint 2026.05.14_02-03 Mobile Current PWA Browser Proof Refresh - Tech Done

## sprint_type

sprint_type: epic

## 用户价值和北极星

用户价值：普通用户和支持人员现在能基于当前 `mobile/web/` 第一屏做验收，而不是基于旧版 local browser proof。当前 proof 覆盖三步主路径、恢复决策、终端动作二次确认、手机设备证据采集、真实手机验收交接会话、PWA 安装提示证据、浏览器验收包、Diagnostics、Support Handoff 和 ACK copy。

产品北极星：继续把手机端做成普通用户唯一入口，同时保持低成本、可复现、可解释的证据链；本轮只推进 Objective 4 的 current PWA local Chromium software proof。

## OKR 映射和 KR 拆解

- Objective 4 / KR1：当前首屏仍围绕选择垃圾站、确认已放入垃圾、一键发车、状态解释和异常处理。
- Objective 4 / KR5：普通用户不接触 ROS2、串口、硬件参数或命令行，也能看到为什么当前不能控制以及下一步需要什么证据。
- Objective 4 / KR7：390x844 与 768x900 两组本地 Chromium viewport 证明当前 PWA 首屏 hit area、overflow、overlap 和 phone-safe copy 均通过。
- Objective 5：本轮没有真实公网/4G/OSS-CDN/DB-queue/worker 外部材料，不上调。

## Task A Full-stack 结果核对

实际改动：

- `pc-tools/evidence/phone_browser_acceptance_gate.py`
- `mobile/test_mobile_web_entrypoint.py`
- `mobile/README.md`
- `docs/product/mobile_user_flow.md`
- `sprints/2026.05.14_02-03_mobile-current-pwa-browser-proof-refresh/evidence/*`

关键证据：

- Browser gate summary：`ok=true`
- Browser path：`/Applications/Google Chrome.app/Contents/MacOS/Google Chrome`
- Evidence boundary：`software_proof_docker_mobile_current_pwa_browser_proof_refresh_gate`
- 390x844：hit/overlap/overflow/current panels/current boundaries/phone-safe all passed，primary actions disabled
- 768x900：hit/overlap/overflow/current panels/current boundaries/phone-safe all passed，primary actions disabled
- 当前首屏 terminal action confirmation、device evidence capture、handoff session、PWA install prompt evidence、browser acceptance bundle、Diagnostics、Support Handoff 和 ACK copy 可见或可用

验证结果：

```text
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest mobile.test_mobile_web_entrypoint
Ran 23 tests ... OK

PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile pc-tools/evidence/phone_browser_acceptance_gate.py mobile/test_mobile_web_entrypoint.py
pass

git diff --check -- pc-tools/evidence/phone_browser_acceptance_gate.py mobile/test_mobile_web_entrypoint.py mobile/README.md docs/product/mobile_user_flow.md sprints/2026.05.14_02-03_mobile-current-pwa-browser-proof-refresh
pass
```

## Task B Robot 结果核对

实际改动：

- `onboard/src/ros2_trashbot_behavior/test/test_remote_bridge.py`
- `onboard/src/ros2_trashbot_behavior/test/test_remote_bridge_protocol.py`
- `docs/interfaces/ros_contracts.md`

关键证据：

- 覆盖 `mobile_current_pwa_browser_proof_refresh`
- 覆盖 `mobile_current_pwa_browser_proof_refresh_summary`
- 覆盖 `phone_current_pwa_browser_proof_refresh`
- metadata-only responses 不触发 collect、confirm_dropoff、cancel、ACK POST、cursor advance、cursor persistence 或 delivery success
- valid command mixed metadata 只执行 command envelope，不把 browser proof refresh metadata 编入 ACK/status

验证结果：

```text
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_remote_bridge.py onboard/src/ros2_trashbot_behavior/test/test_remote_bridge_protocol.py
Ran 129 tests in 65.076s OK

PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile onboard/src/ros2_trashbot_behavior/test/test_remote_bridge.py onboard/src/ros2_trashbot_behavior/test/test_remote_bridge_protocol.py
pass

git diff --check -- onboard/src/ros2_trashbot_behavior/test/test_remote_bridge.py onboard/src/ros2_trashbot_behavior/test/test_remote_bridge_protocol.py docs/interfaces/ros_contracts.md
pass
```

## Product Closeout 改动

- `OKR.md`
- `docs/process/okr_progress_log.md`
- `sprints/2026.05.14_02-03_mobile-current-pwa-browser-proof-refresh/tech-done.md`
- `sprints/2026.05.14_02-03_mobile-current-pwa-browser-proof-refresh/side2side_check.md`
- `sprints/2026.05.14_02-03_mobile-current-pwa-browser-proof-refresh/final.md`

## 证据边界

本轮边界是 `software_proof_docker_mobile_current_pwa_browser_proof_refresh_gate`。它只证明当前 `mobile/web/` PWA 的本地 Chromium-family browser software proof 和 robot metadata-only fence。

`not_proven` 仍包括：真实 iPhone/Android device behavior、production app、真实 PWA install prompt/user choice、真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、production worker/migration、Nav2/fixed-route、WAVE ROVER、HIL、真实 dropoff/cancel completion 和真实 delivery。

ACK、HTTP accepted、receipt、browser proof、evidence package、handoff session 和 install prompt evidence 仍只是 accepted/processing/support metadata，不是 delivery success。

