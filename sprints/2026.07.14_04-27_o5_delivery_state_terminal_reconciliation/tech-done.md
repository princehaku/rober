# Tech Done - O5 Delivery State Terminal Reconciliation

## Sprint Metadata

- sprint_type: epic
- Sprint: `sprints/2026.07.14_04-27_o5_delivery_state_terminal_reconciliation/`
- Implementation owner: `robot-software-engineer`
- Artifact schema: `trashbot.o5.delivery_state_terminal_reconciliation.v1`
- Proof boundary: `software_proof_o5_delivery_state_terminal_reconciliation_only`
- Source summary: `sprints/2026.07.14_00-24_o5_bounded_route_terminal_result_bridge/artifacts/o5_bounded_route_terminal_result_bridge_summary.json`
- Output artifact: `sprints/2026.07.14_04-27_o5_delivery_state_terminal_reconciliation/artifacts/delivery_state_terminal_reconciliation_summary.json`

## 实际改动

- `DeliveryStateMachine` 新增离线 terminal-result reconcile 入口：只接受 `schema=trashbot.o5.bounded_route_terminal_result_bridge.v1`、`proof_boundary=software_proof_o5_bounded_route_terminal_result_bridge_only`、`result_code=mock_route_execution_completed_not_live_delivery`、同 task identity、`terminal_result_state=terminal_result_recorded`、`reconciliation_state=terminal_result_recorded` 和所有安全 false 字段。
- 有效 source 也会进入 fail-closed：`final_state=error`、`reconciliation_status=fail_closed_mock_terminal_result_not_delivery`、`terminal_result_accepted_for_delivery=false`、`delivery_success=false`、`route_execution_success=false`、`safe_to_control=false`、`hil_pass=false`。
- 新增 CLI `onboard/scripts/o5_delivery_state_terminal_reconciliation.py`：只读 source summary，调用 `DeliveryStateMachine.reconcile_terminal_result_summary()`，写出本 sprint artifact。
- 新增测试覆盖 happy fail-closed path、dangerous true field、source schema drift、missing identity、unexpected success/live state 拒绝路径。
- 更新 `docs/product/cloud_4g_infrastructure.md` 与 `docs/product/remote_4g_mvp.md`，明确该 reconciliation 是状态机 fail-closed 解释层，不是 production cloud、route execution、delivery/operator acceptance、dropoff success、HIL 或 safe-to-control 证据。

## 验证结果

```bash
python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/delivery_state_machine.py onboard/scripts/o5_delivery_state_terminal_reconciliation.py
```

结果：通过，无输出。

```bash
python3 -m unittest onboard.src.ros2_trashbot_behavior.test.test_delivery_state_machine onboard.tests.test_o5_delivery_state_terminal_reconciliation
```

结果：

```text
Ran 21 tests in 0.004s
OK
```

```bash
python3 onboard/scripts/o5_delivery_state_terminal_reconciliation.py --source-summary sprints/2026.07.14_00-24_o5_bounded_route_terminal_result_bridge/artifacts/o5_bounded_route_terminal_result_bridge_summary.json --output sprints/2026.07.14_04-27_o5_delivery_state_terminal_reconciliation/artifacts/delivery_state_terminal_reconciliation_summary.json
```

结果：通过，生成 `trashbot.o5.delivery_state_terminal_reconciliation.v1`。关键字段：

```text
result_code=mock_route_execution_completed_not_live_delivery
final_state=error
reconciliation_status=fail_closed_mock_terminal_result_not_delivery
terminal_result_accepted_for_delivery=false
delivery_success=false
route_execution_success=false
safe_to_control=false
hil_pass=false
```

```bash
python3 -m json.tool sprints/2026.07.14_04-27_o5_delivery_state_terminal_reconciliation/artifacts/delivery_state_terminal_reconciliation_summary.json >/dev/null
```

结果：通过，无输出。

```bash
python3 - <<'PY'
import json
from pathlib import Path

p = Path("sprints/2026.07.14_04-27_o5_delivery_state_terminal_reconciliation/artifacts/delivery_state_terminal_reconciliation_summary.json")
d = json.loads(p.read_text())
assert d["schema"] == "trashbot.o5.delivery_state_terminal_reconciliation.v1"
assert d["result_code"] == "mock_route_execution_completed_not_live_delivery"
assert d["terminal_result_accepted_for_delivery"] is False
assert d["delivery_success"] is False
assert d["route_execution_success"] is False
assert d["safe_to_control"] is False
assert d["hil_pass"] is False
assert d.get("final_state") in {"error", "failed", "blocked", "fail_closed"}
events = " ".join(str(e) for e in d.get("state_machine_events", []))
assert "mock" in events.lower()
assert "delivery" in events.lower()
assert "not" in events.lower() or "cannot" in events.lower() or "fail" in events.lower()
print("delivery_state_terminal_reconciliation_acceptance_ok")
PY
```

结果：

```text
delivery_state_terminal_reconciliation_acceptance_ok
```

```bash
rg -n "delivery_state_terminal_reconciliation|mock_route_execution_completed_not_live_delivery|terminal_result_accepted_for_delivery=false|delivery_success=false|safe_to_control=false|route_execution_success=false|hil_pass=false" onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/delivery_state_machine.py onboard/src/ros2_trashbot_behavior/test/test_delivery_state_machine.py onboard/scripts/o5_delivery_state_terminal_reconciliation.py onboard/tests/test_o5_delivery_state_terminal_reconciliation.py docs/product/cloud_4g_infrastructure.md docs/product/remote_4g_mvp.md sprints/2026.07.14_04-27_o5_delivery_state_terminal_reconciliation
```

结果：通过，命中代码、测试、文档和 artifact anchor。

```bash
git diff --check -- onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/delivery_state_machine.py onboard/src/ros2_trashbot_behavior/test/test_delivery_state_machine.py onboard/scripts/o5_delivery_state_terminal_reconciliation.py onboard/tests/test_o5_delivery_state_terminal_reconciliation.py docs/product/cloud_4g_infrastructure.md docs/product/remote_4g_mvp.md sprints/2026.07.14_04-27_o5_delivery_state_terminal_reconciliation
```

结果：通过，无输出。

## 失败定位

本轮验证未出现失败。拒绝路径已由单测覆盖：source schema drift、dangerous true field、missing identity、unexpected live/success state 均在写 artifact 前抛出 `TerminalResultReconciliationError`。

## 剩余风险

- 本轮只证明 `DeliveryStateMachine` 对 mock terminal result 的离线 fail-closed reconcile 语义，不证明 production cloud、真实公网 HTTPS/TLS、真实 4G/SIM、production DB/queue、OSS/CDN live traffic 或真实 phone/browser。
- 本轮不触发 `/cmd_vel`、`/api/base/manual`、NavigateToPose、WAVE ROVER UART 或任何真实机器人控制。
- 本轮不证明真实 route execution、delivery/operator acceptance、dropoff success、HIL pass 或 safe-to-control。
- 下一步若要把状态机从 fail-closed 推进到 success，必须先取得同 run live route execution、operator/dropoff acceptance 和 HIL/safe-to-control 证据。

## 协同需求

- Product：需要在 closeout 阶段更新 `side2side_check.md` / `final.md`，并保持 OKR flat 除非后续取得真实 external、route execution、delivery 或 HIL 证据。
- Hardware：本轮不需要；后续只有 explicit operator approval 后才进入 current live HIL / safe-to-control。
- Autonomy：本轮不需要；后续 route execution success 必须由 live Nav2/controller 或等价现场证据提供。
- Full-Stack：本轮不需要；O6/O7 intake/export 已是上游材料，本轮没有新增 API/UI。
