# PRD - O3 Bounded Route Mock Execution

## Problem

The project has a fresh same-task route material chain through 28 route poses and a bounded command plan, but no safe intermediate artifact that rehearses segment-by-segment route progress without touching live control paths.

Repeating the bounded-plan packaging would not add value. The next non-repeating software step is to run a deterministic mock execution simulation that proves the route material can drive a route-progress state machine while preserving all live-control boundaries.

## User Value

The simulator gives future live route execution a tighter input and expected progress contract:

- Operators can inspect whether every bounded segment produces a progress event.
- Product can distinguish "route progress state machine works in mock" from "robot moved".
- Algorithm can later compare live controller feedback against the same segment order and expected cumulative distance.

## Scope

In scope:

- A local CLI simulator that consumes the accepted bounded route command plan.
- A summary JSON artifact and JSONL progress trace.
- Unit tests for valid simulation, input drift, unsafe true fields, and progress invariants.
- Navigation documentation for the mock-only boundary and next live evidence requirements.
- Sprint closeout records with actual changes, verification, and remaining risk.

Out of scope:

- Real `/cmd_vel`, `/api/base/manual`, NavigateToPose, WAVE ROVER UART, live HIL, or controller/BT execution.
- O6/O7 archive/readback/UI wrapper work.
- Production cloud, CDN, DB/queue, OSS, 4G/SIM, or phone/browser evidence.
- Any OKR percentage increase unless Product acceptance later decides mock execution materially changes scoring.

## Acceptance Criteria

- The artifact schema is `trashbot.o3.bounded_route_mock_execution.v1`.
- The proof boundary is `software_proof_o3_o1_bounded_route_mock_execution_only`.
- The mock status is `mock_route_execution_completed_not_live_route_execution`.
- The summary preserves exact accepted identity:
  - `packet_id=packet_o3_28_pose_same_task_replay_7d57826142b0c79c`
  - `task_id=task_o3_28_pose_fixed_route_consumer_20260713_0402`
  - `route_intent_id=route_intent_20260713_0402_from_20260713_0300_28_pose_structured_path`
  - `route_csv_row_count=28`
  - `segment_count=27`
- The JSONL progress trace has exactly `27` segment completion events with monotonic `segment_index`, `to_order`, elapsed time, and cumulative distance.
- All live-control and success fields remain explicitly false.
- Tests and scoped diff checks pass.
