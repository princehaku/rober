# Final - O3 Lifecycle-Active Graph Readback Repair

## Sprint Metadata

- sprint_type: epic
- Sprint: `sprints/2026.07.12_18-56_o3_lifecycle_active_graph_readback_repair/`
- Product owner: `product-okr-owner`
- Implementation owner: `robot-software-engineer`
- Closeout time: `2026-07-12 18-56 CST`
- Product status: accepted as O3/O1 strict no-motion downstream blocker narrowing / graph-readback unblock only
- Proof boundary: `software_proof_o3_o1_strict_no_motion_lifecycle_active_graph_readback_repair_only`

## 用户价值和产品北极星

用户价值是继续把真实上位机 fixed-route/nav 链路推进到可验证 same-run path generation、route execution、delivery/operator acceptance 和 HIL/production evidence。产品北极星仍是普通手机用户一键发车送垃圾，并得到可验证结果。

本 sprint 不交付用户可见发车能力；它交付的是一个关键诊断变化：lifecycle-active 之后，`managed_runtime_graph_probe_timeout_after_lifecycle_active_log` 不再遮住 downstream readback，primary blocker 现在是 `/scan_reliable_and_best_effort_timeout`。

## OKR 映射和方向判断

- O5：继续约 `85%`，方向仍是暂停 support-only；本轮没有真实公网 HTTPS/TLS、4G/SIM、production DB/queue、worker cutover、OSS/CDN live traffic、真实手机/browser 或 external production evidence。
- O1/O3：继续 strict no-motion 现场链路。本轮接受为 downstream blocker narrowing / graph-readback unblock，但不接受为 path、route、HIL、安全控制或 delivery progress。
- O6/O7：继续约 `93%`，方向仍是等待 live route execution、delivery/operator 或 production readback。
- OKR 结论：O5 继续约 `85%`，O1/O6/O7 继续约 `93%`，`不调整` 百分比，`不归档` KR。
- 方向判断：继续 O3/O1 `/scan` readback split；不回退到 lifecycle inactive、map_server on_configure、loadmap return-code 或 graph timeout primary wording。

## KR 拆解、更新或历史归档

本轮不归档任何 KR。新增证据只进入 O3/O1 supporting evidence chain：

- Primary live artifact: `sprints/2026.07.12_18-56_o3_lifecycle_active_graph_readback_repair/artifacts/live_o10_lifecycle_active_graph_readback_repair.raw.json`
- `status=blocked_with_root_cause`
- `proof.map_server_active=true`
- `proof.amcl_active=true`
- `proof.managed_runtime_log_lifecycle_readback.clean=true`
- `proof.artifact_closeout.primary_root_cause.layer=Nav2 sensor input`
- `proof.artifact_closeout.primary_root_cause.reason=/scan_reliable_and_best_effort_timeout`
- secondary diagnostic/root cause: `managed_runtime_graph_probe_timeout_after_lifecycle_active_log`
- `proof.downstream_recovery_summary.map.ready=true`
- `proof.map_once_observed=true` / `map_once_observed=true`
- `proof.amcl_pose_observed=false`
- TF blocked: `map_to_odom_dynamic_source_missing`
- `path_generation_attempted=false`
- `path_generated=false`

历史归档位置不变：已归档 O3 仍在 `OKR.md` 的归档 Objective 区等待真实现场验证重新激活；详细历史留在 `docs/process/okr_progress_log.md`。本轮没有把任何 KR 移入历史区。

## 本轮核心抓手

Robot Software 把 17:55 的 lifecycle-active graph blocker 往下推进了一层。现在 `/map_server` 与 AMCL lifecycle active 仍成立，`/map` sample 已 observed，graph timeout 不再是 Product primary blocker。Product 接受的当前 blocker 是：

`Nav2 sensor input / /scan_reliable_and_best_effort_timeout / downstream_readback_after_map_server_and_amcl_lifecycle_active_log`

Product 判断：这是 additive readback evidence，不是 mission progress。

## 实际改动和验证结果

Robot Software 已完成 helper/tests/navigation docs/artifacts 侧实现，Product 本轮 closeout 更新 sprint/OKR/process 留档。

Engineering 验证事实来自 `tech-done.md`：

- `python3 -m py_compile onboard/scripts/o10_amcl_nav2_runtime_proof.py` PASS。
- `python3 -m unittest onboard.tests.test_nav2_runtime_proof_helper` PASS with `Ran 131 tests ... OK`。
- `bash -n onboard/scripts/o11_nav2_lifecycle.sh` PASS。
- local strict no-motion run return `2` fail-closed。
- SSH/scp/board deploy/run/pull completed。
- true-board strict no-motion run return `2` with `status=blocked_with_root_cause`。
- scoped `git diff --check` PASS。

No-motion fields remain false:

- `safe_to_control=false`
- `publishes_cmd_vel=false`
- `calls_base_manual=false`
- `uses_base_uart=false`
- `robot_control_executed=false`
- `route_execution_success=false`
- `delivery_success=false`
- `hil_pass=false`
- `path_generation_attempted=false`
- `path_generated=false`

## Product Acceptance

Accepted as O3/O1 strict no-motion downstream blocker narrowing / graph-readback unblock only。

Accepted because:

- `map_server_active=true` and `amcl_active=true` are still proven by managed runtime lifecycle log readback。
- `managed_runtime_log_lifecycle_readback.clean=true`。
- `managed_runtime_graph_probe_timeout_after_lifecycle_active_log` no longer hides downstream readback and is retained only as secondary diagnostic。
- Primary root cause is now concrete: `/scan_reliable_and_best_effort_timeout` under `Nav2 sensor input`。
- `/map` sample was observed after lifecycle-active logs: `map_once_observed=true`。
- strict no-motion invariants stayed fail-closed。

Rejected as mission progress because this is not path generation, route execution, delivery/operator acceptance, current live HIL, safe-to-control, current live map navigation readiness or production cloud/external evidence。

## 优先级和验收口径

Next run P0 owner: `Robot Software`。

验收口径：

- First split `/scan_reliable_and_best_effort_timeout` into publisher endpoint/QoS/window/ROS readback versus LiDAR runtime。
- Keep `managed_runtime_graph_probe_timeout_after_lifecycle_active_log` as secondary unless new evidence makes graph timeout primary again。
- Keep strict no-motion: do not publish `/cmd_vel`, do not call `/api/base/manual`, do not send NavigateToPose, do not open WAVE ROVER UART。
- `Hardware` joins only if LiDAR serial/runtime/wiring becomes primary and the owner reads `docs/vendor/VENDOR_INDEX.md`。
- `Algorithm` waits until `/scan`, `/amcl_pose`, and dynamic `map->odom` are clean enough for planner-only path proof。

## 风险、阻塞和证据链缺口

- `/scan` publisher is visible, but no LaserScan sample was read through BEST_EFFORT or RELIABLE attempts in the proof window。
- `/amcl_pose` remains unobserved, so AMCL localization readiness is still false。
- Dynamic `map->odom` source is still missing, so `map->base_link` remains blocked。
- `path_generation_attempted=false` and `path_generated=false`。
- Still no same-run path generation success, `route.csv`, keyframe, rosbag, replay JSONL, route execution, delivery/operator acceptance, current live HIL, safe-to-control or production external evidence。

## 需要创建或更新的 Sprint 文档

Created or updated in closeout:

- `sprints/2026.07.12_18-56_o3_lifecycle_active_graph_readback_repair/side2side_check.md`
- `sprints/2026.07.12_18-56_o3_lifecycle_active_graph_readback_repair/final.md`
- `OKR.md`
- `docs/process/okr_progress_log.md`
