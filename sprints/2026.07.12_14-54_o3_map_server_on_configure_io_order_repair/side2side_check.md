# Side-by-Side Check - O3 Map Server On-Configure IO Order Repair

## Sprint Metadata

- sprint_type: epic
- Sprint: `sprints/2026.07.12_14-54_o3_map_server_on_configure_io_order_repair/`
- Product owner: `product-okr-owner`
- Implementation owner: `robot-software-engineer`
- Check time: `2026-07-12 15:28 CST`
- Product status: accepted as O3/O1 strict no-motion blocker narrowing only

## 用户价值和产品北极星

用户价值是继续解除真实上位机 fixed-route/nav 的前置阻塞，让后续 `/map`、AMCL、dynamic `map->odom` 和 planner-only path gate 能回到同一现场证据链。产品北极星仍是普通手机用户一键发车送垃圾；本 sprint 不交付路线执行、底盘运动、HIL、送达或生产云能力。

## 对照验收口径

| 项目 | 计划验收 | 实际证据 | Product 判断 |
| --- | --- | --- | --- |
| `/map_server` lifecycle | clean/active，或比 13:54 更窄 root cause | 未 clean/active；root cause 收窄到 `map_server_changestate_response_failure_after_image_load_before_map_read_completed` / `lifecycle_manager_changestate_response_failure_after_image_load_before_map_read_completed` | Accept as blocker narrowing |
| true-board artifact | 必须有真实板 artifact | `artifacts/live_o10_map_server_on_configure_io_order_repair.raw.json`，`status=blocked_with_root_cause` | Accept |
| transition ordering | 记录 configure、map IO、ChangeState ordering | `image_load_started=1783840650.5605125`，`state_change_failed=1783840650.660171`，`map_read_completed=1783840651.0017402` | Accept |
| no-motion | 不发运动、不触底盘 | `path_generation_attempted=false`、`path_generated=false`、`safe_to_control=false`、`publishes_cmd_vel=false`、`calls_base_manual=false`、`robot_control_executed=false`、`route_execution_success=false`、`delivery_success=false`、`hil_pass=false`、`uses_base_uart=false` | Accept |
| OKR/KR | 只有 mission-grade evidence 才调分/归档 | O5 继续约 `85%`，O1/O6/O7 继续约 `93%`，`不调整` 百分比，`不归档` KR | Accept |

## Primary Evidence

- `proof.map_server_transition_callback_probe.canonical_classification=map_server_changestate_response_failure_after_image_load_before_map_read_completed`
- `transition_sequence.configure.lifecycle_manager_configure_requested=true`
- `transition_sequence.configure.map_server_configure_callback_log_observed=true`
- `transition_sequence.configure.yaml_load_started=true`
- `transition_sequence.configure.image_load_started=true`
- `transition_sequence.configure.state_change_failed=true`
- `transition_sequence.configure.state_change_failed_after_image_load_before_map_read_completed=true`
- `transition_sequence.configure.map_read_completed=true`

Activation summary may still contain broader legacy `map_server_activate_callback_failed`; Product acceptance trusts the top root cause and the transition callback probe as primary.

## Product Acceptance

Accepted only as O3/O1 strict no-motion blocker narrowing.

This is not lifecycle clean, path generation, route execution, delivery/operator acceptance, current live HIL, safe-to-control, current live map navigation readiness, or production cloud evidence.

## 剩余风险和下一轮建议

- `/map_server` 仍未 lifecycle clean/active，不能 hand off to Algorithm。
- Robot Software 下一轮检查 lifecycle manager ChangeState future/response timeout vs map IO image decode completion、Nav2 map_server `on_configure` return/image decode timing，并考虑拆出 map_server-only lifecycle proof 与 AMCL configure proof。
- Hardware 暂不介入；只有 LiDAR serial/runtime 变成 primary root cause 时才转 Hardware，并按 `docs/vendor/VENDOR_INDEX.md` 核对硬件事实。
