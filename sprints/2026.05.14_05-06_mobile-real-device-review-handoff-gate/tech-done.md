# Sprint 2026.05.14_05-06 Mobile Real Device Review Handoff Gate - Tech Done

## Sprint 类型

- sprint_type: epic
- 收口时间：2026-05-14 06:00 Asia/Shanghai
- 证据边界：`software_proof_docker_mobile_real_device_review_handoff_gate`

## 用户价值和产品北极星

本轮把真实设备验收材料从上一轮 acceptance decision 推进到可交接人工评审的 review handoff package。普通用户、测试同学和支持同学可以看到 reviewer checklist、decision status、review owner/status、evidence blocker、next required evidence、redaction status、source boundary、ACK-not-delivery 和 `not_proven`，而不是直接面对 raw JSON、ROS topic 或云端内部字段。

产品北极星保持不变：手机是普通用户唯一入口。本轮没有真实 iPhone/Android、production app、真实 PWA install prompt/user choice、真实云、真实 4G、OSS/CDN live traffic、WAVE ROVER、HIL 或真实 delivery，因此只能收口为 Docker/local mobile software proof + robot metadata-only fence。

## OKR 映射

- Objective 4 KR5/KR7：真实设备验收材料从 decision gate 推进到人工评审交接包，支持 owner/status/checklist/blocker/next evidence 的手机首屏展示和 phone-safe 复制。
- Objective 5：本轮没有真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue connectivity 或 production worker/migration，保持约 68%。
- Objective 1/2/3：本轮没有硬件、导航、任务状态机、WAVE ROVER、串口、HIL、Nav2/fixed-route 或真实送达材料，不调整。

## 实际改动

Task A Full-stack 已完成：

- `mobile/web/index.html`
- `mobile/web/app.js`
- `mobile/web/styles.css`
- `mobile/fixtures/mobile_web_status.fixture.json`
- `mobile/test_mobile_web_entrypoint.py`
- `mobile/README.md`
- `docs/product/mobile_user_flow.md`

实现内容：

- 新增 `mobile_real_device_review_handoff`、`mobile_real_device_review_handoff_summary`、`mobile_real_device_review_handoff_package` 的 PWA 消费、派生、展示和复制包。
- 从 `mobile_real_device_acceptance_decision*` 派生 review handoff。
- 首屏展示 reviewer checklist、decision status、review owner/status、evidence blocker、next required evidence、redaction status、source boundary、ACK-not-delivery 和 `not_proven`。
- copy package 过滤敏感字段；Start/Confirm/Cancel 继续 fail closed。

Task B Robot 已完成：

- `onboard/src/ros2_trashbot_behavior/test/test_remote_bridge.py`
- `onboard/src/ros2_trashbot_behavior/test/test_remote_bridge_protocol.py`
- `docs/interfaces/ros_contracts.md`

实现内容：

- 新增 `mobile_real_device_review_handoff*` metadata-only response fence。
- 无 command envelope 时不触发 collect/dropoff/cancel/ACK/cursor，不写 terminal ACK、production readiness、HIL、dropoff/cancel completion 或 delivery success。
- valid command mixed metadata 只执行 command envelope。
- protocol normalization 不让 review handoff metadata 进入 normalized command。
- 文档明确该 metadata 只服务 phone/support/product review handoff，不进入 robot control semantics。

Task C Product 已完成：

- `OKR.md`
- `docs/process/okr_progress_log.md`
- `sprints/2026.05.14_05-06_mobile-real-device-review-handoff-gate/tech-done.md`
- `sprints/2026.05.14_05-06_mobile-real-device-review-handoff-gate/side2side_check.md`
- `sprints/2026.05.14_05-06_mobile-real-device-review-handoff-gate/final.md`

## 验证结果

Task A Full-stack 返回验证：

```text
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest mobile.test_mobile_web_entrypoint
Ran 26 tests in 0.018s
OK

PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile mobile/test_mobile_web_entrypoint.py
pass

node --check mobile/web/app.js
pass

rg review handoff / not_proven / evidence boundary checks
pass

git diff --check scoped to Task A files
pass
```

Task B Robot 返回验证：

```text
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_remote_bridge.py onboard/src/ros2_trashbot_behavior/test/test_remote_bridge_protocol.py
Ran 141 tests in 72.434s
OK

PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile onboard/src/ros2_trashbot_behavior/test/test_remote_bridge.py onboard/src/ros2_trashbot_behavior/test/test_remote_bridge_protocol.py
pass

rg metadata-only / delivery success / production readiness / HIL checks
pass

git diff --check scoped to Task B files
pass
```

Task C Product 本地验收命令结果写入 `final.md`。

## 失败定位

- Task A 首次 unit run 因 fixture copy 出现 literal sensitive field names 失败，已改为 category-level wording 并复验通过。
- Task B 未返回失败。
- Task C closeout 未修改 mobile、onboard 或 `docs/interfaces/ros_contracts.md`。

## 剩余风险

- `software_proof_docker_mobile_real_device_review_handoff_gate` 只证明 Docker/local mobile software proof + robot metadata-only fence。
- review handoff package 是人工评审交接材料，不是验收通过。
- 未证明真实 iPhone/Android、真实手机浏览器行为、production app、真实 PWA install prompt/user choice、真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、production worker/migration、WAVE ROVER、串口、HIL、Nav2/fixed-route、真实 dropoff/cancel completion 或 delivery success。

## 文档同步与工程质量监管

- Full-stack 已同步 `docs/product/mobile_user_flow.md` 与 `mobile/README.md`。
- Robot 已同步 `docs/interfaces/ros_contracts.md`。
- Product 已同步 `OKR.md`、`docs/process/okr_progress_log.md` 和本 sprint closeout。
- 本轮 Product closeout 未直接审查所有代码注释比例；Task A/B 验证与 scoped diff check 已通过，后续若进入代码评审，应继续检查新增技术注释是否保持中文且满足项目规范。
