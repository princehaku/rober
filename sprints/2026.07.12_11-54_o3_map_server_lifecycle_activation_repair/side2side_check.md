# Side2Side Check - O3 Map Server Lifecycle Activation Repair

## Sprint Metadata

- sprint_type: epic
- Sprint: `sprints/2026.07.12_11-54_o3_map_server_lifecycle_activation_repair/`
- Product owner: `product-okr-owner`
- Implementation owner: `robot-software-engineer`
- Check time: `2026-07-12 12:26 CST`
- Product status: accepted as O3/O1 strict no-motion blocker narrowing only
- Proof boundary: `software_proof_o3_o1_strict_no_motion_map_server_lifecycle_activation_repair_only`

## 用户价值和产品北极星

用户价值是让真实上位机的 Nav2 `/map_server` blocker 从上一轮泛化的 lifecycle manager state-change failure，继续收窄到可执行的 activation callback/service/bond/RPC timing 调查点。产品北极星仍是普通手机用户一键发车完成固定路线送垃圾；本 sprint 只处理路线执行前的 map server lifecycle 前置阻塞，不交付路线、送达、HIL 或生产云能力。

## OKR 映射和方向判断

- O5：约 `85%`，仍是最低 Objective，但没有真实 external production evidence；方向 `暂停 support-only`，不继续 readiness/surface/handoff/intake 包装。
- O1/O3：方向 `继续` strict no-motion 现场链路。本轮接受为 `/map_server` lifecycle activation blocker narrowing，服务 O1 current same-run path generation 缺口的前置条件。
- O6/O7：约 `93%`，没有新的 route execution、delivery/operator 或 production readback；方向 `暂停等待新材料`。
- Product 结论：`不调整` OKR 百分比，`不归档` KR。

## Side-by-side 验收

| 验收项 | 计划口径 | 实际证据 | Product 判定 |
| --- | --- | --- | --- |
| Primary live artifact | true-board strict no-motion artifact 必须给出 `/map_server` clean 或更窄 blocker | `live_o10_map_server_lifecycle_activation_repair.raw.json` 为 `status=blocked_with_root_cause` | Accept as narrowing |
| Root cause | 不能只重复 `lifecycle_manager_failed_to_change_state_for_map_server` | `proof.root_causes[0].layer=Nav2 map_server lifecycle activation`、`reason=map_server_activate_callback_failed`、`detail=lifecycle_manager_failed_to_change_state_for_map_server_after_valid_map_readback` | Accept |
| Canonical classification | 输出更窄 configure/activate classification | `proof.map_server_lifecycle_activation.canonical_classification=map_server_activate_callback_failed` | Accept |
| Map readback | 需要证明 yaml/PGM 可读并区分 map 文件问题 | `proof.map_server_lifecycle_activation.map_yaml_pgm_readback.yaml.readable=true`、`pgm.readable=true`、yaml/PGM fields valid for map_server | Accept |
| Optional YAML mode | 不把非主因写成 primary blocker | YAML `mode` missing，但 optional；Nav2 runtime log reports `mode: trinary` | Accept |
| Lifecycle manager setup | 需要确认 node 管辖、timeout、frame/env | managed node list matches `['map_server','amcl']`，`frame_id=map`，`service_timeout_s=12.0`，`bond_timeout_s=8.0`，`RMW_FASTRTPS_USE_SHM=0` | Accept |
| Lifecycle clean | `/map_server` lifecycle clean 后才允许 Algorithm 接后续 path gate | `/map_server` is still not lifecycle-clean/active | Not accepted as clean |
| No-motion safety | 所有 motion/control/delivery/HIL 字段必须 false | `path_generation_attempted=false`、`path_generated=false`、`safe_to_control=false`、`publishes_cmd_vel=false`、`calls_base_manual=false`、`robot_control_executed=false`、`route_execution_success=false`、`delivery_success=false`、`hil_pass=false`、`uses_base_uart=false` | Accept |
| Engineering verification | tests、dry-run、board artifact、diff check 必须有证据 | `py_compile` return 0；unittest return 0 with `Ran 117 tests in 2.281s OK`；local dry-run return 2 fail-closed；board mkdir/scp return 0；original board artifact return 2 kept as graph-timeout secondary；retry board artifact return 2 with primary classification；scoped `git diff --check` return 0 | Accept |

## 不接受项

- 不接受为 lifecycle clean：`/map_server` 仍未 active。
- 不接受为 path generation：`path_generation_attempted=false` 且 `path_generated=false`。
- 不接受为 route execution、delivery、HIL、safe-to-control 或 production evidence。
- 不接受为 Algorithm 可接手信号：Algorithm 等 `/map_server` lifecycle clean 后再接 `/map` sample、AMCL pose、dynamic `map->odom` 和 planner-only path gate。

## KR 拆解、更新或历史归档

本轮没有完成 KR，不移动当前 KR 到历史区。已完成 KR 的历史记录位置：无新增。证据来源仅记录在本 sprint `tech-done.md`、primary artifact、本 `side2side_check.md`、`final.md`、`OKR.md` 和 `docs/process/okr_progress_log.md`。

## Next run

Next run 由 `robot-software-engineer` 主责：inspect Nav2 map_server lifecycle transition callback/service/bond/RPC timing or map_server configure/activate return path。不要继续 O5 support-only；不要 hand off to Algorithm until `/map_server` lifecycle is clean。

## 风险、阻塞和需要补齐的证据链

- Primary blocker: `map_server_activate_callback_failed` / `lifecycle_manager_failed_to_change_state_for_map_server_after_valid_map_readback`。
- Secondary graph-timeout artifact 已保留，但不是 Product primary root cause。
- 仍缺 `/map_server` active、`/map` sample、AMCL pose freshness、dynamic `map->odom`、planner-only path generation、route execution、delivery/operator acceptance、current live HIL、safe-to-control 和 production external evidence。
