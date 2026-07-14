# Tech Plan - O3 Lifecycle-Active Graph Readback Repair

## Objective

Fix or decide the lifecycle-active ROS graph/readback blocker:

`managed_runtime_graph_probe_timeout_after_lifecycle_active_log`

This sprint starts from the 17:55 accepted artifact, where `/map_server active=true`, `amcl_active=true`, and `map_server_lifecycle_active` are already proven by managed runtime logs. Robot Software must not route the next sprint back to older lifecycle-inactive or on-configure blockers unless new true-board evidence disproves 17:55.

## OKR 最低优先级核对

- 当前 `OKR.md` 第 5 节完成度最低的 Objective：O5, about `85%`.
- 本 sprint 是否针对该最低 Objective：否。
- 不针对理由：O5 当前可见工作仍缺真实 external production evidence。`cloud_production_cutover_readiness_packet` 这类 readiness/support packet 已被判定为 `okr_credit_allowed=false`；继续 O5 support-only 只会重复包装缺口，不会提供 HTTPS/TLS、公网入口、production DB/queue、worker cutover、OSS/CDN live traffic、真实手机/browser 或生产外部证据。
- 本 sprint 选择：继续 O3/O1 strict no-motion，因为 17:55 已把 `/map_server` 与 AMCL 推到 lifecycle-active，当前 `managed_runtime_graph_probe_timeout_after_lifecycle_active_log` 是通往 same-run path generation、route execution 和 delivery evidence 的最近可执行 blocker。
- final.md 收口时复核：如果 implementation 只得到 support-only 或 wrapper/readback 边界，O5/O1/O6/O7 百分比保持不变；如果拿到 same-run path generation、route execution、delivery/operator acceptance、current live HIL 或 production external evidence，再由 Product 另行判断 OKR 更新。

## Owner And Single-Line Plan

- Owner: `Robot Software`.
- Collaborators: none for implementation start.
- Algorithm waits until graph/topic readback is clean enough for AMCL/TF/path work.
- Hardware waits unless LiDAR serial/runtime/wiring becomes primary; any hardware claim must first read `docs/vendor/VENDOR_INDEX.md`.

Implementation plan:

1. Preserve 17:55 lifecycle-active readback as the routing baseline.
2. Inspect graph probe wait path, daemon/DDS split, command timeout budget, and lifecycle-active log readback interaction.
3. Fix the helper if timeout is measurement/readback-induced, or classify the blocker more narrowly if graph is clean but downstream topics are blocked.
4. Keep strict no-motion safety fields fail-closed.
5. Update tests/docs/artifacts and write `tech-done.md` with exact evidence.

## File Scope

Allowed implementation files for Robot Software:

- `onboard/scripts/o10_amcl_nav2_runtime_proof.py`
- `onboard/scripts/o11_nav2_lifecycle.sh`
- `onboard/tests/test_nav2_runtime_proof_helper.py`
- `docs/navigation/field_route_evidence_preflight.md`
- `docs/navigation/fixed_route_workflow.md`
- `sprints/2026.07.12_18-56_o3_lifecycle_active_graph_readback_repair/artifacts/`
- `sprints/2026.07.12_18-56_o3_lifecycle_active_graph_readback_repair/tech-done.md`

Product closeout files after implementation:

- `sprints/2026.07.12_18-56_o3_lifecycle_active_graph_readback_repair/side2side_check.md`
- `sprints/2026.07.12_18-56_o3_lifecycle_active_graph_readback_repair/final.md`

Explicitly forbidden without new Product routing:

- O5/O6/O7 implementation files.
- Hardware config, UART, WAVE ROVER, ESP32, serial, baud rate, or vendor-backed hardware changes.
- UI/API/cloud/product code.
- `OKR.md` and `docs/process/okr_progress_log.md` during Robot Software implementation; Product updates those only in closeout if justified.

## Acceptance Commands

Robot Software must run and report these commands.

### Static And Unit Checks

```bash
python3 -m py_compile onboard/scripts/o10_amcl_nav2_runtime_proof.py
```

```bash
python3 -m unittest onboard.tests.test_nav2_runtime_proof_helper
```

```bash
bash -n onboard/scripts/o11_nav2_lifecycle.sh
```

### Local Strict No-Motion Dry Run

Expected on macOS without ROS: fail-closed return code `2`, artifact written under this sprint, and no motion/control booleans enabled.

```bash
mkdir -p sprints/2026.07.12_18-56_o3_lifecycle_active_graph_readback_repair/artifacts
python3 onboard/scripts/o10_amcl_nav2_runtime_proof.py \
  --strict-no-motion \
  --no-base-uart \
  --timeout-s 18 \
  --managed-runtime-opt-in \
  --managed-map-yaml /root/rober/onboard/runtime/maps/trashbot_map.yaml \
  --output-json sprints/2026.07.12_18-56_o3_lifecycle_active_graph_readback_repair/artifacts/local_o10_lifecycle_active_graph_readback_repair.raw.json
```

### True-Board Strict No-Motion Run If Reachable

Use the same board route as 17:55. If SSH is unreachable, record the exact failure and do not replace it with a local-only success claim.

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
  'cd /root/rober/onboard && /usr/bin/timeout 420s /usr/bin/python3.10 scripts/o10_amcl_nav2_runtime_proof.py --strict-no-motion --no-base-uart --timeout-s 18 --managed-runtime-opt-in --managed-map-yaml /root/rober/onboard/runtime/maps/trashbot_map.yaml --output-json /tmp/rober_o10_artifacts/live_o10_lifecycle_active_graph_readback_repair.raw.json'
```

```bash
scp -P 37878 root@192.168.1.11:/tmp/rober_o10_artifacts/live_o10_lifecycle_active_graph_readback_repair.raw.json \
  sprints/2026.07.12_18-56_o3_lifecycle_active_graph_readback_repair/artifacts/live_o10_lifecycle_active_graph_readback_repair.raw.json
```

### Artifact Safety Readback

Robot Software should inspect the local and live artifacts for these fields and include the output in `tech-done.md`:

- `map_server_active`
- `amcl_active`
- `proof.artifact_closeout.primary_root_cause.reason`
- `managed_runtime_graph_probe_timeout_after_lifecycle_active_log`
- `/scan_no_publisher`
- `/map_once_not_observed`
- `/amcl_pose_topic_missing`
- `/tf_topic_missing`
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

### Scoped Diff Check

```bash
git diff --check -- \
  onboard/scripts/o10_amcl_nav2_runtime_proof.py \
  onboard/scripts/o11_nav2_lifecycle.sh \
  onboard/tests/test_nav2_runtime_proof_helper.py \
  docs/navigation/field_route_evidence_preflight.md \
  docs/navigation/fixed_route_workflow.md \
  sprints/2026.07.12_18-56_o3_lifecycle_active_graph_readback_repair
```

## Product Acceptance Gate

Accept as progress only if one of these is true:

- graph/readback becomes clean enough to hand off to Algorithm for AMCL/TF/path; or
- blocked result is narrowed past `managed_runtime_graph_probe_timeout_after_lifecycle_active_log` into a concrete downstream or ROS graph subsystem gate.

Do not accept:

- O5 support-only material.
- A wrapper that repeats old `map_server_lifecycle_not_active`, `map_server_on_configure_return_false_after_valid_map_io_deferred_completion`, or `map_server_changestate_response_false_before_map_io_completion`.
- Any mission claim without same-run path generation, route execution, delivery/operator acceptance, current live HIL, or production external evidence.

## Risks

- True-board SSH may be unreachable; if so, the sprint can only close as local fail-closed planning/implementation evidence and must not claim live progress.
- Graph readback may remain ambiguous after lifecycle-active logs; the minimum acceptable result is a narrower reason with evidence.
- Downstream topics may become the primary blocker, especially `/scan`, `/map`, `/amcl_pose`, or `/tf`.
- LiDAR serial instability remains background noise until evidence makes it primary; Hardware then needs vendor-doc review before any hardware conclusion.
