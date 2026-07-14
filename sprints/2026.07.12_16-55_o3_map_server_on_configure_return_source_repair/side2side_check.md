# Side2Side Check - O3 Map Server On-Configure Return Source Repair

## Sprint Metadata

- sprint_type: epic
- Sprint: `sprints/2026.07.12_16-55_o3_map_server_on_configure_return_source_repair/`
- Product owner: `product-okr-owner`
- Implementation owner: `robot-software-engineer`
- Closeout time: `2026-07-12 17:31 CST`
- Product status: accepted as O3/O1 strict no-motion blocker narrowing only
- Proof boundary: `software_proof_o3_o1_strict_no_motion_map_server_on_configure_return_source_repair_only`

## 用户价值和产品北极星

用户价值仍是把真实上位机 fixed-route/nav 链路推进到可生成同 run path、再进入 route execution 和 delivery/operator acceptance。`/map_server` lifecycle clean/active 是 `/map`、AMCL、dynamic `map->odom`、planner-only path generation 的上游 gate。

本轮没有交付可发车能力；Product 只验收为真实板 strict no-motion blocker narrowing。

## Baseline vs Current Evidence

| 项目 | 15:54 baseline | 2026-07-12 16-55 current |
| --- | --- | --- |
| Sprint | `sprints/2026.07.12_15-54_o3_map_server_changestate_response_repair/` | `sprints/2026.07.12_16-55_o3_map_server_on_configure_return_source_repair/` |
| Primary root cause | `map_server_changestate_response_false_before_map_io_completion` | `map_server_on_configure_return_false_after_valid_map_io_deferred_completion` |
| Classification | ChangeState false before map IO completion | `on_configure` return false source after valid YAML/PGM readback, with map IO completion logged later |
| Map input validity | Timing proof only | `map_input_validation.valid_for_map_server=true`, YAML/PGM readable |
| Excluded sources | no service/RPC timeout | no map_server-scoped exception, no service/RPC timeout, no invalid map input |
| Lifecycle clean | false | false |
| Product decision | accepted narrowing only | accepted narrowing only |

Side-by-side conclusion: current root cause is narrower than 15:54. It is no longer only a lifecycle manager ChangeState timing symptom; it is now classified into `on_configure_return_false_source` with valid map inputs and deferred map IO completion.

## Product Acceptance

Product status: accepted as O3/O1 strict no-motion blocker narrowing only。

Acceptance reasons:

- `status=blocked_with_root_cause`。
- `proof.root_causes[0].reason=map_server_on_configure_return_false_after_valid_map_io_deferred_completion`。
- `proof.map_server_transition_callback_probe.canonical_classification=map_server_on_configure_return_false_after_valid_map_io_deferred_completion`。
- `proof.map_server_transition_callback_probe.on_configure_return_source.source_family=on_configure_return_false_source`。
- `map_input_validation.valid_for_map_server=true`，YAML/PGM readable。
- no map_server-scoped exception。
- no service/RPC timeout。
- map IO completion logged after ChangeState failure。

Product does not accept this as lifecycle clean, path generation, route execution, delivery/operator acceptance, current live HIL, safe-to-control, current live map navigation readiness or production cloud evidence.

## Verification Evidence

Robot Software verification from `tech-done.md`:

- `python3 -m py_compile onboard/scripts/o10_amcl_nav2_runtime_proof.py` return `0`。
- `python3 -m unittest onboard.tests.test_nav2_runtime_proof_helper` final return `0`, with `Ran 127 tests in 2.282s OK`。
- `bash -n onboard/scripts/o11_nav2_lifecycle.sh` return `0`。
- local strict no-motion run return `2` fail-closed。
- board mkdir/scp return `0`。
- true-board strict no-motion run return `2` with narrowed root cause。
- artifact pull return `0`。
- scoped `git diff --check` return `0`。
- anchor checks return `0`。

## No-Motion Gate

No-motion fields remain false:

- `path_generation_attempted=false`
- `path_generated=false`
- `safe_to_control=false`
- `publishes_cmd_vel=false`
- `calls_base_manual=false`
- `uses_base_uart=false`
- `route_execution_success=false`
- `delivery_success=false`
- `hil_pass=false`

This proof remains `software_proof_o3_o1_strict_no_motion_map_server_on_configure_return_source_repair_only`。

## OKR Decision

- O5 remains about `85%`。
- O1 remains about `93%`。
- O6 remains about `93%`。
- O7 remains about `93%`。
- 本轮`不调整`百分比，`不归档` KR。

理由：本轮只收窄 `/map_server` lifecycle blocker，仍没有 same-run path generation success、route execution、delivery/operator acceptance、current live HIL、safe-to-control 或 production external evidence。

## Next Run

Next run: Robot Software continues with Nav2 map_server `loadMapResponseFromYaml` return code, `on_configure` return path, executor/log ordering and lifecycle manager ChangeState response handling。

Do not hand off to Algorithm until `/map_server` lifecycle is clean. Hardware only if LiDAR serial/runtime/wiring becomes primary and `docs/vendor/VENDOR_INDEX.md` plus linked vendor docs are read.

同一 blocker 红线：本轮相比 15:54 已收窄，不算重复；但下一轮若仍只能重复 `map_server_on_configure_return_false_after_valid_map_io_deferred_completion` 而不能修到 active 或继续收窄，则应升级 CEO 或切换 Objective。
