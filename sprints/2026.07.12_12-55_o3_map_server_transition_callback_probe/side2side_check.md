# Side2Side Check - O3 Map Server Transition Callback Probe

## Sprint Metadata

- sprint_type: epic
- Sprint: `sprints/2026.07.12_12-55_o3_map_server_transition_callback_probe/`
- Product owner: `product-okr-owner`
- Implementation owner: `robot-software-engineer`
- Check time: `2026-07-12 13:26 CST`
- Product status: accepted as O3/O1 strict no-motion blocker narrowing only
- Proof boundary: `software_proof_o3_o1_strict_no_motion_map_server_transition_callback_probe_only`

## 用户价值和产品北极星

用户价值是继续把真实上位机 fixed-route/nav 的前置阻塞从 lifecycle activation 层下钻到 map_server configure transition callback 层。产品北极星仍是普通手机用户一键发车送垃圾；本 sprint 不交付路径生成、路线执行、底盘运动、HIL、送达或生产云能力。

## Side2Side 对照

| 检查项 | 上轮 accepted 事实 | 本轮 observed 事实 | Product 判断 |
| --- | --- | --- | --- |
| root cause 粒度 | `map_server_activate_callback_failed` / `lifecycle_manager_failed_to_change_state_for_map_server_after_valid_map_readback` | `map_server_configure_callback_return_failure` / `lifecycle_manager_changestate_response_failure_during_configure_before_deferred_map_read_completed` | 接受。比 activation callback failure 更窄，进入 configure callback return / ChangeState response 层。 |
| observed stage | activation callback failure after valid map readback | `observed_stage=configure` | 接受。当前 primary stage 是 configure，不再把 activate 当作唯一主因。 |
| service/RPC timing | 记录 service/bond timeout 配置，但缺 ChangeState failure 时序 | `service_rpc_timing.inferred_change_state_response=failure`，service family `/map_server/change_state` | 接受。满足本轮 transition callback/service/RPC timing 证据要求。 |
| bond timing | map_server 未 lifecycle clean/active | `bond_timing.bond_stage=not_created_before_configure_return_failure` | 接受。bond 未创建是 configure failure 之后的结果，不是 clean active 证据。 |
| no-motion | 所有 motion/control/delivery/HIL 字段 false | `path_generation_attempted=false`、`path_generated=false`、`safe_to_control=false`、`publishes_cmd_vel=false`、`calls_base_manual=false`、`robot_control_executed=false`、`route_execution_success=false`、`delivery_success=false`、`hil_pass=false`、`uses_base_uart=false` | 接受。strict no-motion 边界未破坏。 |
| OKR 影响 | O5 约 `85%`；O1/O6/O7 约 `93%`；`不调整`；`不归档` | O5 继续约 `85%`；O1/O6/O7 继续约 `93%`；`不调整`；`不归档` | 接受为 blocker narrowing only，不是主 OKR 计分材料。 |

## 验收证据

Canonical true-board artifact:

- `sprints/2026.07.12_12-55_o3_map_server_transition_callback_probe/artifacts/live_o10_map_server_transition_callback_probe.raw.json`
- `status=blocked_with_root_cause`
- top root cause：`Nav2 map_server transition callback / map_server_configure_callback_return_failure / lifecycle_manager_changestate_response_failure_during_configure_before_deferred_map_read_completed`
- `proof.map_server_transition_callback_probe.canonical_classification=map_server_configure_callback_return_failure`
- `proof.map_server_transition_callback_probe.transition_sequence.observed_stage=configure`
- `proof.map_server_transition_callback_probe.service_rpc_timing.inferred_change_state_response=failure`
- `proof.map_server_transition_callback_probe.bond_timing.bond_stage=not_created_before_configure_return_failure`

Engineering validation from `tech-done.md`:

- `python3 -m py_compile onboard/scripts/o10_amcl_nav2_runtime_proof.py` return `0`
- `python3 -m unittest onboard.tests.test_nav2_runtime_proof_helper` return `0`, `Ran 120 tests in 2.273s OK`
- local strict no-motion dry-run return `2` fail-closed
- board mkdir/scp return `0`
- true-board strict no-motion run return `2` with `status=blocked_with_root_cause`
- artifact pull return `0`
- scoped `git diff --check` return `0`

## Product Acceptance

Accepted as O3/O1 strict no-motion blocker narrowing only.

理由：

- 本轮把上一轮 `map_server_activate_callback_failed` 下钻到 `map_server_configure_callback_return_failure`。
- configure stage 的 callback enter、yaml/image load、map read、state change failure、ChangeState response failure 和 bond-not-created 前置关系已结构化记录。
- no-motion 字段全部 false，没有 NavigateToPose、`/cmd_vel`、`/api/base/manual`、WAVE ROVER UART、HIL、route execution 或 delivery 证据。
- 本轮不是 lifecycle clean，不是 path/route/delivery/HIL/production evidence。

## 风险和阻塞

- `/map_server` 仍未 lifecycle clean/active。
- `/map` sample、AMCL pose、dynamic `map->odom`、planner-only path gate 均未恢复。
- LiDAR cleanup 前后仍有串口异常背景噪声，但本轮 accepted primary root cause 是 map_server configure callback return failure，不升级硬件。
- 下一轮仍需 Robot Software 继续查 Nav2 map_server `on_configure` return path、map IO deferred read ordering、lifecycle manager ChangeState response handling、executor timing 和 bond creation 前置条件。

## 责任 Engineer 和下一步

- P0 owner：`robot-software-engineer`
- 下一轮目标：让 `/map_server` lifecycle clean/active，或输出比 `map_server_configure_callback_return_failure` 更窄的 configure callback exception / parameter / map IO / ChangeState RPC root cause。
- Algorithm 暂不接手，等 `/map_server` lifecycle clean 后再恢复 `/map`、AMCL pose、dynamic `map->odom` 和 planner-only path gate。
- Hardware 暂不介入，除非后续新证据把 primary blocker 指向真实串口、接线、波特率或 LiDAR hardware runtime。
