# Tech Done - O3 Map Server Transition Callback Probe

## Sprint Metadata

- sprint_type: epic
- Sprint: `sprints/2026.07.12_12-55_o3_map_server_transition_callback_probe/`
- Owner: `robot-software-engineer`
- Run time: `2026-07-12 13:21:32 CST`
- Result: accepted as strict no-motion narrowed blocker, not lifecycle clean/active

## 实际改动

- `onboard/scripts/o10_amcl_nav2_runtime_proof.py`
  - 新增 `proof.map_server_transition_callback_probe`，schema 为 `trashbot.o10.map_server_transition_callback_probe.v1`。
  - 将 `/map_server` transition proof 拆成 configure/activate stage、`/map_server/change_state` service/RPC timing、bond timing、process status、runtime log window 和 no-motion invariants。
  - 保留上一轮 `proof.map_server_lifecycle_activation` 兼容字段，但本轮主读数改为 transition callback 层。
  - 从 managed runtime pre-cleanup log evidence 合并 `map_server_configure_started`、yaml/image load、map read、state change failed 和 map read ordering，避免 cleanup/SIGINT 或 LiDAR traceback 覆盖主根因。
  - 将 root cause 从泛化 `map_server_activate_callback_failed` 下钻为 `map_server_configure_callback_return_failure`。
- `onboard/tests/test_nav2_runtime_proof_helper.py`
  - 覆盖 configure callback return failure、lifecycle RPC timeout、bond wait timeout、process exit 等 transition 分类。
  - 增加 LiDAR/cleanup traceback 不应覆盖 map_server transition 分类的回归断言。
- `docs/navigation/field_route_evidence_preflight.md`
  - 增加 12:55 transition callback probe 字段读取顺序和 no-motion 证明边界。
- `docs/navigation/fixed_route_workflow.md`
  - 增加 fixed-route/no-motion closeout 对 `map_server_transition_callback_probe` 的消费规则。
- `sprints/2026.07.12_12-55_o3_map_server_transition_callback_probe/artifacts/`
  - 生成 `local_o10_map_server_transition_callback_probe.raw.json`。
  - 生成 `live_o10_map_server_transition_callback_probe.raw.json`。

未改动 `OKR.md`、`docs/process/okr_progress_log.md`、O5/O6/O7 代码、历史 sprint、WAVE ROVER/ESP32/UART/串口/硬件配置。

## Artifact 结论

Local dry-run artifact：

- 文件：`sprints/2026.07.12_12-55_o3_map_server_transition_callback_probe/artifacts/local_o10_map_server_transition_callback_probe.raw.json`
- `status=blocked_with_root_cause`
- `root_causes=[canonical map proof/map_lifecycle_latest_missing, ROS install/source/board_source_preflight_source_failed]`
- `board_source_preflight.classification=board_source_preflight_source_failed`
- `proof.map_server_transition_callback_probe.canonical_classification=map_server_transition_callback_unclassified`
- 解释：macOS 本机无 `/opt/ros/humble/setup.bash` 和 `/root/rober/onboard`，local 只作为 fail-closed artifact，不替代 true-board proof。

True-board artifact：

- 文件：`sprints/2026.07.12_12-55_o3_map_server_transition_callback_probe/artifacts/live_o10_map_server_transition_callback_probe.raw.json`
- `status=blocked_with_root_cause`
- `proof.root_causes[0].layer=Nav2 map_server transition callback`
- `proof.root_causes[0].reason=map_server_configure_callback_return_failure`
- `proof.root_causes[0].detail=lifecycle_manager_changestate_response_failure_during_configure_before_deferred_map_read_completed`
- `proof.map_server_transition_callback_probe.canonical_classification=map_server_configure_callback_return_failure`
- `proof.map_server_transition_callback_probe.transition_sequence.observed_stage=configure`
- `transition_sequence.configure.lifecycle_manager_requested=true`
- `transition_sequence.configure.map_server_callback_entered=true`
- `transition_sequence.configure.yaml_load_started=true`
- `transition_sequence.configure.image_load_started=true`
- `transition_sequence.configure.map_read_completed=true`
- `transition_sequence.configure.state_change_failed=true`
- `transition_sequence.configure.state_change_failed_before_map_read_completed=true`
- `service_rpc_timing.change_state_service_family=/map_server/change_state`
- `service_rpc_timing.inferred_change_state_response=failure`
- `bond_timing.bond_stage=not_created_before_configure_return_failure`
- `activation_summary_reference.canonical_classification=map_server_activate_callback_failed`
- map yaml/PGM readback valid：`yaml_readable=true`、`image_readable=true`、`yaml_fields_valid=true`、`width=261`、`height=113`、`free=425`

这满足本轮“若修不到 lifecycle clean/active，必须比 `map_server_activate_callback_failed` 更窄”的验收口径。当前仍未达到 `/map_server` lifecycle clean/active。

## No-Motion 安全边界

两个 artifact 均保持：

- `safe_to_control=false`
- `publishes_cmd_vel=false`
- `calls_base_manual=false`
- `robot_control_executed=false`
- `route_execution_success=false`
- `delivery_success=false`
- `hil_pass=false`
- `uses_base_uart=false`
- `path_generation_attempted=false`
- `path_generated=false`

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
- 关键输出：`Ran 120 tests in 2.273s`，`OK`。

```bash
python3 onboard/scripts/o10_amcl_nav2_runtime_proof.py \
  --strict-no-motion \
  --no-base-uart \
  --timeout-s 18 \
  --managed-runtime-opt-in \
  --managed-map-yaml /root/rober/onboard/runtime/maps/trashbot_map.yaml \
  --output-json sprints/2026.07.12_12-55_o3_map_server_transition_callback_probe/artifacts/local_o10_map_server_transition_callback_probe.raw.json
```

- 返回码：`2`
- 关键输出：`status=blocked_with_root_cause`，`board_source_preflight_source_failed`。
- 失败定位：本机 macOS 缺少板端 ROS2 setup 和 `/root/rober/onboard`，local artifact 只证明 fail-closed 行为。

```bash
ssh -p 37878 root@192.168.1.11 \
  'mkdir -p /root/rober/onboard/scripts /tmp/rober_o10_artifacts'
```

- 返回码：`0`
- 关键输出：无输出，目录创建/确认成功。

```bash
scp -P 37878 onboard/scripts/o10_amcl_nav2_runtime_proof.py \
  root@192.168.1.11:/root/rober/onboard/scripts/o10_amcl_nav2_runtime_proof.py
```

- 返回码：`0`
- 关键输出：无输出，脚本已同步到板端。

```bash
ssh -p 37878 root@192.168.1.11 \
  'cd /root/rober/onboard && /usr/bin/timeout 420s /usr/bin/python3.10 scripts/o10_amcl_nav2_runtime_proof.py --strict-no-motion --no-base-uart --timeout-s 18 --managed-runtime-opt-in --managed-map-yaml /root/rober/onboard/runtime/maps/trashbot_map.yaml --output-json /tmp/rober_o10_artifacts/live_o10_map_server_transition_callback_probe.raw.json'
```

- 返回码：`2`
- 关键输出：`status=blocked_with_root_cause`，`reason=map_server_configure_callback_return_failure`。
- 失败定位：true-board ROS2 source/CLI/rclpy ready，managed runtime 启动，map yaml/PGM 可读，`map_server` 进入 configure 并加载 yaml/image；lifecycle manager 在 map read 完成前收到 ChangeState failure，activate/bond 阶段未 clean 到达。

```bash
scp -P 37878 root@192.168.1.11:/tmp/rober_o10_artifacts/live_o10_map_server_transition_callback_probe.raw.json \
  sprints/2026.07.12_12-55_o3_map_server_transition_callback_probe/artifacts/live_o10_map_server_transition_callback_probe.raw.json
```

- 返回码：`0`
- 关键输出：无输出，artifact 已拉回 sprint 目录。

```bash
git diff --check -- \
  onboard/scripts/o10_amcl_nav2_runtime_proof.py \
  onboard/scripts/o11_nav2_lifecycle.sh \
  onboard/src/ros2_trashbot_bringup \
  onboard/tests/test_nav2_runtime_proof_helper.py \
  docs/navigation/field_route_evidence_preflight.md \
  docs/navigation/fixed_route_workflow.md \
  sprints/2026.07.12_12-55_o3_map_server_transition_callback_probe
```

- 返回码：`0`
- 关键输出：无输出，scoped diff whitespace check 通过。

## 剩余风险

- `/map_server` lifecycle 仍未 clean/active；当前只证明 blocker 已下钻到 configure callback return / ChangeState response failure。
- 尚未证明 `/map` sample、AMCL pose、dynamic `map->odom`、planner-only path gate、route execution、delivery、HIL 或 production external evidence。
- LiDAR driver 在 runtime cleanup 前后仍出现 `SerialException`，但本轮 helper 已把它隔离为非 map_server transition 主因；硬件串口问题不在本 sprint 范围内。
- 下一轮 Robot Software 应检查 Nav2 map_server `on_configure` return path、map IO completion ordering、lifecycle manager ChangeState response handling、executor timing 和 bond creation 前置条件。

## 协同判断

- Product / OKR Owner：需要验收本轮是否接受为 O3/O1 no-motion blocker 下钻，不建议调整 OKR 百分比。
- Hardware：本轮不需要；没有触碰 WAVE ROVER、ESP32、UART、串口、波特率或接线。
- Autonomy：暂不需要；等 `/map_server` lifecycle clean/active 后再恢复 `/map`、AMCL、dynamic `map->odom` 和 planner-only path gate。
- Full-Stack：不需要；未改 API/UI/触点合同。
