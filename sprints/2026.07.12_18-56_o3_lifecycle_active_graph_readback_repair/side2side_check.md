# Side2Side Check - O3 Lifecycle-Active Graph Readback Repair

## Sprint Metadata

- sprint_type: epic
- Sprint: `sprints/2026.07.12_18-56_o3_lifecycle_active_graph_readback_repair/`
- Product acceptance time: `2026-07-12 18-56 CST`
- Product owner: `product-okr-owner`
- Implementation owner: `Robot Software`
- Product status: accepted as O3/O1 strict no-motion downstream blocker narrowing / graph-readback unblock only
- Proof boundary: `software_proof_o3_o1_strict_no_motion_lifecycle_active_graph_readback_repair_only`

## 用户价值和产品北极星

用户价值仍是普通手机用户一键发车送垃圾，并得到可验证的到达或失败结果。本 sprint 不交付用户可见运动能力；它交付的是现场 Nav2 no-motion 链路中的关键判断：lifecycle-active 后的 graph timeout 不再遮蔽 downstream readback，下一步可以直接拆 `/scan` 样本超时。

产品北极星不变：把真实上位机 fixed-route/nav 链路推进到 same-run path generation、route execution、delivery/operator acceptance、current live HIL 或 production external evidence。

## Side2Side Verdict

| 验收项 | 结果 | Product 判断 |
| --- | --- | --- |
| 17:55 lifecycle-active baseline 是否保持 | PASS | `map_server_active=true`、`amcl_active=true`、`managed_runtime_log_lifecycle_readback.clean=true` 保持成立 |
| graph timeout 是否继续作为 primary blocker | PASS | 不再作为 primary；`managed_runtime_graph_probe_timeout_after_lifecycle_active_log` 只保留为 secondary diagnostic/root cause |
| downstream blocker 是否更具体 | PASS | `proof.artifact_closeout.primary_root_cause.layer=Nav2 sensor input`，`reason=/scan_reliable_and_best_effort_timeout` |
| `/map` 是否恢复 readback | PASS | `proof.downstream_recovery_summary.map.ready=true`，`proof.map_once_observed=true`，`map_once_observed=true` |
| AMCL/TF/path 是否仍 blocked | PASS | `amcl_pose_observed=false`，TF blocked at `map_to_odom_dynamic_source_missing`，`path_generation_attempted=false`，`path_generated=false` |
| no-motion safety fields | PASS | `safe_to_control=false`、`publishes_cmd_vel=false`、`calls_base_manual=false`、`uses_base_uart=false`、`robot_control_executed=false`、`route_execution_success=false`、`delivery_success=false`、`hil_pass=false` |
| OKR percentage movement | PASS | O5 继续约 85%，O1/O6/O7 继续约 93%，`不调整` 百分比，`不归档` KR |

## OKR 映射和方向判断

- O5：继续约 `85%`。本轮没有真实 external production evidence；不能把 no-motion readback 或 support-only material 算作 O5 增量。
- O1/O3：接受为 strict no-motion downstream blocker narrowing / graph-readback unblock only。它是 additive evidence，因为 primary blocker 从 `managed_runtime_graph_probe_timeout_after_lifecycle_active_log` 推进到 `/scan_reliable_and_best_effort_timeout`，且证明 `/map` sample observed after lifecycle-active logs。
- O6/O7：继续约 `93%`。本轮没有 live route execution、delivery/operator acceptance、production readback 或可消费的新同任务材料。
- 方向判断：继续 O3/O1；不调整 OKR 百分比；不归档 KR；不得把本轮包装为 mission progress、path generation、route execution、delivery/operator acceptance、current live HIL、safe-to-control 或 production external evidence。

## 本轮核心抓手

Robot Software 修复了 lifecycle-active 后的 readback 决策：当 lifecycle logs 已 clean，managed runtime graph wait timeout 不再阻断 downstream probes。Product 接受的核心抓手是 downstream primary root cause 被压到 `/scan_reliable_and_best_effort_timeout`，而不是重复消费 graph timeout。

## 验证证据

证据来源：

- `sprints/2026.07.12_18-56_o3_lifecycle_active_graph_readback_repair/tech-done.md`
- `sprints/2026.07.12_18-56_o3_lifecycle_active_graph_readback_repair/artifacts/live_o10_lifecycle_active_graph_readback_repair.raw.json`

Robot Software validation:

- `python3 -m py_compile onboard/scripts/o10_amcl_nav2_runtime_proof.py` exit `0`
- `python3 -m unittest onboard.tests.test_nav2_runtime_proof_helper` -> `Ran 131 tests ... OK`
- `bash -n onboard/scripts/o11_nav2_lifecycle.sh` exit `0`
- local strict no-motion run exit `2` fail-closed
- true-board deploy/run/pull pass, helper `remote_rc=2`
- scoped `git diff --check` pass

## 需要做什么

Next owner: `Robot Software`

下一步先把 `/scan_reliable_and_best_effort_timeout` 拆成以下互斥判断：

- publisher endpoint / QoS mismatch
- proof window or sample wait budget
- ROS readback / CLI / daemon timing
- LiDAR runtime publisher visible but no sample
- LiDAR serial/runtime/wiring only if evidence makes it primary

`Hardware` 只在 LiDAR serial/runtime/wiring 成为 primary blocker 后介入，并且必须先读 `docs/vendor/VENDOR_INDEX.md`。`Algorithm` 等 `/scan`、`/amcl_pose`、dynamic `map->odom` clean enough 后再接 planner-only path proof。

## 风险和证据链缺口

- `/scan` publisher visible，但 BEST_EFFORT / RELIABLE window 未读到 sample。
- `/amcl_pose` 未 observed，AMCL 仍不具备 localization ready evidence。
- dynamic `map->odom` source missing，`map->base_link` 继续 downstream blocked。
- `path_generation_attempted=false`、`path_generated=false`，没有 same-run path proof。
- 没有 route execution、delivery/operator acceptance、current live HIL、safe-to-control 或 production external evidence。

## KR 历史归档

本轮没有完成 KR，不移动 KR 到历史区。历史位置保持：

- `OKR.md` archived Objective 区
- `docs/process/okr_progress_log.md`

本轮只新增 supporting evidence closeout：`2026-07-12 18-56`，不调整、不归档。
