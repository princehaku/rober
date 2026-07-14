# Tech Plan - O5 Bounded Route Terminal Result Bridge

## Sprint Metadata

- sprint_type: epic
- Sprint: `sprints/2026.07.14_00-24_o5_bounded_route_terminal_result_bridge/`
- Product owner: `product-okr-owner`
- Implementation owner: `robot-software-engineer`
- Planned proof boundary: `software_proof_o5_bounded_route_terminal_result_bridge_only`

## OKR 最低优先级核对

1. 当前 `OKR.md` 4.1 节最低 Objective 是 O5：云中转控制面产品化，约 `85%`。
2. 本 sprint 针对该最低 Objective。
3. 本轮不继续消费最近 O5 blocker：`blocked_http_status_not_success_class`、CDN/TLS readiness packet consumption、cloud external evidence review-decision gate。改为消费同一任务的 bounded route mock execution terminal material，推进 O5 command/result/reconciliation 主链路。

## 技术方案

新增一个本地/mock bridge CLI，消费：

`sprints/2026.07.13_23-23_o3_bounded_route_mock_execution/artifacts/algorithm/bounded_route_mock_execution_summary.json`

Bridge 必须复用既有 relay HTTP 主路径：

1. 用 in-process `build_server(...)` 启动本地 relay。
2. `POST /api/commands/collect` 提交 command，使用 source `task_id` 作为 idempotency key 或 command id 的稳定组成。
3. `POST /robots/{robot_id}/commands/{command_id}/terminal-result` 写入 terminal result：
   - `terminal_result_type=delivery_terminal`
   - `task_terminal_state=mock_route_execution_completed_not_live_route_execution`
   - `result_code=mock_route_execution_completed_not_live_delivery`
   - `task_record_ref=<task_id>`
   - `evidence_ref=<safe basename or stable safe ref>`
4. `GET /api/commands/{command_id}/result?robot_id=<robot_id>` 读取 reconciliation v2。
5. 写出 summary artifact：
   - schema: `trashbot.o5.bounded_route_terminal_result_bridge.v1`
   - proof boundary: `software_proof_o5_bounded_route_terminal_result_bridge_only`
   - source schema: `trashbot.o3.bounded_route_mock_execution.v1`
   - relay capabilities: `cloud_phone_command_api`, `cloud_command_terminal_result`, `cloud_command_result_reconciliation`
   - same-task identity fields
   - command/terminal/reconciliation states
   - fixed false fields
   - rejected claims

## 文件范围

Robot Software 允许修改：

- `onboard/scripts/o5_bounded_route_terminal_result_bridge.py`
- `onboard/tests/test_o5_bounded_route_terminal_result_bridge.py`
- `docs/product/cloud_4g_infrastructure.md`
- `docs/product/remote_4g_mvp.md`
- `sprints/2026.07.14_00-24_o5_bounded_route_terminal_result_bridge/tech-done.md`

Product closeout 后允许修改：

- `sprints/2026.07.14_00-24_o5_bounded_route_terminal_result_bridge/side2side_check.md`
- `sprints/2026.07.14_00-24_o5_bounded_route_terminal_result_bridge/final.md`
- `OKR.md`
- `docs/process/okr_progress_log.md`

不得修改：

- 硬件参数、launch、UART、WAVE ROVER 驱动。
- PC/O7 UI。
- 历史 sprint artifact 内容。

## 接口影响

不改变现有 relay HTTP API。Bridge 只作为 CLI consumer 使用既有 API：

- `POST /api/commands/collect`
- `POST /robots/{robot_id}/commands/{command_id}/terminal-result`
- `GET /api/commands/{command_id}/result?robot_id=<robot_id>`

CLI 输出必须 phone-safe / artifact-safe，不回显 raw token、raw URL、local absolute path、traceback、DB/queue URL、Authorization、bearer、serial/UART、WAVE ROVER、ROS topic 或 `/cmd_vel`。

## 验收命令

Robot Software 必须运行并记录结果：

```bash
python3 -m py_compile onboard/scripts/o5_bounded_route_terminal_result_bridge.py onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py
python3 -m unittest onboard.tests.test_o5_bounded_route_terminal_result_bridge
python3 onboard/scripts/o5_bounded_route_terminal_result_bridge.py \
  --source-summary sprints/2026.07.13_23-23_o3_bounded_route_mock_execution/artifacts/algorithm/bounded_route_mock_execution_summary.json \
  --output sprints/2026.07.14_00-24_o5_bounded_route_terminal_result_bridge/artifacts/o5_bounded_route_terminal_result_bridge_summary.json
python3 -m json.tool sprints/2026.07.14_00-24_o5_bounded_route_terminal_result_bridge/artifacts/o5_bounded_route_terminal_result_bridge_summary.json >/dev/null
python3 - <<'PY'
import json
from pathlib import Path
p = Path("sprints/2026.07.14_00-24_o5_bounded_route_terminal_result_bridge/artifacts/o5_bounded_route_terminal_result_bridge_summary.json")
d = json.loads(p.read_text())
assert d["schema"] == "trashbot.o5.bounded_route_terminal_result_bridge.v1"
assert d["proof_boundary"] == "software_proof_o5_bounded_route_terminal_result_bridge_only"
assert d["source_schema"] == "trashbot.o3.bounded_route_mock_execution.v1"
assert d["terminal_result_state"] == "terminal_result_recorded"
assert d["reconciliation_state"] == "terminal_result_recorded"
assert d["task_id"] == "task_o3_28_pose_fixed_route_consumer_20260713_0402"
for key in [
    "delivery_success",
    "route_execution_success",
    "safe_to_control",
    "hil_pass",
    "robot_control_executed",
    "connects_cloud_production",
    "uses_base_uart",
    "publishes_cmd_vel",
    "calls_base_manual",
]:
    assert d[key] is False, key
print("bounded_route_terminal_result_bridge_acceptance_ok")
PY
rg -n "bounded_route_terminal_result_bridge|software_proof_o5_bounded_route_terminal_result_bridge_only|mock_route_execution_completed_not_live_delivery|terminal_result_recorded|cloud_command_result_reconciliation" onboard/scripts/o5_bounded_route_terminal_result_bridge.py onboard/tests/test_o5_bounded_route_terminal_result_bridge.py docs/product/cloud_4g_infrastructure.md docs/product/remote_4g_mvp.md sprints/2026.07.14_00-24_o5_bounded_route_terminal_result_bridge
git diff --check -- onboard/scripts/o5_bounded_route_terminal_result_bridge.py onboard/tests/test_o5_bounded_route_terminal_result_bridge.py docs/product/cloud_4g_infrastructure.md docs/product/remote_4g_mvp.md sprints/2026.07.14_00-24_o5_bounded_route_terminal_result_bridge
```

## 风险边界

- 本轮只证明 local/mock O5 terminal-result bridge 可执行。
- 不证明真实公网 HTTPS/TLS、4G/SIM、production DB/queue、worker cutover、OSS/CDN live traffic、真实手机/browser、真实 route execution、delivery/operator acceptance、HIL 或 safe-to-control。
- 若 source summary 缺失、schema 不匹配、identity 不完整、dangerous true field 出现、terminal result 未记录或 reconciliation 未回读，必须 fail closed，不得写通过 artifact。
