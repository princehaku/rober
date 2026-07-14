# Side2Side Check - O3 Map Server LoadMap Return Code Probe

## Sprint Metadata

- sprint_type: epic
- Sprint: `sprints/2026.07.12_17-55_o3_map_server_loadmap_return_code_probe/`
- Product owner: `product-okr-owner`
- Implementation owner: `robot-software-engineer`
- Closeout time: `2026-07-12 17:55 CST`
- Product status: accepted as O3/O1 strict no-motion lifecycle gate unblock only
- Proof boundary: `software_proof_o3_o1_strict_no_motion_map_server_loadmap_return_code_probe_only`

## 用户价值和产品北极星

产品北极星仍是普通手机用户一键发车送垃圾。当前最短用户价值链是：真实上位机 fixed-route/nav 先能生成 same-run path，再进入 route execution、delivery/operator acceptance 和 HIL/production evidence。

本轮价值是把旧 `/map_server` lifecycle inactive / `on_configure` blocker 从产品验收链里移除：true-board artifact 已通过 managed runtime log lifecycle readback 证明 `/map_server` 与 AMCL active。它仍不是路线执行或送达能力。

## Baseline vs Current Evidence

| 项目 | 16:55 baseline | 2026-07-12 17-55 current |
| --- | --- | --- |
| Sprint | `sprints/2026.07.12_16-55_o3_map_server_on_configure_return_source_repair/` | `sprints/2026.07.12_17-55_o3_map_server_loadmap_return_code_probe/` |
| Lifecycle state | `/map_server` not lifecycle-clean/active | `map_server_active=true` and `amcl_active=true` by managed runtime log lifecycle readback |
| Canonical classification | `map_server_on_configure_return_false_after_valid_map_io_deferred_completion` | `map_server_lifecycle_active` |
| LoadMap/YAML readback | valid map IO, direct return source still unclear | `load_map_response_from_yaml.response_status=success_equivalent_map_read_completed_before_failure` |
| Primary blocker | Nav2 map_server transition callback / on_configure return source | `Managed runtime graph readback / managed_runtime_graph_probe_timeout_after_lifecycle_active_log` |
| Downstream blocked facts | lifecycle not clean, downstream not eligible | `/scan_no_publisher`, `/map_once_not_observed`, `/amcl_pose_topic_missing`, `/tf_topic_missing` |
| Product decision | blocker narrowing only | lifecycle gate unblock accepted; mission progress rejected |

Side-by-side conclusion: current artifact is a real gate movement. Product should not send the next run back to older `map_server_lifecycle_not_active` / `on_configure_return_false` blockers unless new evidence explicitly disproves this 17:55 artifact.

## Product Acceptance

Product status: accepted as O3/O1 strict no-motion lifecycle gate unblock only。

Acceptance reasons:

- true-board artifact `live_o10_map_server_loadmap_return_code_probe.raw.json` has `status=blocked_with_root_cause`。
- `map_server_active=true`。
- `amcl_active=true`。
- `managed_runtime_log_lifecycle_readback.clean=true`。
- `proof.map_server_transition_callback_probe.canonical_classification=map_server_lifecycle_active`。
- `load_map_response_from_yaml.response_status=success_equivalent_map_read_completed_before_failure`。
- direct Nav2 runtime log did not expose a direct LoadMap return code, so the accepted readback is runtime-log equivalent evidence, not a direct return-code claim。

Product rejects this as mission progress because `path_generation_attempted=false`、`path_generated=false`、`safe_to_control=false`、`publishes_cmd_vel=false`、`calls_base_manual=false`、`uses_base_uart=false`、`robot_control_executed=false`、`route_execution_success=false`、`delivery_success=false`、`hil_pass=false`。

## Verification Evidence

Robot Software verification from `tech-done.md`:

- `python3 -m py_compile onboard/scripts/o10_amcl_nav2_runtime_proof.py` PASS。
- `python3 -m unittest onboard.tests.test_nav2_runtime_proof_helper` PASS, `Ran 129 tests in 2.294s` / `OK`。
- `bash -n onboard/scripts/o11_nav2_lifecycle.sh` PASS。
- local strict no-motion run returned `2` fail-closed。
- SSH/scp/board run/pull completed。
- true-board strict no-motion run returned `2` because downstream proof remains blocked, not because SSH/run/pull failed。
- scoped `git diff --check` PASS。

## OKR Decision

- O5 remains about `85%`。
- O1 remains about `93%`。
- O6 remains about `93%`。
- O7 remains about `93%`。
- 本轮`不调整`百分比，`不归档` KR。

理由：本轮解除的是 O3/O1 strict no-motion lifecycle 前置 gate；仍没有 same-run path generation success、route execution、delivery/operator acceptance、current live HIL、safe-to-control 或 production external evidence。

## Next Run

Next P0 owner: `Robot Software`。

验收口径：

- 不要回到旧 `map_server_lifecycle_not_active`、`map_server_on_configure_return_false_after_valid_map_io_deferred_completion` 或 `map_server_changestate_response_false_before_map_io_completion` 作为 primary blocker。
- 先决定并修复 `managed_runtime_graph_probe_timeout_after_lifecycle_active_log`。
- graph/readback 干净后，再顺序处理 `/scan_no_publisher`、`/map_once_not_observed`、`/amcl_pose_topic_missing`、`/tf_topic_missing`。
- `Algorithm` 只在 graph/topic readback 足够干净后接 AMCL/TF/path work。
- `Hardware` 只在 LiDAR serial/runtime/wiring 成为 primary blocker 时介入，并必须先读 `docs/vendor/VENDOR_INDEX.md` 及其指向的 vendor docs。
