# Final - O3 Map Server Configure Failure Repair

## Sprint Metadata

- sprint_type: epic
- Sprint: `sprints/2026.07.12_13-54_o3_map_server_configure_failure_repair/`
- Product owner: `product-okr-owner`
- Implementation owner: `robot-software-engineer`
- Closeout time: `2026-07-12 14:28 CST`
- Product status: accepted as O3/O1 strict no-motion blocker narrowing only
- Proof boundary: `software_proof_o3_o1_strict_no_motion_map_server_configure_failure_repair_only`

## 用户价值和产品北极星

用户价值是继续解除真实上位机 fixed-route/nav 的前置阻塞：上一轮已经把 `/map_server` blocker 下钻到 configure callback return failure，本轮进一步确认 failure 发生在 deferred map read completion 之前，并隔离 FastDDS SHM 噪声。产品北极星仍是普通手机用户一键发车送垃圾；本 sprint 不交付路径生成、路线执行、底盘运动、HIL、送达或生产云能力。

## OKR 映射和方向判断

- O5：继续约 `85%`，方向 `暂停 support-only`。没有真实 HTTPS/TLS、公网入口、production DB/queue、worker cutover、OSS/CDN live traffic、真实手机/browser 或 external production evidence。
- O1/O3：`继续` strict no-motion 现场链路。本轮为 current same-run path generation 与 Nav2 route execution 的 `/map_server` lifecycle 前置 blocker 下钻。
- O6/O7：继续约 `93%`，方向 `暂停等待材料`。没有新的 live route execution、delivery/operator 或 production readback。
- OKR 结论：`不调整` 百分比，`不归档` KR。

## KR 拆解、更新或历史归档

本轮不归档任何 KR。新增证据只进入 O3/O1 supporting chain：

- Primary live artifact `status=blocked_with_root_cause`。
- `proof.root_causes[0].layer=Nav2 map_server transition callback`。
- `proof.root_causes[0].reason=map_server_configure_return_failure_before_deferred_map_read_completed`。
- `proof.root_causes[0].detail=lifecycle_manager_changestate_response_failure_during_configure_before_deferred_map_read_completed`。
- `proof.map_server_transition_callback_probe.canonical_classification=map_server_configure_return_failure_before_deferred_map_read_completed`。
- `runtime_log_window.events.map_read_after_state_change_failure=true`。
- `runtime_log_window.dds_transport_error_text=""`。
- `bond_timing.bond_stage=not_created_before_configure_return_failure`。

## 本轮核心抓手

Robot Software 把 12-55 的 `map_server_configure_callback_return_failure` 下钻到 configure ChangeState failure 与 deferred map read completion ordering：lifecycle manager 发起 `/map_server` configure ChangeState 后收到 failure，map read completion 在 failure 之后才落日志，bond 未在 configure failure 前创建。FastDDS no-SHM guard 已进入 ROS 子进程环境，live artifact 没有 SHM error text，因此 DDS 端口锁不是本轮 primary root cause。

## 实际改动和验证结果

Robot Software 已完成 helper/tests/navigation docs/artifacts 侧实现，Product 本轮 closeout 更新 sprint/OKR/process 留档。

Engineering 验证事实：

- `python3 -m py_compile onboard/scripts/o10_amcl_nav2_runtime_proof.py` return `0`。
- `python3 -m unittest onboard.tests.test_nav2_runtime_proof_helper` return `0` with `Ran 123 tests in 2.272s OK`。
- `bash -n onboard/scripts/o11_nav2_lifecycle.sh` return `0`。
- local strict no-motion dry-run return `2` fail-closed。
- board mkdir/scp return `0`。
- true-board strict no-motion run return `2` with `reason=map_server_configure_return_failure_before_deferred_map_read_completed`。
- artifact pull return `0`。
- scoped `git diff --check` return `0`。

Primary artifact:

- `sprints/2026.07.12_13-54_o3_map_server_configure_failure_repair/artifacts/live_o10_map_server_configure_failure_repair.raw.json`

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

- Primary artifact 从上一轮 `map_server_configure_callback_return_failure` 收窄为 `map_server_configure_return_failure_before_deferred_map_read_completed`。
- artifact 记录 configure ChangeState failure 与 deferred map read completion 的先后关系。
- FastDDS no-SHM guard 已生效，且 live artifact 的 `dds_transport_error_text` 为空。
- 所有 motion/control/delivery/HIL 字段保持 false。
- 本轮不声称 lifecycle clean、path generation、route execution、delivery/operator acceptance、current live HIL、safe-to-control、current live map navigation readiness 或 production cloud evidence。

## 优先级和验收口径

Next run P0：`robot-software-engineer` 继续查 lifecycle manager ChangeState response handling、map_server `on_configure` return path、map IO completion ordering、executor timing 和 bond creation prerequisites。

验收口径：

- `/map_server` lifecycle clean/active，或输出比 `map_server_configure_return_failure_before_deferred_map_read_completed` 更窄的 callback exception / parameter / map IO / ChangeState RPC / executor root cause。
- 继续保持 strict no-motion，不发布 `/cmd_vel`，不调用 `/api/base/manual`，不打开 WAVE ROVER UART。
- 不继续 O5 support-only；不 hand off to Algorithm until `/map_server` lifecycle is clean。

## 风险、阻塞和证据链缺口

- `/map_server` 仍未 lifecycle clean/active。
- `/map` sample、`/amcl_pose`、dynamic `map->odom`、planner-only path generation 均未恢复。
- LiDAR `/dev/ttyACM0` 仍有 `SerialException` 背景噪声，但本轮 artifact primary root cause 已在 map_server transition ordering 层；硬件串口问题不在本 sprint 范围内。
- 仍缺 route execution、delivery/operator acceptance、current live HIL、safe-to-control 和 production external evidence。

## 需要创建或更新的 Sprint 文档

Created or updated in closeout:

- `sprints/2026.07.12_13-54_o3_map_server_configure_failure_repair/side2side_check.md`
- `sprints/2026.07.12_13-54_o3_map_server_configure_failure_repair/final.md`
- `OKR.md`
- `docs/process/okr_progress_log.md`
