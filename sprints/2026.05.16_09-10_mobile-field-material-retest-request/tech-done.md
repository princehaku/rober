# Sprint 2026.05.16_09-10 Mobile Field Material Retest Request - Tech Done

sprint_type: epic

## 1. 实际改动

本轮完成 `software_proof_docker_mobile_field_material_retest_request_gate`，把 08-09 的 `mobile_field_material_review_decision` 评审结果推进为可执行的 route/elevator field retest request。该请求面向下一次现场复测，明确 blockers、next-required-evidence、route/elevator material checklist、owner handoff、same `evidence_ref` 要求和 phone-safe 展示边界。

Task A Autonomy Algorithm Engineer 已完成：

- 新增 `pc-tools/evidence/mobile_field_material_retest_request.py`。
- 新增 `pc-tools/evidence/test_mobile_field_material_retest_request.py`。
- 更新 `pc-tools/README.md`。
- 更新 `docs/navigation/fixed_route_workflow.md`。
- 首次测试发现 unsupported wrapper-schema gap，已修复并复验。

Task B Robot Platform Engineer 已完成：

- 更新 `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py`。
- 更新 `onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`。
- 更新 `docs/interfaces/ros_contracts.md`。
- 新增 `mobile_field_material_retest_request` / summary diagnostics metadata-only consumer，保持 fail-closed 和 no-command 边界。

Task C User Touchpoint Full-Stack Engineer 已完成：

- 更新 `mobile/web/index.html`。
- 更新 `mobile/web/app.js`。
- 更新 `mobile/web/styles.css`。
- 更新 `mobile/fixtures/mobile_web_status.fixture.json`。
- 更新 `mobile/test_mobile_web_entrypoint.py`。
- 更新 `docs/product/mobile_user_flow.md`。
- 新增 first-screen 只读“现场复测请求”panel，Start / Confirm Dropoff / Cancel gating 未改变。

Task D Product Manager / OKR Owner 已完成：

- 新增本文件。
- 新增 `side2side_check.md`。
- 新增 `final.md`。
- 更新 `OKR.md` 当前进度快照。
- 更新 `docs/process/okr_progress_log.md`。

## 2. 验证结果

Task A worker 返回验证：

```text
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile pc-tools/evidence/mobile_field_material_retest_request.py pc-tools/evidence/test_mobile_field_material_retest_request.py
passed

PYTHONDONTWRITEBYTECODE=1 python3 pc-tools/evidence/test_mobile_field_material_retest_request.py
Ran 6 tests ... OK

python3 pc-tools/evidence/mobile_field_material_retest_request.py --help
passed

required rg
passed

git diff --check -- pc-tools/evidence/mobile_field_material_retest_request.py pc-tools/evidence/test_mobile_field_material_retest_request.py pc-tools/README.md docs/navigation/fixed_route_workflow.md
passed
```

Task B worker 返回验证：

```text
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py
Ran 91 tests ... OK

PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py
passed

required rg
passed

git diff --check -- onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py docs/interfaces/ros_contracts.md
passed
```

Task C worker 返回验证：

```text
PYTHONDONTWRITEBYTECODE=1 python3 mobile/test_mobile_web_entrypoint.py
Ran 51 tests in 0.154s OK

PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile mobile/test_mobile_web_entrypoint.py
passed

node --check mobile/web/app.js
passed

required rg
passed

git diff --check -- mobile/web/index.html mobile/web/app.js mobile/web/styles.css mobile/fixtures/mobile_web_status.fixture.json mobile/test_mobile_web_entrypoint.py docs/product/mobile_user_flow.md
passed
```

Task D Product closeout 本地验收命令：

```bash
rg -n "mobile_field_material_retest_request|Objective 5|Objective 2|Objective 3|software_proof_docker_mobile_field_material_retest_request_gate|not_proven|delivery_success=false|primary_actions_enabled=false|不证明|真实公网|只有docker|真实 WAVE ROVER|PR|评审" sprints/2026.05.16_09-10_mobile-field-material-retest-request OKR.md docs/process/okr_progress_log.md
git diff --check -- sprints/2026.05.16_09-10_mobile-field-material-retest-request OKR.md docs/process/okr_progress_log.md
```

结果记录在本轮最终回复中。

## 3. 偏差与修复

- Task A 首次测试发现 unsupported wrapper-schema gap，Autonomy worker 已补齐 fail-closed 处理并重新通过 6 条测试。
- Product closeout 未改动 A/B/C worker 的实现文件，也未提交 git，符合本轮限制。

## 4. 边界与剩余风险

本轮是 Docker/local software proof，证据边界为 `software_proof_docker_mobile_field_material_retest_request_gate`。

本轮明确不证明：真实手机、真实 iPhone/Android device behavior、production app、真实 PWA prompt/user choice、真实 route/elevator field pass、真实 Nav2/fixed-route、真实路线采集、真实 dropoff/cancel completion、delivery success、真实 WAVE ROVER、真实 UART/串口、HIL、Objective 5 external proof、真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue 或 production worker/migration。

状态保持：`not_proven`、`delivery_success=false`、`primary_actions_enabled=false`。

本机只有docker；Objective 5 仍缺真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue 和 worker/migration，不能上调。Objective 1 仍缺真实 WAVE ROVER、UART、Orange Pi 串口、`T=1001` feedback 和 HIL，不能上调。
