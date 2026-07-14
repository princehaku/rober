# Tech Done - O3 Map Server Lifecycle Activation Repair

## Sprint Metadata

- sprint_type: epic
- Sprint: `sprints/2026.07.12_11-54_o3_map_server_lifecycle_activation_repair/`
- Owner: `robot-software-engineer`
- Boundary: strict no-motion `/map_server` lifecycle activation proof only
- Result: accepted as blocker narrowed, not lifecycle clean

## 实际改动

- `onboard/scripts/o10_amcl_nav2_runtime_proof.py`
  - 新增 `proof.map_server_lifecycle_activation` additive summary。
  - 记录 map yaml/PGM exists/readable/hash/size、yaml fields、launch parameters、node identity、lifecycle manager managed node list、runtime log、exception/process/lifecycle readback 和 no-motion invariants。
  - 将 managed runtime map_server 参数固定记录为 `frame_id=map`、`use_sim_time=false`，lifecycle manager 记录 `node_names=["map_server","amcl"]`、`bond_timeout_s=8.0`、`service_timeout_s=12.0`。
  - managed runtime shell 增加 `RMW_FASTRTPS_USE_SHM=0`，降低板端 Fast DDS SHM lock 噪声对 proof 的干扰。
  - 当 runtime log 证明 valid map readback 后 lifecycle manager 报 `Failed to change state for node: map_server`，root cause 归一到 `map_server_activate_callback_failed`。
- `onboard/tests/test_nav2_runtime_proof_helper.py`
  - 新增 targeted unit test 覆盖 valid map yaml/PGM + lifecycle manager state-change failed 的下钻分类。
  - 更新 managed runtime 参数、`RMW_FASTRTPS_USE_SHM=0` 和 root cause filter 断言。
- `docs/navigation/field_route_evidence_preflight.md`
  - 增加 `proof.map_server_lifecycle_activation` 读取合同、分类集合和本轮 true-board 结果说明。
- `docs/navigation/fixed_route_workflow.md`
  - 增加 fixed-route/no-motion closeout 读取顺序，明确本轮仍不能进入 planner/path/motion。
- `sprints/2026.07.12_11-54_o3_map_server_lifecycle_activation_repair/artifacts/`
  - `local_o10_map_server_lifecycle_activation_repair.raw.json`
  - `live_o10_map_server_lifecycle_activation_repair.raw.json`
  - `live_o10_map_server_lifecycle_activation_repair_retry.raw.json`
  - `live_o10_map_server_lifecycle_activation_repair_ros_graph_timeout.raw.json`

本轮未改 `onboard/scripts/o11_nav2_lifecycle.sh`、bringup launch、CMake、硬件配置、UART、WAVE ROVER 或 O5/O6/O7 代码。

## 验证结果

| 命令 | 返回码 | 关键输出 |
|---|---:|---|
| `python3 -m py_compile onboard/scripts/o10_amcl_nav2_runtime_proof.py` | 0 | 编译通过 |
| `python3 -m unittest onboard.tests.test_nav2_runtime_proof_helper` | 0 | `Ran 117 tests in 2.281s`，`OK` |
| `python3 onboard/scripts/o10_amcl_nav2_runtime_proof.py --strict-no-motion --no-base-uart --timeout-s 18 --managed-runtime-opt-in --managed-map-yaml /root/rober/onboard/runtime/maps/trashbot_map.yaml --output-json sprints/2026.07.12_11-54_o3_map_server_lifecycle_activation_repair/artifacts/local_o10_map_server_lifecycle_activation_repair.raw.json` | 2 | macOS 本机 fail-closed：`board_source_preflight_source_failed`、`map_lifecycle_latest_missing`；activation 分类 `map_server_yaml_image_unreadable`；no-motion false 字段保持 |
| `ssh -p 37878 root@192.168.1.11 'mkdir -p /root/rober/onboard/scripts /tmp/rober_o10_artifacts'` | 0 | 远端目录创建/确认成功 |
| `scp -P 37878 onboard/scripts/o10_amcl_nav2_runtime_proof.py root@192.168.1.11:/root/rober/onboard/scripts/o10_amcl_nav2_runtime_proof.py` | 0 | helper 已同步到 true-board |
| true-board 原计划命令，输出到 `/tmp/rober_o10_artifacts/live_o10_map_server_lifecycle_activation_repair.raw.json` | 2 | 该次回退到 `ros2_node_list_timeout`，已保存为 `live_o10_map_server_lifecycle_activation_repair_ros_graph_timeout.raw.json`，不作为 primary |
| true-board retry，命令同上，仅 `--output-json` 改为 `/tmp/rober_o10_artifacts/live_o10_map_server_lifecycle_activation_repair_retry.raw.json` | 2 | primary artifact：`map_server_activate_callback_failed`；随后复制为 canonical `live_o10_map_server_lifecycle_activation_repair.raw.json` |
| `scp -P 37878 root@192.168.1.11:/tmp/rober_o10_artifacts/live_o10_map_server_lifecycle_activation_repair.raw.json .../live_o10_map_server_lifecycle_activation_repair.raw.json` | 0 | 原计划 artifact 已拉取；因该次是 graph timeout，后续用 retry artifact 覆盖 canonical 并保留 timeout 副本 |

Scoped `git diff --check` 在写入本文件后执行，结果见下方最终验收记录。

## True-board Primary Artifact 摘要

Primary artifact:

`sprints/2026.07.12_11-54_o3_map_server_lifecycle_activation_repair/artifacts/live_o10_map_server_lifecycle_activation_repair.raw.json`

关键字段：

- `status=blocked_with_root_cause`
- `proof.root_causes[0].layer=Nav2 map_server lifecycle activation`
- `proof.root_causes[0].reason=map_server_activate_callback_failed`
- `proof.root_causes[0].detail=lifecycle_manager_failed_to_change_state_for_map_server_after_valid_map_readback`
- `proof.map_server_presence_recovery.canonical_classification=map_server_lifecycle_not_active_after_recovery`
- `proof.map_server_presence_recovery.failure_detail=lifecycle_manager_failed_to_change_state_for_map_server`
- `proof.map_server_lifecycle_activation.canonical_classification=map_server_activate_callback_failed`
- `proof.map_server_lifecycle_activation.lifecycle_manager_state_change_result.failed_to_change_state_for_map_server=true`
- `proof.map_server_lifecycle_activation.lifecycle_manager_state_change_result.map_read_after_state_change_failure=true`
- `proof.map_server_lifecycle_activation.map_yaml_pgm_readback.yaml.readable=true`
- `proof.map_server_lifecycle_activation.map_yaml_pgm_readback.yaml.sha256_prefix=1b54312162c67b74`
- `proof.map_server_lifecycle_activation.map_yaml_pgm_readback.pgm.readable=true`
- `proof.map_server_lifecycle_activation.map_yaml_pgm_readback.pgm.sha256_prefix=e88fc83f26dcefba`
- `proof.map_server_lifecycle_activation.map_yaml_pgm_readback.fields.image=trashbot_map.pgm`
- `proof.map_server_lifecycle_activation.map_yaml_pgm_readback.fields.resolution=0.05000000074505806`
- `proof.map_server_lifecycle_activation.map_yaml_pgm_readback.fields.origin=[-5.473848929593875,0.0,0.0]`
- `proof.map_server_lifecycle_activation.map_yaml_pgm_readback.fields.occupied_thresh=0.65`
- `proof.map_server_lifecycle_activation.map_yaml_pgm_readback.fields.free_thresh=0.196`
- `proof.map_server_lifecycle_activation.map_yaml_pgm_readback.fields.mode=null`
- `proof.map_server_lifecycle_activation.map_yaml_pgm_readback.fields.valid_for_map_server=true`
- `proof.map_server_lifecycle_activation.launch_parameters.map_server.parameters.frame_id=map`
- `proof.map_server_lifecycle_activation.launch_parameters.lifecycle_manager.managed_node_list=["map_server","amcl"]`
- `proof.map_server_lifecycle_activation.launch_parameters.lifecycle_manager.service_timeout_s=12.0`
- `proof.map_server_lifecycle_activation.launch_parameters.lifecycle_manager.bond_timeout_s=8.0`
- `proof.map_server_lifecycle_activation.launch_parameters.runtime_environment.RMW_FASTRTPS_USE_SHM=0`
- `proof.board_source_preflight.classification=board_source_preflight_ready`
- `proof.board_source_preflight.cli_ready=true`
- `proof.board_source_preflight.runtime_ready=true`
- `safe_to_control=false`
- `publishes_cmd_vel=false`
- `calls_base_manual=false`
- `robot_control_executed=false`
- `path_generation_attempted=false`
- `delivery_success=false`

Runtime log 关键顺序：

- lifecycle manager starts
- `Configuring map_server`
- `map_server`: `Configuring`
- `map_io`: `Loading yaml file: /root/rober/onboard/runtime/maps/trashbot_map.yaml`
- `map_io`: `Loading image_file: /root/rober/onboard/runtime/maps/trashbot_map.pgm`
- lifecycle manager: `Failed to change state for node: map_server`
- lifecycle manager: `Failed to bring up all requested nodes. Aborting bringup.`
- `map_io`: `Read map ... trashbot_map.pgm: 261 X 113 map @ 0.05 m/cell`

## 失败定位

本轮没有让 `/map_server` lifecycle clean 越过 activation，但已把上一轮 generic
`lifecycle_manager_failed_to_change_state_for_map_server` 收窄到：

`map_server_activate_callback_failed`

证据边界：

- map yaml 与 PGM 都在 true-board 上存在且可读。
- required yaml fields valid；`mode` 在 yaml 文件里缺失，artifact 记录为 optional missing，但 Nav2 log 在加载时显示 `mode: trinary`，因此这不是本轮 primary blocker。
- map_server name/namespace 与 lifecycle manager `managed_node_list` 匹配，不是 name/namespace mismatch。
- map_server process 在 cleanup 前仍 alive，不是 configure 期间进程提前退出。
- lifecycle manager 已进入 map_server configure 并在 valid map readback 后报 state-change failed。

因此下一跳应查 Nav2 map_server transition callback、lifecycle manager service/bond/RPC 时序，或 map_server 在 activate/configure callback 结束时的状态返回，而不是继续把 `/scan`、AMCL、TF 或 planner timeout 写成 primary result。

## 剩余风险

- `/map_server` 仍未证明 active。
- `/map` sample、`/amcl_pose`、dynamic `map->odom`、planner-only path generation 均未恢复。
- true-board ROS graph 仍有一次 `ros2_node_list_timeout` regression，已保存在 secondary artifact，后续复验需要继续区分 graph transient 与 lifecycle activation blocker。
- 本轮未执行 NavigateToPose、未发布 `/cmd_vel`、未调用 `/api/base/manual`、未打开 WAVE ROVER UART；因此没有 HIL、路线执行、送达或 safe-to-control 证据。
- LiDAR `/dev/ttyACM0` read exception 仍可在日志里出现，但本轮不是 primary blocker；若后续变成 `/scan`/LiDAR 主因，需要 Hardware 读取 `docs/vendor/VENDOR_INDEX.md` 后再处理。

## 协同判断

- Product：需要接受本轮为 O3/O1 no-motion blocker 下钻，OKR 百分比不建议提升。
- Hardware：本轮不需要；只有 LiDAR 串口/接线/反馈事实变成 primary blocker 时再介入。
- Autonomy：等 `/map_server` lifecycle clean 后再接 `/map` sample、AMCL pose、dynamic `map->odom` 和 planner-only path gate。
- Full-Stack：本轮不需要。

## 最终验收记录

- `git diff --check -- onboard/scripts/o10_amcl_nav2_runtime_proof.py onboard/scripts/o11_nav2_lifecycle.sh onboard/src/ros2_trashbot_bringup onboard/tests/test_nav2_runtime_proof_helper.py docs/navigation/field_route_evidence_preflight.md docs/navigation/fixed_route_workflow.md sprints/2026.07.12_11-54_o3_map_server_lifecycle_activation_repair` 返回码 `0`，无 whitespace error。
