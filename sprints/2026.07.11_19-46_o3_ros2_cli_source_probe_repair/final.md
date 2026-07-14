# O3 ROS2 CLI Source Probe Repair Final

## Sprint Metadata

- sprint_type: epic
- Sprint: `sprints/2026.07.11_19-46_o3_ros2_cli_source_probe_repair/`
- Product owner: `product-okr-owner`
- Implementation owner: `robot-algorithm-engineer`
- Closeout date: 2026-07-11
- Outcome: source/CLI blocker repaired; downstream AMCL/TF/graph finalization still blocked

## 用户价值和产品北极星

本轮价值是把真实板 no-motion path generation 链路从旧的 `ros2_cli_ok=false` / sourced shell blocker 推进到可继续诊断的下一层。普通用户价值仍落在固定路线送垃圾闭环，但本 sprint 只证明 ROS2 source/CLI/rclpy 前置条件已经 ready，不证明路线执行、送达、HIL 或生产云。

## OKR 映射和方向判断

- O5：保持约 `85%`。本轮没有真实公网 HTTPS/TLS、4G/SIM、production DB/queue、OSS/CDN live traffic 或真实手机/browser 证据。
- O1：保持约 `93%`。本轮是 O3/O1 supporting no-motion source/CLI repair，不是 current same-run path generation success、Nav2 route execution success 或 current live HIL pass。
- O6/O7：保持约 `93%`。本轮没有新的同轮 route execution、delivery record、operator confirmation 或 production readback material 可消费。
- 方向判断：`继续` O3/O1 no-motion localization/path readiness；`暂停` O5 support-only 包装；`不调整` 百分比；`不归档` KR。

## 本轮核心抓手

Algorithm owner 已把 `board_source_preflight` 拆成 source stage、PATH/which、CLI invocation 和 Python/rclpy 四层，并通过 local/unit/live artifact 验证旧 blocker 已移动。Product closeout 只接受该层的 repair，不把 partial runtime material 解释为 path、route、delivery 或 HIL 成功。

## 实际改动

Algorithm owner 已完成并记录在 `tech-done.md`：

- `onboard/scripts/o10_amcl_nav2_runtime_proof.py`
- `onboard/tests/test_nav2_runtime_proof_helper.py`
- `docs/navigation/field_route_evidence_preflight.md`
- `docs/navigation/fixed_route_workflow.md`
- `sprints/2026.07.11_19-46_o3_ros2_cli_source_probe_repair/tech-done.md`
- `sprints/2026.07.11_19-46_o3_ros2_cli_source_probe_repair/artifacts/local_o10_ros2_cli_source_probe_repair.raw.json`
- `sprints/2026.07.11_19-46_o3_ros2_cli_source_probe_repair/artifacts/live_o10_ros2_cli_source_probe_repair.raw.json`

Product closeout 本轮新增或同步：

- `sprints/2026.07.11_19-46_o3_ros2_cli_source_probe_repair/side2side_check.md`
- `sprints/2026.07.11_19-46_o3_ros2_cli_source_probe_repair/final.md`
- `OKR.md`
- `docs/process/okr_progress_log.md`

## 验证结果

Algorithm 验证事实：

- `python3 -m py_compile onboard/scripts/o10_amcl_nav2_runtime_proof.py` exit `0`
- `python3 -m unittest onboard.tests.test_nav2_runtime_proof_helper` exit `0`，`Ran 65 tests in 2.221s OK`
- local helper exit `2`，按预期 fail-closed
- `scp` exit `0`
- live helper exit `255` / interrupted，但 partial artifact 已 pull，pull exit `0`
- scoped `git diff --check` exit `0`

Product closeout 额外执行并记录在最终回复：

- `rg -n "19-46|board_source_preflight_ready|ros2_cli_ok=true|rclpy_import_ok=true|path_generated=false|route_execution_success=false|不调整|不归档" OKR.md docs/process/okr_progress_log.md sprints/2026.07.11_19-46_o3_ros2_cli_source_probe_repair`
- `git diff --check -- OKR.md docs/process/okr_progress_log.md sprints/2026.07.11_19-46_o3_ros2_cli_source_probe_repair`

## Live Artifact 结论

主节点 read-only acceptance 已确认 `artifacts/live_o10_ros2_cli_source_probe_repair.raw.json`：

- `status=interrupted_before_final_artifact`
- `evidence_type=partial_runtime_material`
- `last_successful_phase=graph_discovery`
- `proof.board_source_preflight.classification=board_source_preflight_ready`
- `ros2_cli_ok=true`
- `rclpy_import_ok=true`
- `source_stage_ok=true`
- ROS setup 与 workspace setup 均存在并已 sourced
- `source_stage.elapsed_ms=2979`
- `command -v ros2` 输出 `/opt/ros/humble/bin/ros2`，耗时 `15ms`
- `type -a ros2` 正常，耗时 `14ms`
- `which ros2` 输出 `/opt/ros/humble/bin/ros2`，耗时 `16ms`
- `ros2 --help >/dev/null` 正常，耗时 `2604ms`
- `rclpy_file=/opt/ros/humble/local/lib/python3.10/dist-packages/rclpy/__init__.py`

下游仍 blocked：

- `/amcl_pose_once_not_observed`
- `map_to_odom_not_observed`
- `map_to_base_link_blocked_by_missing_map_to_odom`
- `sigterm_before_final_artifact`
- `path_generation_requested=true`
- `path_generation_attempted=false`
- `path_generated=false`

安全字段仍为 false：

- `safe_to_control=false`
- `publishes_cmd_vel=false`
- `calls_base_manual=false`
- `robot_control_executed=false`
- `route_execution_success=false`
- `delivery_success=false`
- `hil_pass=false`
- `uses_base_uart=false`

## KR 拆解、更新或历史归档

本轮不归档任何 KR。原因是已经完成的是 blocker repair，不是 KR 终态证据：

- 没有 current same-run `path_generated=true`
- 没有 Nav2 route execution success
- 没有 delivery record 或 operator acceptance
- 没有 current live HIL pass
- 没有 production cloud external evidence

当前推进区继续保留 O1 path generation / route execution / HIL 缺口、O5 production external evidence 缺口、O6/O7 current live route/delivery/operator/production material 缺口。

## Blocker 第三轮判断

本 sprint 不触发同一 blocker 第三轮升级。理由：前两轮的旧 blocker 是 `ros2_command_unavailable_after_bash_source` / `board_source_preflight_ros2_cli_unavailable`；本轮 live artifact 已把它推进到 `board_source_preflight_ready`，并确认 `ros2_cli_ok=true`、`rclpy_import_ok=true`。新的 blocker 已转移到 AMCL/TF/graph finalization，因此下一轮应继续 downstream 分层，而不是继续消费旧 ROS2 CLI/source blocker。

## 剩余风险和下一轮建议

- 先把 helper final artifact 有界收口做稳，避免 `sigterm_before_final_artifact` 继续遮住 downstream root cause。
- 分层处理 `/amcl` lifecycle timeout、`/amcl_pose_once_not_observed`、`map_to_odom_not_observed` 和 `map_to_base_link_blocked_by_missing_map_to_odom`。
- 继续保持 no-motion：不发布 `/cmd_vel`，不调用 `/api/base/manual`，不发送 NavigateToPose，不打开 WAVE ROVER UART。
- 只有出现 same-run path、route execution、delivery/operator acceptance、current live HIL 或 production external evidence 后，才允许 O6/O7 消费链或 OKR 百分比变化。
