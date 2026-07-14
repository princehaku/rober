# Tech Done - O3 Map Server On-Configure Return Source Repair

## Sprint Metadata

- sprint_type: epic
- Sprint: `sprints/2026.07.12_16-55_o3_map_server_on_configure_return_source_repair/`
- Owner: `robot-software-engineer`
- Run time: `2026-07-12 17:11 CST`
- Result: `blocked_with_root_cause`
- Proof boundary: `software_proof_o3_o1_strict_no_motion_map_server_on_configure_return_source_repair_only`

## 实际改动

- `onboard/scripts/o10_amcl_nav2_runtime_proof.py`
  - 新增 `map_server_on_configure_return_false_after_valid_map_io_deferred_completion` 分类。
  - 新增 `proof.map_server_transition_callback_probe.on_configure_return_source`，把 15:54 的 ChangeState false timing 继续收窄到 `on_configure_return_false_source`。
  - 新字段会同时记录 map YAML/PGM readback、排除参数/地图文件无效、map_server-scoped exception、service/RPC timeout、DDS SHM transport error，以及 ChangeState false 与 map IO completion 的相对 timing。
  - 修正 source summary：LiDAR traceback 只能留在 runtime 背景噪声里，不能被误判成 map_server exception。
  - 顶层 root cause normalization 也同步升级到新分类，避免 Product closeout 只看到旧 `map_server_changestate_response_false_before_map_io_completion`。
- `onboard/tests/test_nav2_runtime_proof_helper.py`
  - 更新 valid map readback 场景断言，要求输出新 classification、`on_configure_return_source.primary_source` 和排除参数/地图文件无效的字段。
  - 保留 raw log-only 路径的旧 timing 分类，避免未证明 map readback valid 时过度收窄。
- `docs/navigation/field_route_evidence_preflight.md`
  - 记录 16:55 新 artifact 字段、读取方式和 strict no-motion 边界。
- `docs/navigation/fixed_route_workflow.md`
  - 同步 fixed-route 消费规则：新分类仍不能解锁 `/map`、AMCL、TF、planner path、NavigateToPose、route execution、HIL 或 delivery。
- `sprints/2026.07.12_16-55_o3_map_server_on_configure_return_source_repair/artifacts/`
  - 新增 local fail-closed artifact。
  - 新增 true-board strict no-motion artifact。

未修改 `OKR.md`、`docs/process/okr_progress_log.md`、`side2side_check.md`、`final.md`、launch、硬件配置、WAVE ROVER、ESP32、UART、串口、波特率、UI/API 或 O5/O6/O7 文件。

## Artifact 字段

Local strict no-motion artifact：

- Path: `sprints/2026.07.12_16-55_o3_map_server_on_configure_return_source_repair/artifacts/local_o10_map_server_on_configure_return_source_repair.raw.json`
- Command return code: `2`
- `status=blocked_with_root_cause`
- `proof.artifact_closeout.primary_root_cause.reason=map_lifecycle_latest_missing`
- `proof.blockers[1].reason=board_source_preflight_source_failed`
- 定位：macOS 本地没有 `/opt/ros/humble/setup.bash`、`/root/rober/onboard/install/setup.bash` 和目标板 runtime，符合本地 fail-closed 预期。

True-board strict no-motion artifact：

- Path: `sprints/2026.07.12_16-55_o3_map_server_on_configure_return_source_repair/artifacts/live_o10_map_server_on_configure_return_source_repair.raw.json`
- Command return code: `2`
- `status=blocked_with_root_cause`
- `proof.map_server_active=false`
- `proof.artifact_closeout.primary_root_cause.reason=map_server_on_configure_return_false_after_valid_map_io_deferred_completion`
- `proof.artifact_closeout.primary_root_cause.detail=on_configure_returned_failure_after_valid_yaml_image_readback_with_map_io_completion_logged_later`
- `proof.map_server_transition_callback_probe.canonical_classification=map_server_on_configure_return_false_after_valid_map_io_deferred_completion`
- `proof.map_server_transition_callback_probe.on_configure_return_source.primary_source=on_configure_return_false_after_valid_map_inputs_while_map_io_log_completes_later`
- `proof.map_server_transition_callback_probe.on_configure_return_source.source_family=on_configure_return_false_source`
- `map_input_validation.valid_for_map_server=true`
- `map_input_validation.yaml_readable=true`
- `map_input_validation.image_readable=true`
- `map_input_validation.yaml_fields_valid=true`
- `map_input_validation.analysis_ok=true`
- `map_input_validation.width=261`
- `map_input_validation.height=113`
- `map_input_validation.cell_counts.free=425`
- `excluded_sources.parameter_or_map_file_invalid_excluded_by_readback=true`
- `excluded_sources.map_server_exception_text_observed=false`
- `excluded_sources.service_timeout_or_rpc_error_observed=false`
- `excluded_sources.dds_shm_transport_error_observed=false`
- `return_path_evidence.change_state_response_false_before_map_io_completion=true`
- `return_path_evidence.map_server_configure_callback_entered=true`
- `return_path_evidence.yaml_load_started=true`
- `return_path_evidence.image_load_started=true`
- `return_path_evidence.map_read_completed_after_state_failure=true`
- `service_rpc_timing.service_timeout_or_rpc_error_observed_in_log=false`
- `service_rpc_timing.lifecycle_readback_timeout_observed=false`
- `service_rpc_timing.service_timeout_s=12.0`
- `map_io_timing.configure_to_state_failure_ms=23.532`
- `map_io_timing.image_load_to_state_failure_ms=15.643`
- `map_io_timing.state_failure_to_map_read_completed_ms=91.582`
- `map_io_timing.configure_to_map_read_completed_ms=115.115`

关键 runtime log ordering：

```text
[INFO] [1783847387.348673268] [lifecycle_manager]: Configuring map_server
[INFO] [1783847387.352491223] [map_server]: Configuring
[INFO] [1783847387.352824931] [map_io]: Loading yaml file: /root/rober/onboard/runtime/maps/trashbot_map.yaml
[INFO] [1783847387.360380215] [map_io]: Loading image_file: /root/rober/onboard/runtime/maps/trashbot_map.pgm
[ERROR] [1783847387.376023573] [lifecycle_manager]: Failed to change state for node: map_server
[INFO] [1783847387.467605937] [map_io]: Read map /root/rober/onboard/runtime/maps/trashbot_map.pgm: 261 X 113 map @ 0.05 m/cell
```

## No-Motion 安全边界

True-board artifact 继续保持 strict no-motion：

- `path_generation_attempted=false`
- `path_generated=false`
- `safe_to_control=false`
- `publishes_cmd_vel=false`
- `calls_base_manual=false`
- `uses_base_uart=false`
- `route_execution_success=false`
- `delivery_success=false`
- `hil_pass=false`
- `blocked_commands_not_sent` 包含 `/cmd_vel` 和 `navigate_to_pose`
- `blocked_devices_not_opened=["/dev/ttyS5"]`

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

- First run return code: `1`
- Failure: LiDAR `SerialException` traceback 被新 `on_configure_return_source` 误判为 map_server exception。
- 修复：只把 `map_server_exception_text` 作为 map_server exception source，普通 runtime traceback 继续作为背景日志。
- Second run return code: `1`
- Failure: synthetic lifecycle readback timeout noise 抢占了已确认的新 transition classification。
- 修复：当 transition classification 已是 `map_server_on_configure_return_false_after_valid_map_io_deferred_completion` 时，source summary 优先采信该更强证据，再处理 readback timeout。
- Final return code: `0`
- Key output: `Ran 127 tests in 2.282s` / `OK`

```bash
bash -n onboard/scripts/o11_nav2_lifecycle.sh
```

- Return code: `0`
- Output: no output
- Note: `o11_nav2_lifecycle.sh` 未改动；按验收命令做 syntax check，并同步到 board 以保持 helper 调用链一致。

```bash
python3 onboard/scripts/o10_amcl_nav2_runtime_proof.py --strict-no-motion --no-base-uart --timeout-s 18 --managed-runtime-opt-in --managed-map-yaml /root/rober/onboard/runtime/maps/trashbot_map.yaml --output-json sprints/2026.07.12_16-55_o3_map_server_on_configure_return_source_repair/artifacts/local_o10_map_server_on_configure_return_source_repair.raw.json
```

- Return code: `2`
- Key output/artifact: local fail-closed on `map_lifecycle_latest_missing` and `board_source_preflight_source_failed`。
- Failure 定位：本地 macOS 不是目标板 ROS2 runtime，不作为 Nav2/map_server root cause。

```bash
ssh -p 37878 root@192.168.1.11 'mkdir -p /root/rober/onboard/scripts /tmp/rober_o10_artifacts'
```

- Return code: `0`

```bash
scp -P 37878 onboard/scripts/o10_amcl_nav2_runtime_proof.py root@192.168.1.11:/root/rober/onboard/scripts/o10_amcl_nav2_runtime_proof.py
```

- Return code: `0`

```bash
scp -P 37878 onboard/scripts/o11_nav2_lifecycle.sh root@192.168.1.11:/root/rober/onboard/scripts/o11_nav2_lifecycle.sh
```

- Return code: `0`

```bash
ssh -p 37878 root@192.168.1.11 'cd /root/rober/onboard && /usr/bin/timeout 420s /usr/bin/python3.10 scripts/o10_amcl_nav2_runtime_proof.py --strict-no-motion --no-base-uart --timeout-s 18 --managed-runtime-opt-in --managed-map-yaml /root/rober/onboard/runtime/maps/trashbot_map.yaml --output-json /tmp/rober_o10_artifacts/live_o10_map_server_on_configure_return_source_repair.raw.json'
```

- Return code: `2`
- Key output/artifact: `blocked_with_root_cause`，primary root cause 收窄到 `map_server_on_configure_return_false_after_valid_map_io_deferred_completion`。

```bash
scp -P 37878 root@192.168.1.11:/tmp/rober_o10_artifacts/live_o10_map_server_on_configure_return_source_repair.raw.json sprints/2026.07.12_16-55_o3_map_server_on_configure_return_source_repair/artifacts/live_o10_map_server_on_configure_return_source_repair.raw.json
```

- Return code: `0`

```bash
git diff --check -- onboard/scripts/o10_amcl_nav2_runtime_proof.py onboard/scripts/o11_nav2_lifecycle.sh onboard/tests/test_nav2_runtime_proof_helper.py docs/navigation/field_route_evidence_preflight.md docs/navigation/fixed_route_workflow.md sprints/2026.07.12_16-55_o3_map_server_on_configure_return_source_repair
```

- Return code: `0`
- Output: no output

Anchor checks：

```bash
rg -n "map_server_on_configure_return_false_after_valid_map_io_deferred_completion|on_configure_return_source|on_configure_return_false_after_valid_map_inputs|parameter_or_map_file_invalid_excluded_by_readback" onboard/scripts/o10_amcl_nav2_runtime_proof.py onboard/tests/test_nav2_runtime_proof_helper.py docs/navigation/field_route_evidence_preflight.md docs/navigation/fixed_route_workflow.md
```

- Return code: `0`
- Key output: anchors found in helper, tests, and navigation docs.

Live artifact safety check：

- Return code: `0`
- Key output:
  - `map_server_active False`
  - `classification map_server_on_configure_return_false_after_valid_map_io_deferred_completion`
  - `primary_source on_configure_return_false_after_valid_map_inputs_while_map_io_log_completes_later`
  - `path_generation_attempted False`
  - `path_generated False`
  - `safe_to_control False`
  - `calls_base_manual False`
  - `uses_base_uart False`
  - `route_execution_success False`
  - `delivery_success False`
  - `hil_pass False`
  - `publishes_cmd_vel False`
  - `blocked_commands_not_sent_contains_cmd_vel True`
  - `blocked_commands_not_sent_contains_navigate_to_pose True`
  - `blocked_devices_not_opened ['/dev/ttyS5']`

## 失败定位

本轮没有证明 `/map_server active=true`。P0 接受条件走第二条：root cause 比 15:54 更窄。

新的 primary root cause 是：

`map_server_on_configure_return_false_after_valid_map_io_deferred_completion`

具体解释：

- lifecycle manager 请求 configure。
- `/map_server` configure callback 已进入。
- managed map YAML/PGM 可读，YAML 字段有效，runtime analysis OK。
- 没有 map_server-scoped exception。
- 没有 ChangeState service/RPC timeout log。
- 没有 lifecycle readback timeout。
- ChangeState failure/false response 发生在 map IO completion 前约 `91.582ms`。
- `map_io` 后续仍输出 `Read map ...` completion。

因此本轮不再只是重复 `map_server_changestate_response_false_before_map_io_completion`；它已收窄到 `on_configure` return false source bucket：valid map inputs 下，`on_configure` / `loadMapResponseFromYaml` return path 或 executor/log ordering 在 map IO completion log 之前让 lifecycle manager 收到 failure。

下一步应直接查 Nav2 map_server `loadMapResponseFromYaml` return code、callback exception 是否被 lifecycle 层转换、executor/log ordering、以及 lifecycle manager 对 ChangeState response 的处理。

## 剩余风险

- `/map_server active=false`，仍未 lifecycle clean/active。
- `/map` sample、AMCL active、dynamic `map->odom`、planner-only path generation、route execution、delivery/operator acceptance、current live HIL 和 production external evidence 均未证明。
- runtime log 仍有 LiDAR `SerialException` 背景噪声，但本轮 primary root cause 不依赖它；未做硬件判断，也未读取 vendor docs。
- 本轮 artifact 是 strict no-motion software proof，不是 safe-to-control、HIL、route execution、delivery success 或 OKR 百分比提升证据。
- 当前 worktree 已有大量历史未提交改动；本轮只在允许范围内增量修改，没有回滚或整理无关文件。

## 协同判断

- Product / OKR Owner: 需要做 Product closeout，按 blocker narrowing 接受或判定下一轮是否继续同 blocker；本轮不应调整 OKR 百分比。
- Hardware: 暂不需要。只有 LiDAR serial/runtime/wiring 成为 primary root cause 时才接手，并先读 `docs/vendor/VENDOR_INDEX.md`。
- Autonomy: 暂不需要。必须等 `/map_server` lifecycle clean/active 后再恢复 `/map`、AMCL、TF、planner-only path 或 route execution。
- Full-Stack: 不需要。
