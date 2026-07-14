# Tech Plan - O3 Scan QoS Endpoint Readback Split

## Objective

Robot Software 单 owner 继续 O3/O1 strict no-motion，first split 当前 canonical blocker：

`/scan_reliable_and_best_effort_timeout`

本 sprint 从 18:56 accepted artifact 出发：`map_server_active=true`、`amcl_active=true`、`managed_runtime_log_lifecycle_readback.clean=true`、`map_once_observed=true`。不得无证据回退到 lifecycle、map_server configure/on_configure、loadmap、graph timeout wrapper 或 O5 support-only。

## OKR 最低优先级核对

- 当前 `OKR.md` 4.1 / 当前推进区完成度最低的 Objective：O5，约 `85%`。
- 本 sprint 是否针对最低 Objective：否。
- 不针对 O5 的理由：O5 当前缺真实 production/external evidence。继续做 local support-only、wrapper、readiness packet、cutover checklist、external probe readback 或状态面板不会产生 `external_artifact_delta`，只会重复 `okr_credit_allowed=false`，不计 OKR 增量。
- 本 sprint 选择 O3/O1 strict no-motion 的理由：18:56 已把 `/map_server`、AMCL、`/map` sample 推到可接受 baseline，当前最近可执行 blocker 是 `/scan_reliable_and_best_effort_timeout`。拆清它是恢复 `/amcl_pose`、dynamic `map->odom`、same-run path generation、route execution、delivery/operator evidence 的前置条件。
- 收口复核口径：若本轮只产生 readback/helper/docs 或 blocker narrowing，O5/O1/O6/O7 百分比保持 flat；若产生 same-run path generation、route execution、delivery/operator acceptance、current live HIL 或 real production external evidence，Product 再另行评估 OKR percentage update 和 KR 归档。

## Owner, Priority, And Role Split

- P0 owner: `Robot Software`.
- Product owner: `product-okr-owner` only for acceptance and final OKR wording.
- Algorithm: wait until `/scan`, `/amcl_pose`, and dynamic `map->odom` are clean enough for planner-only path proof.
- Hardware: wait until LiDAR runtime/serial/wiring becomes primary after endpoint/QoS/window/ROS readback is separated; then read `docs/vendor/VENDOR_INDEX.md` before any hardware conclusion.
- Full-stack: not involved; independent O7 surface/checklist/handoff is frozen for this sprint.

Priority order:

1. Preserve 18:56 lifecycle-active baseline and canonical artifact fields.
2. Split `/scan_reliable_and_best_effort_timeout` into publisher endpoint vs QoS/window/ROS readback vs LiDAR runtime.
3. Keep all strict no-motion safety booleans false.
4. Emit next-owner decision without claiming mission progress.

## Planned File Scope For Robot Software

Allowed implementation files:

- `onboard/scripts/o10_amcl_nav2_runtime_proof.py`
- `onboard/scripts/o11_nav2_lifecycle.sh`
- `onboard/tests/test_nav2_runtime_proof_helper.py`
- `docs/navigation/field_route_evidence_preflight.md`
- `docs/navigation/fixed_route_workflow.md`
- `sprints/2026.07.12_19-56_o3_scan_qos_endpoint_readback_split/artifacts/`
- `sprints/2026.07.12_19-56_o3_scan_qos_endpoint_readback_split/tech-done.md`

Product closeout files after implementation:

- `sprints/2026.07.12_19-56_o3_scan_qos_endpoint_readback_split/side2side_check.md`
- `sprints/2026.07.12_19-56_o3_scan_qos_endpoint_readback_split/final.md`

Forbidden without new Product routing:

- O5/O6/O7 implementation files.
- Hardware config, UART, WAVE ROVER, ESP32, serial, baudrate, wiring, voltage, firmware, or vendor-backed hardware edits.
- UI/API/cloud/product code.
- `OKR.md` and `docs/process/okr_progress_log.md` during Robot Software implementation; Product may update only during acceptance if evidence justifies it.
- Historical sprint files.

## Interface Boundary

Robot Software may change only the strict no-motion proof/readback contract. The contract must keep these boundaries:

- Input boundary: managed runtime and ROS2/Nav2 readback only.
- Output boundary: structured artifact fields that distinguish publisher endpoint, QoS/window/ROS readback, and LiDAR runtime.
- Safety boundary: no movement, no manual base control, no route execution.
- Handoff boundary: Hardware receives work only after LiDAR runtime/serial/wiring is primary; Algorithm receives work only after `/scan`, `/amcl_pose`, and dynamic `map->odom` are clean enough.

Expected artifact fields or equivalent summaries:

- `/scan` topic type and publisher/endpoint inventory.
- RELIABLE and BEST_EFFORT attempts with timeout/window detail.
- rclpy vs CLI readback status.
- primary root cause and secondary diagnostics.
- `amcl_pose_observed=false` unless newly proven.
- `map_to_odom_dynamic_source_missing` unless newly proven.
- `path_generation_attempted=false`.
- `path_generated=false`.
- all no-motion safety booleans false.

## Strict No-Motion 禁止项

This sprint is strict no-motion and must explicitly preserve:

- no /cmd_vel.
- no `/api/base/manual`.
- no NavigateToPose.
- no WAVE ROVER UART.
- no route execution.
- no base manual relay.
- no safe-to-control claim.

Required false fields:

- `safe_to_control=false`
- `publishes_cmd_vel=false`
- `calls_base_manual=false`
- `uses_base_uart=false`
- `robot_control_executed=false`
- `route_execution_success=false`
- `delivery_success=false`
- `hil_pass=false`

## Implementation Plan

1. Baseline readback: load or reproduce the 18:56 lifecycle-active assumptions and ensure graph timeout remains secondary unless new evidence overturns it.
2. Publisher endpoint split: inventory `/scan` endpoint count, topic type, publisher node/source clue, and whether the endpoint is stable across the proof window.
3. QoS/window/ROS readback split: run or model RELIABLE and BEST_EFFORT attempts with explicit budgets; separate CLI/rclpy/DDS/daemon/window timeout from true no-sample runtime.
4. LiDAR runtime decision: only if endpoint/readback are sufficiently ruled out, classify LiDAR runtime as primary and prepare Hardware handoff requirements.
5. Artifact normalization: promote the most concrete `/scan` cause to primary root cause and keep old graph/lifecycle labels as secondary diagnostics when appropriate.
6. Verification and closeout: update tests/docs, write artifacts, record exact validation output in `tech-done.md`, and leave Product to decide acceptance/OKR wording.

## Acceptance Commands For Robot Software

Robot Software must run and report the following commands after implementation.

```bash
python3 -m py_compile onboard/scripts/o10_amcl_nav2_runtime_proof.py
```

```bash
python3 -m unittest onboard.tests.test_nav2_runtime_proof_helper
```

```bash
bash -n onboard/scripts/o11_nav2_lifecycle.sh
```

Local strict no-motion dry run. On macOS without ROS it may return `2` fail-closed, but it must write an artifact and keep all motion/control fields false.

```bash
mkdir -p sprints/2026.07.12_19-56_o3_scan_qos_endpoint_readback_split/artifacts
python3 onboard/scripts/o10_amcl_nav2_runtime_proof.py \
  --strict-no-motion \
  --no-base-uart \
  --timeout-s 18 \
  --managed-runtime-opt-in \
  --managed-map-yaml /root/rober/onboard/runtime/maps/trashbot_map.yaml \
  --output-json sprints/2026.07.12_19-56_o3_scan_qos_endpoint_readback_split/artifacts/local_o10_scan_qos_endpoint_readback_split.raw.json
```

True-board strict no-motion run if reachable. If SSH is unreachable, record the exact failure and do not replace it with local-only success.

```bash
ssh -p 37878 root@192.168.1.11 \
  'mkdir -p /root/rober/onboard/scripts /tmp/rober_o10_artifacts'
```

```bash
scp -P 37878 onboard/scripts/o10_amcl_nav2_runtime_proof.py \
  root@192.168.1.11:/root/rober/onboard/scripts/o10_amcl_nav2_runtime_proof.py
```

```bash
scp -P 37878 onboard/scripts/o11_nav2_lifecycle.sh \
  root@192.168.1.11:/root/rober/onboard/scripts/o11_nav2_lifecycle.sh
```

```bash
ssh -p 37878 root@192.168.1.11 \
  'cd /root/rober/onboard && /usr/bin/timeout 420s /usr/bin/python3.10 scripts/o10_amcl_nav2_runtime_proof.py --strict-no-motion --no-base-uart --timeout-s 18 --managed-runtime-opt-in --managed-map-yaml /root/rober/onboard/runtime/maps/trashbot_map.yaml --output-json /tmp/rober_o10_artifacts/live_o10_scan_qos_endpoint_readback_split.raw.json'
```

```bash
scp -P 37878 root@192.168.1.11:/tmp/rober_o10_artifacts/live_o10_scan_qos_endpoint_readback_split.raw.json \
  sprints/2026.07.12_19-56_o3_scan_qos_endpoint_readback_split/artifacts/live_o10_scan_qos_endpoint_readback_split.raw.json
```

Artifact safety/readback inspection must include these anchors in `tech-done.md`:

- `/scan_reliable_and_best_effort_timeout`
- publisher endpoint classification
- QoS/window/ROS readback classification
- LiDAR runtime classification if reached
- `map_server_active`
- `amcl_active`
- `managed_runtime_log_lifecycle_readback.clean`
- `amcl_pose_observed`
- `map_to_odom_dynamic_source_missing`
- `path_generation_attempted=false`
- `path_generated=false`
- `safe_to_control=false`
- `publishes_cmd_vel=false`
- `calls_base_manual=false`
- `uses_base_uart=false`
- `robot_control_executed=false`
- `route_execution_success=false`
- `delivery_success=false`
- `hil_pass=false`

Scoped diff check:

```bash
git diff --check -- \
  onboard/scripts/o10_amcl_nav2_runtime_proof.py \
  onboard/scripts/o11_nav2_lifecycle.sh \
  onboard/tests/test_nav2_runtime_proof_helper.py \
  docs/navigation/field_route_evidence_preflight.md \
  docs/navigation/fixed_route_workflow.md \
  sprints/2026.07.12_19-56_o3_scan_qos_endpoint_readback_split
```

## Product Acceptance Gate

Accept as useful sprint progress only if one of these is true:

- Preferred: `/scan` sample readback becomes clean enough that `/amcl_pose` / TF / planner-only path work can proceed.
- Acceptable blocked: artifact narrows `/scan_reliable_and_best_effort_timeout` into publisher endpoint, QoS/window/ROS readback, or LiDAR runtime with clear next owner and command.

Do not accept:

- O5 support-only/wrapper/readiness material.
- Repeating lifecycle、map_server configure/on_configure、loadmap、graph timeout wrapper as primary.
- Any mission progress claim without same-run path generation, route execution, delivery/operator acceptance, current live HIL, or real production external evidence.
- Any no-motion violation.

## OKR Success / Non-Success口径

Success for this sprint:

- `/scan` blocker is split into a narrower actionable cause.
- Next owner is clear: Robot Software, Hardware, or Algorithm.
- Strict no-motion evidence remains clean.

OKR percentage result for normal success:

- Keep O5 about `85%`.
- Keep O1/O6/O7 about `93%`.
- Do not archive KR.
- Record as O3/O1 supporting evidence only.

Non-success:

- If the artifact only repeats `/scan_reliable_and_best_effort_timeout` without endpoint/QoS/window/runtime split, the sprint is not accepted and should be sent back to Robot Software for repair.
- If true-board is unreachable, close only as local fail-closed evidence and state that live progress is not proven.
- If LiDAR runtime becomes primary, do not claim hardware root cause until Hardware reads vendor docs and produces a separate evidence-backed conclusion.

## Risks

- `/scan` endpoint may be visible while samples still timeout across both QoS modes.
- ROS graph/DDS/daemon timing may still pollute the readback layer.
- LiDAR runtime may require Hardware later, but premature hardware edits would violate this sprint boundary.
- `/amcl_pose` and dynamic `map->odom` remain blocked until `/scan` is reliable enough.
- There is still no same-run path success, route execution, `route.csv`, keyframe, rosbag, replay JSONL, delivery/operator acceptance, current live HIL, safe-to-control proof, or production external evidence.
