# Sprint 2026.05.16_05-06 Mobile Route Elevator Handoff Browser Proof - Tech Plan

sprint_type: epic

## 1. 技术方案

本轮新增 `software_proof_docker_mobile_route_elevator_handoff_browser_proof_gate` 语义，但不替换现有 browser proof artifact 边界。实现方式是在现有 `pc-tools/evidence/phone_browser_acceptance_gate.py` 中把最新 `routeElevatorFieldSessionHandoff*` DOM 纳入 key element、panel expectation、boundary expectation 和 evidence summary；运行时仍服务 `mobile/web/` 与 `mobile/fixtures/mobile_web_status.fixture.json`。

这保持现有 gate 的输出路径和兼容字段，同时让本轮 sprint evidence 能证明当前 PWA 的最新 route/elevator handoff panel 被浏览器 gate 覆盖。

## 2. 文件范围

Task A `full-stack-software-engineer` 可改：

- `pc-tools/evidence/phone_browser_acceptance_gate.py`
- `mobile/test_mobile_web_entrypoint.py`
- `mobile/fixtures/mobile_web_status.fixture.json`
- `docs/product/mobile_user_flow.md`

Task B `robot-software-engineer` 可改：

- `docs/interfaces/ros_contracts.md`
- `onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`

Task C `product-okr-owner` 可改：

- `OKR.md`
- `docs/process/okr_progress_log.md`
- `sprints/2026.05.16_05-06_mobile-route-elevator-handoff-browser-proof/tech-done.md`
- `sprints/2026.05.16_05-06_mobile-route-elevator-handoff-browser-proof/side2side_check.md`
- `sprints/2026.05.16_05-06_mobile-route-elevator-handoff-browser-proof/final.md`

范围外文件不得改动。

## 3. 接口影响

- 不新增 `/api/collect` payload。
- 不改变 Start / Confirm Dropoff / Cancel gating。
- 不改变 Robot diagnostics runtime 行为，除非 Task B 发现文档或 test fence 需要补齐。
- browser proof 输出仍是 local Chromium-family proof，只能证明当前 `mobile/web` PWA 本地浏览器渲染与 phone-safe UI 行为。

## 4. 验收命令

Task A 必须运行：

```bash
PYTHONDONTWRITEBYTECODE=1 python3 mobile/test_mobile_web_entrypoint.py
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile pc-tools/evidence/phone_browser_acceptance_gate.py mobile/test_mobile_web_entrypoint.py
node --check mobile/web/app.js
python3 pc-tools/evidence/phone_browser_acceptance_gate.py --output-dir sprints/2026.05.16_05-06_mobile-route-elevator-handoff-browser-proof/evidence
rg -n "routeElevatorFieldSessionHandoffTitle|routeElevatorFieldSessionHandoffBoundary|software_proof_docker_route_elevator_field_session_handoff_gate|mobile_route_elevator_handoff_browser" pc-tools/evidence/phone_browser_acceptance_gate.py mobile/test_mobile_web_entrypoint.py docs/product/mobile_user_flow.md sprints/2026.05.16_05-06_mobile-route-elevator-handoff-browser-proof
git diff --check -- pc-tools/evidence/phone_browser_acceptance_gate.py mobile/test_mobile_web_entrypoint.py mobile/fixtures/mobile_web_status.fixture.json docs/product/mobile_user_flow.md
```

若本机缺 Chromium-family browser，Task A 必须记录 browser gate 的实际失败输出，并保留其余静态围栏通过结果。

Task B 必须运行：

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py
rg -n "route_elevator_field_session_handoff|metadata-only|delivery_success=false|primary_actions_enabled=false|software_proof_docker_route_elevator_field_session_handoff_gate" docs/interfaces/ros_contracts.md onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py
git diff --check -- docs/interfaces/ros_contracts.md onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py
```

Task C 必须运行：

```bash
rg -n "mobile_route_elevator_handoff_browser|Objective 4|Objective 5|not real|不证明|真实手机|delivery_success=false" sprints/2026.05.16_05-06_mobile-route-elevator-handoff-browser-proof OKR.md docs/process/okr_progress_log.md docs/product/mobile_user_flow.md
git diff --check -- sprints/2026.05.16_05-06_mobile-route-elevator-handoff-browser-proof OKR.md docs/process/okr_progress_log.md docs/product/mobile_user_flow.md
```

## 5. OKR 最低优先级核对

1. 当前 `OKR.md` 4.1 数值最低 Objective：Objective 5，约 66%。
2. 本 sprint 不直接针对 Objective 5。
3. 理由：Objective 5 当前下一步需要真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue connectivity、production worker/migration 或真实外部材料；本机只有 Docker，继续做本地 O5 metadata depth 会重复消费同一 blocker。Objective 4 约 75%，是当前最低可行动作；最新 sprint 明确 mobile/web 只新增只读 panel，但未证明真实手机/browser。本轮用 local Chromium-family browser proof 覆盖最新 route/elevator handoff panel，功能向前且证据边界清晰。

## 6. 风险边界

本轮最多形成 `software_proof_docker_mobile_route_elevator_handoff_browser_proof_gate` 或 browser-gate blocked evidence。它不是真实 iPhone/Android、production app、真实 PWA prompt/user choice、真实 route/elevator field pass、真实 Nav2/fixed-route、HIL、dropoff/cancel completion、delivery success 或 Objective 5 external proof。
