# Tech Done - O3 Live Upper-Computer Same-Window Evidence

## Sprint Metadata

- sprint_type: epic
- Sprint: `sprints/2026.07.14_18-45_o3_live_upper_computer_same_window_evidence/`
- Implementation and integration owner: `robot-algorithm-engineer`
- Target: `root@192.168.1.11:37878`
- Helper result: `nav2_no_motion_path_generation_runtime_observed`
- Contract result: `partial_success_blocked_missing_dynamic_map_to_odom_source_inventory`
- Proof boundary: `robot_runtime_o3_strict_no_motion_localization_planner_evidence_only`

## 自主能力目标和本轮抓手

本轮对真实上位机执行 fresh strict no-motion capture，主链为：

```text
/scan -> /amcl_pose -> map/amcl lifecycle -> map_to_odom -> ComputePathToPose
```

现场成功观察 `/scan`、`/amcl_pose`、active map/AMCL lifecycle、tf2 buffer 中的
`map->odom` 变换和 28-point planner-only path；但 `/tf` endpoint/source inventory 未被 helper
观察到，因此 `tf_readiness_summary.map_to_odom_dynamic.dynamic_source_observed=false`。本轮保留
成功事实和 exact gap，不把 tf2 buffer transform 或 path success 提升为 clean dynamic-source、
route execution、delivery、HIL 或 safe-to-control 证明。

## Hardware 事实解歧与 Retry Preflight

首次 preflight 保留了 lifecycle synthesized status 的 `230400` 与 live diagnostics `150000`
冲突，并按 gate 停止 helper。Hardware read-only audit 后，本 owner 再次独立执行有界只读复核，
证据保存在 `artifacts/algorithm/preflight.retry.*` 与 `preflight.retry.summary.json`。

Retry preflight 结果：

```text
preflight_retry_exit_code=0
remote_hostname=op-z3-b6.home
remote_time=2026-07-14T19:31:18,152535228+08:00
top_level_baudrate=150000
baudrate_readback_source=driver_diagnostics_latest.serial.serial_baudrate
baudrate_readback_status=current_with_reference_conflict
lifecycle 230400 candidate status=reference_conflict_not_current
persisted_pid=550851
persisted_serial_port=/dev/ttyACM0
persisted_baudrate=150000
ros_param /lidar_driver serial_baudrate=150000
```

Manager/driver `/proc` argv 均包含 `/dev/ttyACM0` 和 `150000`。2 秒 fresh diagnostics 窗口：

```text
parsed_packet_count: 48936662 -> 48937171
published_scan_count: 2599905 -> 2599931
diagnostics_counters_increased=true
```

因此 retry 允许复用 existing lifecycle。Helper 始终带：

```text
--reuse-existing-lidar-lifecycle
--managed-lidar-serial-port /dev/ttyACM0
--managed-lidar-serial-baudrate 150000
```

Remote proof 确认：

```text
managed_lidar_policy=reuse_existing_lidar_lifecycle_no_driver_start
managed_lidar_driver_started_by_helper=false
```

没有 stop/start lifecycle，也没有启动第二个 LiDAR driver。

## SSH / Capture / SCP 结果

本机 macOS 首次按原命令调用 GNU `timeout` 失败，原始证据继续保留：

```text
local_executor_attempt_1_exit_code=127
stderr=command not found: timeout
remote_contact_attempted=false
```

后续 SSH outer budget 使用 `perl alarm` 做 macOS 有界兼容层；remote helper 仍使用 tech plan
原定 `timeout --signal=INT --kill-after=15s 450s`，planner budget 为 30 秒。

最终 current-window retry：

```text
preflight_exit_code=0
capture_exit_code=0
scp_exit_code=0
remote_raw_path=/root/rober/onboard/runtime/o3_live_upper_computer_same_window_20260714T113117Z.raw.json
local_helper_sha256=56215a5325b29fe8c08c4d36b761f237d299d99d473f85a210f996ddad44df33
remote_helper_sha256=56215a5325b29fe8c08c4d36b761f237d299d99d473f85a210f996ddad44df33
helper_sha256_match=true
```

## Live 关键事实

同一次 remote raw artifact 输出：

```text
status=nav2_no_motion_path_generation_runtime_observed
scan_once_observed=true
amcl_pose_observed=true
amcl_pose.frame_id=map
map_server_active=true
amcl_active=true
tf_chain_observed.map_to_odom=true
tf_chain_observed.odom_to_base_link=true
tf_chain_observed.map_to_base_link=true
tf_readiness_summary.map_to_odom_dynamic.observed=true
tf_readiness_summary.map_to_odom_dynamic.dynamic_source_observed=false
tf_readiness_summary.map_to_odom_dynamic.source_class=missing
tf_readiness_summary.blocked_reason=/tf_topic_missing
path_generation_attempted=true
path_generated=true
path_point_count=28
path_structured_pose_count=28
```

Planner boundary 为 strict no-motion `ComputePathToPose`。Remote helper exit `0` 和 28-point path
证明 planner-only path generation 成功；不证明 dynamic `/tf` source inventory clean，更不证明
NavigateToPose、controller/BT、fixed-route execution 或 delivery。

## Exact Root Cause

最终 capture envelope 在顶层保留：

```text
layer=localization_tf_dynamic_source_contract
reason=map_to_odom_dynamic_source_not_observed_in_tf_source_inventory
detail=same-run tf2_echo map->odom and 28-point path were observed, but /tf endpoint/source
       inventory remained missing and dynamic_source_observed=false
```

该 gap 不影响如实记录 helper 的 planner-only success，但阻止完整 Product contract 变为 clean。
本轮遵照主节点验收口径，不修改 helper；local/remote helper SHA 在 capture 时完全一致。

下一条最小 no-motion 复验命令：

```bash
source /opt/ros/humble/setup.bash && \
source /root/rober/onboard/install/setup.bash && \
timeout 30s ros2 topic echo /tf tf2_msgs/msg/TFMessage --once
```

## 实际改动

本轮最终改动仅位于当前 sprint：

- `artifacts/algorithm/live_upper_computer_same_window_evidence.raw.json`
  - 最终 capture envelope，嵌入 fresh remote proof、initial gate 历史、Hardware-disambiguated
    provenance、exit codes、双端 SHA 和 exact root cause。
- `artifacts/algorithm/live_upper_computer_same_window_evidence.remote.raw.json`
  - 从真实上位机 scp 拉回的 helper 原始 JSON。
- `artifacts/algorithm/live_upper_computer_same_window_evidence.{stdout,stderr}.log`
  - 最终 helper stdout/stderr。
- `artifacts/algorithm/live_upper_computer_same_window_evidence.{exit_code,scp_exit_code}.txt`
  - 最终 helper/scp exit code。
- `artifacts/algorithm/live_upper_computer_same_window_evidence.remote.first_helper.raw.json` 与
  `live_upper_computer_same_window_evidence.first_helper.*`
  - 在最终 envelope 写入前保存的首次 helper success 原始证据和 exact gap。
- `artifacts/algorithm/preflight.retry.{stdout,stderr}.log`、
  `preflight.retry.exit_code.txt`、
  `preflight.retry.summary.json`、`radar_status.retry.raw.json`、
  `lidar_lifecycle_status.retry.raw.json`
  - retry 前 current 150000 lifecycle 独立只读复核。
- `artifacts/algorithm/run_id.initial_gate.txt`、`remote_raw_path.initial_gate.txt`、
  `capture_retry_{started,finished}_at_utc.txt`
  - 保留首次 gate 与 retry provenance。
- 本 `tech-done.md`。

没有修改 `pre_start.md`、`prd.md`、`tech-plan.md`、`OKR.md`、hardware/launch/map/Nav2 参数。
最终没有修改 helper/tests/docs；本轮不运行 helper-change-only 的额外单测。

## 验证结果

- 主 capture envelope `python3 -m json.tool`：通过。
- remote raw JSON、retry radar/status/summary JSON `json.tool`：通过。
- tech plan Python contract assertion：通过，输出 live facts；完整 clean 条件因 dynamic source
  gap 未成立，且 `exact_root_causes` 非空。
- required-field `rg`：通过。
- scoped `git diff --check`：通过。

所有顶层与 remote `proof` safety fields 固定：

```text
safe_to_control=false
publishes_cmd_vel=false
calls_base_manual=false
uses_base_uart=false
robot_control_executed=false
route_execution_success=false
delivery_success=false
hil_pass=false
```

## 数据、接口与安全影响

- 新增 current-window `/scan`、AMCL pose、TF buffer、lifecycle 和 28 structured poses 的真实板
  artifact；没有消费历史 artifact 作为 current proof。
- 没有新增或修改产品接口。
- 没有 `/cmd_vel`、`/api/base/manual`、NavigateToPose、controller/BT、WAVE ROVER UART、
  `/dev/ttyS5` 或任何非零底盘命令。
- 只证明 strict no-motion localization/planner evidence，不证明 route execution、delivery、HIL、
  operator acceptance、safe-to-control 或 O5 production cloud。

## 剩余风险和下一步

1. `/tf` endpoint/source inventory 没有观察到 dynamic `map->odom` source；虽然 tf2 buffer 变换与
   28-point path 成功，完整 same-window dynamic-source contract 仍未 clean。
2. AMCL log 包含短暂 `Couldn't determine robot's pose associated with laser scan` 与 message-filter
   drop；本次最终仍观察到 fresh AMCL pose 和 path，但下一轮应确认稳定窗口而非单次 happy path。
3. latest radar scan-proof material 本身仍 stale；本轮 helper 的 fresh `/scan` observation 是新的
   current proof，但不能把历史 scan-proof freshness 改写为 fresh。
4. Route execution、delivery/operator acceptance、current live HIL 和 safe-to-control 全部未证明，
   不应据此上调这些完成度或归档 KR。
