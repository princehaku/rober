# Sprint 2026.05.13_16-17 Mobile Web Browser Proof Gate - Final

## 结论

本 sprint 完成 Objective 4 的 `mobile/web` real local Chromium-family browser proof。Task A/B 的实现和验证证据足够支持 Objective 4 从约 68% 保守上调到约 70%；Objective 1/2/3/5 不调整。

证据边界是 `software_proof_docker_mobile_web_browser_proof_gate`。本轮不是真实 iPhone/Android device behavior、production app、真实 PWA install prompt、真实云/4G、OSS/CDN live traffic、production DB/queue、Nav2/fixed-route、WAVE ROVER、HIL 或真实送达。

## 用户价值和产品北极星

用户价值：测试者或售后支持可以用真实本地 Chrome 打开当前 `mobile/web/` PWA，拿到 390x844 与 768x900 截图、JSON 和 summary，确认手机首屏、浏览器验收包、Diagnostics、Support Handoff 和 fail-closed 主操作在真实浏览器里成立。

产品北极星：普通用户只用手机完成垃圾交付；在真实设备和生产链路未闭环前，手机入口必须可验证、可解释、可交接、fail closed，而不是把 ACK 或本地 proof 误写成真实送达。

## OKR 映射和进度

- Objective 4 KR1：手机流程从当前 `mobile/web/` 静态入口推进到真实本地 browser proof。
- Objective 4 KR4：browser evidence summary 和 acceptance bundle 成为可交接的诊断材料。
- Objective 4 KR5：普通用户可在浏览器首屏理解阻塞原因，不需要命令行、ROS2 或硬件知识。
- Objective 4 KR7：真实本地 browser 证明主流手机尺寸下 touch target、overflow、overlap、ACK copy、Diagnostics、Support Handoff 和 fail-closed action gate 均通过。

OKR 更新：

- Objective 4：约 68% -> 约 70%。
- Objective 1/2/3/5：不调整。

## 实际改动

Task A Full-stack 已完成：

- `pc-tools/evidence/phone_browser_acceptance_gate.py`
- `mobile/README.md`
- `docs/product/mobile_user_flow.md`
- `mobile/test_mobile_web_entrypoint.py`
- `sprints/2026.05.13_16-17_mobile-web-browser-proof-gate/evidence/mobile_web_browser_390x844.json`
- `sprints/2026.05.13_16-17_mobile-web-browser-proof-gate/evidence/mobile_web_browser_390x844.png`
- `sprints/2026.05.13_16-17_mobile-web-browser-proof-gate/evidence/mobile_web_browser_768x900.json`
- `sprints/2026.05.13_16-17_mobile-web-browser-proof-gate/evidence/mobile_web_browser_768x900.png`
- `sprints/2026.05.13_16-17_mobile-web-browser-proof-gate/evidence/mobile_web_browser_acceptance_summary.json`

Task B Robot 已完成：

- `docs/interfaces/ros_contracts.md`
- `onboard/src/ros2_trashbot_behavior/test/test_remote_bridge.py`
- `onboard/src/ros2_trashbot_behavior/test/test_remote_bridge_protocol.py`

Task C Product Closeout 已完成：

- `OKR.md`
- `docs/process/okr_progress_log.md`
- `sprints/2026.05.13_16-17_mobile-web-browser-proof-gate/tech-done.md`
- `sprints/2026.05.13_16-17_mobile-web-browser-proof-gate/side2side_check.md`
- `sprints/2026.05.13_16-17_mobile-web-browser-proof-gate/final.md`

## 验证结果

Task A 返回：

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

Task B 返回：

```text
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_remote_bridge.py onboard/src/ros2_trashbot_behavior/test/test_remote_bridge_protocol.py
Ran 94 tests in 47.671s
OK

PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile onboard/src/ros2_trashbot_behavior/test/test_remote_bridge.py onboard/src/ros2_trashbot_behavior/test/test_remote_bridge_protocol.py
exit 0

git diff --check -- docs/interfaces/ros_contracts.md onboard/src/ros2_trashbot_behavior/test/test_remote_bridge.py onboard/src/ros2_trashbot_behavior/test/test_remote_bridge_protocol.py
exit 0
```

Task C closeout 验收：

```text
test -f OKR.md && test -f docs/process/okr_progress_log.md && test -f docs/product/mobile_user_flow.md && test -f docs/interfaces/ros_contracts.md
exit 0

git diff --check -- OKR.md docs/process/okr_progress_log.md sprints/2026.05.13_16-17_mobile-web-browser-proof-gate
exit 0
```

## 风险和阻塞

- 仍缺真实 iPhone/Android device behavior、production app、真实 PWA install prompt。
- 仍缺真实云/4G、OSS/CDN live traffic、production DB/queue。
- 仍缺 Nav2/fixed-route、WAVE ROVER、HIL 和真实送达。
- ACK 仍只是 accepted/processing evidence，不是 delivery success、dropoff success、cancel completed 或 true task completion。
- 本轮未独立复跑 Task A/B 的工程测试；Product closeout 采用 A/B worker 返回的验证证据，并执行 sprint closeout 文件验收。

## 下一步

Objective 4 上调后，当前最低完成度为 Objective 5（约 67%）。如果继续 Objective 5，下一轮必须引入真实 OSS/CDN、4G/SIM、云账号或 production DB/queue 外部证据，避免继续增加本地 metadata 深度；如果外部环境仍不可用，应回到 Objective 4 的真实手机设备/browser、production app 或 PWA install prompt 验收缺口，除非 CEO 明确指定其他优先级。
