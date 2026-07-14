# Final - O3 Map Server ChangeState Response Repair

## Sprint Metadata

- sprint_type: epic
- Sprint: `sprints/2026.07.12_15-54_o3_map_server_changestate_response_repair/`
- Product owner: `product-okr-owner`
- Implementation owner: `robot-software-engineer`
- Closeout time: `2026-07-12 16:25 CST`
- Product status: accepted as O3/O1 strict no-motion blocker narrowing only
- Proof boundary: `software_proof_o3_o1_strict_no_motion_map_server_changestate_response_repair_only`

## 用户价值和产品北极星

用户价值是继续解除真实上位机 fixed-route/nav 的前置阻塞：`/map_server` lifecycle clean/active 是 `/map`、AMCL、dynamic `map->odom`、planner-only path、后续路线执行和送达证据的上游 gate。产品北极星仍是普通手机用户一键发车送垃圾；本 sprint 不交付路线执行、底盘运动、HIL、送达、operator acceptance 或生产云能力。

## OKR 映射和方向判断

- O5：继续约 `85%`，方向仍是暂停 support-only。没有真实 HTTPS/TLS、公网入口、production DB/queue、worker cutover、OSS/CDN live traffic、真实手机/browser 或 external production evidence。
- O1/O3：继续 strict no-motion 现场链路。本轮只把 current same-run path generation 与 Nav2 route execution 的 `/map_server` lifecycle 前置 blocker 继续下钻。
- O6/O7：继续约 `93%`，方向仍是等待 live route execution、delivery/operator 或 production readback。
- OKR 结论：O5 继续约 `85%`，O1/O6/O7 继续约 `93%`，`不调整` 百分比，`不归档` KR。

## KR 拆解、更新或历史归档

本轮不归档任何 KR。新增证据只进入 O3/O1 supporting chain：

- Primary live artifact `status=blocked_with_root_cause`。
- `proof.root_causes[0].reason=map_server_changestate_response_false_before_map_io_completion`。
- `proof.artifact_closeout.primary_root_cause.reason=map_server_changestate_response_false_before_map_io_completion`。
- `proof.map_server_transition_callback_probe.canonical_classification=map_server_changestate_response_false_before_map_io_completion`。
- `proof.map_server_transition_callback_probe.service_rpc_timing.changestate_response_false_before_map_io_completion=true`。
- `proof.map_server_transition_callback_probe.service_rpc_timing.service_timeout_or_rpc_error_observed_in_log=false`。
- `proof.map_server_transition_callback_probe.service_rpc_timing.service_timeout_s=12.0`。
- `map_io_timing.image_load_to_state_failure_ms=43.624`。
- `map_io_timing.state_failure_to_map_read_completed_ms=93.266`。
- `map_io_timing.configure_to_map_read_completed_ms=139.415`。

历史归档位置不变：已归档 O3 仍在 `OKR.md` 的归档 Objective 区等待真实现场验证重新激活；本轮没有把任何 KR 移入历史区。

## 本轮核心抓手

Robot Software 没有修到 `/map_server active`，但把 14:54 的 `map_server_changestate_response_failure_after_image_load_before_map_read_completed` 继续收窄为 `map_server_changestate_response_false_before_map_io_completion` / `lifecycle_manager_changestate_response_false_while_map_io_completed_later`。

关键 ordering 是：lifecycle manager configure requested，map_server callback entered，YAML/image load started，ChangeState response false，随后 map read completed。该结果说明当前 primary blocker 不再只是“image load 后 read 完成前失败”的宽泛描述，而是 ChangeState response false 与 map IO completion 的时序窗口。

## 实际改动和验证结果

Robot Software 已完成 helper/tests/navigation docs/artifacts 侧实现，Product 本轮 closeout 更新 sprint/OKR/process 留档。

Engineering 验证事实来自 `tech-done.md`：

- `python3 -m py_compile onboard/scripts/o10_amcl_nav2_runtime_proof.py` return `0`。
- `python3 -m unittest onboard.tests.test_nav2_runtime_proof_helper` return `0` with `Ran 127 tests in 2.283s OK`。
- `bash -n onboard/scripts/o11_nav2_lifecycle.sh` return `0`。
- local strict no-motion dry-run return `2` fail-closed。
- board mkdir/scp return `0`。
- true-board strict no-motion run return `2` with narrowed root cause。
- artifact pull return `0`。
- scoped `git diff --check` return `0`。

Primary artifact:

- `sprints/2026.07.12_15-54_o3_map_server_changestate_response_repair/artifacts/live_o10_map_server_changestate_response_repair.raw.json`

No-motion fields remain false:

- `path_generation_attempted=false`
- `path_generated=false`
- `safe_to_control=false`
- `calls_base_manual=false`
- `uses_base_uart=false`
- `route_execution_success=false`
- `delivery_success=false`
- `hil_pass=false`

## Product Acceptance

Accepted as O3/O1 strict no-motion blocker narrowing only。

理由：

- Primary artifact 比 14:54 更窄，定位到 ChangeState response false while map IO still incomplete。
- service RPC 证据显示 `changestate_response_false_before_map_io_completion=true`，且没有 service timeout 或 RPC error log。
- map IO timing 显示 failure 后约 `93.266ms` 才 map read completed。
- 所有 motion/control/delivery/HIL 字段保持 false。
- 本轮不声称 lifecycle clean、path generation、route execution、delivery/operator acceptance、current live HIL、safe-to-control、current live map navigation readiness 或 production cloud evidence。

## 优先级和验收口径

Next run P0：`robot-software-engineer` 检查 Nav2 map_server `on_configure` return false path、ChangeState response false while map IO still incomplete、executor/service future timing、map IO sync/async ordering。

验收口径：

- `/map_server` lifecycle clean/active；或输出比 `map_server_changestate_response_false_before_map_io_completion` 更窄的 callback exception、return false source、parameter、executor/service future 或 map IO sync/async root cause。
- 继续保持 strict no-motion，不发布 `/cmd_vel`，不调用 `/api/base/manual`，不打开 WAVE ROVER UART。
- 不继续 O5 support-only；不 hand off to Algorithm until `/map_server` lifecycle is clean。
- Hardware only if LiDAR serial/runtime becomes primary and vendor docs are read。

## 风险、阻塞和证据链缺口

- `/map_server` 仍未 lifecycle clean/active。
- `/map` sample、AMCL、dynamic `map->odom`、planner-only path generation 均未恢复。
- 仍没有 same-run path generation success、`route.csv`、keyframe、rosbag、replay JSONL、route execution、delivery/operator acceptance、current live HIL、safe-to-control 或 production external evidence。
- runtime log 里仍可能有 LiDAR serial/runtime 背景噪声，但本轮 primary root cause 不依赖它；只有 LiDAR serial/runtime 成为 primary 时才转 Hardware，并先读 `docs/vendor/VENDOR_INDEX.md`。

## 需要创建或更新的 Sprint 文档

Created or updated in closeout:

- `sprints/2026.07.12_15-54_o3_map_server_changestate_response_repair/side2side_check.md`
- `sprints/2026.07.12_15-54_o3_map_server_changestate_response_repair/final.md`
- `OKR.md`
- `docs/process/okr_progress_log.md`
