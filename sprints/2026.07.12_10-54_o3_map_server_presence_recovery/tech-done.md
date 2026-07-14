# tech-done

- sprint_type: epic
- owner: Robot Software Engineer
- scope: O3/O1 strict no-motion `/map_server` presence recovery
- date: 2026-07-12

## 实际改动

本轮扩展 `onboard/scripts/o10_amcl_nav2_runtime_proof.py`，新增
`proof.map_server_presence_recovery`，schema 为
`trashbot.o10.map_server_presence_recovery.v1`。该字段把 09-54 的只读
`map_server_node_absent` 诊断升级为显式 recovery proof，固定记录：

- `recovery_attempted`
- `recovery_path.managed_runtime_requested`
- `recovery_path.managed_runtime_started`
- `managed_map_yaml.basename` / `configured_basename` / `exists` / `sha256_prefix`
- managed runtime process/log evidence
- `/map_server` node/lifecycle presence
- strict no-motion safety invariants

新增分类覆盖：

- `presence_recovery_not_requested_read_only_existing_graph`
- `managed_map_yaml_missing`
- `managed_map_yaml_unreadable`
- `managed_runtime_start_failed`
- `managed_runtime_process_exited_before_map_server_presence`
- `managed_runtime_graph_unreadable_after_start`
- `managed_runtime_started_map_server_not_observed`
- `lifecycle_manager_not_serving_map_server`
- `map_server_lifecycle_rpc_timeout_after_recovery`
- `map_server_lifecycle_not_active_after_recovery`
- `map_server_lifecycle_command_failed_after_recovery`
- `map_server_lifecycle_active`

同时补充 requested map yaml basename 保留逻辑：即使本机没有
`/root/rober/onboard/runtime/maps/trashbot_map.yaml`，local fail-closed artifact 也会记录
`basename=trashbot_map.yaml`，不会把显式 CLI 输入丢成空。

验收返工补充 root cause 归因收敛：当 `managed_runtime_requested=true`、
`managed_runtime_started=true`，且 managed runtime log/process evidence 已证明
`map_server`、`lifecycle_manager` 曾启动并读取 `trashbot_map.yaml`/`trashbot_map.pgm` 时，
helper 不再把 ROS package probe timeout 或 ROS graph timeout 写成顶层 `*_missing` root
cause。此类探测结果仍保留在 `proof.package_availability`、`proof.commands.package_checks`
和 `proof.root_cause_filtering.suppressed_root_causes` 中，作为诊断噪声；顶层
`proof.root_causes` 收敛为 presence recovery 主读数：
`map_server_lifecycle_not_active_after_recovery` /
`lifecycle_manager_failed_to_change_state_for_map_server`。

测试文件 `onboard/tests/test_nav2_runtime_proof_helper.py` 新增 10-54 targeted tests，
覆盖 read-only not requested、managed map yaml missing、managed runtime 后仍 Node-not-found、
runtime log 显示 map_server lifecycle transition failed、active case safety false，以及
runtime evidence 覆盖 package probe 噪声时的 root cause 过滤。

文档同步更新：

- `docs/navigation/field_route_evidence_preflight.md`
- `docs/navigation/fixed_route_workflow.md`

两份文档补充 `proof.map_server_presence_recovery` 的读取顺序、分类集合、map yaml path policy、
与 09-54 visibility summary 的优先级关系，以及仍禁止 NavigateToPose、`/cmd_vel`、
`/api/base/manual` 和 WAVE ROVER UART。

## Artifact

本轮生成 artifact：

- local dry-run: `sprints/2026.07.12_10-54_o3_map_server_presence_recovery/artifacts/local_o10_map_server_presence_recovery.raw.json`
- local command log: `sprints/2026.07.12_10-54_o3_map_server_presence_recovery/artifacts/local_o10_map_server_presence_recovery.command.log`
- live board: `sprints/2026.07.12_10-54_o3_map_server_presence_recovery/artifacts/live_o10_map_server_presence_recovery.raw.json`
- live command log: `sprints/2026.07.12_10-54_o3_map_server_presence_recovery/artifacts/live_o10_map_server_presence_recovery.command.log`

live board 关键字段：

```json
{
  "status": "blocked_with_root_cause",
  "board_source_preflight": "board_source_preflight_ready",
  "lightweight_cli_ready": true,
  "cli_ready": true,
  "runtime_ready": true,
  "managed_runtime_requested": true,
  "managed_runtime_started": true,
  "managed_runtime_boundary": "explicit_opt_in_managed_localization_runtime_no_motion",
  "map_server_presence_recovery": {
    "canonical_classification": "map_server_lifecycle_not_active_after_recovery",
    "failure_detail": "lifecycle_manager_failed_to_change_state_for_map_server",
    "next_step": "inspect_map_server_configure_error_and_map_yaml_runtime_log",
    "recovery_attempted": true,
    "managed_map_yaml": {
      "basename": "trashbot_map.yaml",
      "image_basename": "trashbot_map.pgm",
      "exists": true,
      "sha256_prefix": "1b54312162c67b74"
    },
    "node_presence": {
      "log_inferred_map_server_configure_started": true,
      "log_inferred_map_yaml_loaded": true,
      "log_inferred_map_server_state_change_failed": true
    }
  },
  "root_cause_filtering": {
    "applied": true,
    "reason": "managed_runtime_log_evidence_overrides_package_probe_missing_root_causes",
    "suppressed_root_causes": [
      "ros2_node_list_timeout",
      "map_lifecycle_proof_not_clean",
      "ros2_trashbot_bringup_missing",
      "ros2_trashbot_nav_missing",
      "nav2_map_server_missing",
      "nav2_amcl_missing",
      "nav2_lifecycle_manager_missing"
    ]
  },
  "root_causes": [
    {
      "layer": "Nav2 map_server presence recovery",
      "reason": "map_server_lifecycle_not_active_after_recovery",
      "detail": "lifecycle_manager_failed_to_change_state_for_map_server"
    }
  ],
  "safe_to_control": false,
  "publishes_cmd_vel": false,
  "calls_base_manual": false,
  "robot_control_executed": false,
  "route_execution_success": false,
  "delivery_success": false,
  "hil_pass": false,
  "uses_base_uart": false,
  "path_generation_attempted": false,
  "path_generated": false
}
```

解释：本轮已经越过 09-54 的 `managed_runtime_requested=false` / read-only existing graph
边界。true-board helper 明确尝试 `--managed-runtime-opt-in`，managed runtime 已启动，map yaml
存在且 map_server 运行日志显示已加载 `trashbot_map.yaml`。新 blocker 不再是
`map_server_node_absent`，也不是 `nav2_*_missing` package probe 噪声，而是 map_server
configure/lifecycle transition failed。

local dry-run 关键字段：

```json
{
  "status": "blocked_with_root_cause",
  "board_source_preflight": "board_source_preflight_source_failed",
  "managed_runtime_requested": true,
  "managed_runtime_started": false,
  "map_server_presence_recovery": {
    "canonical_classification": "managed_map_yaml_missing",
    "basename": "trashbot_map.yaml",
    "source": "explicit_cli_managed_map_yaml_missing"
  },
  "safe_to_control": false,
  "publishes_cmd_vel": false,
  "calls_base_manual": false,
  "path_generation_attempted": false,
  "path_generated": false
}
```

local 失败定位：macOS 本机缺 `/opt/ros/humble/setup.bash` 和
`/root/rober/onboard/runtime/maps/trashbot_map.yaml`，因此按预期 fail-closed；该结果只证明
本地无 ROS2/map 环境下 helper 仍保留 no-motion 与 requested map yaml basename，不作为 board
运行结论。

## 验证结果

```bash
python3 -m py_compile onboard/scripts/o10_amcl_nav2_runtime_proof.py
```

结果：通过，exit code 0。

```bash
python3 -m unittest onboard.tests.test_nav2_runtime_proof_helper
```

结果：通过，`Ran 116 tests in 2.284s`，`OK`。

```bash
python3 onboard/scripts/o10_amcl_nav2_runtime_proof.py \
  --strict-no-motion \
  --no-base-uart \
  --timeout-s 18 \
  --managed-runtime-opt-in \
  --managed-map-yaml /root/rober/onboard/runtime/maps/trashbot_map.yaml \
  --output-json sprints/2026.07.12_10-54_o3_map_server_presence_recovery/artifacts/local_o10_map_server_presence_recovery.raw.json
```

结果：exit code 2，预期 fail-closed。关键结论：
`managed_runtime_requested=true`、`managed_runtime_started=false`、
`map_server_presence_recovery.canonical_classification=managed_map_yaml_missing`，
并保留 `managed_map_yaml.basename=trashbot_map.yaml`。stdout/stderr 已保存到
`artifacts/local_o10_map_server_presence_recovery.command.log`。

```bash
ssh -p 37878 root@192.168.1.11 \
  'mkdir -p /root/rober/onboard/scripts /tmp/rober_o10_artifacts'
```

结果：通过，exit code 0。

```bash
scp -P 37878 onboard/scripts/o10_amcl_nav2_runtime_proof.py \
  root@192.168.1.11:/root/rober/onboard/scripts/o10_amcl_nav2_runtime_proof.py
```

结果：通过，exit code 0。

```bash
ssh -p 37878 root@192.168.1.11 \
  'cd /root/rober/onboard && /usr/bin/timeout 420s /usr/bin/python3.10 scripts/o10_amcl_nav2_runtime_proof.py --strict-no-motion --no-base-uart --timeout-s 18 --managed-runtime-opt-in --managed-map-yaml /root/rober/onboard/runtime/maps/trashbot_map.yaml --output-json /tmp/rober_o10_artifacts/live_o10_map_server_presence_recovery.raw.json'
```

结果：exit code 2，按 helper 语义表示 blocked artifact 已写出。关键结论：
`managed_runtime_requested=true`、`managed_runtime_started=true`、
`managed_runtime_boundary=explicit_opt_in_managed_localization_runtime_no_motion`、
`managed_map_yaml.exists=true`、`managed_map_yaml.basename=trashbot_map.yaml`、
`managed_map_yaml.sha256_prefix=1b54312162c67b74`、
`map_server_presence_recovery.canonical_classification=map_server_lifecycle_not_active_after_recovery`、
`failure_detail=lifecycle_manager_failed_to_change_state_for_map_server`、
`root_cause_filtering.applied=true`。顶层 `proof.root_causes` 只剩
`Nav2 map_server presence recovery / map_server_lifecycle_not_active_after_recovery`，被过滤的
诊断噪声包括 `ros2_node_list_timeout`、`map_lifecycle_proof_not_clean`、
`ros2_trashbot_bringup_missing`、`ros2_trashbot_nav_missing`、`nav2_map_server_missing`、
`nav2_amcl_missing` 和 `nav2_lifecycle_manager_missing`。stdout/stderr 已保存到
`artifacts/live_o10_map_server_presence_recovery.command.log`。

```bash
scp -P 37878 root@192.168.1.11:/tmp/rober_o10_artifacts/live_o10_map_server_presence_recovery.raw.json \
  sprints/2026.07.12_10-54_o3_map_server_presence_recovery/artifacts/live_o10_map_server_presence_recovery.raw.json
```

结果：通过，exit code 0。

```bash
git diff --check -- \
  onboard/scripts/o10_amcl_nav2_runtime_proof.py \
  onboard/scripts/o11_nav2_lifecycle.sh \
  onboard/src/ros2_trashbot_bringup \
  onboard/tests/test_nav2_runtime_proof_helper.py \
  docs/navigation/field_route_evidence_preflight.md \
  docs/navigation/fixed_route_workflow.md \
  sprints/2026.07.12_10-54_o3_map_server_presence_recovery
```

结果：通过，exit code 0。

## No-motion 安全边界

本轮没有发送 NavigateToPose，没有发布 `/cmd_vel`，没有调用 `/api/base/manual`，没有打开
WAVE ROVER UART。local 与 live artifact 中以下字段均为 false：

- `safe_to_control`
- `publishes_cmd_vel`
- `calls_base_manual`
- `robot_control_executed`
- `route_execution_success`
- `delivery_success`
- `hil_pass`
- `uses_base_uart`
- `path_generation_attempted`
- `path_generated`

`/scan`、TF、planner/path 仍只作为 guarded downstream context；本轮 primary 证据仅为
managed runtime opt-in 后的 `/map_server` presence/lifecycle recovery proof。

## 失败定位

本轮 true-board 已不再是 09-54 的 read-only `map_server_node_absent`。更窄 blocker 是：

- managed runtime 已启动；
- `trashbot_map.yaml` 存在并被 map_server 读取；
- runtime log 显示 lifecycle manager 开始 `Configuring map_server`；
- runtime log 显示 `Failed to change state for node: map_server`；
- helper 收口为 `map_server_lifecycle_not_active_after_recovery`。

本轮 live artifact 还记录 `managed_runtime_wait_result.reason=ros2_node_list_timeout`，并且日志中出现
LiDAR driver `SerialException: device reports readiness to read but returned no data`。该 LiDAR 现象不能当成本轮 primary success 或 primary blocker；它说明下一轮如果要恢复 `/scan`，
需要单独拆 LiDAR serial/runtime 占用或断连问题。

## 剩余风险和协同

剩余风险：

- `/map_server` 仍未 active，`/map` sample、AMCL pose、dynamic `map->odom`、planner/path
  readiness、route execution、delivery success 和 HIL 仍未证明。
- ROS2 graph 仍有 daemon/node list timeout 和 duplicate node warning；这会影响 lifecycle readback
  稳定性。
- LiDAR `/dev/ttyACM0` 读空或多进程占用风险存在，但本轮没有改硬件配置，也没有触碰 WAVE ROVER UART。

需要协同：

- Product：验收本轮是否接受为 O3/O1 strict no-motion presence recovery delta，OKR 百分比应保持 flat。
- Algorithm：等 map_server lifecycle transition 修复后，继续 `/map`、AMCL pose、dynamic `map->odom`
  和 planner-only path gate。
- Hardware：本轮不需要参与 map_server lifecycle 修复；若下一轮消费 `/scan` 或 LiDAR runtime，
  需要 Hardware 复核 `/dev/ttyACM0` 读空/多进程占用，不涉及 WAVE ROVER UART。
- Full-Stack：不需要；未触碰 O5/O6/O7 API/UI surface。
