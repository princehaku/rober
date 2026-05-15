# Sprint 2026.05.16_07-08 Mobile Field Material Intake - Tech Done

sprint_type: epic

## 1. 实际改动

Task A `full-stack-software-engineer` 已完成手机端入口：

- `mobile/web/index.html`
- `mobile/web/app.js`
- `mobile/web/styles.css`
- `mobile/fixtures/mobile_web_status.fixture.json`
- `mobile/test_mobile_web_entrypoint.py`
- `docs/product/mobile_user_flow.md`

结果：首屏新增 `mobile_field_material_intake` panel，显示 safe entry/evidence_ref、真实设备/PWA checklist、route/elevator field materials、same-evidence-ref status，支持 whitelist-only copy/export。Start / Confirm Dropoff / Cancel gating 未改，仍 fail closed。

Task B `robot-software-engineer` 已完成 Robot diagnostics metadata-only consumer：

- `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py`
- `onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`
- `docs/interfaces/ros_contracts.md`

结果：新增 `mobile_field_material_intake` / `_summary` metadata-only diagnostics consumer、schema/boundary 校验、bad JSON/missing/unsupported/unsafe/success claim fail-closed、`latest_status` 清理和 env 入口。command/ACK/control/cursor/persistence/terminal ACK/Nav2/HIL/dropoff/cancel/delivery success 旗标强制 false。

Task C `autonomy-engineer` 已完成 pc-tools intake/gate：

- `pc-tools/evidence/mobile_field_material_intake.py`
- `pc-tools/evidence/test_mobile_field_material_intake.py`
- `pc-tools/README.md`
- `docs/navigation/fixed_route_workflow.md`

结果：新增 fail-closed `pc-tools` intake/gate，把真实设备/PWA observation、route/elevator field materials、Nav2/fixed-route runtime log、task record、completion signal、dropoff/cancel material status 收到同一 safe `evidence_ref` 下检查。

Task D `product-okr-owner` 已完成工程收口：

- `sprints/2026.05.16_07-08_mobile-field-material-intake/tech-done.md`
- `sprints/2026.05.16_07-08_mobile-field-material-intake/side2side_check.md`
- `sprints/2026.05.16_07-08_mobile-field-material-intake/final.md`
- `OKR.md`
- `docs/process/okr_progress_log.md`

## 2. 验证结果

Task A 验证：

```text
PYTHONDONTWRITEBYTECODE=1 python3 mobile/test_mobile_web_entrypoint.py
Ran 49 tests ... OK

PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile mobile/test_mobile_web_entrypoint.py
OK

node --check mobile/web/app.js
OK

required rg
OK

git diff --check -- mobile/web/index.html mobile/web/app.js mobile/web/styles.css mobile/fixtures/mobile_web_status.fixture.json mobile/test_mobile_web_entrypoint.py docs/product/mobile_user_flow.md
OK
```

Task B 验证：

```text
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py
Ran 87 tests ... OK

required rg
OK

git diff --check -- onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py docs/interfaces/ros_contracts.md
OK
```

Task C 验证：

```text
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile pc-tools/evidence/mobile_field_material_intake.py pc-tools/evidence/test_mobile_field_material_intake.py
OK

PYTHONDONTWRITEBYTECODE=1 python3 pc-tools/evidence/test_mobile_field_material_intake.py
Ran 5 tests ... OK

python3 pc-tools/evidence/mobile_field_material_intake.py --help
OK

required rg
OK

git diff --check -- pc-tools/evidence/mobile_field_material_intake.py pc-tools/evidence/test_mobile_field_material_intake.py pc-tools/README.md docs/navigation/fixed_route_workflow.md
OK
```

Task C 首轮 unittest 发现 evidence-ref mismatch 被 precheck 层优先拦截；测试断言按更严格 fail-closed 顺序修正后通过。

Task D closeout 验证见 `final.md`，包括 required `rg`、scoped `git diff --check`、commit 和 push。

## 3. 证据边界

本轮证据边界是 `software_proof_docker_mobile_field_material_intake_gate`。

本轮不证明真实手机、真实 iPhone/Android device behavior、production app、真实 PWA prompt/user choice、真实 route/elevator field pass、真实 Nav2/fixed-route、dropoff/cancel completion、delivery success、HIL、WAVE ROVER/UART 或 Objective 5 external proof。

## 4. 偏差和剩余风险

- Objective 4 可从约 77% 保守上调到约 78%，因为本轮把 precheck 推进为 phone-safe material intake surface + Robot diagnostics consumer + pc-tools gate。
- Objective 2/3 只作为 same-evidence-ref 现场材料摄取支撑，不上调。
- Objective 5 仍约 66%，因为没有真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、production worker/migration 或其他真实外部 O5 材料。
- 剩余风险是还需要真实设备/PWA observation、真实 route/elevator field materials、Nav2/fixed-route runtime log、同一 `evidence_ref` 的 task record/completion signal、dropoff/cancel completion 或 delivery result 材料。
