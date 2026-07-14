# Final - O3 Map Server Lifecycle Activation Repair

## Sprint Metadata

- sprint_type: epic
- Sprint: `sprints/2026.07.12_11-54_o3_map_server_lifecycle_activation_repair/`
- Product owner: `product-okr-owner`
- Implementation owner: `robot-software-engineer`
- Closeout time: `2026-07-12 12:26 CST`
- Product status: accepted as O3/O1 strict no-motion blocker narrowing only
- Proof boundary: `software_proof_o3_o1_strict_no_motion_map_server_lifecycle_activation_repair_only`

## 用户价值和产品北极星

用户价值是把真实上位机 fixed-route/nav 前置阻塞继续收窄：上一轮证明 `/map_server` 已启动并读取 map yaml/PGM 后 state change failed，本轮进一步确认 map 文件和 lifecycle manager 管辖关系不是 primary blocker，当前 primary blocker 是 `map_server_activate_callback_failed`。产品北极星仍是普通手机用户一键发车送垃圾；本 sprint 不交付路径生成、路线执行、底盘运动、HIL、送达或生产云能力。

## OKR 映射和方向判断

- O5：继续约 `85%`，方向 `暂停 support-only`。没有真实 HTTPS/TLS、公网入口、production DB/queue、worker cutover、OSS/CDN live traffic、真实手机/browser 或 external production evidence。
- O1/O3：`继续` strict no-motion 现场链路。本轮是 O3/O1 supporting blocker narrowing，为 O1 current same-run path generation 缺口解除前置 map_server blocker。
- O6/O7：继续约 `93%`，方向 `暂停等待材料`。没有新的 live route execution、delivery/operator 或 production readback。
- OKR 结论：`不调整` 百分比，`不归档` KR。

## KR 拆解、更新或历史归档

本轮不归档任何 KR。新增证据只进入 O3/O1 supporting chain：

- Primary live artifact `status=blocked_with_root_cause`。
- `proof.root_causes[0].layer=Nav2 map_server lifecycle activation`。
- `proof.root_causes[0].reason=map_server_activate_callback_failed`。
- `proof.root_causes[0].detail=lifecycle_manager_failed_to_change_state_for_map_server_after_valid_map_readback`。
- `proof.map_server_lifecycle_activation.canonical_classification=map_server_activate_callback_failed`。

已完成 KR 历史记录位置：无新增完成 KR，历史区不更新。证据来源为 `tech-done.md`、primary artifact、`side2side_check.md`、本 `final.md`、`OKR.md` closeout note 和 `docs/process/okr_progress_log.md`。

## 本轮核心抓手

Robot Software 把 10-54 的 generic `lifecycle_manager_failed_to_change_state_for_map_server` 下钻到 activation callback failure：map yaml/PGM 在 true-board 上 readable 且字段 valid，lifecycle manager managed node list 与 `/map_server` 匹配，`frame_id=map`，`service_timeout_s=12.0`，`bond_timeout_s=8.0`，`RMW_FASTRTPS_USE_SHM=0`。YAML `mode` 缺失是 optional，Nav2 log reports `mode: trinary`，不是本轮 primary blocker。

## 实际改动和验证结果

Robot Software 已完成 helper/tests/navigation docs/artifacts 侧实现，Product 本轮 closeout 更新 sprint/OKR/process 留档。

Engineering 验证事实：

- `python3 -m py_compile onboard/scripts/o10_amcl_nav2_runtime_proof.py` return 0。
- `python3 -m unittest onboard.tests.test_nav2_runtime_proof_helper` return 0 with `Ran 117 tests in 2.281s OK`。
- local strict no-motion dry-run return 2 fail-closed。
- board mkdir/scp return 0。
- original board artifact return 2，保留为 graph-timeout secondary。
- retry board artifact return 2，primary classification 为 `map_server_activate_callback_failed`。
- scoped `git diff --check` return 0。

Primary artifact:

- `sprints/2026.07.12_11-54_o3_map_server_lifecycle_activation_repair/artifacts/live_o10_map_server_lifecycle_activation_repair.raw.json`

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

- Primary artifact 从上一轮 generic lifecycle manager state-change failure，收窄为 `map_server_activate_callback_failed`。
- Valid map readback 已发生，yaml/PGM readable 且 fields valid for map_server。
- lifecycle manager 管辖关系、timeouts、frame/env 已记录，不是 name/namespace mismatch。
- 所有 motion/control/delivery/HIL 字段保持 false。
- 本轮不声称 lifecycle clean、path generation、route execution、delivery/operator acceptance、current live HIL、safe-to-control、current live map navigation readiness 或 production cloud evidence。

## 优先级和验收口径

Next run P0：`robot-software-engineer` inspect Nav2 map_server lifecycle transition callback/service/bond/RPC timing or map_server configure/activate return path。

验收口径：

- `/map_server` lifecycle clean/active，或输出比 `map_server_activate_callback_failed` 更窄的 callback/service/bond/RPC timing failure。
- 继续保持 strict no-motion，不发布 `/cmd_vel`，不调用 `/api/base/manual`，不打开 WAVE ROVER UART。
- 不继续 O5 support-only；不 hand off to Algorithm until `/map_server` lifecycle is clean。

## 风险、阻塞和证据链缺口

- `/map_server` is still not lifecycle-clean/active。
- `/map` sample、`/amcl_pose`、dynamic `map->odom`、planner-only path generation 均未恢复。
- Secondary `ros2_node_list_timeout` regression 已保留，但 Product primary root cause 是 activation callback failure after valid map readback。
- 仍缺 route execution、delivery/operator acceptance、current live HIL、safe-to-control 和 production external evidence。

## 需要创建或更新的 Sprint 文档

Created or updated in closeout:

- `sprints/2026.07.12_11-54_o3_map_server_lifecycle_activation_repair/side2side_check.md`
- `sprints/2026.07.12_11-54_o3_map_server_lifecycle_activation_repair/final.md`
- `OKR.md`
- `docs/process/okr_progress_log.md`
