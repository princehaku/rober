# Tech Done - O3 Map Server Configure Failure Repair

## Sprint Metadata

- sprint_type: epic
- Sprint: `sprints/2026.07.12_13-54_o3_map_server_configure_failure_repair/`
- Owner: `robot-software-engineer`
- Run time: `2026-07-12 14:16:50 CST`
- Result: blocked with narrower strict no-motion root cause, not lifecycle clean/active

## 实际改动

- `onboard/scripts/o10_amcl_nav2_runtime_proof.py`
  - 让 `run_ros()` 与 managed runtime 子进程统一继承 `RMW_FASTRTPS_USE_SHM=0` 和 `FASTDDS_BUILTIN_TRANSPORTS=UDPv4`，避免 FastDDS SHM 端口锁把 graph/lifecycle RPC 混成泛化 blocker。
  - 新增 `map_server_configure_return_failure_before_deferred_map_read_completed` 与 `map_server_configure_return_failure_after_map_read_completed` 分类，把 12:55 的 generic configure callback failure 继续拆到 map IO / ChangeState ordering。
  - 新增 `map_server_change_state_rpc_dds_shm_transport_port_lock` 分类和日志字段；若后续再次出现 `open_and_lock_file failed`，artifact 会直接收口到 DDS/RPC 层。
  - `managed_runtime_presence_log_evidence()` 增加 `log_tail` fallback，避免只有已采集日志文本时 root cause normalization 回退。
- `onboard/tests/test_nav2_runtime_proof_helper.py`
  - 新增 source-prefix DDS guard、FastDDS SHM port-lock、before/after map read ordering 分类测试。
- `docs/navigation/field_route_evidence_preflight.md`
  - 同步 13:54 proof boundary、DDS guard 和新的 configure ordering 分类。
- `docs/navigation/fixed_route_workflow.md`
  - 同步 fixed-route closeout 对 13:54 artifact 的读取规则和安全边界。
- `sprints/2026.07.12_13-54_o3_map_server_configure_failure_repair/artifacts/`
  - 生成 `local_o10_map_server_configure_failure_repair.raw.json`。
  - 生成 `live_o10_map_server_configure_failure_repair.raw.json`。

未改动 `OKR.md`、`docs/process/okr_progress_log.md`、O5/O6/O7 API/UI/archive 代码、WAVE ROVER/ESP32/UART/串口/波特率/接线/硬件配置。未修改 `o11_nav2_lifecycle.sh` 或 bringup launch。

## Artifact 结论

Local dry-run artifact：

- 文件：`sprints/2026.07.12_13-54_o3_map_server_configure_failure_repair/artifacts/local_o10_map_server_configure_failure_repair.raw.json`
- 返回码：`2`
- `status=blocked_with_root_cause`
- 主因：`canonical map proof/map_lifecycle_latest_missing` 与 `ROS install/source/board_source_preflight_source_failed`
- 解释：macOS 本机缺少 `/opt/ros/humble/setup.bash` 与 `/root/rober/onboard`，local 只证明 fail-closed 行为，不替代 true-board proof。

True-board artifact：

- 文件：`sprints/2026.07.12_13-54_o3_map_server_configure_failure_repair/artifacts/live_o10_map_server_configure_failure_repair.raw.json`
- 返回码：`2`
- `status=blocked_with_root_cause`
- `proof.board_source_preflight.classification=board_source_preflight_ready`
- `proof.managed_runtime_started=true`
- `proof.map_server_active=false`
- `proof.amcl_active=false`
- `proof.root_causes[0].layer=Nav2 map_server transition callback`
- `proof.root_causes[0].reason=map_server_configure_return_failure_before_deferred_map_read_completed`
- `proof.root_causes[0].detail=lifecycle_manager_changestate_response_failure_during_configure_before_deferred_map_read_completed`
- `proof.map_server_transition_callback_probe.canonical_classification=map_server_configure_return_failure_before_deferred_map_read_completed`
- `proof.map_server_transition_callback_probe.transition_sequence.observed_stage=configure`
- `transition_sequence.configure.lifecycle_manager_requested=true`
- `transition_sequence.configure.map_server_callback_entered=true`
- `transition_sequence.configure.yaml_load_started=true`
- `transition_sequence.configure.image_load_started=true`
- `transition_sequence.configure.map_read_completed=true`
- `transition_sequence.configure.state_change_failed=true`
- `transition_sequence.configure.state_change_failed_before_map_read_completed=true`
- `service_rpc_timing.inferred_change_state_response=failure`
- `bond_timing.bond_stage=not_created_before_configure_return_failure`
- `runtime_log_window.dds_transport_error_text=""`

本轮没有修到 `/map_server` lifecycle clean/active；但 primary root cause 已从上一轮 `map_server_configure_callback_return_failure` 收窄为 configure ChangeState failure 与 deferred map read completion 的 ordering 问题。

## No-Motion 安全边界

全部 artifact 继续固定：

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
- 关键输出：`Ran 123 tests in 2.272s`，`OK`。

```bash
python3 onboard/scripts/o10_amcl_nav2_runtime_proof.py \
  --strict-no-motion \
  --no-base-uart \
  --timeout-s 18 \
  --managed-runtime-opt-in \
  --managed-map-yaml /root/rober/onboard/runtime/maps/trashbot_map.yaml \
  --output-json sprints/2026.07.12_13-54_o3_map_server_configure_failure_repair/artifacts/local_o10_map_server_configure_failure_repair.raw.json
```

- 返回码：`2`
- 关键输出：`status=blocked_with_root_cause`，`board_source_preflight_source_failed`。
- 失败定位：本机 macOS 无 ROS2 Humble board workspace，local artifact 只证明 helper fail-closed。

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
  'cd /root/rober/onboard && /usr/bin/timeout 420s /usr/bin/python3.10 scripts/o10_amcl_nav2_runtime_proof.py --strict-no-motion --no-base-uart --timeout-s 18 --managed-runtime-opt-in --managed-map-yaml /root/rober/onboard/runtime/maps/trashbot_map.yaml --output-json /tmp/rober_o10_artifacts/live_o10_map_server_configure_failure_repair.raw.json'
```

- 返回码：`2`
- 关键输出：`status=blocked_with_root_cause`，`reason=map_server_configure_return_failure_before_deferred_map_read_completed`。
- 失败定位：true-board ROS/source/rclpy ready，managed runtime 启动；lifecycle manager 发起 `/map_server` configure ChangeState 后收到 failure，map read completion 在 failure 之后才落日志，bond 未在 configure failure 前创建。

```bash
scp -P 37878 root@192.168.1.11:/tmp/rober_o10_artifacts/live_o10_map_server_configure_failure_repair.raw.json \
  sprints/2026.07.12_13-54_o3_map_server_configure_failure_repair/artifacts/live_o10_map_server_configure_failure_repair.raw.json
```

- 返回码：`0`

附加只读诊断：

- `ssh -p 37878 root@192.168.1.11 'grep -R "service_timeout" -n /opt/ros/humble/include /opt/ros/humble/share/nav2_lifecycle_manager 2>/dev/null | head -40'`
- 返回码：`0`
- 结论：board installed headers/share 未显示 `nav2_lifecycle_manager` 自身的 `service_timeout` header 命中；本轮未基于该只读结果修改 launch/params。

```bash
bash -n onboard/scripts/o11_nav2_lifecycle.sh
```

- 返回码：`0`
- 关键输出：无输出，shell 语法检查通过。
- 说明：本轮未编辑该文件，但 scoped worktree 中它已是 dirty 状态，因此保守补跑语法检查。

## 剩余风险

- `/map_server` 仍未 lifecycle clean/active；本轮是 strict no-motion blocker narrowing，不是修复完成。
- 仍未证明 `/map` sample、AMCL pose、dynamic `map->odom`、planner-only path generation、route execution、delivery、HIL 或 production external evidence。
- LiDAR `/dev/ttyACM0` 仍有 `SerialException` 背景噪声，但 artifact primary root cause 已在 map_server transition ordering 层；本轮不触碰硬件串口配置。
- 下一步应继续查 lifecycle manager ChangeState 与 map_server `on_configure` / map IO completion ordering，必要时对比 Nav2 Humble lifecycle manager timeout/transition semantics；在 `/map_server` clean 前不交给 Algorithm 做 AMCL/TF/path gate。

## 协同判断

- Product / OKR Owner：需要验收本轮是否接受为 O3/O1 no-motion blocker 下钻；不建议调整 OKR 百分比。
- Hardware：暂不需要。本轮没有触碰 WAVE ROVER、ESP32、UART、串口、波特率或接线；LiDAR 串口异常若后续成为主因再转 Hardware 读取 vendor 资料。
- Autonomy：暂不需要；等 `/map_server` lifecycle clean/active 后再恢复 `/map`、AMCL、dynamic `map->odom` 和 planner-only path gate。
- Full-Stack：不需要；未改 API/UI/触点合同。
