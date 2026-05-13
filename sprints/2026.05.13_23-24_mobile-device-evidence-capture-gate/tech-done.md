# Sprint 2026.05.13_23-24 Mobile Device Evidence Capture Gate - Tech Done

## Sprint 声明

- sprint_type: epic
- 收口时间：2026-05-13 23:17 Asia/Shanghai
- 统一证据边界：`software_proof_docker_mobile_device_evidence_capture_gate`

## A/B 证据核对结论

Task A Full-stack 文件范围符合 `tech-plan.md`：只改 `mobile/web/index.html`、`mobile/web/app.js`、`mobile/web/styles.css`、`mobile/fixtures/mobile_web_status.fixture.json`、`mobile/test_mobile_web_entrypoint.py`、`mobile/README.md`、`docs/product/mobile_user_flow.md`。新增“手机设备证据采集”面板、复制入口和 phone-safe evidence package，覆盖 viewport、touch target、display-mode/PWA、service worker/offline shell、client timestamp、ACK 语义、`not_proven` 和 `software_proof_docker_mobile_device_evidence_capture_gate`。文案保守，没有把 evidence package 写成真实 iPhone/Android device behavior、production app 或真实 PWA install prompt 通过。

Task B Robot 文件范围符合 `tech-plan.md`：只改 `onboard/src/ros2_trashbot_behavior/test/test_remote_bridge.py`、`onboard/src/ros2_trashbot_behavior/test/test_remote_bridge_protocol.py`、`docs/interfaces/ros_contracts.md`。新增 worker-level 和 protocol-level metadata-only / valid-command mixed-envelope tests，覆盖 `mobile_device_evidence_capture`、`mobile_device_evidence_capture_summary`、`mobile_device_evidence_package`。未改 production `remote_bridge.py`，未扩大到生产 robot runtime。

## 实际改动

Task A Full-stack：

- `mobile/web/index.html`
- `mobile/web/app.js`
- `mobile/web/styles.css`
- `mobile/fixtures/mobile_web_status.fixture.json`
- `mobile/test_mobile_web_entrypoint.py`
- `mobile/README.md`
- `docs/product/mobile_user_flow.md`

Task B Robot：

- `onboard/src/ros2_trashbot_behavior/test/test_remote_bridge.py`
- `onboard/src/ros2_trashbot_behavior/test/test_remote_bridge_protocol.py`
- `docs/interfaces/ros_contracts.md`

Task C Product：

- `OKR.md`
- `docs/process/okr_progress_log.md`
- `sprints/2026.05.13_23-24_mobile-device-evidence-capture-gate/tech-done.md`
- `sprints/2026.05.13_23-24_mobile-device-evidence-capture-gate/side2side_check.md`
- `sprints/2026.05.13_23-24_mobile-device-evidence-capture-gate/final.md`

## 验证结果

Task A Full-stack：

```text
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest mobile.test_mobile_web_entrypoint
Ran 20 tests in 0.012s
OK

PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile mobile/test_mobile_web_entrypoint.py
OK

node --check mobile/web/app.js
OK

git diff --check -- mobile/web/index.html mobile/web/app.js mobile/web/styles.css mobile/fixtures/mobile_web_status.fixture.json mobile/test_mobile_web_entrypoint.py mobile/README.md docs/product/mobile_user_flow.md
OK
```

Task B Robot：

```text
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_remote_bridge.py onboard/src/ros2_trashbot_behavior/test/test_remote_bridge_protocol.py
Ran 117 tests in 59.880s
OK

PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile onboard/src/ros2_trashbot_behavior/test/test_remote_bridge.py onboard/src/ros2_trashbot_behavior/test/test_remote_bridge_protocol.py
passed

git diff --check -- onboard/src/ros2_trashbot_behavior/test/test_remote_bridge.py onboard/src/ros2_trashbot_behavior/test/test_remote_bridge_protocol.py docs/interfaces/ros_contracts.md
passed
```

Task C Product closeout 运行文件存在性、关键边界检索和 scoped `git diff --check`，结果记录在最终回复。

## OKR 调整

Objective 4 从约 75% 谨慎上调到约 76%。理由是本轮把真实手机/browser/PWA 验收前的设备证据采集，推进为 `mobile/web/` 首屏可见、可复制、phone-safe 的软件护栏；同时 Robot fence 证明这些 metadata 不触发 action、ACK、cursor 或 delivery result。

Objective 5 保持约 68%。本轮没有真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue connectivity、production worker/migration 或其他真实外部 O5 材料。

Objective 1/2/3 不调整。本轮未新增真实 WAVE ROVER、UART、T=1001 feedback、HIL、Nav2/fixed-route、任务复盘或真实 delivery 证据。

## 剩余风险

本轮不证明真实 iPhone/Android device behavior、production app、真实 PWA install prompt、真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、production worker/migration、Nav2/fixed-route、WAVE ROVER、HIL、真实 dropoff/cancel completion 或真实 delivery。ACK、HTTP accepted、receipt、terminal confirmation 和 evidence package 仍只是 accepted/processing/support metadata，不是 delivery success。
