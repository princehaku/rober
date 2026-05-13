# Sprint 2026.05.13_23-24 Mobile Device Evidence Capture Gate - Final

## 结论

本 sprint 完成 `software_proof_docker_mobile_device_evidence_capture_gate`。Objective 4 从约 75% 谨慎上调到约 76%；Objective 5 没有真实外部材料，保持约 68%；Objective 1/2/3 不调整。

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

Task C Product closeout 运行文件存在性、关键边界检索和 scoped `git diff --check`，结果记录在本次最终回复。

## OKR 收口

Objective 4 上调到约 76%，理由：

- `mobile/web/` 首屏新增“手机设备证据采集”面板。
- evidence package 可采集、展示并复制 phone-safe viewport、touch target、display-mode/PWA、service worker/offline shell、client timestamp、ACK 语义和 `not_proven`。
- 复制包保持白名单过滤，不能包含 token、Authorization、OSS AK/SK、root password、DB/queue URL、raw ROS topic、`/cmd_vel`、串口、硬件参数、本地路径、traceback、checksum 或完整 artifact。
- Start Delivery、Confirm Dropoff、Cancel 继续依赖既有 readiness、acceptance bundle 和 command_safety，设备证据包本身不放行动作。
- Robot compatibility fence 证明 metadata-only response 不触发 action、ACK 或 cursor；valid command-envelope mixed metadata 只按 command envelope 执行。
- A/B targeted tests、`py_compile`、`node --check` 和 scoped diff check 均通过。

Objective 5 保持约 68%，理由：

- 本轮没有真实公网 HTTPS/TLS。
- 本轮没有 4G/SIM。
- 本轮没有 OSS/CDN live traffic。
- 本轮没有 production DB/queue connectivity。
- 本轮没有 production worker/migration。
- 本轮没有其他真实外部 O5 材料。

Objective 1/2/3 不调整：

- 未新增真实 WAVE ROVER、UART、T=1001 feedback、HIL、Nav2/fixed-route、任务复盘或真实 delivery 证据。

## OKR 最低优先级核对复盘

`tech-plan.md` 写明当前最低 Objective 是 Objective 5，约 68%。本轮没有针对 Objective 5，是因为该 Objective 的 completion 必须依赖至少一种真实外部材料：公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue connectivity 或 production worker/migration。

A/B/C 执行期间没有拿到上述材料。因此本轮转向 Docker-only 下可推进的 Objective 4，补齐手机端设备证据采集能力。这个判断在 final 收口时仍成立，且没有重复消费 O5 的外部材料 blocker。

## 证据边界

`software_proof_docker_mobile_device_evidence_capture_gate` 只证明 Docker/local mobile software proof 和 robot metadata-only fence。

不证明：

- 真实 iPhone/Android device behavior。
- production app。
- 真实 PWA install prompt。
- 真实公网 HTTPS/TLS。
- 4G/SIM。
- OSS/CDN live traffic。
- production DB/queue。
- production worker/migration。
- Nav2/fixed-route。
- WAVE ROVER。
- HIL。
- 真实 dropoff/cancel completion。
- 真实 delivery。

ACK、HTTP accepted、receipt、terminal confirmation 和 evidence package 仍只是 accepted/processing/support metadata，不是 delivery success。

## 未完成事项和风险

- 需要真实 iPhone/Android device behavior、production app 或真实 PWA install prompt，才能继续提升 Objective 4 的真实设备验收证据。
- 需要真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue 或 production worker/migration，才能继续提升 Objective 5。
- 需要 Nav2/fixed-route、WAVE ROVER、HIL、真实 dropoff/cancel completion 和真实 delivery，才能把手机侧 ACK/证据包从 support metadata 推进到真实任务结果证据。

## 下一步建议

下一轮继续按 `OKR.md` 4.1 重排。若没有真实外部 O5 材料，优先推进 Objective 4 的真实 iPhone/Android device behavior、production app、真实 PWA install prompt 或当前设备证据包的真实移动设备采集证明；不要继续堆本地 O5 metadata depth。
