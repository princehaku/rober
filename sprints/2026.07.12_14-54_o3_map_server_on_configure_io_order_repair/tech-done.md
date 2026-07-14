# Tech Done - O3 Map Server On-Configure IO Order Repair

## Sprint Metadata

- sprint_type: epic
- Sprint: `sprints/2026.07.12_14-54_o3_map_server_on_configure_io_order_repair/`
- Owner: `robot-software-engineer`
- Run time: `2026-07-12 15:19:57 CST`
- Result: blocked with narrower strict no-motion root cause, not `/map_server` lifecycle clean/active

## 实际改动

- `onboard/scripts/o10_amcl_nav2_runtime_proof.py`
  - 新增 managed runtime log window 选择逻辑，优先消费包含 configure、ChangeState、yaml/image/map IO 的 pre-cleanup runtime log，避免 cleanup tail 让 `line_indices` 为空。
  - `map_server_transition_callback_probe` 新增 lifecycle manager request、map_server callback、AMCL configure、line index 和 ROS log timestamp 字段。
  - 新增并接入 `map_server_changestate_response_failure_after_image_load_before_map_read_completed` 分类：当 lifecycle manager 的 ChangeState failure 发生在 `/map_server` callback 已进入、`image_file` 已开始加载、`Read map` 尚未完成时作为 primary root cause。
  - 新增 `map_server_configure_completed_lifecycle_blocked_by_amcl_configure_failure` fallback 分类；若后续窗口越过 map_server map read 并在 AMCL configure 失败，不再回退成泛化 presence evidence。
- `onboard/tests/test_nav2_runtime_proof_helper.py`
  - 增加 pre-cleanup log 优先级、after-image-before-map-read 分类和 AMCL-after-map-server fallback 的回归测试。
  - 更新旧 configure ordering 测试期望，确保顶层 normalized root cause 与 transition summary 保持一致。
- `docs/navigation/field_route_evidence_preflight.md`
  - 同步 14:54 proof boundary、new classification 和 no-motion 读取规则。
- `docs/navigation/fixed_route_workflow.md`
  - 同步 fixed-route closeout 对新 transition classification 的消费规则。
- `sprints/2026.07.12_14-54_o3_map_server_on_configure_io_order_repair/artifacts/`
  - 生成/更新 `local_o10_map_server_on_configure_io_order_repair.raw.json`。
  - 生成/更新 `live_o10_map_server_on_configure_io_order_repair.raw.json`。

未改动 `OKR.md`、`docs/process/okr_progress_log.md`、O5/O6/O7 API/UI/archive 代码、WAVE ROVER/ESP32/UART/串口/波特率/接线/硬件配置。未修改 `onboard/scripts/o11_nav2_lifecycle.sh` 或 bringup launch。

## Artifact 结论

Local dry-run artifact：

- 文件：`sprints/2026.07.12_14-54_o3_map_server_on_configure_io_order_repair/artifacts/local_o10_map_server_on_configure_io_order_repair.raw.json`
- 返回码：`2`
- `status=blocked_with_root_cause`
- 主因：`canonical map proof/map_lifecycle_latest_missing` 与 `ROS install/source/board_source_preflight_source_failed`
- 解释：macOS 本机缺少 `/opt/ros/humble/setup.bash` 与 `/root/rober/onboard`，local artifact 只证明 helper fail-closed，不替代 true-board proof。

True-board final artifact：

- 文件：`sprints/2026.07.12_14-54_o3_map_server_on_configure_io_order_repair/artifacts/live_o10_map_server_on_configure_io_order_repair.raw.json`
- 返回码：`2`
- `status=blocked_with_root_cause`
- `proof.board_source_preflight.classification=board_source_preflight_ready`
- `proof.managed_runtime_started=true`
- `proof.map_server_active=false`
- `proof.amcl_active=false`
- `proof.root_causes[0].layer=Nav2 map_server transition callback`
- `proof.root_causes[0].reason=map_server_changestate_response_failure_after_image_load_before_map_read_completed`
- `proof.root_causes[0].detail=lifecycle_manager_changestate_response_failure_after_image_load_before_map_read_completed`
- `proof.map_server_transition_callback_probe.canonical_classification=map_server_changestate_response_failure_after_image_load_before_map_read_completed`
- `transition_sequence.configure.lifecycle_manager_configure_requested=true`
- `transition_sequence.configure.map_server_configure_callback_log_observed=true`
- `transition_sequence.configure.yaml_load_started=true`
- `transition_sequence.configure.image_load_started=true`
- `transition_sequence.configure.state_change_failed=true`
- `transition_sequence.configure.state_change_failed_after_image_load_before_map_read_completed=true`
- `transition_sequence.configure.map_read_completed=true`
- `transition_sequence.event_timestamps_s.image_load_started=1783840650.5605125`
- `transition_sequence.event_timestamps_s.state_change_failed=1783840650.660171`
- `transition_sequence.event_timestamps_s.map_read_completed=1783840651.0017402`
- `next_step=inspect_lifecycle_manager_change_state_future_timeout_vs_map_io_image_decode_completion`

本轮没有修到 `/map_server` lifecycle clean/active；但 primary root cause 已从 13:54 的 `map_server_configure_return_failure_before_deferred_map_read_completed` 继续收窄到 image load 已开始、map read 完成前的 ChangeState failure 窗口。

## No-Motion 安全边界

最终 local/live artifact 均保持：

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

本轮未发送 NavigateToPose，未发布 `/cmd_vel`，未调用 `/api/base/manual`，未打开 WAVE ROVER UART，未改硬件配置。

## 验证结果

```bash
python3 -m py_compile onboard/scripts/o10_amcl_nav2_runtime_proof.py
```

- 返回码：`0`
- 关键输出：无输出，编译通过。

```bash
python3 -m unittest onboard.tests.test_nav2_runtime_proof_helper
```

- 返回码：`0`
- 关键输出：`Ran 125 tests in 2.263s`，`OK`。

`onboard/scripts/o11_nav2_lifecycle.sh` 本轮未修改，因此未追加 `bash -n`；13:54 的 lifecycle script dirty 状态未由本轮扩大。

```bash
python3 onboard/scripts/o10_amcl_nav2_runtime_proof.py \
  --strict-no-motion \
  --no-base-uart \
  --timeout-s 18 \
  --managed-runtime-opt-in \
  --managed-map-yaml /root/rober/onboard/runtime/maps/trashbot_map.yaml \
  --output-json sprints/2026.07.12_14-54_o3_map_server_on_configure_io_order_repair/artifacts/local_o10_map_server_on_configure_io_order_repair.raw.json
```

- 返回码：`2`
- 关键输出：`status=blocked_with_root_cause`，`board_source_preflight_source_failed`。
- 失败定位：本机 macOS 无 ROS2 Humble board workspace，local artifact 只证明 fail-closed。

```bash
ssh -p 37878 root@192.168.1.11 \
  'mkdir -p /root/rober/onboard/scripts /tmp/rober_o10_artifacts'
```

- 返回码：`0`

```bash
scp -P 37878 onboard/scripts/o10_amcl_nav2_runtime_proof.py \
  root@192.168.1.11:/root/rober/onboard/scripts/o10_amcl_nav2_runtime_proof.py
```

- 返回码：`0`

```bash
ssh -p 37878 root@192.168.1.11 \
  'cd /root/rober/onboard && /usr/bin/timeout 420s /usr/bin/python3.10 scripts/o10_amcl_nav2_runtime_proof.py --strict-no-motion --no-base-uart --timeout-s 18 --managed-runtime-opt-in --managed-map-yaml /root/rober/onboard/runtime/maps/trashbot_map.yaml --output-json /tmp/rober_o10_artifacts/live_o10_map_server_on_configure_io_order_repair.raw.json'
```

- 返回码：`2`
- 关键输出：`status=blocked_with_root_cause`，`reason=map_server_changestate_response_failure_after_image_load_before_map_read_completed`。
- 失败定位：true-board ROS/source/rclpy ready，managed runtime 启动；`/map_server` configure callback 已进入，yaml/image load 已开始，lifecycle manager 在 `Read map` 完成前记录 ChangeState failure。当前不是 DDS SHM port-lock、不是 callback 未进入、不是 map yaml/PGM 缺失。

```bash
scp -P 37878 root@192.168.1.11:/tmp/rober_o10_artifacts/live_o10_map_server_on_configure_io_order_repair.raw.json \
  sprints/2026.07.12_14-54_o3_map_server_on_configure_io_order_repair/artifacts/live_o10_map_server_on_configure_io_order_repair.raw.json
```

- 返回码：`0`

```bash
git diff --check -- \
  onboard/scripts/o10_amcl_nav2_runtime_proof.py \
  onboard/scripts/o11_nav2_lifecycle.sh \
  onboard/src/ros2_trashbot_bringup \
  onboard/tests/test_nav2_runtime_proof_helper.py \
  docs/navigation/field_route_evidence_preflight.md \
  docs/navigation/fixed_route_workflow.md \
  sprints/2026.07.12_14-54_o3_map_server_on_configure_io_order_repair
```

- 返回码：`0`
- 关键输出：无输出，scoped diff whitespace check 通过。

## 失败定位

最终 primary blocker：

- `map_server_changestate_response_failure_after_image_load_before_map_read_completed`

解释：

- lifecycle manager 已发起 `/map_server` configure。
- `/map_server` callback 已进入。
- map yaml 已加载，image file 已开始加载。
- lifecycle manager 在 `image_load_started` 后、`map_read_completed` 前记录 `Failed to change state for node: map_server`。
- 因此本轮不再只是 13:54 的 “before deferred map read completed”，而是压到 image decode/map IO completion 与 ChangeState future response 的 ordering 窗口。

本轮中间复验还观察到一次变体：map read 完成后 lifecycle manager 进入 `Configuring amcl` 并在 AMCL configure 失败。helper 已新增 `map_server_configure_completed_lifecycle_blocked_by_amcl_configure_failure` 分类；如果后续稳定复现该变体，说明 map_server configure blocker 已移动到 AMCL lifecycle，但仍不等于 `/map_server active`。

## 剩余风险

- `/map_server` 仍未 lifecycle clean/active，本轮是 strict no-motion root cause narrowing，不是修复完成。
- 尚未证明 `/map` sample、AMCL pose、dynamic `map->odom`、planner-only path generation、route execution、delivery、HIL 或 production external evidence。
- ROS graph/daemon 仍有慢查询和 timeout 背景，live artifact 中 `ros2 daemon status`、`ros2 --help`、部分 graph batch 仍可超时；本轮 primary root cause 由 runtime log window 而不是这些 graph timeout 决定。
- LiDAR `/dev/ttyACM0` 仍出现 `SerialException` 背景噪声；本轮没有触碰硬件串口配置，也没有把该噪声当 primary root cause。
- 下一步建议检查 Nav2 lifecycle manager ChangeState future timeout/response handling、`nav2_map_server` image decode/map IO completion timing，以及是否需要把 map_server-only lifecycle proof 与 AMCL configure proof 分离。

## 协同判断

- Product / OKR Owner：需要验收本轮是否接受为 O3/O1 strict no-motion blocker 下钻；不建议调整 OKR 百分比。
- Hardware：暂不需要。本轮没有触碰 WAVE ROVER、ESP32、UART、串口、波特率或接线；LiDAR 串口异常若后续成为 primary root cause 再转 Hardware 并读取 vendor 资料。
- Autonomy：暂不需要；等 `/map_server` lifecycle clean/active 后再恢复 `/map`、AMCL、dynamic `map->odom` 和 planner-only path gate。
- Full-Stack：不需要；未改 API/UI/触点合同。
