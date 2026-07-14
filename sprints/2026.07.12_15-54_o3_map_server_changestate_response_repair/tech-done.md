# Tech Done - O3 Map Server ChangeState Response Repair

## Sprint Metadata

- sprint_type: epic
- Sprint: `sprints/2026.07.12_15-54_o3_map_server_changestate_response_repair/`
- Owner: `robot-software-engineer`
- Run time: `2026-07-12 16:12 CST`
- Result: `blocked_with_root_cause`
- Proof boundary: `software_proof_o3_o1_strict_no_motion_map_server_transition_callback_probe_only`

## 实际改动

- `onboard/scripts/o10_amcl_nav2_runtime_proof.py`
  - 新增 `map_server_changestate_response_false_before_map_io_completion` 分类，用于区分 lifecycle manager 已收到 ChangeState failure，但 `map_io` 仍在完成读取的情况。
  - 新增 map IO 与 ChangeState failure 的相对时间字段，记录 `configure_to_state_failure_ms`、`image_load_to_state_failure_ms`、`state_failure_to_map_read_completed_ms` 等证据。
  - 收窄 `state_change_failed_before_map_server_configure_callback`，避免在已有 `[map_server]: Configuring`、YAML、image 或 map read 证据时误判为 callback 未进入。
  - 修正 configure sequence 中 `map_server_callback_entered` 的来源，使其只由真正的 map_server configure callback log 触发。
- `onboard/tests/test_nav2_runtime_proof_helper.py`
  - 更新 map_server lifecycle failure 断言，要求新分类和新 timing 字段稳定输出。
  - 新增 response false before map IO completion 的单元测试。
  - 新增 callback log missing 场景测试，防止缺少 callback log 时被误归入 map IO completion 分类。
- `docs/navigation/field_route_evidence_preflight.md`
  - 记录新 artifact 分类、timing 字段读取方式和 strict no-motion 边界。
- `docs/navigation/fixed_route_workflow.md`
  - 同步 consumer workflow，明确该分类不解锁 `/map`、AMCL、TF、planner path、NavigateToPose 或 route execution。
- `sprints/2026.07.12_15-54_o3_map_server_changestate_response_repair/artifacts/`
  - 生成 local dry-run artifact、true-board final artifact 和一次 delay8 诊断 artifact。

未改动 `OKR.md`、`docs/process/okr_progress_log.md`、O5/O6/O7 代码、WAVE ROVER、ESP32、UART、串口、波特率、接线或硬件配置。本轮未修改 bringup package，因此没有 board 侧 bringup sync/build。

## Artifact 字段

Local strict no-motion dry-run artifact：

- Path: `sprints/2026.07.12_15-54_o3_map_server_changestate_response_repair/artifacts/local_o10_map_server_changestate_response_repair.raw.json`
- Command return code: `2`
- `status=blocked_with_root_cause`
- `proof.board_source_preflight.classification=board_source_preflight_source_failed`
- `proof.managed_runtime_started=false`
- `proof.root_causes[0].reason=map_lifecycle_latest_missing`
- `proof.root_causes[1].reason=board_source_preflight_source_failed`
- 定位：macOS 本地没有目标板 `/root/rober/onboard` 和 ROS2 source 环境，符合 fail-closed 预期。

True-board strict no-motion final artifact：

- Path: `sprints/2026.07.12_15-54_o3_map_server_changestate_response_repair/artifacts/live_o10_map_server_changestate_response_repair.raw.json`
- Command return code: `2`
- `status=blocked_with_root_cause`
- `proof.artifact_closeout.primary_root_cause.reason=map_server_changestate_response_false_before_map_io_completion`
- `proof.artifact_closeout.primary_root_cause.detail=lifecycle_manager_changestate_response_false_while_map_io_completed_later`
- `proof.root_causes[0].layer=Nav2 map_server transition callback`
- `proof.root_causes[0].reason=map_server_changestate_response_false_before_map_io_completion`
- `proof.board_source_preflight.classification=board_source_preflight_ready`
- `proof.managed_runtime_started=true`
- `proof.map_server_active=false`
- `proof.amcl_active=false`
- `proof.map_server_transition_callback_probe.canonical_classification=map_server_changestate_response_false_before_map_io_completion`
- `proof.map_server_transition_callback_probe.service_rpc_timing.changestate_response_false_before_map_io_completion=true`
- `proof.map_server_transition_callback_probe.service_rpc_timing.inferred_change_state_response=failure`
- `proof.map_server_transition_callback_probe.service_rpc_timing.service_timeout_or_rpc_error_observed_in_log=false`
- `proof.map_server_transition_callback_probe.service_rpc_timing.service_timeout_s=12.0`
- `map_io_timing.change_state_response_false_while_map_io_incomplete=true`
- `map_io_timing.configure_to_state_failure_ms=46.149`
- `map_io_timing.image_load_to_state_failure_ms=43.624`
- `map_io_timing.yaml_load_to_state_failure_ms=45.897`
- `map_io_timing.state_failure_to_map_read_completed_ms=93.266`
- `map_io_timing.configure_to_map_read_completed_ms=139.415`
- `map_io_timing.map_read_completed_after_state_failure=true`
- `map_io_timing.state_failure_after_image_before_map_read=true`
- `transition_sequence.configure.lifecycle_manager_configure_requested=true`
- `transition_sequence.configure.map_server_callback_entered=true`
- `transition_sequence.configure.map_server_configure_callback_log_observed=true`
- `transition_sequence.configure.yaml_load_started=true`
- `transition_sequence.configure.image_load_started=true`
- `transition_sequence.configure.state_change_failed=true`
- `transition_sequence.configure.map_read_completed=true`
- `transition_sequence.configure.state_change_failed_before_map_server_configure_callback=false`

关键 runtime log ordering：

```text
[INFO] [1783843791.518132581] [lifecycle_manager]: Configuring map_server
[INFO] [1783843791.525153282] [map_server]: Configuring
[INFO] [1783843791.525405115] [map_io]: Loading yaml file: /root/rober/onboard/runtime/maps/trashbot_map.yaml
[INFO] [1783843791.527678321] [map_io]: Loading image_file: /root/rober/onboard/runtime/maps/trashbot_map.pgm
[ERROR] [1783843791.571302068] [lifecycle_manager]: Failed to change state for node: map_server
[INFO] [1783843791.664568556] [map_io]: Read map /root/rober/onboard/runtime/maps/trashbot_map.pgm: 261 X 113 map @ 0.05 m/cell
```

Delay8 diagnostic artifact：

- Path: `sprints/2026.07.12_15-54_o3_map_server_changestate_response_repair/artifacts/live_o10_delay8_probe.raw.json`
- Command return code: `2`
- Purpose: 诊断 `--managed-lifecycle-start-delay-s 8` 是否能绕过当前失败。
- Result: 未修复 lifecycle，且分类退回更宽的 before-deferred/configure failure，因此没有作为最终验收 artifact。

## No-Motion 安全边界

True-board final artifact 保持 strict no-motion：

- `path_generation_attempted=false`
- `path_generated=false`
- `safe_to_control=false`
- `publishes_cmd_vel=false`
- `calls_base_manual=false`
- `sends_navigate_to_pose=false`
- `uses_base_uart=false`
- `robot_control_executed=false`
- `route_execution_success=false`
- `delivery_success=false`
- `hil_pass=false`

本轮没有发布 `/cmd_vel`，没有调用 `/api/base/manual`，没有发送 NavigateToPose，没有打开 WAVE ROVER UART，也没有修改硬件配置。

## 验证结果

```bash
python3 -m py_compile onboard/scripts/o10_amcl_nav2_runtime_proof.py
```

- Return code: `0`
- Output: no output

```bash
python3 -m unittest onboard.tests.test_nav2_runtime_proof_helper
```

- Return code: `0`
- Key output: `Ran 127 tests in 2.283s` / `OK`

```bash
bash -n onboard/scripts/o11_nav2_lifecycle.sh
```

- Return code: `0`
- Output: no output
- Note: `o11_nav2_lifecycle.sh` was not changed in this sprint, but it is in the allowed scope and had existing worktree changes, so syntax was rechecked.

```bash
python3 onboard/scripts/o10_amcl_nav2_runtime_proof.py \
  --strict-no-motion \
  --no-base-uart \
  --timeout-s 18 \
  --managed-runtime-opt-in \
  --managed-map-yaml /root/rober/onboard/runtime/maps/trashbot_map.yaml \
  --output-json sprints/2026.07.12_15-54_o3_map_server_changestate_response_repair/artifacts/local_o10_map_server_changestate_response_repair.raw.json
```

- Return code: `2`
- Key output/artifact: local fail-closed on `board_source_preflight_source_failed` and `map_lifecycle_latest_missing`.
- Failure定位：本地 macOS 不具备 target board ROS2 runtime/source path；未作为 hardware 或 Nav2 root cause。

```bash
ssh -p 37878 root@192.168.1.11 \
  'mkdir -p /root/rober/onboard/scripts /tmp/rober_o10_artifacts'
```

- Return code: `0`

```bash
scp -P 37878 onboard/scripts/o10_amcl_nav2_runtime_proof.py \
  root@192.168.1.11:/root/rober/onboard/scripts/o10_amcl_nav2_runtime_proof.py
```

- Return code: `0`

```bash
scp -P 37878 onboard/scripts/o11_nav2_lifecycle.sh \
  root@192.168.1.11:/root/rober/onboard/scripts/o11_nav2_lifecycle.sh
```

- Return code: `0`
- Note: synchronized because the file had existing worktree changes and was part of the allowed validation scope; this sprint did not edit it.

```bash
ssh -p 37878 root@192.168.1.11 \
  'cd /root/rober/onboard && /usr/bin/timeout 420s /usr/bin/python3.10 scripts/o10_amcl_nav2_runtime_proof.py --strict-no-motion --no-base-uart --timeout-s 18 --managed-runtime-opt-in --managed-map-yaml /root/rober/onboard/runtime/maps/trashbot_map.yaml --output-json /tmp/rober_o10_artifacts/live_o10_map_server_changestate_response_repair.raw.json'
```

- Return code: `2`
- Key output/artifact: `blocked_with_root_cause`, narrowed to `map_server_changestate_response_false_before_map_io_completion`.

```bash
scp -P 37878 root@192.168.1.11:/tmp/rober_o10_artifacts/live_o10_map_server_changestate_response_repair.raw.json \
  sprints/2026.07.12_15-54_o3_map_server_changestate_response_repair/artifacts/live_o10_map_server_changestate_response_repair.raw.json
```

- Return code: `0`

Scoped `git diff --check` is recorded after this file is written.

```bash
git diff --check -- \
  onboard/scripts/o10_amcl_nav2_runtime_proof.py \
  onboard/scripts/o11_nav2_lifecycle.sh \
  onboard/src/ros2_trashbot_bringup \
  onboard/tests/test_nav2_runtime_proof_helper.py \
  docs/navigation/field_route_evidence_preflight.md \
  docs/navigation/fixed_route_workflow.md \
  sprints/2026.07.12_15-54_o3_map_server_changestate_response_repair
```

- Return code: `0`
- Output: no output

## 失败定位

本轮没有修复到 `/map_server active`。更窄 root cause 是：

`map_server_changestate_response_false_before_map_io_completion`

具体解释：

- lifecycle manager 在 `1783843791.518132581` 请求 configure `map_server`。
- `/map_server` configure callback 在 `1783843791.525153282` 已进入。
- YAML load 在 `1783843791.525405115` 开始，image load 在 `1783843791.527678321` 开始。
- lifecycle manager 在 `1783843791.571302068` 收到 ChangeState failure。
- `map_io` 在 `1783843791.664568556` 才输出 map read completed。
- 因此 failure 不是发生在 callback 未进入前，也不是 service timeout；它是 ChangeState response false 出现在 map IO 尚未完成的窗口内，而 map read 后续仍完成。

下一步应检查 Nav2 `map_server` `on_configure` return false path、map IO 异步/日志 ordering、executor service response 时序，或 lifecycle manager 对同一 callback 的 response 判断路径。若后续 evidence 显示 LiDAR serial/runtime/接线成为 primary root cause，需停止软件推断并交给 Hardware 读取 `docs/vendor/VENDOR_INDEX.md`。

## 剩余风险

- `/map_server active=false`，`/map`、AMCL、dynamic `map->odom`、planner path、route execution、delivery 和 HIL 都没有解锁。
- 本轮 artifact 仍是 strict no-motion software proof，不是 production、HIL、路线执行或交付成功证据。
- runtime log 里仍有 LiDAR `SerialException` 背景噪声；本轮 primary root cause 不依赖它，不做硬件结论。
- 当前 worktree 有大量历史未提交改动；本轮只在允许范围内做最小增量，没有回滚或清理无关文件。

## 协同判断

- Product / OKR Owner: 需要确认本轮是 root cause narrowing，不应调整 OKR 百分比。
- Hardware: 暂不需要；只有 LiDAR serial/runtime/接线成为 primary root cause 时才接手。
- Autonomy: 暂不需要；等待 `/map_server` lifecycle clean/active 后再恢复 `/map`、AMCL、TF、planner-only path。
- Full-Stack: 不需要。
