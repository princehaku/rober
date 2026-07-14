# Final - O3 Map Server Transition Callback Probe

## Sprint Metadata

- sprint_type: epic
- Sprint: `sprints/2026.07.12_12-55_o3_map_server_transition_callback_probe/`
- Product owner: `product-okr-owner`
- Implementation owner: `robot-software-engineer`
- Closeout time: `2026-07-12 13:26 CST`
- Product status: accepted as O3/O1 strict no-motion blocker narrowing only
- Proof boundary: `software_proof_o3_o1_strict_no_motion_map_server_transition_callback_probe_only`

## 用户价值和产品北极星

用户价值是把真实上位机 fixed-route/nav 的前置阻塞继续收窄：上一轮证明 map yaml/PGM 可读但 `/map_server` activation callback failed，本轮进一步确认 primary blocker 在 configure callback return / ChangeState response failure 层。产品北极星仍是普通手机用户一键发车送垃圾；本 sprint 不交付路径生成、路线执行、底盘运动、HIL、送达或生产云能力。

## OKR 映射和方向判断

- O5：继续约 `85%`，方向 `暂停 support-only`。没有真实 HTTPS/TLS、公网入口、production DB/queue、worker cutover、OSS/CDN live traffic、真实手机/browser 或 external production evidence。
- O1/O3：`继续` strict no-motion 现场链路。本轮是 O3/O1 supporting blocker narrowing，为 O1 current same-run path generation 和 Nav2 route execution 缺口解除 map_server 前置 blocker。
- O6/O7：继续约 `93%`，方向 `暂停等待材料`。没有新的 live route execution、delivery/operator 或 production readback。
- OKR 结论：`不调整` 百分比，`不归档` KR。

## KR 拆解、更新或历史归档

本轮不归档任何 KR。新增证据只进入 O3/O1 supporting chain：

- Primary live artifact `status=blocked_with_root_cause`。
- `proof.root_causes[0].layer=Nav2 map_server transition callback`。
- `proof.root_causes[0].reason=map_server_configure_callback_return_failure`。
- `proof.root_causes[0].detail=lifecycle_manager_changestate_response_failure_during_configure_before_deferred_map_read_completed`。
- `proof.map_server_transition_callback_probe.canonical_classification=map_server_configure_callback_return_failure`。
- `proof.map_server_transition_callback_probe.transition_sequence.observed_stage=configure`。
- `proof.map_server_transition_callback_probe.service_rpc_timing.inferred_change_state_response=failure`。
- `proof.map_server_transition_callback_probe.bond_timing.bond_stage=not_created_before_configure_return_failure`。

已完成 KR 历史记录位置：无新增完成 KR，历史区不更新。证据来源为 `tech-plan.md`、`tech-done.md`、primary artifact、`side2side_check.md`、本 `final.md`、`OKR.md` closeout note 和 `docs/process/okr_progress_log.md`。

## 本轮核心抓手

Robot Software 把 11-54 的 `map_server_activate_callback_failed` 继续下钻到 configure transition callback return failure：map_server 已进入 configure，lifecycle manager 已请求 state transition，yaml/image load 和 map read 相关事件进入日志窗口，但 ChangeState response inferred failure，并且 bond 在 configure return failure 前未创建。

## 实际改动和验证结果

Robot Software 已完成 helper/tests/navigation docs/artifacts 侧实现，Product 本轮 closeout 更新 sprint/OKR/process 留档。

Engineering 验证事实：

- `python3 -m py_compile onboard/scripts/o10_amcl_nav2_runtime_proof.py` return `0`。
- `python3 -m unittest onboard.tests.test_nav2_runtime_proof_helper` return `0` with `Ran 120 tests in 2.273s OK`。
- local strict no-motion dry-run return `2` fail-closed。
- board mkdir/scp return `0`。
- true-board strict no-motion run return `2` with `reason=map_server_configure_callback_return_failure`。
- artifact pull return `0`。
- scoped `git diff --check` return `0`。

Primary artifact:

- `sprints/2026.07.12_12-55_o3_map_server_transition_callback_probe/artifacts/live_o10_map_server_transition_callback_probe.raw.json`

No-motion fields remain false:

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

## Product Acceptance

Accepted as O3/O1 strict no-motion blocker narrowing only.

理由：

- Primary artifact 从上一轮 activation callback failure，收窄为 `map_server_configure_callback_return_failure`。
- transition sequence 明确 `observed_stage=configure`，并记录 callback entered、yaml/image load、map read、state change failure、ChangeState inferred failure 和 bond-not-created 前置关系。
- 所有 motion/control/delivery/HIL 字段保持 false。
- 本轮不声称 lifecycle clean、path generation、route execution、delivery/operator acceptance、current live HIL、safe-to-control、current live map navigation readiness 或 production cloud evidence。

## 优先级和验收口径

Next run P0：`robot-software-engineer` inspect Nav2 map_server `on_configure` return path、map IO deferred read ordering、lifecycle manager ChangeState response handling、executor timing 和 bond creation 前置条件。

验收口径：

- `/map_server` lifecycle clean/active，或输出比 `map_server_configure_callback_return_failure` 更窄的 configure callback exception / parameter / map IO / ChangeState RPC root cause。
- 继续保持 strict no-motion，不发布 `/cmd_vel`，不调用 `/api/base/manual`，不打开 WAVE ROVER UART。
- 不继续 O5 support-only；不 hand off to Algorithm until `/map_server` lifecycle is clean。

## 风险、阻塞和证据链缺口

- `/map_server` is still not lifecycle-clean/active。
- `/map` sample、`/amcl_pose`、dynamic `map->odom`、planner-only path generation 均未恢复。
- LiDAR driver cleanup 前后仍有串口异常背景噪声，但本轮 helper 已把它隔离为非 map_server transition 主因；硬件串口问题不在本 sprint 范围内。
- 仍缺 route execution、delivery/operator acceptance、current live HIL、safe-to-control 和 production external evidence。

## 需要创建或更新的 Sprint 文档

Created or updated in closeout:

- `sprints/2026.07.12_12-55_o3_map_server_transition_callback_probe/side2side_check.md`
- `sprints/2026.07.12_12-55_o3_map_server_transition_callback_probe/final.md`
- `OKR.md`
- `docs/process/okr_progress_log.md`
