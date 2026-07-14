# Final - O3 Map Server Graph/Lifecycle Visibility

## Sprint Metadata

- sprint_type: epic
- Sprint: `sprints/2026.07.12_09-54_o3_map_server_graph_lifecycle_visibility/`
- Product owner: `product-okr-owner`
- Implementation owner: `robot-software-engineer`
- Closeout time: `2026-07-12 10:29 CST`
- Product status: accepted as strict no-motion diagnostic delta
- Proof boundary: `software_proof_o3_o1_strict_no_motion_map_server_graph_lifecycle_visibility_only`

## 用户价值和产品北极星

用户价值是让真实上位机在不运动、不控制底盘的前提下，把 `/map_server` retry `Node not found` 明确收敛为 `map_server_node_absent`，为下一轮恢复 map server node/process/lifecycle manager presence 提供精确入口。

产品北极星仍是普通手机用户一键发车完成固定路线送垃圾。本 sprint 不交付 path generation、route execution、delivery/operator acceptance、current live HIL、safe-to-control、current live map navigation readiness 或 production cloud evidence。

## OKR 映射和方向判断

- O5：继续约 `85%`，`暂停`。没有真实公网 HTTPS/TLS、4G/SIM、production DB/queue、worker cutover、OSS/CDN live traffic、真实手机/browser 或 external production evidence。
- O1/O3：`继续`，但只接受为 O3/O1 strict no-motion diagnostic delta。本轮收窄 current same-run path generation 前的 `/map_server` blocker。
- O6/O7：继续约 `93%`，`不调整`。没有新的 same-task route execution、delivery record、operator acceptance 或 production readback material。
- OKR 结论：`不调整` 百分比，`不归档` KR。

## KR 拆解、更新或历史归档

本轮不归档任何 KR。新增证据只进入 O1/O3 supporting chain：

- `proof.map_server_graph_lifecycle_visibility.schema=trashbot.o10.map_server_graph_lifecycle_visibility.v1`
- `canonical_classification=map_server_node_absent`
- `failure_detail=lifecycle_retry_node_not_found`
- `board_source_preflight_ready`
- `lightweight_cli_ready=true`
- `cli_ready=true`
- `runtime_ready=true`
- `amcl_lifecycle_reference.current_active=true`
- current retry stdout contains `active [3]`

已完成 KR 历史记录位置：无新增完成 KR，历史区不更新。证据来源为 `tech-done.md`、live artifact、`side2side_check.md`、本 `final.md`、`OKR.md` Key Results closeout note 和 `docs/process/okr_progress_log.md`。

## 本轮核心抓手

Robot Software 新增 `proof.map_server_graph_lifecycle_visibility` 摘要，把 `/map_server` node graph、daemon/DDS visibility、lifecycle first/retry readback、managed runtime/process context 和 canonical classification 汇总到一个 schema。Product 验收以 live artifact 为准，不把 worker shorthand 当作顶层字段。

## 实际改动和验证结果

Robot Software 已完成 helper/tests/navigation docs/artifacts 侧实现，Product 本轮 closeout 更新 sprint/OKR/process 留档。

验证事实：

- `python3 -m py_compile onboard/scripts/o10_amcl_nav2_runtime_proof.py` RC `0`。
- `python3 -m unittest onboard.tests.test_nav2_runtime_proof_helper` passed，`Ran 110 tests ... OK`。
- local strict no-motion dry-run RC `2`，按预期 fail-closed。
- board SSH/SCP passed。
- live helper RC `2`，写出 blocked artifact。
- scoped `git diff --check` passed。

Live artifact:

- `sprints/2026.07.12_09-54_o3_map_server_graph_lifecycle_visibility/artifacts/live_o10_map_server_graph_lifecycle_visibility.raw.json`

关键字段：

- `status=blocked_with_root_cause`
- `evidence_type=blocked_with_root_cause`
- `map_lifecycle_preflight.classification=map_lifecycle_preflight_map_server_inactive`
- `map_lifecycle_preflight.blocking_reasons.map_server=map_server_lifecycle_command_failed`
- `/map_server` first attempt `lifecycle_command_timeout`
- `/map_server` retry `returncode=1`, `stderr="Node not found\n"`
- `canonical_classification=map_server_node_absent`
- `failure_detail=lifecycle_retry_node_not_found`
- `amcl_lifecycle_reference.current_active=true`
- current `/amcl` retry stdout contains `active [3]`
- previous accepted fact: `08-55 /amcl retry stdout contains active [3]`

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

Accepted as O3/O1 strict no-motion diagnostic delta.

理由：

- It advances from generic `/map_server` lifecycle failure to `map_server_node_absent`.
- It preserves the accepted `/amcl active [3]` fact using actual artifact fields: `current_active=true` and retry stdout contains `active [3]`.
- It keeps all motion/control/delivery/HIL fields false.
- It does not claim current live map navigation readiness or mission progress.

## 优先级和验收口径

下一轮 P0：`robot-software-engineer` restores `/map_server` node/process/lifecycle manager presence so lifecycle readback moves beyond `Node not found`.

验收口径：

- `/map_server` no longer returns `Node not found`.
- lifecycle readback is clean enough for Algorithm to resume `/map`, TF and planner/path readiness.
- Safety fields remain false unless a separately planned and accepted motion/HIL sprint exists.

## 风险、阻塞和证据链缺口

- `/map_server` absent remains the exact blocker.
- `/amcl current_active=true` does not prove AMCL pose freshness, dynamic `map->odom`, localization ready or path generation.
- No current same-run path generation success, route execution, delivery/operator acceptance, current live HIL, production cloud or user-action closure was produced.
- Hardware is not needed unless later evidence proves LiDAR serial/runtime/wiring facts.

## 需要创建或更新的 Sprint 文档

Created or updated in closeout:

- `sprints/2026.07.12_09-54_o3_map_server_graph_lifecycle_visibility/side2side_check.md`
- `sprints/2026.07.12_09-54_o3_map_server_graph_lifecycle_visibility/final.md`
- `OKR.md`
- `docs/process/okr_progress_log.md`
