# Sprint 2026.05.14_04-05 Mobile Real Device Acceptance Decision Gate - Tech Done

## Sprint 类型

- sprint_type: epic
- 收口时间：2026-05-14 04:15 Asia/Shanghai
- 证据边界：`software_proof_docker_mobile_real_device_acceptance_decision_gate`

## 用户价值和产品北极星

用户价值是把上一轮已导入的真实设备验收材料，从“收到材料”推进到“能判定能否进入人工评审”。普通手机用户、支持同学和工程同学看到的是 decision、blocker list、next required evidence、redaction status 和 `not_proven`，而不是把 ACK、intake package 或本地浏览器 metadata 误解为真实设备验收通过。

产品北极星不变：手机是普通用户唯一入口；用户不需要理解 SSH、ROS2、串口、raw JSON、云端内部设施或机器人控制协议，也能知道当前为什么不能发车、还缺什么证据、什么时候需要人工支持。

## OKR 映射

- Objective 4 KR5：用户验收标准从材料收集推进到材料判定，明确 `accepted_for_review` 只表示可进入人工评审。
- Objective 4 KR7：围绕真实 iPhone/Android、production app、真实 PWA install prompt/user choice、viewport/browser 和首屏可交互证据建立 phone-safe decision gate。
- Objective 5：本轮没有真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue connectivity、production worker/migration 或真实外部 O5 材料，不提升 O5。

## 实际改动

### Task A - Full-stack

Task A 已由 `full-stack-software-engineer` 完成。改动文件：

- `mobile/web/index.html`
- `mobile/web/app.js`
- `mobile/web/styles.css`
- `mobile/fixtures/mobile_web_status.fixture.json`
- `mobile/test_mobile_web_entrypoint.py`
- `mobile/README.md`
- `docs/product/mobile_user_flow.md`

实现结果：

- `mobile/web` 首屏新增“真实设备验收决策”panel。
- 消费或派生 `mobile_real_device_acceptance_decision`、`mobile_real_device_acceptance_decision_summary`、`mobile_real_device_acceptance_decision_package`。
- 展示 `accepted_for_review`、`blocked_missing_evidence`、`rejected_unsafe_or_unredacted`、blocker list、next required evidence、redaction status、source boundary、ACK semantics 和 `not_proven`。
- `accepted_for_review` 只表示材料可进入人工评审，不等于真实设备、production app、PWA prompt/user choice 或 delivery success 已通过。

Task A 验证结果：

```text
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest mobile.test_mobile_web_entrypoint
Ran 25 tests ... OK

PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile mobile/test_mobile_web_entrypoint.py
pass

node --check mobile/web/app.js
pass

rg ... mobile docs/product/mobile_user_flow.md
pass

git diff --check -- mobile/web/index.html mobile/web/app.js mobile/web/styles.css mobile/fixtures/mobile_web_status.fixture.json mobile/test_mobile_web_entrypoint.py mobile/README.md docs/product/mobile_user_flow.md sprints/2026.05.14_04-05_mobile-real-device-acceptance-decision-gate/tech-done.md
pass
```

### Task B - Robot

Task B 已由 `robot-software-engineer` 完成。改动文件：

- `onboard/src/ros2_trashbot_behavior/test/test_remote_bridge.py`
- `onboard/src/ros2_trashbot_behavior/test/test_remote_bridge_protocol.py`
- `docs/interfaces/ros_contracts.md`

实现结果：

- 增加 `mobile_real_device_acceptance_decision*` metadata-only fence。
- 证明 metadata-only response 不触发 collect、confirm_dropoff、cancel、ACK POST、cursor advance、cursor persistence、terminal ACK、production readiness、HIL、dropoff success、cancel completed 或 delivery success。
- 证明 valid command mixed metadata 时只执行 command envelope，acceptance decision metadata 不进入 normalized command、ACK、status、cursor 或 terminal result。

Task B 验证结果：

```text
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_remote_bridge.py onboard/src/ros2_trashbot_behavior/test/test_remote_bridge_protocol.py
Ran 137 tests in 70.310s OK

PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile onboard/src/ros2_trashbot_behavior/test/test_remote_bridge.py onboard/src/ros2_trashbot_behavior/test/test_remote_bridge_protocol.py
pass

rg ... onboard/src/ros2_trashbot_behavior/test docs/interfaces/ros_contracts.md
pass

git diff --check -- onboard/src/ros2_trashbot_behavior/test/test_remote_bridge.py onboard/src/ros2_trashbot_behavior/test/test_remote_bridge_protocol.py docs/interfaces/ros_contracts.md sprints/2026.05.14_04-05_mobile-real-device-acceptance-decision-gate/tech-done.md
pass
```

### Task C - Product

Task C 本次完成 closeout、OKR 和 progress log 更新。改动文件：

- `OKR.md`
- `docs/process/okr_progress_log.md`
- `sprints/2026.05.14_04-05_mobile-real-device-acceptance-decision-gate/tech-done.md`
- `sprints/2026.05.14_04-05_mobile-real-device-acceptance-decision-gate/side2side_check.md`
- `sprints/2026.05.14_04-05_mobile-real-device-acceptance-decision-gate/final.md`

## 优先级和验收口径

- P0 已完成：decision gate fail closed，缺材料、材料不安全、redaction 未通过、仍缺真实设备/PWA/production app 时不能打开 Start/Confirm/Cancel。
- P0 已完成：Robot fence 证明 metadata-only response 不污染 command、ACK、cursor、terminal result、success 或 production readiness。
- P1 已完成：decision package 仅作为 phone-safe metadata，保留 blocker、next required evidence、source boundary 和 `not_proven`。
- P1 已完成：产品 closeout 明确 `software_proof_docker_mobile_real_device_acceptance_decision_gate` 不是真实设备、production app、PWA prompt/user choice、O5 外部材料、HIL 或 delivery success。

## 失败定位

Task C closeout 验收未发现失败项。Task A/B 返回结果中没有需要 Product 重新派修的失败；本次未运行 Task A/B 的实现测试，只核对其返回证据并运行 Task C 规定的 closeout 验收命令。

## 剩余风险

- 真实手机设备、真实 iPhone/Android device behavior、production app、真实 PWA install prompt/user choice 仍未证明。
- Objective 5 仍缺真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue connectivity、production worker/migration 或其他真实外部材料。
- Nav2/fixed-route、WAVE ROVER、HIL、真实 dropoff/cancel completion 和真实 delivery success 仍未证明。
- `accepted_for_review` 只能进入人工评审，不是验收通过；ACK、HTTP accepted、receipt、intake package、decision package、browser proof、handoff session 和 install prompt evidence 都不是 delivery success。

## OKR 最低优先级核对

Objective 5 仍是最低完成度，约 68%。本 sprint 不推进 O5 的理由在收口时仍成立：本机没有真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue connectivity 或 production worker/migration 材料。继续堆本地 O5 metadata 会重复消费同一外部证据 blocker；本轮实际推进的是 Objective 4 的真实设备验收决策门。
