# Side2Side Check - O3 Lifecycle CLI Budget Recovery

## Sprint Metadata

- sprint_type: epic
- Sprint: `sprints/2026.07.12_08-55_o3_lifecycle_cli_budget_recovery/`
- Product owner: `product-okr-owner`
- Implementation owner: `robot-software-engineer`
- Product acceptance time: `2026-07-12 09:29 Asia/Shanghai`
- Proof boundary: `software_proof_o3_o1_strict_no_motion_lifecycle_cli_budget_recovery_only`

## Product Acceptance Judgment

Product accepts this sprint as an O3/O1 strict no-motion diagnostic delta only.

The user value is not a new route or delivery result. The value is that the real-board lifecycle readback moved from a broad timeout bucket to a more actionable split: source and lightweight CLI readiness stayed clean, `/amcl` recovered to `active [3]` on retry, while `/map_server` still failed graph/lifecycle visibility with `Node not found`.

This is not path generation, route execution, delivery/operator acceptance, current live HIL, safe-to-control evidence, production cloud evidence, or any proof that the robot can move.

## Evidence Checked

- `tech-done.md` records Robot Software changes for `lifecycle_cli_budget_recovery`, first/retry lifecycle command summaries, tests, local dry-run, board scp/run/pull, and scoped diff check.
- Live artifact: `artifacts/live_o10_lifecycle_cli_budget_recovery.raw.json`.
- Artifact status: `status=blocked_with_root_cause`, `evidence_type=blocked_with_root_cause`.
- Readiness did not regress: `board_source_preflight_ready`, `lightweight_cli_ready=true`, `cli_ready=true`, `runtime_ready=true`.
- Lifecycle result: `map_lifecycle_preflight_map_server_inactive` with `map_server_lifecycle_command_failed`.
- `/map_server` first attempt: `lifecycle_command_timeout`.
- `/map_server` retry: `returncode=1`, `stderr="Node not found\n"`.
- `/amcl` first attempt: `lifecycle_command_timeout`.
- `/amcl` retry: stdout contains `active [3]`.
- Downstream probes were correctly gated: `scan_probe_skipped_until_lifecycle_cli_readback_clean`, `map_probe_skipped_until_lifecycle_cli_readback_clean`, `odom_probe_skipped_until_lifecycle_cli_readback_clean`, `tf_source_probe_skipped_until_lifecycle_cli_readback_clean`.

## Safety Check

Accepted safety fields remain fail-closed:

- `path_generation_attempted=false`
- `path_generated=false`
- `safe_to_control=false`
- `publishes_cmd_vel=false`
- `calls_base_manual=false`
- `robot_control_executed=false`
- `route_execution_success=false`
- `delivery_success=false`
- `hil_pass=false`
- `uses_base_uart=false`

No NavigateToPose, no `/cmd_vel`, no `/api/base/manual`, and no WAVE ROVER UART evidence was introduced.

## OKR Decision

- O5 remains about `85%`; this sprint does not provide external production evidence.
- O1 remains about `93%`; this sprint does not provide current live HIL, current same-run path generation success, or Nav2 route execution success.
- O6 remains about `93%`; this sprint does not provide live route execution, delivery record, operator acceptance, or production readback material.
- O7 remains about `93%`; this sprint does not provide new operator-facing evidence consumption beyond the diagnostic chain.
- `不调整` OKR percentage.
- `不归档` KR.

## Next Owner And Gate

Next owner should be `robot-software-engineer`.

Next blocker: restore `/map_server` graph/lifecycle visibility. The next sprint should prove whether `/map_server` is absent from the graph, blocked by lifecycle manager/process startup, hidden by daemon/DDS graph visibility, or failing due to helper lifecycle command timing.

`robot-algorithm-engineer` should join only after lifecycle readback is clean enough to consume `/scan`, `/map`, TF, and planner/path readiness. `rober-hardware-engineer` is not needed unless new evidence proves LiDAR serial/runtime/wiring facts.
