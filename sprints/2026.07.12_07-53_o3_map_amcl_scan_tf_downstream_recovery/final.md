# Final - O3 Map/AMCL/Scan/TF Downstream Recovery

## Sprint Metadata

- sprint_type: epic
- Sprint: `sprints/2026.07.12_07-53_o3_map_amcl_scan_tf_downstream_recovery/`
- Product owner: `product-okr-owner`
- Implementation owner: `robot-software-engineer`
- Closeout time: `2026-07-12 08:31 CST`
- Proof boundary: `software_proof_o3_o1_strict_no_motion_downstream_recovery_only`
- Outcome: accepted as O3/O1 strict no-motion downstream diagnostic delta; no OKR percentage change.

## 用户价值和产品北极星

用户价值是把真实板 no-motion runtime 从“source/CLI/lightweight readiness 已可用”继续推进到“map lifecycle、AMCL lifecycle、scan sample、map topic 与 TF 的下游 root cause 可读、可复验”。产品北极星仍是普通手机用户一键发车完成固定路线送垃圾；本 sprint 不交付路线执行、不交付送达、不交付 safe-to-control，也不证明 HIL。

## OKR 映射和方向判断

- O5：保持约 `85%`，`不调整`。O5 仍是最低 Objective，但本轮没有真实 production cloud、HTTPS/TLS、4G/SIM、production DB/queue、worker cutover、OSS/CDN live traffic、真实手机/browser 或 external production evidence。
- O1：保持约 `93%`，`不调整`。本轮没有 current same-run path generation success、Nav2 route execution success、current live HIL、safe-to-control、底盘反馈增量或真实控制执行。
- O6/O7：保持约 `93%`，`不调整`。本轮没有新的 same-task route execution、delivery record、operator acceptance、production readback 或可消费 mission material。
- 方向判断：`继续` O3/O1 strict no-motion downstream recovery；`暂停` O5 support-only lane；`不归档` KR。

## KR 拆解、更新或历史归档

本轮 `不归档` 任何 KR。

原因：

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
- 没有 same-run path generation success、route execution、delivery/operator acceptance、current live HIL 或 production external evidence

已完成 KR 历史记录位置：本轮无新增完成 KR，历史区不更新。证据只作为 O3/O1 supporting diagnostic delta 记录在本 sprint 的 `tech-done.md`、`side2side_check.md`、`final.md`、`OKR.md` Key Results 和 `docs/process/okr_progress_log.md`。

## 本轮核心抓手和实际结果

本轮核心抓手是让 `robot-software-engineer` 在 strict no-motion 下游恢复中，把上一轮粗粒度 `map_server/amcl inactive`、`/scan_no_publisher`、`/map_once_not_observed`、`/tf_topic_missing` 拆成更准确的 lifecycle command timeout、publisher-visible sample timeout、map topic missing 与 TF missing。

Robot Software 实际改动由 `tech-done.md` 记录，Product 收口确认只涉及 helper、tests、navigation docs 和本 sprint artifacts。关键事实如下：

1. helper 新增 `proof.downstream_recovery_summary`，覆盖 readiness inputs、map lifecycle、scan、map、AMCL、TF 和 path gate。
2. 修复 `/scan` 分类：endpoint inventory 已看到 publisher 时，不再误报 `/scan_no_publisher`。
3. Targeted unittest 通过：`Ran 100 tests in 2.269s OK`。
4. Local dry-run RC `2`，按预期 fail-closed，`classification=board_source_preflight_source_failed`，符合 macOS 无 `/opt/ros/humble/setup.bash` 边界。
5. True-board scp/run/pull 成功；live run RC `2`，产出 canonical artifact `artifacts/live_o10_map_amcl_scan_tf_downstream_recovery.raw.json`。
6. Scoped `git diff --check` RC `0`。

Product closeout 实际改动：

- `sprints/2026.07.12_07-53_o3_map_amcl_scan_tf_downstream_recovery/side2side_check.md`
- `sprints/2026.07.12_07-53_o3_map_amcl_scan_tf_downstream_recovery/final.md`
- `OKR.md`
- `docs/process/okr_progress_log.md`

## 验证结果

Robot Software 验证事实：

- `python3 -m py_compile onboard/scripts/o10_amcl_nav2_runtime_proof.py` RC `0`。
- `python3 -m unittest onboard.tests.test_nav2_runtime_proof_helper` RC `0`，输出 `Ran 100 tests in 2.269s OK`。
- Local fail-closed helper dry-run RC `2`，artifact written。
- True-board helper push RC `0`。
- True-board strict no-motion helper run RC `2`，artifact written。
- True-board artifact pull RC `0`。
- Scoped `git diff --check` RC `0`。

Product closeout 验收命令：

```bash
rg -n "07-53|map_amcl_scan_tf_downstream|downstream_recovery_summary|board_source_preflight_ready|lightweight_cli_ready=true|cli_ready=true|runtime_ready=true|map_lifecycle_preflight_map_server_and_amcl_inactive|map_server_lifecycle_command_timeout|amcl_lifecycle_command_timeout|/scan_reliable_and_best_effort_timeout|/map_topic_missing|/tf_topic_missing|Ran 100|path_generation_attempted=false|path_generated=false|safe_to_control=false|不调整|不归档" OKR.md docs/process/okr_progress_log.md sprints/2026.07.12_07-53_o3_map_amcl_scan_tf_downstream_recovery
```

```bash
git diff --check -- OKR.md docs/process/okr_progress_log.md sprints/2026.07.12_07-53_o3_map_amcl_scan_tf_downstream_recovery
```

## Live Artifact 结论

Canonical artifact:

- `sprints/2026.07.12_07-53_o3_map_amcl_scan_tf_downstream_recovery/artifacts/live_o10_map_amcl_scan_tf_downstream_recovery.raw.json`

关键字段：

- `status=blocked_with_root_cause`
- `board_source_preflight.classification=board_source_preflight_ready`
- `lightweight_cli_ready=true`
- `cli_ready=true`
- `runtime_ready=true`
- `map_lifecycle_preflight.classification=map_lifecycle_preflight_map_server_and_amcl_inactive`
- `map_lifecycle_preflight.blocking_reasons.map_server=map_server_lifecycle_command_timeout`
- `map_lifecycle_preflight.blocking_reasons.amcl=amcl_lifecycle_command_timeout`
- `downstream_recovery_summary.scan.publisher_count=1`
- `downstream_recovery_summary.scan.blocked_reason=/scan_reliable_and_best_effort_timeout`
- `downstream_recovery_summary.map.blocked_reason=map_server_lifecycle_command_timeout`
- `downstream_recovery_summary.map.topic_sample.blocked_reason=/map_topic_missing`
- `downstream_recovery_summary.amcl.blocked_reason=amcl_lifecycle_not_active`
- `downstream_recovery_summary.tf.blocked_reason=/tf_topic_missing`

No-motion 字段继续固定：

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

## Product Judgment

本轮满足 Product acceptance gate，但结论必须保守：

- Accepted：Robot Software implementation accepted as O3/O1 strict no-motion downstream diagnostic delta。
- Accepted：`board_source_preflight_ready`、`lightweight_cli_ready=true`、`cli_ready=true`、`runtime_ready=true` 均保持成立，没有回退到 source/path mismatch 或 `ros2 --help` 单点 gate。
- Accepted：map lifecycle blocker 已明确为 `/map_server` 与 `/amcl` lifecycle command timeout，而不是仅复述 inactive。
- Accepted：canonical `/scan` 结论不是 `/scan_no_publisher`。首次 live artifact 中 publisher_count=1 却误标 `/scan_no_publisher`，Robot Software 已修复分类器并重跑，最终为 publisher visible + `/scan_reliable_and_best_effort_timeout`。
- Not accepted as mission progress：没有 same-run path generation success、route execution、delivery/operator acceptance、current live HIL、safe-to-control 或 production external evidence。

## Blocker 重复消费判断

本轮不按与 `06-54` 同一 blocker 重复消费处理。

理由：

1. `06-54` 的增量是 lightweight CLI readiness 放行，downstream blocker 仍偏粗粒度。
2. `07-53` 保持 `board_source_preflight_ready`、`lightweight_cli_ready=true`、`cli_ready=true`、`runtime_ready=true`，并新增 canonical `downstream_recovery_summary`。
3. `/scan` 从误报 `/scan_no_publisher` 修正为 `publisher_count=1` 且 `/scan_reliable_and_best_effort_timeout`。
4. map/AMCL 从 generic inactive 收窄为 `map_server_lifecycle_command_timeout` 与 `amcl_lifecycle_command_timeout`。

## 剩余风险

- `/map_server` 与 `/amcl` lifecycle command timeout 仍未修复；下一轮必须先处理 `ros2 lifecycle get /map_server` 和 `ros2 lifecycle get /amcl` timeout。
- `/scan` publisher 已可见但 sample timeout，可能是 QoS/window、LiDAR runtime 发布节奏或 driver 状态；不能在没有下一轮证据时猜测串口、波特率或接线。
- `/map_topic_missing` 与 `/tf_topic_missing` 仍未解除，dynamic `map->odom` source 尚未观测。
- planner-only path gate 未运行，`path_generation_attempted=false`、`path_generated=false`。
- 本轮仍是 O3/O1 supporting no-motion diagnostic delta，不是 route execution、delivery/operator acceptance、HIL 或 production evidence。

## 下一轮建议

优先级 P0：继续 O3/O1 strict no-motion lane，由 `robot-software-engineer` 直接处理 lifecycle command timeouts：`ros2 lifecycle get /map_server` 与 `ros2 lifecycle get /amcl` timeout。先让 lifecycle readback clean，再继续 `/scan` publisher-visible sample timeout、`/map_topic_missing` 与 `/tf_topic_missing`。

优先级 P1：如果下一轮证据证明 `/scan_reliable_and_best_effort_timeout` 依赖 LiDAR serial/runtime/接线事实，再交 `rober-hardware-engineer`，并必须先读 `docs/vendor/VENDOR_INDEX.md` 与本地 vendor 资料。当前仍禁止 NavigateToPose、`/cmd_vel`、`/api/base/manual` 和 WAVE ROVER UART。
