# Sprint 2026.05.13_13-14 Mobile Device Acceptance Readiness Gate - Tech Done

## Sprint 声明

- sprint_type: epic
- 主目标：Objective 4 手机用户体验与低成本量产边界。
- 证据边界：`software_proof_docker_mobile_device_acceptance_readiness_gate`。
- 当前时间：2026-05-13 13:12 Asia/Shanghai。

## 实际改动

### Task A - Full-stack Mobile Gate

责任 Engineer：`full-stack-software-engineer`。

改动文件：

- `mobile/web/index.html`
- `mobile/web/app.js`
- `mobile/web/styles.css`
- `mobile/fixtures/mobile_web_status.fixture.json`
- `mobile/test_mobile_web_entrypoint.py`
- `mobile/README.md`
- `docs/product/mobile_user_flow.md`

结果：

- 手机首屏新增“手机验收准备”面板，展示 viewport/touch、PWA/offline、diagnostics/cloud gate、production app readiness、恢复建议、ACK 语义和 `software_proof_docker_mobile_device_acceptance_readiness_gate`。
- 缺真实手机/browser、production app 或真实 PWA install prompt 时，Start/Confirm/Cancel 继续 fail closed。
- Diagnostics 和 Support Handoff 仍可见，支持用户或售后在动作禁用时复制安全诊断信息。

### Task B - Robot Metadata Compatibility Fence

责任 Engineer：`robot-software-engineer`。

改动文件：

- `onboard/src/ros2_trashbot_behavior/test/test_remote_bridge.py`
- `onboard/src/ros2_trashbot_behavior/test/test_remote_bridge_protocol.py`
- `docs/interfaces/ros_contracts.md`

结果：

- remote bridge/protocol metadata-only fixtures 覆盖 `mobile_device_acceptance_readiness`、`phone_device_acceptance_readiness`、`mobile_browser_acceptance_readiness`。
- 证明这些字段不触发 collect/dropoff/cancel、不 POST ACK、不推进或持久化 `last_terminal_ack_id`。
- 接口文档明确这些字段是 phone/support metadata，不属于 command/status/ACK envelope。

### Task C - Product Closeout

责任 Owner：`product-okr-owner`。

改动文件：

- `OKR.md`
- `docs/process/okr_progress_log.md`
- `sprints/2026.05.13_13-14_mobile-device-acceptance-readiness-gate/tech-done.md`
- `sprints/2026.05.13_13-14_mobile-device-acceptance-readiness-gate/side2side_check.md`
- `sprints/2026.05.13_13-14_mobile-device-acceptance-readiness-gate/final.md`

结果：

- Objective 4 从约 64% 保守上调到约 66%。
- Objective 1/2/3/5 不调整。
- closeout 明确本轮只形成 Docker/local software proof，不声明真实手机设备/browser、production app、真实 PWA install prompt、真实云/4G、OSS/CDN live traffic、production DB/queue、Nav2/fixed-route、WAVE ROVER、HIL 或真实送达。

## 验证结果

### Task A 验证

```text
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest mobile.test_mobile_web_entrypoint
Ran 11 tests OK

PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile mobile/test_mobile_web_entrypoint.py
OK

git diff --check -- mobile/web/index.html mobile/web/app.js mobile/web/styles.css mobile/fixtures/mobile_web_status.fixture.json mobile/test_mobile_web_entrypoint.py mobile/README.md docs/product/mobile_user_flow.md
OK
```

### Task B 验证

```text
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_remote_bridge.py onboard/src/ros2_trashbot_behavior/test/test_remote_bridge_protocol.py
Ran 85 tests OK

PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile onboard/src/ros2_trashbot_behavior/test/test_remote_bridge.py onboard/src/ros2_trashbot_behavior/test/test_remote_bridge_protocol.py
OK

git diff --check -- onboard/src/ros2_trashbot_behavior/test/test_remote_bridge.py onboard/src/ros2_trashbot_behavior/test/test_remote_bridge_protocol.py docs/interfaces/ros_contracts.md
OK
```

### Task C 验收命令

```text
test -f OKR.md && test -f docs/process/okr_progress_log.md && test -f docs/product/mobile_user_flow.md && test -f docs/interfaces/ros_contracts.md
exit 0

git diff --check -- OKR.md docs/process/okr_progress_log.md sprints/2026.05.13_13-14_mobile-device-acceptance-readiness-gate
exit 0
```

## 偏差

- 无代码或测试改动由 Task C 执行。
- 本轮 closeout 使用 Task A/B 已返回的验证摘要作为工程证据，Task C 只运行计划指定的路径存在与 scoped diff check 验收。

## 剩余风险

- 没有真实手机设备/browser 验收。
- 没有 production app、账号、登录、应用商店打包或真实 PWA install prompt。
- 没有真实云/4G、OSS/CDN live traffic、production DB/queue。
- 没有 Nav2/fixed-route、WAVE ROVER、HIL 或真实送达。
- ACK 仍只是 accepted/processing evidence，不是 delivery success。
