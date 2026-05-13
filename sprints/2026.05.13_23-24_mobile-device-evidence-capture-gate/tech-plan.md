# Sprint 2026.05.13_23-24 Mobile Device Evidence Capture Gate - Tech Plan

## 总体方案

本 sprint 是 Epic，采用 A/B 并行、C 收口：

- Task A Full-stack 在 `mobile/web/` 做浏览器端 device evidence capture、展示、复制、fixture、targeted mobile unittest 和 `docs/product/mobile_user_flow.md`。
- Task B Robot compatibility fence 在 remote bridge/protocol tests 和 `docs/interfaces/ros_contracts.md` 证明新 metadata 不进入 command/ACK/cursor/robot execution。
- Task C Product 等 A/B 返回后更新 OKR、progress log 和本 sprint 收口文档。

统一证据边界：`software_proof_docker_mobile_device_evidence_capture_gate`。本边界只证明 Docker/local mobile software proof 与 robot metadata-only fence。

## OKR 最低优先级核对

1. 当前 `OKR.md` 4.1 完成度最低的 Objective 是 Objective 5：云中转 + OSS/CDN 数据通路产品化，约 68%。
2. 本 sprint 不直接针对 Objective 5，而是针对 Objective 4：手机用户体验与低成本量产边界。
3. 不针对 Objective 5 的具体理由：`OKR.md` 第 6 节和上一轮 `final.md` 明确，Objective 5 completion 需要至少一种真实外部材料，包括真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue connectivity 或 production worker/migration。当前本机没有这些材料，继续推进本地 O5 metadata depth 会重复消费同一 blocker。Objective 4 仍有可执行抓手：补齐真实手机/browser/PWA 验收前的 phone-safe 证据采集能力。

## 接口和证据边界

新增或升级的 phone-safe metadata 名称建议为：

- `mobile_device_evidence_capture`
- `mobile_device_evidence_capture_summary`
- `mobile_device_evidence_package`

字段建议：

- `schema=trashbot.mobile_device_evidence_capture.v1`
- `schema_version=1`
- `source=mobile_web`
- `viewport`
- `touch_target`
- `display_mode`
- `pwa_install_prompt`
- `service_worker`
- `offline_shell`
- `client_timestamp`
- `safe_phone_copy`
- `ack_semantics=accepted_processing_only_not_delivery_success`
- `evidence_boundary=software_proof_docker_mobile_device_evidence_capture_gate`
- `not_proven`

这些字段只能作为 phone/support metadata。它们不是 robot command、remote ACK、cursor instruction、delivery result、production readiness、HIL 或真实 device acceptance proof。metadata 出现在 valid command envelope 外时必须被 robot bridge 忽略；metadata 与 valid command envelope 混合时，只能按 valid command envelope 执行，metadata 不得进入 ACK/status 编码。

## Task A - Full-stack

Owner：`full-stack-software-engineer`

允许改动文件：

- `mobile/web/index.html`
- `mobile/web/app.js`
- `mobile/web/styles.css`
- `mobile/fixtures/mobile_web_status.fixture.json`
- `mobile/test_mobile_web_entrypoint.py`
- `mobile/README.md`
- `docs/product/mobile_user_flow.md`

实现要求：

1. 在 `mobile/web/` 首屏新增或升级 “手机设备证据采集” 面板。
2. 采集或显示 viewport、touch target、display-mode/PWA、service worker/offline shell、client timestamp、evidence boundary、`not_proven` 和 ACK 语义。
3. 增加复制 phone-safe evidence package 的入口；复制内容必须过滤敏感字段和 robot/raw 技术字段。
4. 缺真实手机/browser、production app、真实 PWA install prompt 时，Start Delivery、Confirm Dropoff、Cancel 继续 fail closed。
5. 保持现有 Start confirmation、operation log、action feedback、terminal action confirmation 语义不倒退。
6. `docs/product/mobile_user_flow.md` 与 `mobile/README.md` 必须同步写清新 evidence capture 的字段、边界和 not-proven 范围。

验收命令：

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest mobile.test_mobile_web_entrypoint
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile mobile/test_mobile_web_entrypoint.py
node --check mobile/web/app.js
git diff --check -- mobile/web/index.html mobile/web/app.js mobile/web/styles.css mobile/fixtures/mobile_web_status.fixture.json mobile/test_mobile_web_entrypoint.py mobile/README.md docs/product/mobile_user_flow.md
```

输出要求：

- 实际改动文件列表。
- 上述命令关键输出。
- 若失败，给出失败定位和已修复/未修复状态。
- 剩余风险，尤其是真实手机设备/browser、production app 和真实 PWA install prompt 未证明范围。

## Task B - Robot Compatibility Fence

Owner：`robot-software-engineer`

允许改动文件：

- `onboard/src/ros2_trashbot_behavior/test/test_remote_bridge.py`
- `onboard/src/ros2_trashbot_behavior/test/test_remote_bridge_protocol.py`
- `docs/interfaces/ros_contracts.md`

生产 `remote_bridge` 代码默认禁止改，除非 targeted tests 证明必须最小修复。若需要改生产代码，必须先返回失败定位、最小修复理由和建议扩大文件范围。

实现要求：

1. 增加 `mobile_device_evidence_capture` / summary / evidence package metadata-only tests。
2. 证明 metadata-only response 不触发 collect、confirm_dropoff、cancel、ACK POST、cursor advance、cursor persistence 或 delivery success claim。
3. 证明 metadata 与 valid command envelope 混合时，只执行 command envelope，不把 evidence capture metadata 编入 ACK/status。
4. `docs/interfaces/ros_contracts.md` 必须写清这些字段是 phone/support metadata，不是 command、ACK、cursor、delivery result、production readiness、HIL 或真实 device proof。

验收命令：

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_remote_bridge.py onboard/src/ros2_trashbot_behavior/test/test_remote_bridge_protocol.py
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile onboard/src/ros2_trashbot_behavior/test/test_remote_bridge.py onboard/src/ros2_trashbot_behavior/test/test_remote_bridge_protocol.py
git diff --check -- onboard/src/ros2_trashbot_behavior/test/test_remote_bridge.py onboard/src/ros2_trashbot_behavior/test/test_remote_bridge_protocol.py docs/interfaces/ros_contracts.md
```

输出要求：

- 实际改动文件列表。
- 上述命令关键输出。
- 若失败，给出失败定位和是否需要扩大生产代码范围。
- 剩余风险，尤其是本地 metadata fence 不证明真实 robot execution、Nav2/fixed-route、WAVE ROVER、HIL 或 delivery。

## Task C - Product Closeout

Owner：`product-okr-owner`

允许改动文件：

- `OKR.md`
- `docs/process/okr_progress_log.md`
- `sprints/2026.05.13_23-24_mobile-device-evidence-capture-gate/tech-done.md`
- `sprints/2026.05.13_23-24_mobile-device-evidence-capture-gate/side2side_check.md`
- `sprints/2026.05.13_23-24_mobile-device-evidence-capture-gate/final.md`

执行条件：

Task C 只能在 Task A 和 Task B 都返回后执行。Product 必须核对 A/B 文件范围、验证输出、证据边界和 not-proven 文案，再决定 Objective 4 是否谨慎上调。没有真实外部 O5 材料时，Objective 5 不上调。

验收命令：

```bash
test -f sprints/2026.05.13_23-24_mobile-device-evidence-capture-gate/tech-done.md && test -f sprints/2026.05.13_23-24_mobile-device-evidence-capture-gate/side2side_check.md && test -f sprints/2026.05.13_23-24_mobile-device-evidence-capture-gate/final.md
rg -n "software_proof_docker_mobile_device_evidence_capture_gate|Objective 4|Objective 5|真实 iPhone/Android|production app|真实 PWA install prompt|ACK|not_proven" OKR.md docs/process/okr_progress_log.md sprints/2026.05.13_23-24_mobile-device-evidence-capture-gate
git diff --check -- OKR.md docs/process/okr_progress_log.md sprints/2026.05.13_23-24_mobile-device-evidence-capture-gate/tech-done.md sprints/2026.05.13_23-24_mobile-device-evidence-capture-gate/side2side_check.md sprints/2026.05.13_23-24_mobile-device-evidence-capture-gate/final.md
```

输出要求：

- A/B 证据核对结论。
- 实际改动文件列表。
- Product 验收命令关键输出。
- OKR 调整或不调整理由。
- 剩余风险和下一步建议。

## 并行启动要求

`Task A Full-stack` 和 `Task B Robot Compatibility Fence` 文件范围互不重叠，后续主会话必须在同一轮并行启动两个 `spawn_agent(agent_type=worker)`。两个 worker prompt 必须包含对应 `.codex/agents/<role>.toml` 的完整 prompt、以上本轮任务、文件范围、验收命令和输出要求。

`Task C Product Closeout` 不得与 A/B 并行；必须等 A/B 返回后再执行。

## 本轮非目标

本 sprint 不证明真实 iPhone/Android device behavior、production app、真实 PWA install prompt、真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、production worker/migration、Nav2/fixed-route、WAVE ROVER、HIL、真实 dropoff completion、真实 cancel completion 或真实 delivery。ACK、HTTP accepted、receipt、evidence package 和 terminal confirmation 仍只是 accepted/processing/support evidence，不是 delivery success。
