# Tech Plan - O3 Bounded Route Mock Execution

## Sprint Metadata

- sprint_type: epic
- Sprint: `sprints/2026.07.13_23-23_o3_bounded_route_mock_execution/`
- Owner: `robot-algorithm-engineer`
- Proof boundary: `software_proof_o3_o1_bounded_route_mock_execution_only`

## OKR 最低优先级核对

1. 当前 `OKR.md` 里完成度最低的 Objective 是 O5，约 `85%`。
2. 本 sprint 不直接针对 O5。
3. 原因：O5 最新两类可推进软件工作已经关闭为 support-only：13:13/19:19 CDN/TLS 4xx probe/readiness packet consumption，以及 22:20 cloud external review-decision gate。当前缺口是 success-class real external production evidence；本环境没有新的真实公网/生产 DB/queue/OSS/4G/phone-browser 材料。继续写 O5 wrapper 会重复消费同一 blocker。本 sprint 转向 O1/O3 的不重复 mock route execution simulation，使用已接受 28-pose bounded route material推进可验证软件闭环。

## Implementation Scope

Allowed write paths:

- `onboard/scripts/o3_bounded_route_mock_execution.py`
- `onboard/tests/test_o3_bounded_route_mock_execution.py`
- `docs/navigation/bounded_route_mock_execution.md`
- `sprints/2026.07.13_23-23_o3_bounded_route_mock_execution/tech-done.md`
- `sprints/2026.07.13_23-23_o3_bounded_route_mock_execution/artifacts/algorithm/`

Do not modify outside this scope without returning to the main node for approval.

## Input Contract

Primary input:

- `sprints/2026.07.13_08-09_o3_bounded_route_command_plan/artifacts/algorithm/bounded_route_command_plan.json`

Required accepted source facts:

- `schema=trashbot.o3.bounded_route_command_plan.v1`
- `execution_plan_status=blocked_pending_live_safety_gate`
- `packet_id=packet_o3_28_pose_same_task_replay_7d57826142b0c79c`
- `task_id=task_o3_28_pose_fixed_route_consumer_20260713_0402`
- `route_intent_id=route_intent_20260713_0402_from_20260713_0300_28_pose_structured_path`
- `route_csv_row_count=28`
- `segment_count=27`
- no-motion guards include `no /cmd_vel`, `no /api/base/manual`, `no NavigateToPose`, `no WAVE ROVER UART`
- required false fields: `route_execution_success`, `delivery_success`, `hil_pass`, `safe_to_control`, `robot_control_executed`, `publishes_cmd_vel`, `calls_base_manual`, `uses_base_uart`

## Output Contract

Create a CLI:

```bash
python3 onboard/scripts/o3_bounded_route_mock_execution.py \
  --bounded-plan sprints/2026.07.13_08-09_o3_bounded_route_command_plan/artifacts/algorithm/bounded_route_command_plan.json \
  --output-dir sprints/2026.07.13_23-23_o3_bounded_route_mock_execution/artifacts/algorithm
```

Expected outputs:

- `bounded_route_mock_execution_summary.json`
- `bounded_route_mock_execution_progress.jsonl`

Summary must include:

- `schema=trashbot.o3.bounded_route_mock_execution.v1`
- `mock_execution_status=mock_route_execution_completed_not_live_route_execution`
- `proof_boundary=software_proof_o3_o1_bounded_route_mock_execution_only`
- source identity and counts from the bounded plan
- `mock_segment_progress_count=27`
- `progress_jsonl_event_count=27`
- `mock_execution_completed=true`
- fixed false fields, including all live-control and success claims
- rejected claims covering live route execution, fixed-route movement, controller/BT execution, `/cmd_vel`, `/api/base/manual`, NavigateToPose, WAVE ROVER UART, HIL, delivery, safe-to-control, and O5 production evidence

Progress JSONL must include one safe progress event per segment:

- `event_type=mock_segment_completed_not_live_control`
- `segment_index`
- `from_order`
- `to_order`
- `distance_m`
- `elapsed_s`
- `cumulative_distance_m`
- `safe_to_control=false`
- `route_execution_success=false`

## Verification Commands

The worker must run and report:

```bash
python3 -m py_compile onboard/scripts/o3_bounded_route_mock_execution.py
```

```bash
python3 -m unittest onboard.tests.test_o3_bounded_route_mock_execution
```

```bash
python3 onboard/scripts/o3_bounded_route_mock_execution.py \
  --bounded-plan sprints/2026.07.13_08-09_o3_bounded_route_command_plan/artifacts/algorithm/bounded_route_command_plan.json \
  --output-dir sprints/2026.07.13_23-23_o3_bounded_route_mock_execution/artifacts/algorithm
```

```bash
python3 -m json.tool sprints/2026.07.13_23-23_o3_bounded_route_mock_execution/artifacts/algorithm/bounded_route_mock_execution_summary.json >/dev/null
```

```bash
python3 - <<'PY'
import json
from pathlib import Path
summary = json.loads(Path("sprints/2026.07.13_23-23_o3_bounded_route_mock_execution/artifacts/algorithm/bounded_route_mock_execution_summary.json").read_text())
events = [json.loads(line) for line in Path("sprints/2026.07.13_23-23_o3_bounded_route_mock_execution/artifacts/algorithm/bounded_route_mock_execution_progress.jsonl").read_text().splitlines()]
assert summary["schema"] == "trashbot.o3.bounded_route_mock_execution.v1"
assert summary["mock_execution_status"] == "mock_route_execution_completed_not_live_route_execution"
assert summary["proof_boundary"] == "software_proof_o3_o1_bounded_route_mock_execution_only"
assert summary["mock_segment_progress_count"] == 27
assert summary["progress_jsonl_event_count"] == 27
assert len(events) == 27
assert [event["segment_index"] for event in events] == list(range(27))
assert all(event["event_type"] == "mock_segment_completed_not_live_control" for event in events)
for key in ("route_execution_success", "delivery_success", "hil_pass", "safe_to_control", "robot_control_executed", "publishes_cmd_vel", "calls_base_manual", "uses_base_uart"):
    assert summary[key] is False
    assert all(event.get(key, False) is False for event in events if key in event)
print("bounded_route_mock_execution_acceptance_ok")
PY
```

```bash
rg -n "bounded_route_mock_execution|mock_route_execution_completed_not_live_route_execution|software_proof_o3_o1_bounded_route_mock_execution_only|route_execution_success=false|safe_to_control=false" \
  onboard/scripts/o3_bounded_route_mock_execution.py \
  onboard/tests/test_o3_bounded_route_mock_execution.py \
  docs/navigation/bounded_route_mock_execution.md \
  sprints/2026.07.13_23-23_o3_bounded_route_mock_execution
```

```bash
git diff --check -- \
  onboard/scripts/o3_bounded_route_mock_execution.py \
  onboard/tests/test_o3_bounded_route_mock_execution.py \
  docs/navigation/bounded_route_mock_execution.md \
  sprints/2026.07.13_23-23_o3_bounded_route_mock_execution
```

## Risk Boundary

- This sprint must keep OKR wording conservative. It may be accepted as local/mock route-progress simulation only.
- It must not mark route execution, delivery, HIL, safe-to-control, O5 production, or KR archival as complete.
- If any validation fails, the worker must diagnose, repair, rerun, and record the failure and fix in `tech-done.md`.
