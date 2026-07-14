# Tech Done - O3 Lifecycle CLI Budget Recovery

## Sprint Metadata

- sprint_type: epic
- Sprint: `sprints/2026.07.12_08-55_o3_lifecycle_cli_budget_recovery/`
- Owner: `robot-software-engineer`
- Proof boundary: `software_proof_o3_o1_strict_no_motion_lifecycle_cli_budget_recovery_only`
- Closeout time: 2026-07-12 09:22 Asia/Shanghai

## Actual Changes

- `onboard/scripts/o10_amcl_nav2_runtime_proof.py`
  - Added `lifecycle_cli_budget_recovery` command-summary fields for `/map_server` and `/amcl`.
  - Added first/retry lifecycle attempts with 10s first budget and retry budget derived from `--timeout-s` capped at 24s.
  - Preserved command, timeout budget, elapsed, stdout, stderr, returncode, timed_out, graph visibility, final classification, and next step.
  - Moved lifecycle readback before AMCL/TF downstream collection.
  - Skipped `/scan`, `/map`, `/odom`, AMCL node info, map server info, and TF source probes until lifecycle readback is clean.
  - Treated captured `active [3]` stdout as `active` even when a process-level timeout had already occurred.

- `onboard/tests/test_nav2_runtime_proof_helper.py`
  - Added tests for first/retry lifecycle budget recovery.
  - Added tests for active first-attempt retry skip.
  - Added tests for active stdout with timeout.
  - Added text anchor test for downstream skip boundaries.

- `docs/navigation/field_route_evidence_preflight.md`
  - Documented `08-55` lifecycle CLI budget recovery fields and live artifact interpretation.

- `docs/navigation/fixed_route_workflow.md`
  - Documented fixed-route read order: lifecycle first, downstream/path only after `/map_server` and `/amcl` are clean.

- `sprints/2026.07.12_08-55_o3_lifecycle_cli_budget_recovery/artifacts/`
  - Wrote local and live raw artifacts.

## Verification Results

```bash
python3 -m py_compile onboard/scripts/o10_amcl_nav2_runtime_proof.py
```

- RC: 0

```bash
python3 -m unittest onboard.tests.test_nav2_runtime_proof_helper
```

- RC: 0
- Result: `Ran 104 tests in 2.253s - OK`

```bash
mkdir -p sprints/2026.07.12_08-55_o3_lifecycle_cli_budget_recovery/artifacts
python3 onboard/scripts/o10_amcl_nav2_runtime_proof.py \
  --strict-no-motion \
  --no-base-uart \
  --timeout-s 18 \
  --output-json sprints/2026.07.12_08-55_o3_lifecycle_cli_budget_recovery/artifacts/local_o10_lifecycle_cli_budget_recovery.raw.json
```

- RC: 2
- Expected on macOS: blocked because `/opt/ros/humble/setup.bash` is missing.
- Key fields: `status=blocked_with_root_cause`, `board_source_preflight.classification=board_source_preflight_source_failed`, `map_lifecycle_preflight.classification=map_lifecycle_preflight_skipped_without_ros2_cli`.
- Safety: `safe_to_control=false`, `publishes_cmd_vel=false`, `calls_base_manual=false`, `uses_base_uart=false`, `path_generation_attempted=false`, `path_generated=false`.

```bash
scp -P 37878 onboard/scripts/o10_amcl_nav2_runtime_proof.py \
  root@192.168.1.11:/root/rober/onboard/scripts/o10_amcl_nav2_runtime_proof.py
```

- RC: 0

```bash
ssh -p 37878 root@192.168.1.11 \
  'cd /root/rober/onboard && /usr/bin/timeout 420s /usr/bin/python3.10 scripts/o10_amcl_nav2_runtime_proof.py --strict-no-motion --no-base-uart --timeout-s 18 --output-json /tmp/live_o10_lifecycle_cli_budget_recovery.raw.json'
```

- RC: 2
- Meaning: helper returned `blocked_with_root_cause`; SSH transport succeeded.

```bash
scp -P 37878 root@192.168.1.11:/tmp/live_o10_lifecycle_cli_budget_recovery.raw.json \
  sprints/2026.07.12_08-55_o3_lifecycle_cli_budget_recovery/artifacts/live_o10_lifecycle_cli_budget_recovery.raw.json
```

- RC: 0

## Live Artifact Key Fields

Artifact:
`sprints/2026.07.12_08-55_o3_lifecycle_cli_budget_recovery/artifacts/live_o10_lifecycle_cli_budget_recovery.raw.json`

- `status=blocked_with_root_cause`
- `proof.board_source_preflight.classification=board_source_preflight_ready`
- `proof.map_lifecycle_preflight.classification=map_lifecycle_preflight_map_server_inactive`
- `proof.map_lifecycle_preflight.blocking_reasons.map_server=map_server_lifecycle_command_failed`
- `/map_server` first attempt: `classification=lifecycle_command_timeout`, `timeout_s=10.0`, `timed_out=true`
- `/map_server` retry attempt: `classification=lifecycle command failed`, `timeout_s=18.0`, `returncode=1`, `stderr="Node not found\n"`
- `/amcl` first attempt: `classification=lifecycle_command_timeout`, `timeout_s=10.0`, `timed_out=true`
- `/amcl` retry attempt: `classification=active`, `timeout_s=18.0`, `returncode=0`, stdout contains `active [3]`
- `downstream_recovery_summary.lifecycle_readback_clean=false`
- `commands.scan_once.boundary=scan_probe_skipped_until_lifecycle_cli_readback_clean`
- `commands.map_once.boundary=map_probe_skipped_until_lifecycle_cli_readback_clean`
- `commands.odom_once.boundary=odom_probe_skipped_until_lifecycle_cli_readback_clean`
- `commands.tf_source_probe.boundary=tf_source_probe_skipped_until_lifecycle_cli_readback_clean`

Safety fields:

- `safe_to_control=false`
- `publishes_cmd_vel=false`
- `calls_base_manual=false`
- `robot_control_executed=false`
- `route_execution_success=false`
- `delivery_success=false`
- `hil_pass=false`
- `uses_base_uart=false`
- `path_generation_attempted=false`
- `path_generated=false`

## Failure Location

The current live root cause is no longer generic lifecycle timeout for both nodes.

- `/amcl` recovered to `active [3]` on retry.
- `/map_server` did not recover; retry returned `Node not found`.
- Lifecycle graph visibility probe itself timed out, while daemon-safe readback later observed graph/topic recovery and a node list that included `/amcl`, `/planner_server`, `/lifecycle_manager`, and LiDAR/static TF nodes but not `/map_server`.

Current next blocker: restore `/map_server` graph/lifecycle visibility before consuming `/scan`, `/map`, `/tf`, or path-generation downstream evidence.

## Remaining Risk

- This is no-motion diagnostic evidence only; it does not prove localization, planner path, route execution, HIL, delivery, or production/cloud evidence.
- The live board still reports package availability root causes in this helper run; that may be a sourced CLI/package-list budget artifact and should not override the direct lifecycle finding without a dedicated package readback.
- `RTPS_TRANSPORT_SHM` warnings appeared in `/amcl` retry stdout; they did not prevent `active [3]`, but they are still relevant for daemon/DDS graph stability.

## Collaboration Needed

- Product: keep OKR percentage flat; this is supporting O3/O1 diagnostic delta, not mission progress.
- Robot Software: next owner for `/map_server` lifecycle/graph visibility recovery.
- Hardware: not required; no WAVE ROVER, UART, voltage, wiring, or mechanical facts were touched.
- Algorithm: not required until lifecycle readback is clean and downstream `/scan`/`/map`/TF evidence can be collected.
- Full-stack: not required.

## No-Motion Confirmation

This sprint did not call NavigateToPose, did not publish `/cmd_vel`, did not call `/api/base/manual`, and did not open WAVE ROVER UART.
