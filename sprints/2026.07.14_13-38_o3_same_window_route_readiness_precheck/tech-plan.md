# Tech Plan - O3 Same-Window Route Readiness Precheck

## Sprint Metadata

- sprint_type: epic
- Sprint: `sprints/2026.07.14_13-38_o3_same_window_route_readiness_precheck/`
- Product owner: `product-okr-owner`
- Implementation owner: `robot-algorithm-engineer`
- Proof boundary: `software_proof_o3_o1_same_window_route_readiness_precheck_only`
- Implementation mode: single-owner closure.

## OKR 最低优先级核对

1. 当前 `OKR.md` 4.1 里完成度最低的 Objective 是 O5，约 `85%`。O1 约 `94%`，O6/O7 约 `93%`。
2. 本 sprint 不直接针对 O5。
3. 原因：O5 当前缺 success-class production/cloud evidence、真实 4G/SIM、production DB/queue、OSS/CDN live traffic、真实手机/browser proof；最近 terminal-result bridge/intake/export/reconciliation、delivery-state live-success、operator gate、CDN/TLS 4xx 等 support-only slices 已明确不能重复消费。
4. 最近 O7 voice runtime preflight、offline smoke、voice speaker ACK/failure、voice TTS draft 也已消费；未获授权的 real voice runtime smoke 不能继续推进。
5. 本 sprint 转向 O3/O1 strict no-motion route-readiness precheck，消费已有 bounded plan/mock execution/controlled gate material，只做 same-window live route blocker 收敛。预期 O5 继续约 `85%`，O1 继续约 `94%`，O6/O7 继续约 `93%`，KR `不归档`。

## Direction and Evidence Boundary

方向判断：`调整`。本轮从 O5/O7 support-only wrapper 循环切到 O3/O1 route execution 前置证据。

本轮必须证明的是：已接受的 same-task route material 可以被 Algorithm 层 fail-closed precheck 消费，并输出下一次 same-window live route/HIL 前必须补齐的证据清单。

本轮不得证明：route execution、fixed-route movement、Nav2 controller/BT execution、delivery success、operator acceptance、current live HIL、safe-to-control、O5 production/cloud、真实机器人控制或真实硬件集成。

Required no-motion guards:

- no /cmd_vel
- no /api/base/manual
- no NavigateToPose
- no WAVE ROVER UART

Required false fields:

- `route_execution_success=false`
- `delivery_success=false`
- `hil_pass=false`
- `safe_to_control=false`
- `robot_control_executed=false`
- `publishes_cmd_vel=false`
- `calls_base_manual=false`
- `uses_base_uart=false`

## Owner 分工

- `robot-algorithm-engineer`: implement, test, repair, and update `tech-done.md`.
- `product-okr-owner`: after implementation evidence exists, review `tech-done.md`, update `side2side_check.md`, `final.md`, `OKR.md`, and progress log.
- No parallel owner needed. The file scope is Algorithm route evidence only.

## 文件范围

Implementation owner may edit only the smallest necessary subset under:

- `onboard/scripts/o3_same_window_route_readiness_precheck.py`
- `onboard/tests/test_o3_same_window_route_readiness_precheck.py`
- `docs/navigation/same_window_route_readiness_precheck.md`
- `sprints/2026.07.14_13-38_o3_same_window_route_readiness_precheck/tech-done.md`
- `sprints/2026.07.14_13-38_o3_same_window_route_readiness_precheck/artifacts/algorithm/`

Implementation owner must not edit:

- WAVE ROVER, ESP32, UART, Orange Pi hardware config, launch control parameters, `/cmd_vel`, `/api/base/manual`, NavigateToPose, Nav2 controller/BT execution, or production cloud code.
- O7 voice runtime, O6/O7 readback/export/action receipt, O5 terminal-result, delivery-state, operator gate, CDN/TLS, or cloud wrapper code.
- Existing closed sprint files.
- `OKR.md`, `docs/process/okr_progress_log.md`, `side2side_check.md`, or `final.md` before Product acceptance.

## Input Contract

Primary read-only inputs:

- `sprints/2026.07.13_07-07_o3_controlled_route_execution_gate_record/artifacts/algorithm/controlled_route_execution_gate_record.json`
- `sprints/2026.07.13_08-09_o3_bounded_route_command_plan/artifacts/algorithm/bounded_route_command_plan.json`
- `sprints/2026.07.13_23-23_o3_bounded_route_mock_execution/artifacts/algorithm/bounded_route_mock_execution_summary.json`
- `sprints/2026.07.13_23-23_o3_bounded_route_mock_execution/artifacts/algorithm/bounded_route_mock_execution_progress.jsonl`

Optional read-only context:

- `sprints/2026.07.13_10-12_o1_live_stop_hil_capture_gate/artifacts/hardware/stop_hil_capture_gate.json`

Required source facts:

- `packet_id=packet_o3_28_pose_same_task_replay_7d57826142b0c79c`
- `task_id=task_o3_28_pose_fixed_route_consumer_20260713_0402`
- `route_intent_id=route_intent_20260713_0402_from_20260713_0300_28_pose_structured_path`
- `route_csv_row_count=28`
- `segment_count=27`
- `mock_execution_status=mock_route_execution_completed_not_live_route_execution`
- all source control/success fields remain false.

If identity, counts, schemas, source statuses, or false fields drift, the precheck must fail closed and not write a success-shaped artifact.

## Output Contract

Create a CLI:

```bash
python3 onboard/scripts/o3_same_window_route_readiness_precheck.py \
  --gate-record sprints/2026.07.13_07-07_o3_controlled_route_execution_gate_record/artifacts/algorithm/controlled_route_execution_gate_record.json \
  --bounded-plan sprints/2026.07.13_08-09_o3_bounded_route_command_plan/artifacts/algorithm/bounded_route_command_plan.json \
  --mock-execution-summary sprints/2026.07.13_23-23_o3_bounded_route_mock_execution/artifacts/algorithm/bounded_route_mock_execution_summary.json \
  --mock-execution-progress sprints/2026.07.13_23-23_o3_bounded_route_mock_execution/artifacts/algorithm/bounded_route_mock_execution_progress.jsonl \
  --output-dir sprints/2026.07.14_13-38_o3_same_window_route_readiness_precheck/artifacts/algorithm
```

Expected output:

- `same_window_route_readiness_precheck_summary.json`

Summary must include:

- `schema=trashbot.o3.same_window_route_readiness_precheck.v1`
- `same_window_route_readiness_status=blocked_missing_same_window_live_evidence`
- `proof_boundary=software_proof_o3_o1_same_window_route_readiness_precheck_only`
- exact source identity and counts from the route chain
- accepted source artifact refs and short status summary
- `missing_evidence` with explicit operator approval, current live stop/HIL, same-window `/scan`, AMCL pose, dynamic `map_to_odom`, Nav2/controller result, and delivery/operator acceptance
- `next_live_capture_allowed=false`
- all required false fields listed above
- rejected claims covering route execution, fixed-route movement, Nav2 controller/BT, `/cmd_vel`, `/api/base/manual`, NavigateToPose, WAVE ROVER UART, HIL, delivery, safe-to-control, and O5 production/cloud evidence

## 接口影响

No runtime ROS2 interface should change. This is an offline artifact generator and tests only.

No robot-side endpoint, ROS2 topic publisher, serial path, hardware config, cloud endpoint, O6 archive endpoint, O7 UI/API, microphone/speaker runtime, TTS provider call, ASR provider call, or robot control path may be introduced.

## 验收命令

Implementation owner must run and report:

```bash
python3 -m py_compile onboard/scripts/o3_same_window_route_readiness_precheck.py
```

```bash
python3 -m unittest onboard.tests.test_o3_same_window_route_readiness_precheck
```

```bash
python3 onboard/scripts/o3_same_window_route_readiness_precheck.py \
  --gate-record sprints/2026.07.13_07-07_o3_controlled_route_execution_gate_record/artifacts/algorithm/controlled_route_execution_gate_record.json \
  --bounded-plan sprints/2026.07.13_08-09_o3_bounded_route_command_plan/artifacts/algorithm/bounded_route_command_plan.json \
  --mock-execution-summary sprints/2026.07.13_23-23_o3_bounded_route_mock_execution/artifacts/algorithm/bounded_route_mock_execution_summary.json \
  --mock-execution-progress sprints/2026.07.13_23-23_o3_bounded_route_mock_execution/artifacts/algorithm/bounded_route_mock_execution_progress.jsonl \
  --output-dir sprints/2026.07.14_13-38_o3_same_window_route_readiness_precheck/artifacts/algorithm
```

```bash
python3 -m json.tool sprints/2026.07.14_13-38_o3_same_window_route_readiness_precheck/artifacts/algorithm/same_window_route_readiness_precheck_summary.json >/dev/null
```

```bash
python3 - <<'PY'
import json
from pathlib import Path
summary = json.loads(Path("sprints/2026.07.14_13-38_o3_same_window_route_readiness_precheck/artifacts/algorithm/same_window_route_readiness_precheck_summary.json").read_text())
assert summary["schema"] == "trashbot.o3.same_window_route_readiness_precheck.v1"
assert summary["same_window_route_readiness_status"] == "blocked_missing_same_window_live_evidence"
assert summary["proof_boundary"] == "software_proof_o3_o1_same_window_route_readiness_precheck_only"
assert summary["packet_id"] == "packet_o3_28_pose_same_task_replay_7d57826142b0c79c"
assert summary["task_id"] == "task_o3_28_pose_fixed_route_consumer_20260713_0402"
assert summary["route_csv_row_count"] == 28
assert summary["segment_count"] == 27
for key in ("route_execution_success", "delivery_success", "hil_pass", "safe_to_control", "robot_control_executed", "publishes_cmd_vel", "calls_base_manual", "uses_base_uart", "next_live_capture_allowed"):
    assert summary[key] is False
for required in ("explicit_operator_approval", "current_live_stop_hil", "same_window_scan_readiness", "same_window_amcl_pose_readiness", "same_window_map_to_odom_tf_readiness", "nav2_controller_result", "delivery_or_operator_acceptance"):
    assert required in summary["missing_evidence"]
print("same_window_route_readiness_precheck_acceptance_ok")
PY
```

```bash
rg -n "same_window_route_readiness_precheck|blocked_missing_same_window_live_evidence|software_proof_o3_o1_same_window_route_readiness_precheck_only|route_execution_success=false|delivery_success=false|hil_pass=false|safe_to_control=false|no /cmd_vel|no /api/base/manual|no NavigateToPose|no WAVE ROVER UART" \
  onboard/scripts/o3_same_window_route_readiness_precheck.py \
  onboard/tests/test_o3_same_window_route_readiness_precheck.py \
  docs/navigation/same_window_route_readiness_precheck.md \
  sprints/2026.07.14_13-38_o3_same_window_route_readiness_precheck
```

```bash
git diff --check -- \
  onboard/scripts/o3_same_window_route_readiness_precheck.py \
  onboard/tests/test_o3_same_window_route_readiness_precheck.py \
  docs/navigation/same_window_route_readiness_precheck.md \
  sprints/2026.07.14_13-38_o3_same_window_route_readiness_precheck
```

## 子 Agent Prompt 要点

When dispatching the implementation owner, include:

- Role: `robot-algorithm-engineer`
- Task: implement strict no-motion O3/O1 same-window route readiness precheck artifact.
- File scope: script, test, navigation doc, this sprint `tech-done.md`, and this sprint `artifacts/algorithm/`.
- Required proof boundary: `software_proof_o3_o1_same_window_route_readiness_precheck_only`.
- Required status: `blocked_missing_same_window_live_evidence`.
- Required no-motion guards and false fields listed above.
- Required validation commands listed above.

## Product Acceptance Gate

Product should accept only if:

- the artifact consumes the existing route chain instead of inventing a new route identity;
- the result is a blocker/readiness precheck, not route execution;
- all live control, HIL, delivery, and production claims are fixed false;
- the missing evidence list directly prepares the next live route/HIL capture sprint;
- `tech-done.md` records actual files, validation output, failure/repair notes if any, remaining risk, and next required live evidence.

Product should keep KR status as `不归档`; this sprint is not mission-grade evidence and should keep OKR percentages flat.
