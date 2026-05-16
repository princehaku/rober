# Sprint 2026.05.16_19-20 Route Task Terminal Review Decision - Tech Done

sprint_type: epic

## 1. 实际改动

Task A Autonomy 已完成 `route_task_terminal_review_decision` PC evidence gate：

- 新增 `pc-tools/evidence/route_task_terminal_review_decision.py`
- 新增 `pc-tools/evidence/test_route_task_terminal_review_decision.py`
- 更新 `pc-tools/README.md`
- 更新 `docs/navigation/fixed_route_workflow.md`

Task A 产出 `trashbot.route_task_terminal_review_decision.v1` / `trashbot.route_task_terminal_review_decision_summary.v1`，把上一轮 `route_task_terminal_completion_rehearsal` summary 转为 review decision、decision reason、owner handoff、next required evidence 和 field retest request guidance。边界固定为 `software_proof_docker_route_task_terminal_review_decision_gate`、`not_proven`、`delivery_success=false`、`primary_actions_enabled=false`。

Task B Robot 已完成 diagnostics metadata-only consumer：

- 更新 `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py`
- 更新 `onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`
- 更新 `docs/interfaces/ros_contracts.md`

Task B 新增 `route_task_terminal_review_decision` / `route_task_terminal_review_decision_summary` 只读消费，支持 explicit ref、env、status 和 nested diagnostics source；缺失、unsupported、unsafe、same evidence_ref mismatch 均 fail closed，不触发 collect、dropoff、cancel、ACK、cursor、Nav2、WAVE ROVER、HIL、dropoff/cancel completion 或 delivery success。

Task C Full-stack 已完成 mobile/web 只读 panel：

- 更新 `mobile/web/app.js`
- 更新 `mobile/web/styles.css`
- 更新 `mobile/web/test_mobile_web_entrypoint.py`
- 更新 `mobile/web/fixtures/status.json`
- 更新 `docs/product/mobile_user_flow.md`

Task C 新增只读“终态复核决策” panel，展示 review decision、decision reason、safe evidence_ref、owner handoff、next required evidence、field retest request guidance、boundary、`not_proven`、`delivery_success=false`、`primary_actions_enabled=false`。copy/export whitelist-only，Start / Confirm Dropoff / Cancel gating 未改。

Task D Product closeout 已完成：

- 创建本文件
- 创建 `side2side_check.md`
- 创建 `final.md`
- 更新 `OKR.md`
- 更新 `docs/process/okr_progress_log.md`

## 2. 验证结果

Task A 验证：

```text
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile pc-tools/evidence/route_task_terminal_review_decision.py
passed

PYTHONDONTWRITEBYTECODE=1 python3 -m unittest pc-tools/evidence/test_route_task_terminal_review_decision.py
Ran 8 tests in 0.011s
OK

python3 pc-tools/evidence/route_task_terminal_review_decision.py --help
passed

required rg
passed

git diff --check -- pc-tools/evidence/route_task_terminal_review_decision.py pc-tools/evidence/test_route_task_terminal_review_decision.py pc-tools/README.md docs/navigation/fixed_route_workflow.md
passed
```

Task B 验证：

```text
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py
passed

PYTHONDONTWRITEBYTECODE=1 python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py
Ran 110 tests in 0.119s
OK

required rg
passed

git diff --check -- onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py docs/interfaces/ros_contracts.md
passed
```

Task C 验证：

```text
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest mobile.web.test_mobile_web_entrypoint
12 tests OK

node --check mobile/web/app.js
passed

required rg
passed

git diff --check -- mobile/web/app.js mobile/web/styles.css mobile/web/test_mobile_web_entrypoint.py mobile/web/fixtures/status.json docs/product/mobile_user_flow.md
passed
```

Task D closeout 验证见 `final.md`。

## 3. 偏差和失败定位

本轮没有报告未修复的 worker 验证失败。三条工程链路均保持 software proof only，未扩大到真实现场、真实硬件、真实手机或 Objective 5 external proof。

Product closeout 对 OKR 的处理为保守上调：Objective 2 约 79% -> 约 80%，Objective 3 约 79% -> 约 80%，Objective 4 约 88% -> 约 89%。Objective 1 保持约 75%，因为最近两轮已消费 PR #5 硬件 blocker，本轮无真实 WAVE ROVER/UART/HIL。Objective 5 保持约 66%，因为本轮仍无真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue 或 worker/migration。

## 4. 剩余风险

- 不证明真实 Nav2/fixed-route。
- 不证明真实 route/elevator field pass。
- 不证明真实 dropoff/cancel completion。
- 不证明 delivery success。
- 不证明真实手机/browser 或 production app。
- 不证明 WAVE ROVER、UART、HIL、`T=1001` feedback、`/odom`、`/imu/data` 或 `/battery` 实机样本。
- 不证明 Objective 5 external proof、公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue 或 production worker/migration。
