# Sprint 2026.05.14_11-12 Mobile Field Trial Runbook Execution Gate - Tech Done

## Sprint Type

sprint_type: epic

## 实际改动

Task A - User Touchpoint Full-Stack Engineer：

- `mobile/web/index.html`：首屏新增“现场试跑执行清单”panel，展示 readiness、open items、八项 execution checklist、`safe_to_control=false`、ACK 非 delivery success、`not_proven` 与 evidence boundary。
- `mobile/web/app.js`：新增 `mobile_real_device_field_trial_runbook_execution`、`mobile_real_device_field_trial_runbook_execution_summary`、`mobile_real_device_field_trial_runbook_execution_copy` 的派生、归一化、渲染和 whitelist-only copy payload。
- `mobile/web/styles.css`：补齐 runbook execution panel 的移动端/桌面布局。
- `mobile/test_mobile_web_entrypoint.py`：新增静态围栏，确认 runbook execution family 可见、可复制、覆盖八项 checklist、保持 fail-closed，且不触发 Start/Confirm/Cancel。
- `mobile/README.md`、`docs/product/mobile_user_flow.md`：同步手机端现场试跑执行清单规则、copy 白名单和证据边界。

Task B - Robot Platform Engineer：

- `onboard/src/ros2_trashbot_behavior/test/test_remote_bridge.py`：新增 worker-level metadata-only response 与 mixed valid-command coverage，证明 runbook execution metadata 不驱动 robot action、ACK、cursor、terminal ACK、production readiness、HIL、dropoff/cancel completion 或 delivery success。
- `onboard/src/ros2_trashbot_behavior/test/test_remote_bridge_protocol.py`：新增 protocol normalization coverage，证明 command envelope 外的 runbook execution metadata 被忽略，metadata-only response 不合成 command 或 ACK。
- `docs/interfaces/ros_contracts.md`：补充 `mobile_real_device_field_trial_runbook_execution*` family 的 phone/support/product metadata-only 合同。

Task C - Product Closeout：

- `tech-done.md`、`side2side_check.md`、`final.md`：完成 sprint closeout。
- `OKR.md`：更新 4.1 当前快照和下一轮优先级口径。
- `docs/process/okr_progress_log.md`：追加本 sprint 摘要。

## 验证结果

Task A 已返回验证：

```text
python3 -m unittest mobile.test_mobile_web_entrypoint
Ran 31 tests in 0.038s
OK

python3 -m py_compile mobile/test_mobile_web_entrypoint.py
pass

node --check mobile/web/app.js
pass

required rg
pass

git diff --check -- mobile/web/index.html mobile/web/app.js mobile/web/styles.css mobile/test_mobile_web_entrypoint.py mobile/README.md docs/product/mobile_user_flow.md
pass
```

Task B 已返回验证：

```text
python3 -m unittest onboard.src.ros2_trashbot_behavior.test.test_remote_bridge onboard.src.ros2_trashbot_behavior.test.test_remote_bridge_protocol
Ran 165 tests in 84.933s
OK
ResourceWarning: one existing warning in remote bridge tests

python3 -m py_compile onboard/src/ros2_trashbot_behavior/test/test_remote_bridge.py onboard/src/ros2_trashbot_behavior/test/test_remote_bridge_protocol.py
pass

required rg
pass

git diff --check -- onboard/src/ros2_trashbot_behavior/test/test_remote_bridge.py onboard/src/ros2_trashbot_behavior/test/test_remote_bridge_protocol.py docs/interfaces/ros_contracts.md
pass
```

Task C 本地验收在本文件写入后执行：

```bash
rg -n "software_proof_docker_mobile_real_device_field_trial_runbook_execution_gate|mobile_real_device_field_trial_runbook_execution|Objective 5|Objective 4|safe_to_control=false|accepted_processing_only_not_delivery_success|not_proven|现场试跑执行" OKR.md docs/process/okr_progress_log.md sprints/2026.05.14_11-12_mobile-field-trial-runbook-execution-gate
git diff --check -- OKR.md docs/process/okr_progress_log.md sprints/2026.05.14_11-12_mobile-field-trial-runbook-execution-gate
```

## 偏差与修复

- 本轮没有真实 O5 外部材料，按 pre_start 与 tech-plan 的 stop rule 转向 Objective 4；Objective 5 不上调。
- 本轮没有真实手机、production app、真实 PWA install prompt/user choice、真实云、4G/SIM、OSS/CDN live traffic、production DB/queue、WAVE ROVER、HIL 或真实送达材料。
- Task B 验证出现一个既有 `ResourceWarning`，测试 exit 0；本轮不扩大修复范围。

## 剩余风险

- `software_proof_docker_mobile_real_device_field_trial_runbook_execution_gate` 只证明 Docker/local mobile software proof + robot metadata-only fence。
- `mobile_real_device_field_trial_runbook_execution*` 是现场试跑执行清单和 support metadata，不是真实手机验收、production app readiness、真实 PWA prompt/user choice、O5 外部 proof、HIL、dropoff/cancel completion 或 delivery success。
- 下一步若仍没有 O5 外部材料，应使用本轮清单去收集真实 iPhone/Android device behavior、production app、真实 PWA install prompt/user choice、offline/touch/visual/material redaction 的现场证据，而不是继续叠加本地 metadata。
