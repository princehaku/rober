# Final - O3 Map Server On-Configure IO Order Repair

## Sprint Metadata

- sprint_type: epic
- Sprint: `sprints/2026.07.12_14-54_o3_map_server_on_configure_io_order_repair/`
- Product owner: `product-okr-owner`
- Implementation owner: `robot-software-engineer`
- Closeout time: `2026-07-12 15:28 CST`
- Product status: accepted as O3/O1 strict no-motion blocker narrowing only
- Proof boundary: `software_proof_o3_o1_strict_no_motion_map_server_on_configure_io_order_repair_only`

## 用户价值和产品北极星

用户价值是继续解除真实上位机 fixed-route/nav 的前置阻塞：本轮没有修到 `/map_server` lifecycle clean/active，但把 failure 窗口从 13:54 的 deferred map read completion 前进一步压到 image load 已开始、map read 完成前的 ChangeState failure。产品北极星仍是普通手机用户一键发车送垃圾；本 sprint 不交付路径生成、路线执行、底盘运动、HIL、送达或生产云能力。

## OKR 映射和方向判断

- O5：继续约 `85%`，方向 `暂停 support-only`。没有真实 HTTPS/TLS、公网入口、production DB/queue、worker cutover、OSS/CDN live traffic、真实手机/browser 或 external production evidence。
- O1/O3：`继续` strict no-motion 现场链路。本轮为 current same-run path generation 与 Nav2 route execution 的 `/map_server` lifecycle 前置 blocker 下钻。
- O6/O7：继续约 `93%`，方向 `暂停等待材料`。没有新的 live route execution、delivery/operator 或 production readback。
- OKR 结论：O5 继续约 `85%`，O1/O6/O7 继续约 `93%`，`不调整` 百分比，`不归档` KR。

## KR 拆解、更新或历史归档

本轮不归档任何 KR。新增证据只进入 O3/O1 supporting chain：

- Primary live artifact `status=blocked_with_root_cause`。
- `proof.root_causes[0].layer=Nav2 map_server transition callback`。
- `proof.root_causes[0].reason=map_server_changestate_response_failure_after_image_load_before_map_read_completed`。
- `proof.root_causes[0].detail=lifecycle_manager_changestate_response_failure_after_image_load_before_map_read_completed`。
- `proof.map_server_transition_callback_probe.canonical_classification=map_server_changestate_response_failure_after_image_load_before_map_read_completed`。
- `transition_sequence.configure.lifecycle_manager_configure_requested=true`。
- `transition_sequence.configure.map_server_configure_callback_log_observed=true`。
- `transition_sequence.configure.yaml_load_started=true`。
- `transition_sequence.configure.image_load_started=true`。
- `transition_sequence.configure.state_change_failed=true`。
- `transition_sequence.configure.state_change_failed_after_image_load_before_map_read_completed=true`。
- `transition_sequence.configure.map_read_completed=true`。

## 本轮核心抓手

Robot Software 把 13:54 的 `map_server_configure_return_failure_before_deferred_map_read_completed` 继续下钻到 `map_server_changestate_response_failure_after_image_load_before_map_read_completed`：lifecycle manager 已请求 configure，map_server callback 已进入，YAML 与 image load 已开始，ChangeState failure 发生在 image load 之后、`Read map` 完成之前。

Activation summary may still contain broader legacy `map_server_activate_callback_failed`; Product closeout trusts top root cause and `proof.map_server_transition_callback_probe.canonical_classification` as primary.

## 实际改动和验证结果

Robot Software 已完成 helper/tests/navigation docs/artifacts 侧实现，Product 本轮 closeout 更新 sprint/OKR/process 留档。

Engineering 验证事实：

- `python3 -m py_compile onboard/scripts/o10_amcl_nav2_runtime_proof.py` return `0`。
- `python3 -m unittest onboard.tests.test_nav2_runtime_proof_helper` return `0` with `Ran 125 tests in 2.263s OK`。
- local strict no-motion dry-run return `2` fail-closed。
- board mkdir/scp return `0`。
- true-board strict no-motion run return `2` with `reason=map_server_changestate_response_failure_after_image_load_before_map_read_completed`。
- artifact pull return `0`。
- scoped `git diff --check` return `0`。

Primary artifact:

- `sprints/2026.07.12_14-54_o3_map_server_on_configure_io_order_repair/artifacts/live_o10_map_server_on_configure_io_order_repair.raw.json`

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

Accepted as O3/O1 strict no-motion blocker narrowing only。

理由：

- Primary artifact 比 13:54 更窄，定位到 image load started 后、map read completed 前的 ChangeState failure。
- artifact 记录了 configure request、callback log、YAML/image load、state-change failure 和 map-read completion 的时间顺序。
- 所有 motion/control/delivery/HIL 字段保持 false。
- 本轮不声称 lifecycle clean、path generation、route execution、delivery/operator acceptance、current live HIL、safe-to-control、current live map navigation readiness 或 production cloud evidence。

## 优先级和验收口径

Next run P0：`robot-software-engineer` 检查 lifecycle manager ChangeState future/response timeout vs map IO image decode completion、Nav2 map_server `on_configure` return/image decode timing，并考虑拆分 map_server-only lifecycle proof 与 AMCL configure proof。

验收口径：

- `/map_server` lifecycle clean/active，或输出比 `map_server_changestate_response_failure_after_image_load_before_map_read_completed` 更窄的 callback exception / parameter / map IO / ChangeState RPC / executor root cause。
- 继续保持 strict no-motion，不发布 `/cmd_vel`，不调用 `/api/base/manual`，不打开 WAVE ROVER UART。
- 不继续 O5 support-only；不 hand off to Algorithm until `/map_server` lifecycle is clean。
- Hardware only if LiDAR serial/runtime becomes primary and vendor docs are read.

## 风险、阻塞和证据链缺口

- `/map_server` 仍未 lifecycle clean/active。
- `/map` sample、`/amcl_pose`、dynamic `map->odom`、planner-only path generation 均未恢复。
- LiDAR `/dev/ttyACM0` 仍有 `SerialException` 背景噪声，但本轮 artifact primary root cause 已在 map_server transition ordering 层；硬件串口问题不在本 sprint 范围内。
- 仍缺 route execution、delivery/operator acceptance、current live HIL、safe-to-control 和 production external evidence。

## 需要创建或更新的 Sprint 文档

Created or updated in closeout:

- `sprints/2026.07.12_14-54_o3_map_server_on_configure_io_order_repair/side2side_check.md`
- `sprints/2026.07.12_14-54_o3_map_server_on_configure_io_order_repair/final.md`
- `OKR.md`
- `docs/process/okr_progress_log.md`
