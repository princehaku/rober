# Final - O3 Lifecycle CLI Budget Recovery

## Sprint Metadata

- sprint_type: epic
- Sprint: `sprints/2026.07.12_08-55_o3_lifecycle_cli_budget_recovery/`
- Product owner: `product-okr-owner`
- Implementation owner: `robot-software-engineer`
- Closeout time: `2026-07-12 09:29 Asia/Shanghai`
- Proof boundary: `software_proof_o3_o1_strict_no_motion_lifecycle_cli_budget_recovery_only`
- Product status: accepted as strict no-motion diagnostic delta

## 用户价值和产品北极星

用户价值是让真实上位机在不运动、不控制底盘的前提下，把 lifecycle blocker 从"两边 timeout"推进成可执行的下一步：`/amcl` retry 已读到 `active [3]`，`/map_server` retry 仍是 `Node not found`，因此下轮应该直接恢复 `/map_server` graph/lifecycle visibility。

产品北极星仍是普通手机用户一键发车完成固定路线送垃圾。本 sprint 只推进路径生成前的诊断链，不交付路线执行、底盘控制、送达闭环或云端生产证据。

## OKR Mapping And Direction

- O5：`暂停`，继续保持约 `85%`。本轮没有真实公网 HTTPS/TLS、4G/SIM、production DB/queue、worker cutover、OSS/CDN live traffic、真实手机/browser 或 external production evidence。
- O3/O1：`继续`，但只接受为 O3/O1 strict no-motion diagnostic delta。它缩窄了 current same-run path generation 前的 lifecycle blocker，但没有产生 path 或 route proof。
- O6/O7：`不调整`，继续约 `93%`。没有新的 same-task route execution、delivery record、operator acceptance 或 production readback material。
- 方向判断：继续 O3/O1 no-motion，下一轮由 Robot Software 修 `/map_server` graph/lifecycle visibility；Algorithm 在 lifecycle clean 后再接 `/scan`、`/map`、TF/path readiness。
- KR 历史归档：`不归档`，没有 KR 达到完成证据。

## Product Acceptance

Accepted.

Robot Software implementation met the Product acceptance boundary:

- Implemented `lifecycle_cli_budget_recovery` and first/retry lifecycle command summaries.
- Kept source/readiness result clean: `board_source_preflight_ready`, `lightweight_cli_ready=true`, `cli_ready=true`, `runtime_ready=true`.
- Preserved strict no-motion safety fields.
- Correctly skipped downstream scan/map/odom/TF probes until lifecycle CLI readback is clean.
- Produced a live board artifact and scoped verification evidence.

This sprint is not path generation, route execution, delivery/operator acceptance, current live HIL, safe-to-control proof, production cloud evidence, current live map navigation readiness, or any WAVE ROVER/UART/hardware result.

## Validation Evidence

Robot Software recorded:

- `python3 -m py_compile onboard/scripts/o10_amcl_nav2_runtime_proof.py` RC `0`.
- `python3 -m unittest onboard.tests.test_nav2_runtime_proof_helper` RC `0`, `Ran 104 tests in 2.253s - OK`.
- Local dry-run RC `2`, fail-closed as expected because macOS lacks `/opt/ros/humble/setup.bash`.
- Board helper `scp` RC `0`.
- Board strict no-motion run RC `2`, producing a blocked artifact.
- Live artifact pull RC `0`.
- Scoped `git diff --check` RC `0`.
- `rg` anchors RC `0`.

Live artifact: `sprints/2026.07.12_08-55_o3_lifecycle_cli_budget_recovery/artifacts/live_o10_lifecycle_cli_budget_recovery.raw.json`.

Key fields:

- `status=blocked_with_root_cause`
- `evidence_type=blocked_with_root_cause`
- `proof.board_source_preflight.classification=board_source_preflight_ready`
- `lightweight_cli_ready=true`
- `cli_ready=true`
- `runtime_ready=true`
- `proof.map_lifecycle_preflight.classification=map_lifecycle_preflight_map_server_inactive`
- `proof.map_lifecycle_preflight.blocking_reasons.map_server=map_server_lifecycle_command_failed`
- `/map_server` first attempt `lifecycle_command_timeout`
- `/map_server` retry `returncode=1`, `stderr="Node not found\n"`
- `/amcl` first attempt `lifecycle_command_timeout`
- `/amcl` retry stdout contains `active [3]`
- `scan_probe_skipped_until_lifecycle_cli_readback_clean`
- `map_probe_skipped_until_lifecycle_cli_readback_clean`
- `odom_probe_skipped_until_lifecycle_cli_readback_clean`
- `tf_source_probe_skipped_until_lifecycle_cli_readback_clean`

Safety fields:

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

## OKR Closeout

No OKR percentage changes:

- O5 stays about `85%`.
- O1 stays about `93%`.
- O6 stays about `93%`.
- O7 stays about `93%`.

Decision: `不调整` percentages and `不归档` KR.

Reason: this sprint narrowed lifecycle diagnosis but still lacks current same-run path generation success, Nav2 route execution success, delivery/operator acceptance, current live HIL, safe-to-control evidence, real production cloud evidence, real user action, and production readback.

## Remaining Risk

- `/map_server` graph/lifecycle visibility is still not restored.
- `/amcl` can be read as `active [3]` on retry, but that does not prove AMCL pose freshness, dynamic `map->odom`, or localization readiness.
- Downstream `/scan`, `/map`, `/odom`, and TF probes were intentionally skipped until lifecycle CLI readback is clean; their latest state is not refreshed by this sprint.
- `RTPS_TRANSPORT_SHM` warnings appeared in `/amcl` retry stdout and may still matter for daemon/DDS stability, but they did not block `/amcl active [3]`.

## Next Round Recommendation

Next sprint should stay with `robot-software-engineer` and restore `/map_server` graph/lifecycle visibility. The acceptance gate should distinguish node absence, lifecycle manager/process startup, daemon/DDS graph visibility, and helper command budget/timing.

`robot-algorithm-engineer` should join only after lifecycle readback is clean enough to consume `/scan`, `/map`, TF, and planner/path readiness. `rober-hardware-engineer` is not needed unless new evidence proves LiDAR serial/runtime/wiring facts.
