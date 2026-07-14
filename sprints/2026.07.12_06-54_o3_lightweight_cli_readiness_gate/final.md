# Final - O3 Lightweight CLI Readiness Gate

## Sprint Metadata

- sprint_type: epic
- Sprint: `sprints/2026.07.12_06-54_o3_lightweight_cli_readiness_gate/`
- Product owner: `product-okr-owner`
- Implementation owner: `robot-software-engineer`
- Closeout time: `2026-07-12 07:36 CST`
- Proof boundary: `software_proof_o3_o1_strict_no_motion_runtime_diagnostic_only`
- Outcome: accepted as lightweight CLI readiness delta; mission gates remain blocked.

## 用户价值和产品北极星

用户价值是把 true-board helper 从“`ros2 --help` 冷启动超时就卡死 preflight”推进到“lightweight CLI readiness 已经放行，helper 能真实进入 downstream lifecycle/topic probes”。产品北极星仍是普通手机用户一键发车完成固定路线送垃圾；本轮不是路线闭环，只是把 no-motion runtime 主路径重新推回 map/AMCL/TF/path gate 之前。

## OKR 映射和方向判断

- O5：保持约 `85%`，`不调整`。本轮没有真实 production cloud、HTTPS/TLS、4G/SIM、production DB/queue、worker cutover、OSS/CDN live traffic、真实手机/browser 或 external production evidence。
- O1：保持约 `93%`，`不调整`。本轮没有 current same-run path generation success、Nav2 route execution success、current live HIL、safe-to-control、底盘反馈增量或真实控制执行。
- O6/O7：保持约 `93%`，`不调整`。本轮没有新的 same-task route execution、delivery record、operator acceptance、production readback 或可消费 mission material。
- 方向判断：`继续` O3/O1 strict no-motion runtime recovery；`暂停` O5 support-only lane；`不归档` KR。

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

本轮核心抓手是把 helper 的 CLI readiness 从单一 heavy help gate 改成 heavy/light/`rclpy` 三层，并让 `ros2 node list` 这种 true-board 已证明可返回的 lightweight readiness 成为主放行信号。

Robot Software 实际改动由 `tech-done.md` 记录，Product 收口确认只涉及 helper、tests、navigation docs 和本 sprint artifacts。关键事实如下：

1. helper 新增 heavy/light/`rclpy` 三层 readiness，`ros2 --help >/dev/null` 保留为诊断项，不再单独阻塞 `cli_ready`。
2. Targeted unittest 通过：`Ran 97 tests in 2.260s OK`。
3. Local dry-run RC `2`，按预期 fail-closed，`classification=board_source_preflight_source_failed`，符合 macOS 无 `/opt/ros/humble/setup.bash` 边界。
4. True-board push RC `0`；240s strict no-motion run RC `124`，但 artifact 已写出并拉回；330s strict no-motion run RC `2`，artifact 已写出并拉回。
5. 240s artifact 已证明 `classification=board_source_preflight_ready`、`lightweight_readiness.primary_label=ros2_node_list`、`cli_ready=true`、`runtime_ready=true`，且 `recent_commands` 已进入 lifecycle/topic probes。
6. 330s artifact 明确 `classification=board_source_preflight_ready`、`source_stage_ok=true`、`ros2_cli_path_ok=true`、`rclpy_import_ok=true`、`lightweight_cli_ready=true`、`cli_ready=true`、`runtime_ready=true`。
7. New canonical blocker 已前移到 `map_lifecycle_preflight_map_server_and_amcl_inactive`、`amcl_lifecycle_not_active`、`/tf_topic_missing`，并伴随 `/scan_no_publisher`、`/map_once_not_observed` 类 downstream no-motion blocker。

Product closeout 实际改动：

- `sprints/2026.07.12_06-54_o3_lightweight_cli_readiness_gate/side2side_check.md`
- `sprints/2026.07.12_06-54_o3_lightweight_cli_readiness_gate/final.md`
- `OKR.md`
- `docs/process/okr_progress_log.md`

## 验证结果

Robot Software 验证事实：

- `python3 -m py_compile onboard/scripts/o10_amcl_nav2_runtime_proof.py` RC `0`。
- `python3 -m unittest onboard.tests.test_nav2_runtime_proof_helper` RC `0`，输出 `Ran 97 tests in 2.260s OK`。
- Local fail-closed helper dry-run RC `2`，artifact written。
- True-board helper push RC `0`。
- 240s strict no-motion helper run RC `124`，artifact written and pulled。
- 330s strict no-motion helper run RC `2`，artifact written and pulled。
- Scoped `git diff --check` RC `0`。

Product closeout 验收命令：

```bash
rg -n "06-54|lightweight_cli_readiness|board_source_preflight_ready|lightweight_cli_ready=true|cli_ready=true|runtime_ready=true|ros2_node_list|map_lifecycle_preflight_map_server_and_amcl_inactive|/tf_topic_missing|/scan_no_publisher|Ran 97|path_generation_attempted=false|path_generated=false|safe_to_control=false|不调整|不归档" OKR.md docs/process/okr_progress_log.md sprints/2026.07.12_06-54_o3_lightweight_cli_readiness_gate
```

```bash
git diff --check -- OKR.md docs/process/okr_progress_log.md sprints/2026.07.12_06-54_o3_lightweight_cli_readiness_gate
```

## Live Artifact 结论

Artifacts:

- `sprints/2026.07.12_06-54_o3_lightweight_cli_readiness_gate/artifacts/live_o10_lightweight_cli_readiness.raw.json`
- `sprints/2026.07.12_06-54_o3_lightweight_cli_readiness_gate/artifacts/live_o10_lightweight_cli_readiness_330s.raw.json`

关键字段：

- `status=interrupted_before_final_artifact`（240s）
- `status=blocked_with_root_cause`（330s）
- `board_source_preflight.classification=board_source_preflight_ready`
- `source_stage_ok=true`
- `ros2_cli_path_ok=true`
- `rclpy_import_ok=true`
- `lightweight_cli_ready=true`
- `lightweight_readiness.primary_label=ros2_node_list`
- `lightweight_readiness.successful_labels=["ros2_node_list"]`
- `lightweight_readiness.timed_out_labels=["ros2_daemon_status"]`
- `ros2_cli_invocation_ok=false`
- `cli_ready=true`
- `runtime_ready=true`
- `map_lifecycle_preflight.classification=map_lifecycle_preflight_map_server_and_amcl_inactive`
- `amcl_readiness_summary.blocked_reason=amcl_lifecycle_not_active`
- `tf_readiness_summary.blocked_reason=/tf_topic_missing`

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

- Accepted：helper 已不再停在 `board_source_preflight_ros2_cli_invocation_timeout`；true-board canonical artifact 证明 `board_source_preflight_ready`、`lightweight_cli_ready=true`、`cli_ready=true`、`runtime_ready=true`。
- Accepted：240s artifact 虽被外层 timeout 打断，但已经证明 helper 实际进入 lifecycle/topic probes，因此本轮不是“timeout 换皮”。
- Accepted：新的 primary blocker 已前移到 `map_server/amcl inactive`、`/scan_no_publisher`、`/map_once_not_observed`、`/tf_topic_missing`。
- Not accepted：没有 same-run path generation success、route execution、delivery/operator acceptance、current live HIL、safe-to-control 或 production external evidence。

Product 判断以 `330s` final artifact 为 canonical closeout，以 `240s` artifact 证明 helper 已进入 downstream probes；不会把 `ros2 daemon status` 的 timeout 重新升级成 primary blocker，因为它在本轮已降为 lightweight 诊断项。

## Blocker 重复消费判断

本轮不按与 `05-52` 同一 blocker 重复消费处理。

理由：

1. `05-52` 的 primary blocker 仍是 `board_source_preflight_ros2_cli_invocation_timeout`，helper 还未放行 `cli_ready`。
2. `06-54` 已让 `board_source_preflight_ready`、`lightweight_cli_ready=true`、`cli_ready=true`、`runtime_ready=true` 成立。
3. 当前 blocker 已明确下沉到 `map_lifecycle_preflight_map_server_and_amcl_inactive`、`amcl_lifecycle_not_active`、`/tf_topic_missing` 与 `/scan_no_publisher` 类 downstream no-motion runtime facts。

下一轮不能回到 O5 support-only、source/path mismatch 或 `ros2 --help` 单点 gate。应由 `robot-software-engineer` 直接继续 map lifecycle、AMCL、TF 和 `/scan` runtime blocker；如果涉及 LiDAR publisher/runtime/串口事实，再交 `rober-hardware-engineer` 读取 `docs/vendor/VENDOR_INDEX.md` 补硬件事实。

## 剩余风险

- `ros2 daemon status` 仍在 `3.0s` 预算内 timeout，后续可能还要继续区分 daemon slow path 与 graph/runtime slow path，但它已不是本轮 primary blocker。
- 240s 验收命令不足以自然收口完整 helper closeout；当前 canonical closeout 依赖补充的 330s strict no-motion artifact。
- downstream 仍没有 `map_server_active=true`、`amcl_active=true`、`amcl_pose_observed=true`、dynamic `map->odom=true`、`path_generation_attempted=true` 或 `path_generated=true`。
- 本轮仍是 O3/O1 supporting no-motion diagnostic delta，不是 path generation、route execution、delivery/operator acceptance、HIL 或 production evidence。

## 下一轮建议

优先级 P0：继续 O3/O1 strict no-motion lane，由 `robot-software-engineer` 直接打 `map_server/amcl inactive`、`/scan_no_publisher`、`/map_once_not_observed`、`/tf_topic_missing`，不要回到 O5 support-only、source/path mismatch 或 `ros2 --help` gate。

优先级 P1：若 `/scan_no_publisher` 需要核对 LiDAR runtime、串口、进程状态或板级接线事实，再交 `rober-hardware-engineer` 读取 `docs/vendor/VENDOR_INDEX.md` 与 vendor 本地资料后补硬件边界。当前仍禁止 NavigateToPose、`/cmd_vel`、`/api/base/manual` 和 WAVE ROVER UART。
