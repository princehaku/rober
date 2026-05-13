# Sprint 2026.05.13_15-16 Mobile Browser Acceptance Bundle Gate - Tech Done

## Sprint 声明

- sprint_type: epic
- closeout_time: 2026-05-13 15:19 Asia/Shanghai
- status: done
- evidence_boundary: `software_proof_docker_mobile_browser_acceptance_bundle_gate`

## 用户价值和产品北极星

普通手机用户、测试者和售后支持现在可以在手机首屏看到并复制一份浏览器验收包，知道当前本地/Docker browser gate 能证明什么、哪些真实验收仍缺失，以及为什么 Start/Confirm/Cancel 仍被保守禁用。

产品北极星保持不变：普通用户只用手机完成垃圾交付；当系统尚未达到真实设备验收时，手机必须清楚解释边界、阻止误操作，并提供可复盘的支持交接材料。

## OKR 映射和 KR 拆解

- Objective 4 KR1：手机最小流程补齐“浏览器验收包/验收证据”入口。
- Objective 4 KR4：远程诊断最小数据包推进为可复制、脱敏的 phone/support metadata。
- Objective 4 KR5：普通用户无需命令行、ROS2、串口或硬件调试，也能知道当前为什么不能发车。
- Objective 4 KR7：手机首屏继续向中文优先、主路径清晰、fail-closed 的用户体验推进。

本轮只形成 Docker/local software proof，不更新 Objective 1/2/3/5。

## 本轮核心抓手

1. Full-stack 将已有 readiness、offline、diagnostics、cloud gate、action feedback 与 ACK 语义组织成手机首屏“浏览器验收包”。
2. Robot 补 metadata-only compatibility fence，保证 bundle 字段不进入 command/status/ACK envelope。
3. Product closeout 保守更新 Objective 4，并明确真实手机/browser、production app、真实 PWA install prompt 等缺口仍未关闭。

## 实际改动

Task A - Full-stack Mobile Browser Acceptance Bundle Gate：

- `mobile/web/index.html`
- `mobile/web/app.js`
- `mobile/web/styles.css`
- `mobile/fixtures/mobile_web_status.fixture.json`
- `mobile/test_mobile_web_entrypoint.py`
- `mobile/README.md`
- `docs/product/mobile_user_flow.md`

实现结果：

- 首屏新增“浏览器验收包”面板和复制入口。
- 优先消费 `mobile_browser_acceptance_bundle`、`phone_browser_acceptance_bundle`、`mobile_acceptance_evidence_bundle`，缺失时从 phone-safe fields 派生 blocked 摘要。
- 缺少真实手机/browser、production app、真实 PWA install prompt 时保持 blocked-by-design。
- Start/Confirm/Cancel fail closed，Diagnostics/Support Handoff 可用。
- ACK 文案保持 accepted/processing evidence，不写成 delivery success。

Task B - Robot Metadata Compatibility Fence：

- `onboard/src/ros2_trashbot_behavior/test/test_remote_bridge.py`
- `onboard/src/ros2_trashbot_behavior/test/test_remote_bridge_protocol.py`
- `docs/interfaces/ros_contracts.md`

实现结果：

- 加入 `mobile_browser_acceptance_bundle`、`phone_browser_acceptance_bundle`、`mobile_acceptance_evidence_bundle` metadata-only fences。
- 证明 metadata-only responses 不调用 backend action、不 POST ACK、不推进内存 cursor、不持久化 `last_terminal_ack_id`。
- 证明 protocol normalization 不把 bundle 放进 command envelope。
- ROS contract 明确这些字段只属于 phone/support metadata。

Task C - Product Closeout：

- `OKR.md`
- `docs/process/okr_progress_log.md`
- `sprints/2026.05.13_15-16_mobile-browser-acceptance-bundle-gate/tech-done.md`
- `sprints/2026.05.13_15-16_mobile-browser-acceptance-bundle-gate/side2side_check.md`
- `sprints/2026.05.13_15-16_mobile-browser-acceptance-bundle-gate/final.md`

实现结果：

- Objective 4 从约 66% 保守上调到约 68%。
- Objective 1/2/3/5 不调整。
- 进度日志顶部追加本轮记录。
- sprint closeout 明确本轮不是真实手机/browser、production app、真实 PWA install prompt、真实云/4G、OSS/CDN live traffic、production DB/queue、Nav2/fixed-route、WAVE ROVER、HIL 或真实送达。

## 验证结果

Task A 已返回：

```text
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest mobile.test_mobile_web_entrypoint
Ran 12 tests in 0.005s
OK

PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile mobile/test_mobile_web_entrypoint.py
exit 0

git diff --check -- mobile/web/index.html mobile/web/app.js mobile/web/styles.css mobile/fixtures/mobile_web_status.fixture.json mobile/test_mobile_web_entrypoint.py mobile/README.md docs/product/mobile_user_flow.md
exit 0
```

Task B 已返回：

```text
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_remote_bridge.py onboard/src/ros2_trashbot_behavior/test/test_remote_bridge_protocol.py
Ran 92 tests in 46.536s
OK

PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile onboard/src/ros2_trashbot_behavior/test/test_remote_bridge.py onboard/src/ros2_trashbot_behavior/test/test_remote_bridge_protocol.py
exit 0

git diff --check -- onboard/src/ros2_trashbot_behavior/test/test_remote_bridge.py onboard/src/ros2_trashbot_behavior/test/test_remote_bridge_protocol.py docs/interfaces/ros_contracts.md
exit 0
```

Task C 验收命令：

```text
test -f OKR.md && test -f docs/process/okr_progress_log.md && test -f docs/product/mobile_user_flow.md && test -f docs/interfaces/ros_contracts.md
exit 0

git diff --check -- OKR.md docs/process/okr_progress_log.md sprints/2026.05.13_15-16_mobile-browser-acceptance-bundle-gate
exit 0
```

## 偏差

- 无范围偏差：Task C 只更新 closeout、OKR 和进度日志文件。
- 未追加真实设备、真实云、真实机器人或 HIL 证据。
- 未改 Task A/B implementation files。

## 剩余风险

- 仍缺真实手机/browser、production app、真实 PWA install prompt。
- 仍缺真实云/4G、OSS/CDN live traffic、production DB/queue。
- 仍缺 Nav2/fixed-route、WAVE ROVER、HIL 和真实送达。
- ACK 仍只是 accepted/processing evidence，不是 delivery success。
