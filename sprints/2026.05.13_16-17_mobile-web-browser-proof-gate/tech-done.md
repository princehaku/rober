# Sprint 2026.05.13_16-17 Mobile Web Browser Proof Gate - Tech Done

## Sprint 声明

- sprint_type: epic
- closeout_time: 2026-05-13 16:33 Asia/Shanghai
- status: done
- evidence_boundary: `software_proof_docker_mobile_web_browser_proof_gate`

## 用户价值和产品北极星

普通手机用户、测试者和售后支持现在有一份由真实本地 Chromium-family browser 生成的 `mobile/web/` PWA 验收证据：截图、结构化 JSON、summary 和 copyable browser acceptance bundle 都落在本 sprint evidence 目录，可用于判断当前手机入口是否在真实浏览器里可见、可读、可复制、fail closed。

产品北极星保持不变：普通用户只用手机完成垃圾交付；在真实手机设备、production app、真实 PWA install prompt、真实云/4G 和机器人闭环证据缺失时，手机入口必须明确边界、阻止误操作，并把 ACK 保持为 accepted/processing evidence。

## OKR 映射和 KR 拆解

- Objective 4 KR1：手机最小流程从静态 fixture/string smoke 推进到当前 `mobile/web/` PWA 的真实本地 browser proof。
- Objective 4 KR4：远程诊断最小数据包和 browser acceptance bundle 具备可截图、可复制、可交接证据。
- Objective 4 KR5：普通用户不接触命令行、ROS2 或硬件调试，也能看见阻塞原因、Diagnostics 和 Support Handoff。
- Objective 4 KR7：390x844 与 768x900 两个 viewport 均通过 44px hit area、无 overlap、无 horizontal overflow、ACK 可见且不写成 delivery success、phone-safe copy 等 browser 验收。

本轮只更新 Objective 4；Objective 1/2/3/5 不调整。

## 本轮核心抓手

1. Full-stack 将 browser acceptance gate 指向当前 dependency-free `mobile/web/` PWA，而不是旧入口或只跑字符串单测。
2. Robot 补 metadata-only compatibility fence，确保 browser proof/bundle/summary 字段不触发 backend action、ACK、cursor 或 command envelope。
3. Product closeout 只按 A/B 已完成证据更新 sprint、OKR 和 progress log，并保留所有非声明边界。

## 实际改动

Task A - Full-stack Mobile Web Browser Proof Gate：

- `pc-tools/evidence/phone_browser_acceptance_gate.py`
- `mobile/README.md`
- `docs/product/mobile_user_flow.md`
- `mobile/test_mobile_web_entrypoint.py`
- `sprints/2026.05.13_16-17_mobile-web-browser-proof-gate/evidence/mobile_web_browser_390x844.json`
- `sprints/2026.05.13_16-17_mobile-web-browser-proof-gate/evidence/mobile_web_browser_390x844.png`
- `sprints/2026.05.13_16-17_mobile-web-browser-proof-gate/evidence/mobile_web_browser_768x900.json`
- `sprints/2026.05.13_16-17_mobile-web-browser-proof-gate/evidence/mobile_web_browser_768x900.png`
- `sprints/2026.05.13_16-17_mobile-web-browser-proof-gate/evidence/mobile_web_browser_acceptance_summary.json`

实现结果：

- Browser gate 现在服务当前 `/Users/m4/apps/rober/mobile/web`，并使用 `mobile/fixtures/mobile_web_status.fixture.json` 作为 `/api/status` 与 `/api/diagnostics` phone-safe fixture。
- `mobile_web_browser_acceptance_summary.json` 为 `ok=true`，browser 为 `/Applications/Google Chrome.app/Contents/MacOS/Google Chrome`。
- 390x844 与 768x900 均 passed：44px hit area、无 overlap、无 horizontal overflow、ACK visible 且 not delivery success、Diagnostics accessible、Support Handoff available、browser acceptance bundle visible/copyable、Start/Confirm/Cancel disabled、phone-safe visible text passed。
- Evidence boundary 为 `software_proof_docker_mobile_web_browser_proof_gate`。

Task B - Robot Metadata Compatibility Fence：

- `docs/interfaces/ros_contracts.md`
- `onboard/src/ros2_trashbot_behavior/test/test_remote_bridge.py`
- `onboard/src/ros2_trashbot_behavior/test/test_remote_bridge_protocol.py`

实现结果：

- 文档化 `mobile_web_browser_proof`、`phone_browser_proof`、`mobile_browser_proof_summary` 为 `software_proof_docker_mobile_web_browser_proof_gate` 下的 metadata-only 字段。
- Protocol/bridge fence 证明 metadata-only responses 不调用 backend actions、不 POST ACK、不推进 `last_ack_id`、不持久化 `last_terminal_ack_id`。
- 有效 command 与 browser metadata 混合时，只保留 command envelope，metadata 不污染命令语义。

Task C - Product Closeout：

- `OKR.md`
- `docs/process/okr_progress_log.md`
- `sprints/2026.05.13_16-17_mobile-web-browser-proof-gate/tech-done.md`
- `sprints/2026.05.13_16-17_mobile-web-browser-proof-gate/side2side_check.md`
- `sprints/2026.05.13_16-17_mobile-web-browser-proof-gate/final.md`

实现结果：

- Objective 4 从约 68% 保守上调到约 70%。
- Objective 1/2/3/5 不调整。
- 进度日志顶部追加本轮记录。
- sprint closeout 明确本轮不是真实 iPhone/Android device behavior、production app、真实 PWA install prompt、真实云/4G、OSS/CDN live traffic、production DB/queue、Nav2/fixed-route、WAVE ROVER、HIL 或真实送达。

## 验证结果

Task A 已返回：

```text
PYTHONDONTWRITEBYTECODE=1 python3 pc-tools/evidence/phone_browser_acceptance_gate.py --output-dir sprints/2026.05.13_16-17_mobile-web-browser-proof-gate/evidence
summary ok=true
browser=/Applications/Google Chrome.app/Contents/MacOS/Google Chrome
viewports=390x844,768x900
evidence_boundary=software_proof_docker_mobile_web_browser_proof_gate

PYTHONDONTWRITEBYTECODE=1 python3 -m unittest mobile.test_mobile_web_entrypoint
Ran 13 tests
OK

PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile pc-tools/evidence/phone_browser_acceptance_gate.py mobile/test_mobile_web_entrypoint.py
exit 0

git diff --check -- pc-tools/evidence/phone_browser_acceptance_gate.py mobile/README.md docs/product/mobile_user_flow.md mobile/test_mobile_web_entrypoint.py
exit 0
```

Task B 已返回：

```text
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_remote_bridge.py onboard/src/ros2_trashbot_behavior/test/test_remote_bridge_protocol.py
Ran 94 tests in 47.671s
OK

PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile onboard/src/ros2_trashbot_behavior/test/test_remote_bridge.py onboard/src/ros2_trashbot_behavior/test/test_remote_bridge_protocol.py
exit 0

git diff --check -- docs/interfaces/ros_contracts.md onboard/src/ros2_trashbot_behavior/test/test_remote_bridge.py onboard/src/ros2_trashbot_behavior/test/test_remote_bridge_protocol.py
exit 0
```

Task C 验收命令：

```text
test -f OKR.md && test -f docs/process/okr_progress_log.md && test -f docs/product/mobile_user_flow.md && test -f docs/interfaces/ros_contracts.md
exit 0

git diff --check -- OKR.md docs/process/okr_progress_log.md sprints/2026.05.13_16-17_mobile-web-browser-proof-gate
exit 0
```

## 偏差

- 无范围偏差：Task C 只更新允许的 closeout、OKR 和 progress log 文件。
- Task A/B 证据来自对应 worker 返回；Product closeout 未重新运行 Task A/B 的实现测试。
- 未新增真实设备、真实云、真实机器人、真实硬件或 HIL 证据。
- 未改 Task A/B implementation files。

## 剩余风险

- 仍缺真实 iPhone/Android device behavior、production app、真实 PWA install prompt。
- 仍缺真实云/4G、OSS/CDN live traffic、production DB/queue。
- 仍缺 Nav2/fixed-route、WAVE ROVER、HIL 和真实送达。
- ACK 仍只是 accepted/processing evidence，不是 delivery success、dropoff success、cancel completed 或 true task completion。
