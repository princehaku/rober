# Sprint 2026.05.14_15-16 Mobile Current PWA Field Trial Browser Proof - Tech Done

sprint_type: epic

## 实际改动

### Task A - full-stack-software-engineer

- 更新 `pc-tools/evidence/phone_browser_acceptance_gate.py`，将 current PWA browser proof 边界刷新为 `software_proof_docker_mobile_current_pwa_field_trial_browser_proof_gate`。
- 更新 `mobile/test_mobile_web_entrypoint.py`、`mobile/README.md`、`docs/product/mobile_user_flow.md`，同步当前 field-trial 首屏组合、phone-safe copy、`safe_to_control=false`、`accepted_processing_only_not_delivery_success` 和 `not_proven` 口径。
- 生成本 sprint evidence：
  - `evidence/mobile_current_pwa_field_trial_browser_390x844.json`
  - `evidence/mobile_current_pwa_field_trial_browser_390x844.png`
  - `evidence/mobile_current_pwa_field_trial_browser_768x900.json`
  - `evidence/mobile_current_pwa_field_trial_browser_768x900.png`
  - `evidence/mobile_current_pwa_field_trial_browser_acceptance_summary.json`

### Task B - robot-software-engineer

- 更新 `onboard/src/ros2_trashbot_behavior/test/test_remote_bridge.py`、`onboard/src/ros2_trashbot_behavior/test/test_remote_bridge_protocol.py`，新增 `mobile_current_pwa_field_trial_browser_proof*` metadata-only fence。
- 更新 `docs/interfaces/ros_contracts.md`，明确该 metadata family 是 `software_proof`，不是真实手机、O5 external proof、HIL 或 delivery success。
- Robot fence 证明 metadata-only response 不触发 collect/dropoff/cancel、ACK POST、cursor advance/persistence、terminal ACK、production readiness、HIL、dropoff/cancel completion 或 delivery success；mixed valid-command 只执行合法 `trashbot.remote.v1` collect envelope。

## 验证结果

### Task A

- Browser gate：390x844 与 768x900 均 `passed=true`。
- 关键 browser summary：`current_panels_status=passed`、`current_boundaries_status=passed`、`field_trial_package_visible=true`、`field_trial_review_visible=true`、`field_trial_runbook_execution_visible=true`、`field_trial_evidence_record_visible=true`、`field_trial_evidence_verdict_visible=true`、`field_trial_retest_execution_visible=true`、`primary_actions_disabled=true`、`phone_safe_status=passed`。
- `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest mobile.test_mobile_web_entrypoint`：`Ran 34 tests ... OK`。
- `py_compile` pass。
- 指定 `rg` pass。
- scoped `git diff --check` pass。

### Task B

- `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_remote_bridge.py onboard/src/ros2_trashbot_behavior/test/test_remote_bridge_protocol.py`：`Ran 180 tests in 93.287s OK`。
- `py_compile` pass。
- 指定 `rg` pass。
- scoped `git diff --check` pass。

## 偏差与失败定位

- 无实现失败需要 Product 继续派修。
- 本轮没有修改真实控制语义、ACK POST 语义、cursor persistence、terminal ACK 或 production readiness。
- 本轮没有新增 O4 metadata panel，也没有新增 O5 本地 metadata rung。

## 剩余风险

- `software_proof_docker_mobile_current_pwa_field_trial_browser_proof_gate` 只证明本地 Chromium-family browser proof 和 robot metadata-only fence。
- 仍未证明真实 iPhone/Android、production app、真实 PWA install prompt/user choice、O5 external proof、公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、Nav2/fixed-route、WAVE ROVER、HIL、dropoff/cancel completion 或 delivery success。
