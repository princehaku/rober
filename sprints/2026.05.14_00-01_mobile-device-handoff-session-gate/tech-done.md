# Sprint 2026.05.14_00-01 Mobile Device Handoff Session Gate - Tech Done

## Sprint 声明

- sprint_type: epic
- 完成时间：2026-05-14 00:16 Asia/Shanghai
- 目标 Objective：Objective 4 手机用户体验与低成本量产边界
- 统一证据边界：`software_proof_docker_mobile_device_handoff_session_gate`
- 本轮功能名：`mobile-device-handoff-session`

## A/B 实际改动核对

Task A Full-stack 已在允许范围内完成：

- `mobile/web/index.html`
- `mobile/web/app.js`
- `mobile/web/styles.css`
- `mobile/fixtures/mobile_web_status.fixture.json`
- `mobile/test_mobile_web_entrypoint.py`
- `mobile/README.md`
- `docs/product/mobile_user_flow.md`

实际交付为首屏“真实手机验收交接会话”面板和复制入口。页面展示入口 URL/摘要、session id、client reference、真实手机验收步骤、device/browser/PWA/install prompt/offline shell/touch target/viewport 观察项，并生成脱敏 phone-safe handoff package。该 package 可引用 `mobile_device_evidence_capture`，但不得写成真实设备验收通过；缺真实手机/browser、production app、真实 PWA install prompt 时，Start Delivery、Confirm Dropoff、Cancel 继续 fail closed。

Task B Robot compatibility fence 已在允许范围内完成：

- `onboard/src/ros2_trashbot_behavior/test/test_remote_bridge.py`
- `onboard/src/ros2_trashbot_behavior/test/test_remote_bridge_protocol.py`
- `docs/interfaces/ros_contracts.md`

实际交付为 `mobile_device_handoff_session` / summary / package metadata-only worker/protocol fences。Robot 侧证明 metadata-only response 不触发 collect、confirm_dropoff、cancel，不 POST ACK，不推进或持久化 cursor，不写 delivery success；valid command mixed metadata 只按 command envelope 执行，不把 handoff metadata 编入 ACK/status。未修改生产 `remote_bridge`。

## 验证结果

Task A 验证输出：

- `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest mobile.test_mobile_web_entrypoint` -> `Ran 21 tests in 0.013s OK`
- `PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile mobile/test_mobile_web_entrypoint.py` -> pass
- `node --check mobile/web/app.js` -> pass
- `git diff --check -- mobile/web/index.html mobile/web/app.js mobile/web/styles.css mobile/fixtures/mobile_web_status.fixture.json mobile/test_mobile_web_entrypoint.py mobile/README.md docs/product/mobile_user_flow.md` -> pass

Task B 验证输出：

- `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_remote_bridge.py onboard/src/ros2_trashbot_behavior/test/test_remote_bridge_protocol.py` -> `Ran 121 tests in 61.586s OK`
- `PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile onboard/src/ros2_trashbot_behavior/test/test_remote_bridge.py onboard/src/ros2_trashbot_behavior/test/test_remote_bridge_protocol.py` -> pass
- `git diff --check -- onboard/src/ros2_trashbot_behavior/test/test_remote_bridge.py onboard/src/ros2_trashbot_behavior/test/test_remote_bridge_protocol.py docs/interfaces/ros_contracts.md` -> pass

Product Task C closeout 验证见 `side2side_check.md` 与 `final.md`。

## Product 验收结论

A/B 文件范围、验证输出、phone-safe copy、ACK 非成功语义和 `not_proven` 文案符合 `prd.md` 与 `tech-plan.md`。本轮 evidence boundary 只能写为 `software_proof_docker_mobile_device_handoff_session_gate`。

Objective 4 可从约 76% 谨慎上调到约 77%，因为真实手机验收交接从口头流程变成了可见、可复制、可被 robot metadata fence 隔离的软件护栏。Objective 5 不上调，因为本轮没有真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue connectivity、production worker/migration 或其他真实外部 O5 材料。

## 剩余风险

- 未证明真实 iPhone/Android device behavior。
- 未证明 production app。
- 未证明真实 PWA install prompt。
- 未证明真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue 或 production worker/migration。
- 未证明 Nav2/fixed-route、WAVE ROVER、HIL、真实 dropoff/cancel completion 或真实 delivery。
- ACK、HTTP accepted、receipt、evidence package 和 handoff session 仍只是 accepted/processing/support metadata，不是 delivery success。
