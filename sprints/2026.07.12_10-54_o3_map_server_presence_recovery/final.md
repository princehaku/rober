# Final - O3 Map Server Presence Recovery

## Sprint Metadata

- sprint_type: epic
- Sprint: `sprints/2026.07.12_10-54_o3_map_server_presence_recovery/`
- Product owner: `product-okr-owner`
- Implementation owner: `robot-software-engineer`
- Closeout time: `2026-07-12 12:07 CST`
- Product status: accepted as O3/O1 strict no-motion presence recovery delta only
- Proof boundary: `software_proof_o3_o1_strict_no_motion_map_server_presence_recovery_only`

## 用户价值和产品北极星

用户价值是把真实上位机当前 `/map_server` presence blocker 从 09-54 的 read-only `Node not found`，推进到 explicit managed runtime recovery proof 的更窄失败点。产品北极星仍是普通手机用户一键发车完成固定路线送垃圾；本 sprint 不交付路线生成、路线执行、底盘控制、HIL、投递或云端生产能力。

## OKR 映射和方向判断

- O5：继续约 `85%`，方向 `暂停 support-only`。没有真实 external production evidence，不允许用 readiness packet、surface、review 或 handoff 继续计分。
- O1/O3：`继续`。本轮接受为 strict no-motion `/map_server` presence recovery delta，服务 current same-run path generation 缺口的前置条件。
- O6/O7：继续约 `93%`，方向 `暂停等待材料`。没有新的 route execution、delivery/operator 或 production readback。
- OKR 结论：`不调整` 百分比，`不归档` KR。

## KR 拆解、更新或历史归档

本轮不归档任何 KR。新增证据只进入 O3/O1 supporting chain：

- `status=blocked_with_root_cause`
- `managed_runtime_requested=true`
- `managed_runtime_started=true`
- `managed_runtime_boundary=explicit_opt_in_managed_localization_runtime_no_motion`
- `managed_runtime_cleanup_ok=true`
- `proof.map_server_presence_recovery.canonical_classification=map_server_lifecycle_not_active_after_recovery`
- `failure_detail=lifecycle_manager_failed_to_change_state_for_map_server`
- `root_cause_filtering.applied=true`

已完成 KR 历史记录位置：无新增完成 KR，历史区不更新。证据来源为 `tech-done.md`、live artifact、`side2side_check.md`、本 `final.md`、`OKR.md` closeout note 和 `docs/process/okr_progress_log.md`。

## 本轮核心抓手

Robot Software 把 helper 从默认 read-only existing graph 诊断升级为 explicit opt-in managed localization runtime no-motion recovery proof。Product 验收以返工后的 live artifact 为准：package-missing / graph-timeout 噪声只保留在 `root_cause_filtering.suppressed_root_causes`，顶层 root cause 收敛到 map_server lifecycle/configure failure。

## 实际改动和验证结果

Robot Software 已完成 helper/tests/navigation docs/artifacts 侧实现，Product 本轮 closeout 更新 sprint/OKR/process 留档。

Engineering 验证事实：

- `python3 -m py_compile onboard/scripts/o10_amcl_nav2_runtime_proof.py` exit code `0`。
- `python3 -m unittest onboard.tests.test_nav2_runtime_proof_helper` passed，`Ran 116 tests in 2.284s`，`OK`。
- local strict no-motion dry-run exit code `2`，按预期 fail-closed。
- board SSH/SCP passed。
- live helper exit code `2`，写出 blocked artifact。
- scoped `git diff --check` passed。

Live artifact:

- `sprints/2026.07.12_10-54_o3_map_server_presence_recovery/artifacts/live_o10_map_server_presence_recovery.raw.json`

关键字段：

- `status=blocked_with_root_cause`
- `evidence_type=blocked_with_root_cause`
- `managed_runtime_requested=true`
- `managed_runtime_started=true`
- `managed_runtime_boundary=explicit_opt_in_managed_localization_runtime_no_motion`
- `managed_runtime_cleanup_ok=true`
- `proof.map_server_presence_recovery.canonical_classification=map_server_lifecycle_not_active_after_recovery`
- `failure_detail=lifecycle_manager_failed_to_change_state_for_map_server`
- `root_cause_filtering.applied=true`
- top `proof.root_causes` only contains `Nav2 map_server presence recovery / map_server_lifecycle_not_active_after_recovery / lifecycle_manager_failed_to_change_state_for_map_server`

Runtime log 关键事实：

- lifecycle manager starts。
- map_server enters `Configuring`。
- `trashbot_map.yaml` and `trashbot_map.pgm` load。
- lifecycle manager reports `Failed to change state for node: map_server`。

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

Accepted as O3/O1 strict no-motion presence recovery delta only.

理由：

- 本轮已越过 09-54 的 `managed_runtime_requested=false` / read-only existing graph 边界。
- live artifact 证明 managed runtime 已显式请求并启动，map yaml 和 pgm 已被 map_server 读取。
- Robot Software 初版存在 root-cause 误导，返工后已把 package-missing / graph-timeout 噪声压到 `root_cause_filtering.suppressed_root_causes`，顶层 root cause 只保留 `map_server_lifecycle_not_active_after_recovery`。
- 所有 motion/control/delivery/HIL 字段保持 false。
- 本轮不声称 same-run path generation、route execution、delivery/operator acceptance、current live HIL、safe-to-control、current live map navigation readiness 或 production cloud evidence。

## 优先级和验收口径

下一轮 P0：`robot-software-engineer` 修复或继续收窄 `lifecycle_manager_failed_to_change_state_for_map_server`，让 `/map_server` lifecycle transition clean，或输出可执行的 configure error。

验收口径：

- `/map_server` lifecycle transition 不再失败在 `Failed to change state for node: map_server`。
- `/map` sample、AMCL pose、dynamic `map->odom` 和 planner-only path gate 在 lifecycle clean 后再由 Algorithm 接手。
- Safety fields remain false unless a separately planned and accepted motion/HIL sprint exists。

## 风险、阻塞和证据链缺口

- 当前 blocker 是 `map_server_lifecycle_not_active_after_recovery` / `lifecycle_manager_failed_to_change_state_for_map_server`。
- ROS2 graph 仍有 daemon/node-list timeout 和 duplicate/FastDDS port warning 风险，但不是本轮顶层 root cause。
- LiDAR `/dev/ttyACM0` 读空或多进程占用出现在日志中，但本轮没有改硬件配置，也不把它当 primary blocker。
- 仍缺 same-run path generation success、route execution、delivery/operator acceptance、current live HIL、safe-to-control、current live map navigation readiness 和 production cloud evidence。

## 需要创建或更新的 Sprint 文档

Created or updated in closeout:

- `sprints/2026.07.12_10-54_o3_map_server_presence_recovery/side2side_check.md`
- `sprints/2026.07.12_10-54_o3_map_server_presence_recovery/final.md`
- `OKR.md`
- `docs/process/okr_progress_log.md`
