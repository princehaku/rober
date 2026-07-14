# Tech Plan - O5 Delivery State Terminal Reconciliation

## Sprint Metadata

- sprint_type: epic
- Sprint: `sprints/2026.07.14_04-27_o5_delivery_state_terminal_reconciliation/`
- Product owner: `product-okr-owner`
- Implementation owner: `robot-software-engineer`
- Target Objective: Objective 5 云中转控制面产品化
- Planned artifact schema: `trashbot.o5.delivery_state_terminal_reconciliation.v1`
- Planned proof boundary: `software_proof_o5_delivery_state_terminal_reconciliation_only`

## OKR 最低优先级核对

1. 当前 `OKR.md` 4.1 节最低 Objective 是 Objective 5，约 `85%`。
2. 本 sprint 针对该最低 Objective，但不重复 production/external blocker wrapper。
3. 选择理由：真实 production/external evidence unavailable；最近 O5 CDN/TLS `4xx` probe、readiness packet consumption、cloud external review-decision、O5 bounded-route terminal-result bridge，以及 O6/O7 terminal-result intake/export 均为 support-only。本轮改走 O5/O1/O3 交付状态机 fail-closed 主链路，消费既有 terminal result，但明确不提升为真实 delivery、route execution、HIL 或 safe-to-control。

## 技术方案

Robot Software 新增 `delivery_state_terminal_reconciliation` 离线 reconcile 能力：

1. 读取 source summary：
   - `sprints/2026.07.14_00-24_o5_bounded_route_terminal_result_bridge/artifacts/o5_bounded_route_terminal_result_bridge_summary.json`
2. 校验 source schema 与 source boundary：
   - `schema=trashbot.o5.bounded_route_terminal_result_bridge.v1`
   - `result_code=mock_route_execution_completed_not_live_delivery`
   - `delivery_success=false`
   - `route_execution_success=false`
   - `safe_to_control=false`
   - `hil_pass=false`
3. 把 terminal result 输入 `DeliveryStateMachine` 的离线 reconcile 入口。
4. 状态机必须产出可读事件，解释 mock terminal result 不能当真实 route execution、dropoff success、delivery/operator acceptance、HIL 或 safe-to-control。
5. 写出 summary artifact：
   - `schema=trashbot.o5.delivery_state_terminal_reconciliation.v1`
   - `source_schema=trashbot.o5.bounded_route_terminal_result_bridge.v1`
   - `result_code=mock_route_execution_completed_not_live_delivery`
   - `terminal_result_accepted_for_delivery=false`
   - `delivery_success=false`
   - `route_execution_success=false`
   - `safe_to_control=false`
   - `hil_pass=false`
   - `final_state=error` 或等价 fail-closed
   - `reconciliation_status=fail_closed_mock_terminal_result_not_delivery` 或等价短状态
   - `rejected_claims` 覆盖 production cloud、route execution、delivery/operator acceptance、dropoff success、HIL、safe-to-control 和 robot control。

## 文件范围

Robot Software 允许修改：

- `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/delivery_state_machine.py`
- `onboard/src/ros2_trashbot_behavior/test/test_delivery_state_machine.py`
- `onboard/scripts/o5_delivery_state_terminal_reconciliation.py`
- `onboard/tests/test_o5_delivery_state_terminal_reconciliation.py`
- `docs/product/cloud_4g_infrastructure.md`
- `docs/product/remote_4g_mvp.md`
- `sprints/2026.07.14_04-27_o5_delivery_state_terminal_reconciliation/tech-done.md`

Product closeout 后允许修改：

- `sprints/2026.07.14_04-27_o5_delivery_state_terminal_reconciliation/side2side_check.md`
- `sprints/2026.07.14_04-27_o5_delivery_state_terminal_reconciliation/final.md`
- `OKR.md`
- `docs/process/okr_progress_log.md`

不得修改：

- WAVE ROVER、ESP32、Orange Pi、UART、launch、硬件参数或真实控制路径。
- O6/O7 archive/readback、PC workstation、UI 或 mission bundle export。
- 历史 sprint artifact 内容。

## 接口影响

本轮不改变对外 HTTP API，不新增云端 production 依赖。CLI 只读 source summary 并写本 sprint artifact。

`DeliveryStateMachine` 新增或复用的 reconcile 入口必须保持 fail-closed：

- 只要 source 不是明确可验的真实 delivery/operator acceptance，就不得进入 success final state。
- `terminal_result_accepted_for_delivery=false` 必须是顶层可断言字段。
- `delivery_success=false`、`route_execution_success=false`、`safe_to_control=false`、`hil_pass=false` 必须同时出现在顶层和固定 false invariant/readable event 中。

## 验收命令

Robot Software 必须运行并记录结果：

```bash
python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/delivery_state_machine.py onboard/scripts/o5_delivery_state_terminal_reconciliation.py
```

```bash
python3 -m unittest onboard.src.ros2_trashbot_behavior.test.test_delivery_state_machine onboard.tests.test_o5_delivery_state_terminal_reconciliation
```

```bash
python3 onboard/scripts/o5_delivery_state_terminal_reconciliation.py --source-summary sprints/2026.07.14_00-24_o5_bounded_route_terminal_result_bridge/artifacts/o5_bounded_route_terminal_result_bridge_summary.json --output sprints/2026.07.14_04-27_o5_delivery_state_terminal_reconciliation/artifacts/delivery_state_terminal_reconciliation_summary.json
```

```bash
python3 -m json.tool sprints/2026.07.14_04-27_o5_delivery_state_terminal_reconciliation/artifacts/delivery_state_terminal_reconciliation_summary.json >/dev/null
```

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

```bash
rg -n "delivery_state_terminal_reconciliation|mock_route_execution_completed_not_live_delivery|terminal_result_accepted_for_delivery=false|delivery_success=false|safe_to_control=false|route_execution_success=false|hil_pass=false" onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/delivery_state_machine.py onboard/src/ros2_trashbot_behavior/test/test_delivery_state_machine.py onboard/scripts/o5_delivery_state_terminal_reconciliation.py onboard/tests/test_o5_delivery_state_terminal_reconciliation.py docs/product/cloud_4g_infrastructure.md docs/product/remote_4g_mvp.md sprints/2026.07.14_04-27_o5_delivery_state_terminal_reconciliation
```

```bash
git diff --check -- onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/delivery_state_machine.py onboard/src/ros2_trashbot_behavior/test/test_delivery_state_machine.py onboard/scripts/o5_delivery_state_terminal_reconciliation.py onboard/tests/test_o5_delivery_state_terminal_reconciliation.py docs/product/cloud_4g_infrastructure.md docs/product/remote_4g_mvp.md sprints/2026.07.14_04-27_o5_delivery_state_terminal_reconciliation
```

## 子 Agent 派发要求

派给 `robot-software-engineer` 时必须包含完整角色 prompt、上述文件范围、上述验收命令和输出要求。该 owner 单线负责实现、测试、修复和 `tech-done.md` 留档。

输出必须返回：

1. 实际改动的文件列表
2. 验证命令输出结果
3. 失败定位
4. 剩余风险

## 风险与边界

- 本轮只证明 delivery state machine 对 mock terminal result 的 fail-closed reconcile 语义。
- 不证明 production cloud、真实 route execution、delivery/operator acceptance、dropoff success、HIL、safe-to-control、`/cmd_vel`、`/api/base/manual`、NavigateToPose 或 WAVE ROVER UART。
- 如果 source artifact 缺失、schema 不匹配、`result_code` 不是 `mock_route_execution_completed_not_live_delivery`、危险字段为 true、或状态机输出 success final state，CLI 和测试必须 fail closed。
- 若实现阶段发现需要跨 O6/O7 或硬件路径，必须先返回 Product 复核；不得扩大本 sprint 为 wrapper/intake/export 工作。
