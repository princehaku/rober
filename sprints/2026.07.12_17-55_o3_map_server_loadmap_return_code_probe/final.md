# Final - O3 Map Server LoadMap Return Code Probe

## Sprint Metadata

- sprint_type: epic
- Sprint: `sprints/2026.07.12_17-55_o3_map_server_loadmap_return_code_probe/`
- Product owner: `product-okr-owner`
- Implementation owner: `robot-software-engineer`
- Closeout time: `2026-07-12 17:55 CST`
- Product status: accepted as O3/O1 strict no-motion lifecycle gate unblock only
- Proof boundary: `software_proof_o3_o1_strict_no_motion_map_server_loadmap_return_code_probe_only`

## 用户价值和产品北极星

用户价值是把真实上位机 fixed-route/nav 链路推到 same-run path generation、route execution、delivery/operator acceptance 和 HIL/production evidence。产品北极星仍是普通手机用户一键发车送垃圾。

本 sprint 不交付用户可见发车能力；它交付的是一个关键上游 gate 的事实变化：`/map_server` 和 AMCL lifecycle 已 active，下一步 blocker 必须转向 lifecycle-active 后的 graph/downstream readback。

## OKR 映射和方向判断

- O5：继续约 `85%`，方向仍是暂停 support-only；本轮没有真实公网 HTTPS/TLS、4G/SIM、production DB/queue、worker cutover、OSS/CDN live traffic、真实手机/browser 或 external production evidence。
- O1/O3：继续 strict no-motion 现场链路。本轮接受为 `/map_server` + AMCL lifecycle gate unblock，但不接受为 path、route、HIL 或 delivery progress。
- O6/O7：继续约 `93%`，方向仍是等待 live route execution、delivery/operator 或 production readback。
- OKR 结论：O5 继续约 `85%`，O1/O6/O7 继续约 `93%`，`不调整` 百分比，`不归档` KR。
- 方向判断：继续 O3/O1 lifecycle-active graph/downstream readback；不回退到旧 map_server lifecycle inactive/on_configure blockers。

## KR 拆解、更新或历史归档

本轮不归档任何 KR。新增证据只进入 O3/O1 supporting evidence chain：

- Primary live artifact: `sprints/2026.07.12_17-55_o3_map_server_loadmap_return_code_probe/artifacts/live_o10_map_server_loadmap_return_code_probe.raw.json`
- `status=blocked_with_root_cause`
- `map_server_active=true`
- `amcl_active=true`
- `managed_runtime_log_lifecycle_readback.clean=true`
- `proof.map_server_transition_callback_probe.canonical_classification=map_server_lifecycle_active`
- `load_map_response_from_yaml.response_status=success_equivalent_map_read_completed_before_failure`
- `load_map_response_from_yaml.return_code=not_logged_by_nav2_map_server_runtime`
- `proof.artifact_closeout.primary_root_cause.reason=managed_runtime_graph_probe_timeout_after_lifecycle_active_log`
- secondary blocked facts: `/scan_no_publisher`、`/map_once_not_observed`、`/amcl_pose_topic_missing`、`/tf_topic_missing`

历史归档位置不变：已归档 O3 仍在 `OKR.md` 的归档 Objective 区等待真实现场验证重新激活；本轮没有把任何 KR 移入历史区。

## 本轮核心抓手

Robot Software 把 16:55 的 on_configure return-source blocker 越过了：runtime logs show `Server map_server connected with bond`、`Server amcl connected with bond`、`Managed nodes are active`，artifact 因此标记 `map_server_active=true` 和 `amcl_active=true`。

新的 primary blocker 是：

`Managed runtime graph readback / managed_runtime_graph_probe_timeout_after_lifecycle_active_log / map_server_and_amcl_lifecycle_active_logged_but_graph_wait_or_downstream_readback_not_clean`

Product 判断：这是 lifecycle gate unblock，不是 mission progress。

## 实际改动和验证结果

Robot Software 已完成 helper/tests/navigation docs/artifacts 侧实现，Product 本轮 closeout 更新 sprint/OKR/process 留档。

Engineering 验证事实来自 `tech-done.md`：

- `python3 -m py_compile onboard/scripts/o10_amcl_nav2_runtime_proof.py` PASS。
- `python3 -m unittest onboard.tests.test_nav2_runtime_proof_helper` PASS with `Ran 129 tests in 2.294s` / `OK`。
- `bash -n onboard/scripts/o11_nav2_lifecycle.sh` PASS。
- local strict no-motion run return `2` fail-closed。
- SSH/scp/board run/pull completed。
- true-board strict no-motion run return `2` because downstream proof remains blocked。
- scoped `git diff --check` PASS。

No-motion fields remain false:

- `path_generation_attempted=false`
- `path_generated=false`
- `safe_to_control=false`
- `publishes_cmd_vel=false`
- `calls_base_manual=false`
- `uses_base_uart=false`
- `robot_control_executed=false`
- `route_execution_success=false`
- `delivery_success=false`
- `hil_pass=false`

## Product Acceptance

Accepted as O3/O1 strict no-motion lifecycle gate unblock only。

Accepted because:

- `map_server_active=true` and `amcl_active=true` are proven by managed runtime log lifecycle readback。
- `managed_runtime_log_lifecycle_readback.clean=true`。
- canonical map-server classification is now `map_server_lifecycle_active`。
- `load_map_response_from_yaml.response_status=success_equivalent_map_read_completed_before_failure` excludes the older “map never read” family, while direct return code remains not logged by Nav2 runtime。
- strict no-motion invariants stayed fail-closed。

Rejected as mission progress because this is not path generation, route execution, delivery/operator acceptance, current live HIL, safe-to-control, current live map navigation readiness or production cloud/external evidence。

## 优先级和验收口径

Next run P0 owner: `Robot Software`。

验收口径：

- 首先 fix/decide `managed_runtime_graph_probe_timeout_after_lifecycle_active_log`。
- 不得把下一轮 primary blocker 回退为旧 `map_server_lifecycle_not_active`、`map_server_on_configure_return_false_after_valid_map_io_deferred_completion` 或 `map_server_changestate_response_false_before_map_io_completion`，除非新 true-board evidence 推翻 17:55 artifact。
- graph/readback clean 后，再处理 `/scan_no_publisher`、`/map_once_not_observed`、`/amcl_pose_topic_missing`、`/tf_topic_missing`。
- `Algorithm` 只在 graph/topic readback clean enough 后接 AMCL/TF/path work。
- `Hardware` 只在 LiDAR serial/runtime/wiring becomes primary 时介入，并先读 `docs/vendor/VENDOR_INDEX.md`。
- strict no-motion 继续保持：不发布 `/cmd_vel`，不调用 `/api/base/manual`，不发送 NavigateToPose，不打开 WAVE ROVER UART。

## 风险、阻塞和证据链缺口

- lifecycle 已 active，但 ROS graph readback can still time out after lifecycle active logs。
- `/scan` publisher/sample、`/map` topic/sample、`/amcl_pose` topic 和 `/tf` 仍未证明。
- planner-only path gate 未 ready，`path_generation_attempted=false` and `path_generated=false`。
- LiDAR driver log still shows serial instability, but it is not the accepted primary blocker until graph/downstream readback proves LiDAR serial/runtime/wiring is primary。
- 仍没有 same-run path generation success、`route.csv`、keyframe、rosbag、replay JSONL、route execution、delivery/operator acceptance、current live HIL、safe-to-control 或 production external evidence。

## 需要创建或更新的 Sprint 文档

Created or updated in closeout:

- `sprints/2026.07.12_17-55_o3_map_server_loadmap_return_code_probe/side2side_check.md`
- `sprints/2026.07.12_17-55_o3_map_server_loadmap_return_code_probe/final.md`
- `OKR.md`
- `docs/process/okr_progress_log.md`
