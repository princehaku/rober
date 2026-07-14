# Side2Side Check - O3 Map/AMCL/Scan/TF Downstream Recovery

## Sprint Metadata

- sprint_type: epic
- Sprint: `sprints/2026.07.12_07-53_o3_map_amcl_scan_tf_downstream_recovery/`
- Product owner: `product-okr-owner`
- Implementation owner: `robot-software-engineer`
- Closeout time: `2026-07-12 08:31 CST`
- Proof boundary: `software_proof_o3_o1_strict_no_motion_downstream_recovery_only`
- Product status: accepted as downstream diagnostic delta; mission gates remain blocked.

## 用户价值和产品北极星

用户价值是把 true-board strict no-motion helper 从上一轮的 `board_source_preflight_ready` 和 `lightweight_cli_ready=true`，继续推进到 map、AMCL、scan、map topic 与 TF 的下游 blocker 可读、可复验。产品北极星仍是普通手机用户一键发车完成固定路线送垃圾；本 sprint 只证明路径生成前的诊断链更清楚，不证明路线执行、送达或硬件安全。

## 与上轮 06-54 对照

上一轮 `06-54` 的 canonical 结论是：`board_source_preflight_ready`、`lightweight_cli_ready=true`、`cli_ready=true`、`runtime_ready=true` 已成立，helper 已进入 lifecycle/topic probes，但下游仍只有 `map_lifecycle_preflight_map_server_and_amcl_inactive`、`amcl_lifecycle_not_active`、`/tf_topic_missing`、`/scan_no_publisher`、`/map_once_not_observed` 等较粗 blocker。

本轮 canonical live artifact `artifacts/live_o10_map_amcl_scan_tf_downstream_recovery.raw.json` 进一步收窄为：

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
- `downstream_recovery_summary.map.topic_sample.blocked_reason=/map_topic_missing`
- `downstream_recovery_summary.amcl.blocked_reason=amcl_lifecycle_not_active`
- `downstream_recovery_summary.tf.blocked_reason=/tf_topic_missing`

Product 判断：这不是重复 `/scan_no_publisher` 包装。首个 live artifact 暴露了 `publisher_count=1` 却被误标为 `/scan_no_publisher` 的分类 bug，Robot Software 修复分类器并重跑后，canonical 结论变成 publisher visible + BEST_EFFORT/RELIABLE sample timeout。

## 验收对照

| 验收项 | 结果 | Product 判断 |
| --- | --- | --- |
| Readiness 不回退 | `board_source_preflight_ready`、`lightweight_cli_ready=true`、`cli_ready=true`、`runtime_ready=true` 保持成立 | Accept |
| Map/AMCL lifecycle 分层 | `/map_server` 与 `/amcl` lifecycle command 都是 timeout，分别记录 `map_server_lifecycle_command_timeout` 与 `amcl_lifecycle_command_timeout` | Accept |
| Scan 分层 | `downstream_recovery_summary.scan.publisher_count=1`，blocked reason 为 `/scan_reliable_and_best_effort_timeout` | Accept |
| Map topic 分层 | 顶层受 `map_server_lifecycle_command_timeout` 阻塞，topic sample 为 `/map_topic_missing` | Accept |
| AMCL/TF 分层 | AMCL blocked at `amcl_lifecycle_not_active`，TF blocked at `/tf_topic_missing` | Accept |
| 验证证据 | `py_compile` RC `0`；targeted unittest `Ran 100 tests in 2.269s OK`；local dry-run RC `2` fail-closed；board scp/run/pull 成功；live run RC `2` 且产出 artifact；scoped `git diff --check` RC `0` | Accept |
| Mission 证据 | 未产生 `path_generation_attempted=true`、`path_generated=true`、route execution、delivery/operator acceptance、HIL 或 production evidence | Not mission progress |

## No-motion 安全验收

本轮 accepted artifact 保持 strict no-motion：

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

Product 验收结论：没有 NavigateToPose，没有 `/cmd_vel`，没有 `/api/base/manual`，没有 WAVE ROVER UART。

## OKR 和 KR 判断

- O5：仍为最低约 `85%`，但缺真实 external production evidence，本轮继续不消费 O5 support-only lane。
- O1/O6/O7：仍约 `93%`，`不调整` 百分比。
- O3/O1 no-motion：本轮 accepted as supporting diagnostic delta，只帮助下一轮继续逼近 same-run path generation 前置条件。
- KR 历史归档：`不归档`。本轮没有完成 KR，也没有更新历史区。

## 风险和下一步

剩余 blocker 的顺序必须保持：

1. 先由 `robot-software-engineer` 直接处理 `ros2 lifecycle get /map_server` 与 `ros2 lifecycle get /amcl` 的 command timeout。
2. lifecycle command timeout 收窄后，再复验 `/scan` publisher-visible sample timeout，区分 QoS/window、LiDAR runtime 发布节奏或 driver 状态。
3. 然后处理 `/map_topic_missing` 与 `/tf_topic_missing`。
4. 只有下一轮证据证明 `/scan_reliable_and_best_effort_timeout` 落到 LiDAR serial/runtime/接线事实时，才升级 `rober-hardware-engineer`，并必须先读 `docs/vendor/VENDOR_INDEX.md`。

本轮没有未处理的 Product acceptance blocker；剩余风险是 runtime/lifecycle/topic/TF 尚未恢复，仍不能进入 planner-only path gate。
