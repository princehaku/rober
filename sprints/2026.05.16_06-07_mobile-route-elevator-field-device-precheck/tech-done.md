# Sprint 2026.05.16_06-07 Mobile Route Elevator Field Device Precheck - Tech Done

sprint_type: epic

## 1. 实际改动

Task A `full-stack-software-engineer` 完成移动端 first-screen `mobile_route_elevator_field_device_precheck` panel，改动：

- `mobile/web/index.html`
- `mobile/web/app.js`
- `mobile/web/styles.css`
- `mobile/fixtures/mobile_web_status.fixture.json`
- `mobile/test_mobile_web_entrypoint.py`
- `docs/product/mobile_user_flow.md`

交付内容：首屏新增真实设备/路线电梯现场 precheck 面板，支持 whitelist copy/export，展示 route/elevator handoff reference、真实设备/PWA observation checklist、field material list、`delivery_success=false`、`primary_actions_enabled=false` 和 `not_proven`。Start / Confirm Dropoff / Cancel gating 未改变。

Task B `robot-software-engineer` 完成 Robot diagnostics metadata-only fence，改动：

- `docs/interfaces/ros_contracts.md`
- `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py`
- `onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`

交付内容：新增 `mobile_route_elevator_field_device_precheck` / `_summary` diagnostics gate，固定 `software_proof_docker_mobile_route_elevator_field_device_precheck_gate` 边界，fail-closed 处理 unsafe source，并从 `latest_status` 剥离 precheck metadata，避免 sanitizer bypass。不改变 collect、dropoff、cancel、ACK、control、Nav2、HIL、dropoff/cancel completion 或 delivery success。

Task C `autonomy-engineer` 完成 pc-tools precheck helper/gate，改动：

- `pc-tools/evidence/mobile_route_elevator_field_device_precheck.py`
- `pc-tools/evidence/test_mobile_route_elevator_field_device_precheck.py`
- `pc-tools/README.md`
- `docs/navigation/fixed_route_workflow.md`

交付内容：新增 `trashbot.mobile_route_elevator_field_device_precheck.v1`、summary/copy schemas、same-evidence-ref、required route/elevator materials、device/PWA checklist 和 fail-closed 校验。缺失、坏 JSON、schema mismatch、boundary mismatch、evidence mismatch、unsafe copy 和 success claims 均拒绝。

Task D `product-okr-owner` 完成产品收口，改动：

- `OKR.md`
- `docs/process/okr_progress_log.md`
- `sprints/2026.05.16_06-07_mobile-route-elevator-field-device-precheck/tech-done.md`
- `sprints/2026.05.16_06-07_mobile-route-elevator-field-device-precheck/side2side_check.md`
- `sprints/2026.05.16_06-07_mobile-route-elevator-field-device-precheck/final.md`

## 2. 验证结果

Task A 验证：

```text
PYTHONDONTWRITEBYTECODE=1 python3 mobile/test_mobile_web_entrypoint.py
Ran 48 tests ... OK

PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile mobile/test_mobile_web_entrypoint.py
pass

node --check mobile/web/app.js
pass

required rg
pass

git diff --check -- mobile/web/index.html mobile/web/app.js mobile/web/styles.css mobile/fixtures/mobile_web_status.fixture.json mobile/test_mobile_web_entrypoint.py docs/product/mobile_user_flow.md
pass
```

Task A 首轮失败定位：`mobile/test_mobile_web_entrypoint.py` 中一处 assertion 放置位置错误，已修复并重跑通过。

Task B 验证：

```text
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py
Ran 85 tests in 0.088s OK

required rg
pass

git diff --check -- docs/interfaces/ros_contracts.md onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py
pass
```

Task C 验证：

```text
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile pc-tools/evidence/mobile_route_elevator_field_device_precheck.py pc-tools/evidence/test_mobile_route_elevator_field_device_precheck.py
pass

PYTHONDONTWRITEBYTECODE=1 python3 pc-tools/evidence/test_mobile_route_elevator_field_device_precheck.py
Ran 6 tests ... OK

python3 pc-tools/evidence/mobile_route_elevator_field_device_precheck.py --help
pass

required rg
pass

git diff --check -- pc-tools/evidence/mobile_route_elevator_field_device_precheck.py pc-tools/evidence/test_mobile_route_elevator_field_device_precheck.py pc-tools/README.md docs/navigation/fixed_route_workflow.md
pass
```

Task D 验证在 closeout 文件完成后执行，结果记录在 `final.md`。

## 3. OKR 最低优先级核对

当前 `OKR.md` 4.1 数值最低 Objective 仍是 Objective 5，约 66%。本 sprint 未直接推进 Objective 5，因为缺真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue connectivity、production worker/migration 或真实外部材料；继续做本地 metadata 会重复消费同一 blocker。

本轮实际主目标是 Objective 4：把上一轮 local browser proof 转成真实设备/现场前的统一手机 precheck/export 入口。Objective 4 可从约 76% 保守上调到约 77%。Objective 2 / Objective 3 只得到 route/elevator field materials precheck 和 same-evidence-ref 准备支撑，保持约 76%。Objective 1 保持约 73%。Objective 5 保持约 66%；not real Objective 5 external proof。

## 4. 剩余风险

本轮证据边界是 `software_proof_docker_mobile_route_elevator_field_device_precheck_gate`。

不证明：真实手机、真实 iPhone/Android device behavior、production app、真实 PWA prompt/user choice、真实 route/elevator field pass、真实 Nav2/fixed-route、真实 dropoff/cancel completion、delivery success、WAVE ROVER、真实串口/UART、HIL、真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、production worker/migration 或 Objective 5 external proof。

