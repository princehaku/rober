# Final - O3 Map Server On-Configure Return Source Repair

## Sprint Metadata

- sprint_type: epic
- Sprint: `sprints/2026.07.12_16-55_o3_map_server_on_configure_return_source_repair/`
- Product owner: `product-okr-owner`
- Implementation owner: `robot-software-engineer`
- Closeout time: `2026-07-12 17:35 CST`
- Product status: accepted as O3/O1 strict no-motion blocker narrowing only
- Proof boundary: `software_proof_o3_o1_strict_no_motion_map_server_on_configure_return_source_repair_only`

## 用户价值和产品北极星

产品北极星仍是普通手机用户一键发车送垃圾。当前用户价值链最短阻塞是 `/map_server` lifecycle：只有它 clean/active 后，Algorithm 才能继续验证 `/map`、AMCL、dynamic `map->odom`、planner-only path generation、route execution 和 delivery/operator acceptance。

本 sprint 不交付路线执行、底盘运动、HIL、送达、operator acceptance 或生产云能力；它只把 O3/O1 strict no-motion 现场 blocker 继续下钻。

## OKR 映射和方向判断

- O5：继续约 `85%`，方向仍是暂停 support-only。没有真实 HTTPS/TLS、公网入口、production DB/queue、worker cutover、OSS/CDN live traffic、真实手机/browser 或 external production evidence。
- O1/O3：继续 strict no-motion 现场链路。本轮只把 current same-run path generation 与 Nav2 route execution 的 `/map_server` lifecycle 前置 blocker 继续收窄。
- O6/O7：继续约 `93%`，方向仍是等待 live route execution、delivery/operator 或 production readback。
- OKR 结论：O5 继续约 `85%`，O1/O6/O7 继续约 `93%`，`不调整` 百分比，`不归档` KR。

方向判断：继续 O3/O1 blocker narrowing；不要回到 O5 support-only；不要 hand off to Algorithm until `/map_server` lifecycle is clean。

## KR 拆解、更新或历史归档

本轮不归档任何 KR。新增证据只进入 O3/O1 supporting evidence chain：

- Primary live artifact: `sprints/2026.07.12_16-55_o3_map_server_on_configure_return_source_repair/artifacts/live_o10_map_server_on_configure_return_source_repair.raw.json`
- `status=blocked_with_root_cause`
- `proof.root_causes[0].reason=map_server_on_configure_return_false_after_valid_map_io_deferred_completion`
- `proof.map_server_transition_callback_probe.canonical_classification=map_server_on_configure_return_false_after_valid_map_io_deferred_completion`
- `proof.map_server_transition_callback_probe.on_configure_return_source.source_family=on_configure_return_false_source`
- `proof.map_server_transition_callback_probe.on_configure_return_source.primary_source=on_configure_return_false_after_valid_map_inputs_while_map_io_log_completes_later`
- `map_input_validation.valid_for_map_server=true`
- YAML/PGM readable
- no map_server-scoped exception
- no service/RPC timeout
- map IO completion logged after ChangeState failure

历史归档位置不变：已归档 O3 仍在 `OKR.md` 的归档 Objective 区等待真实现场验证重新激活；本轮没有把任何 KR 移入历史区。

## 本轮核心抓手

Robot Software 没有修到 `/map_server active`，但把 15:54 的 `map_server_changestate_response_false_before_map_io_completion` 继续收窄到：

`map_server_on_configure_return_false_after_valid_map_io_deferred_completion`

关键事实：

- lifecycle manager 请求 configure。
- `/map_server` configure callback 已进入。
- managed map YAML/PGM 可读，YAML 字段有效，runtime analysis OK。
- 没有 map_server-scoped exception。
- 没有 ChangeState service/RPC timeout log。
- ChangeState failure/false response 发生在 map IO completion 前约 `91.582ms`。
- `map_io` 后续仍输出 `Read map ...` completion。

Product 判断：这比 15:54 更窄，不算重复消费同一 blocker。

## 实际改动和验证结果

Robot Software 已完成 helper/tests/navigation docs/artifacts 侧实现，Product 本轮 closeout 更新 sprint/OKR/process 留档。

Engineering 验证事实来自 `tech-done.md`：

- `python3 -m py_compile onboard/scripts/o10_amcl_nav2_runtime_proof.py` return `0`。
- `python3 -m unittest onboard.tests.test_nav2_runtime_proof_helper` final return `0` with `Ran 127 tests in 2.282s OK`。
- `bash -n onboard/scripts/o11_nav2_lifecycle.sh` return `0`。
- local strict no-motion run return `2` fail-closed。
- board mkdir/scp return `0`。
- true-board strict no-motion run return `2` with narrowed root cause。
- artifact pull return `0`。
- scoped `git diff --check` return `0`。
- anchor checks return `0`。

No-motion fields remain false:

- `path_generation_attempted=false`
- `path_generated=false`
- `safe_to_control=false`
- `publishes_cmd_vel=false`
- `calls_base_manual=false`
- `uses_base_uart=false`
- `route_execution_success=false`
- `delivery_success=false`
- `hil_pass=false`

## Product Acceptance

Product status: accepted as O3/O1 strict no-motion blocker narrowing only。

Accepted because:

- New primary root cause is `map_server_on_configure_return_false_after_valid_map_io_deferred_completion`。
- `on_configure_return_source.source_family=on_configure_return_false_source` gives a narrower return-source bucket than 15:54.
- `map_input_validation.valid_for_map_server=true` and YAML/PGM readable exclude invalid map input as primary.
- No map_server-scoped exception, service/RPC timeout, or DDS SHM transport error is primary.
- strict no-motion invariants stayed fail-closed.

Rejected as mission progress because this is not lifecycle clean, path generation, route execution, delivery/operator acceptance, current live HIL, safe-to-control, current live map navigation readiness or production cloud evidence.

## 优先级和验收口径

Next run P0 owner: `robot-software-engineer`。

Next run: inspect Nav2 map_server `loadMapResponseFromYaml` return code、`on_configure` return path、executor/log ordering、lifecycle manager ChangeState response handling。

验收口径：

- 首选 `/map_server` lifecycle clean/active。
- 如果仍 blocked，必须继续比 `map_server_on_configure_return_false_after_valid_map_io_deferred_completion` 更窄，而不是重复包装同一 blocker。
- strict no-motion 继续保持：不发布 `/cmd_vel`，不调用 `/api/base/manual`，不发送 NavigateToPose，不打开 WAVE ROVER UART。
- Hardware only if LiDAR serial/runtime/wiring becomes primary and vendor docs are read。

## 风险、阻塞和证据链缺口

- `/map_server active=false`，仍未 lifecycle clean/active。
- `/map` sample、AMCL active、dynamic `map->odom`、planner-only path generation 均未恢复。
- 仍没有 same-run path generation success、`route.csv`、keyframe、rosbag、replay JSONL、route execution、delivery/operator acceptance、current live HIL、safe-to-control 或 production external evidence。
- runtime log 仍有 LiDAR `SerialException` 背景噪声，但本轮 primary root cause 不依赖它；只有 LiDAR serial/runtime/wiring 成为 primary 时才转 Hardware，并先读 `docs/vendor/VENDOR_INDEX.md`。
- 同一 blocker 红线：本轮相比 15:54 已收窄，不算重复；下一轮若仍只能重复 `map_server_on_configure_return_false_after_valid_map_io_deferred_completion` 而不能修到 active 或继续收窄，则应升级 CEO 或切换 Objective。

## 需要创建或更新的 Sprint 文档

Created or updated in closeout:

- `sprints/2026.07.12_16-55_o3_map_server_on_configure_return_source_repair/side2side_check.md`
- `sprints/2026.07.12_16-55_o3_map_server_on_configure_return_source_repair/final.md`
- `OKR.md`
- `docs/process/okr_progress_log.md`
