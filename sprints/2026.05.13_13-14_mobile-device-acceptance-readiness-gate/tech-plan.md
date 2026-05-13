# Sprint 2026.05.13_13-14 Mobile Device Acceptance Readiness Gate - Tech Plan

## OKR 最低优先级核对

1. 当前 `OKR.md` 4.1 最低 Objective：Objective 4，约 64%。
2. 本 sprint 是否针对最低 Objective：是。
3. 依据：Objective 5 在 `2026.05.13_12-13_cloud-db-queue-external-probe-gate` 后约 65%，Objective 4 的主要缺口仍是手机设备/browser、production app、真实 PWA install prompt 和真实用户可用体验证据。

## 技术方案

### Task A - Full-Stack Mobile Gate

文件范围：

- `mobile/web/index.html`
- `mobile/web/app.js`
- `mobile/web/styles.css`
- `mobile/fixtures/mobile_web_status.fixture.json`
- `mobile/test_mobile_web_entrypoint.py`
- `mobile/README.md`
- `docs/product/mobile_user_flow.md`

实现：

- 新增 `mobileDeviceAcceptanceReadinessFromStatus(status, readiness, diagnostics)` helper，优先消费 `mobile_device_acceptance_readiness`、`phone_device_acceptance_readiness`、`mobile_browser_acceptance_readiness`。
- 缺失时返回 blocked 默认摘要，证据边界为 `software_proof_docker_mobile_device_acceptance_readiness_gate`。
- 首页新增 panel，展示 viewport/touch/PWA/offline/diagnostics/cloud gate、production app readiness、recovery hint、ACK 语义和 evidence boundary。
- 主操作 gate 额外要求 `primary_actions_enabled=true` 且 `production_app_ready=true` 或后端显式 `safe_to_control=true`；缺失或 blocked 时 fail closed。

验收命令：

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest mobile.test_mobile_web_entrypoint
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile mobile/test_mobile_web_entrypoint.py
git diff --check -- mobile/web/index.html mobile/web/app.js mobile/web/styles.css mobile/fixtures/mobile_web_status.fixture.json mobile/test_mobile_web_entrypoint.py mobile/README.md docs/product/mobile_user_flow.md
```

### Task B - Robot Metadata Compatibility Fence

文件范围：

- `onboard/src/ros2_trashbot_behavior/test/test_remote_bridge.py`
- `onboard/src/ros2_trashbot_behavior/test/test_remote_bridge_protocol.py`
- `docs/interfaces/ros_contracts.md`

实现：

- 增加 metadata-only response fixtures，覆盖 `mobile_device_acceptance_readiness`、`phone_device_acceptance_readiness`、`mobile_browser_acceptance_readiness`。
- 断言无 valid `trashbot.remote.v1` command 时，不触发 backend action、不 POST ACK、不推进或持久化 cursor。
- 文档说明这些字段是 phone/support metadata，不属于 command/status/ACK envelope。

验收命令：

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_remote_bridge.py onboard/src/ros2_trashbot_behavior/test/test_remote_bridge_protocol.py
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile onboard/src/ros2_trashbot_behavior/test/test_remote_bridge.py onboard/src/ros2_trashbot_behavior/test/test_remote_bridge_protocol.py
git diff --check -- onboard/src/ros2_trashbot_behavior/test/test_remote_bridge.py onboard/src/ros2_trashbot_behavior/test/test_remote_bridge_protocol.py docs/interfaces/ros_contracts.md
```

### Task C - Product Closeout

文件范围：

- `OKR.md`
- `docs/process/okr_progress_log.md`
- `sprints/2026.05.13_13-14_mobile-device-acceptance-readiness-gate/tech-done.md`
- `sprints/2026.05.13_13-14_mobile-device-acceptance-readiness-gate/side2side_check.md`
- `sprints/2026.05.13_13-14_mobile-device-acceptance-readiness-gate/final.md`

实现：

- 汇总 Task A/B 证据，更新 Objective 4 进度和边界。
- 明确本轮仍不证明真实手机设备/browser、production app、真实云/4G、OSS/CDN live traffic、Nav2/fixed-route、WAVE ROVER、HIL 或真实送达。
- 验证所有引用路径存在。

验收命令：

```bash
test -f OKR.md && test -f docs/process/okr_progress_log.md && test -f docs/product/mobile_user_flow.md && test -f docs/interfaces/ros_contracts.md
git diff --check -- OKR.md docs/process/okr_progress_log.md sprints/2026.05.13_13-14_mobile-device-acceptance-readiness-gate
```

## 风险边界

- Docker/local software proof 只能证明手机入口消费 phone-safe readiness 并保持动作 fail closed。
- 本轮不运行真实手机、真实浏览器设备、真实云/4G、Nav2、WAVE ROVER 或 HIL。
- ACK 仍是 accepted/processing evidence，不是 delivery success。
