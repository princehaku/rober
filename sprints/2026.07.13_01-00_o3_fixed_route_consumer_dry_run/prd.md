# PRD - O3 Fixed Route Consumer Dry Run

## Product Problem

The 00:00 sprint created a route-intent packet, but it is still route material rather than route execution. It has stable identity and useful files, yet its pose materialization is partial: the source path proof says `path_point_count=21`, while the accepted packet only materializes 14 stdout-tail poses plus request start/goal anchors.

The next product problem is therefore not "create another packet". The next product problem is whether this packet can be consumed by a fixed-route dry-run consumer without motion, or whether the route material must be strengthened into full structured path poses before route execution can be planned.

## User Value And North Star

普通用户最终只关心小车能否可靠送达垃圾并给出可信状态。为了到达这个目标，产品需要一条可追溯的证据链：planner-only path proof -> route-intent packet -> consumer dry-run/material validation -> route execution record -> delivery/operator/HIL/production evidence.

This sprint owns the third step. It should make the route-intent packet usable by the next evidence producer while keeping every safety and mission claim conservative.

## Inputs

- `sprints/2026.07.13_00-00_o3_fixed_route_intent_replay_material/artifacts/algorithm/route_intent_summary.json`
- `sprints/2026.07.13_00-00_o3_fixed_route_intent_replay_material/artifacts/algorithm/route_intent_replay.jsonl`
- `sprints/2026.07.13_00-00_o3_fixed_route_intent_replay_material/artifacts/algorithm/route.csv`
- `route_intent_id=route_intent_20260713_0000_from_20260712_2157_path_proof`
- `task_id=task_o3_fixed_route_intent_20260713_0000`

## Product Requirements

P0 requirements:

- Build or run a strict no-motion fixed-route consumer dry-run/material validation against the 00:00 packet.
- Confirm identity consistency across summary, JSONL, CSV, source proof ref, and `task_id`.
- Confirm route order, start/goal anchors, frame fields, materialized pose count, and partial materialization boundary.
- Preserve source evidence fields: `path_generation_attempted=true`, `path_generated=true`, `path_point_count=21`, `fallback_mode=ros2_cli_action_send_goal`.
- Preserve safety and mission false fields: `route_execution_success=false`, `delivery_success=false`, `hil_pass=false`, plus all control/HIL false fields.
- Output one of:
  - consumer dry-run summary JSON plus dry-run events JSONL/CSV, or
  - stronger full structured path poses material if the dry-run consumer cannot be trusted with partial stdout-tail input.

P1 requirements:

- Emit clear `next_evidence_required` for route execution, delivery/operator acceptance, current live HIL, and production evidence.
- Keep O6/O7 future consumption in mind by using stable field names and safe relative refs.
- Fail closed on missing files, route identity mismatch, unsafe true fields, malformed JSONL/CSV, or unbounded claims.

## Non-Goals

This sprint must not do or claim:

- route execution
- NavigateToPose
- controller/BT execution
- `/cmd_vel`
- `/api/base/manual`
- WAVE ROVER UART
- hardware HIL
- delivery success
- safe-to-control
- production cloud/external evidence
- O5 support-only readiness packet or checklist
- standalone O6/O7 surface work

## OKR Mapping And Direction Judgment

- O5 remains the lowest current Objective at about `85%`, but Product pauses O5 support-only work because real external production evidence is still missing.
- O1 remains about `94%` after the 21:57 same-run planner-only path proof. This sprint can strengthen O3/O1 route material but should not move O1 unless it produces stronger evidence than consumer dry-run, such as route execution or HIL, which is out of scope here.
- O6/O7 remain about `93%`; they should only move if they later consume real or stronger mission material. This sprint does not implement their consumers.
- Direction: continue O3/O1 strict no-motion; do not archive KR.

## Acceptance Criteria

Accept if `robot-algorithm-engineer` produces a material validation package that includes:

- stable `route_intent_id` and `task_id`
- consumed refs to 00:00 `route_intent_summary.json`, `route_intent_replay.jsonl`, and `route.csv`
- dry-run result or stronger full structured path material
- pass/fail details for identity, order, frame, pose count, start/goal anchors, and safety invariants
- `strict no-motion` boundary text
- `route_execution_success=false`
- `delivery_success=false`
- `hil_pass=false`
- next exact command or evidence class for the following sprint

Reject if the output:

- repeats the 00:00 packet without a consumer validation delta
- claims full 21-point replay while only using `partial_stdout_tail_only`
- claims route execution, delivery, HIL, safe-to-control, production cloud, NavigateToPose, `/cmd_vel`, `/api/base/manual`, or WAVE ROVER UART
- lacks structured validation output
- hides a parse/schema blocker behind Product wording

## Responsible Engineer

- Primary owner: `robot-algorithm-engineer`
- Product acceptance: `product-okr-owner`
- Robot Software: support only if a helper/export path blocks material production
- Hardware: not involved unless a future sprint explicitly enters real hardware/HIL; this sprint must not touch hardware facts or vendor-backed configuration
- Full-stack: not involved unless a future O7 sprint consumes the dry-run material

## Evidence And Risk

Known risk: the current packet is partial stdout-tail material. If consumer dry-run cannot produce a reliable route-order validation, the accepted result should be a narrow blocker or a full structured path export plan/material, not an execution claim.

Required remaining evidence after this sprint:

- explicit route execution record
- delivery/operator acceptance
- current live HIL
- safe-to-control proof
- production external evidence for O5
