# O3 ROS2 CLI Source Probe Repair Tech Done

## Sprint Metadata

- sprint_type: epic
- Sprint: `sprints/2026.07.11_19-46_o3_ros2_cli_source_probe_repair/`
- Owner: `robot-algorithm-engineer`
- Finished at: `2026-07-11 20:18:12 CST`
- Scope boundary: no-motion Algorithm helper repair; no WAVE ROVER, ESP32, UART, launch hardware defaults, O6/O7 UI, cloud relay, phone, or PC touchpoint changes.

## 自主能力目标和本轮抓手

本轮目标是修复 O3 no-motion live helper 对 board sourced shell / ROS2 CLI 的泛化误判。抓手是把原来一条 `source ...; command -v ros2` 的黑盒 preflight 拆成 source、PATH/which、CLI invocation、Python/rclpy 四层 artifact 字段和单测，让 `ros2_cli_ok=false` 时能落到更窄分类；如果 ROS2 CLI 实际可用，则进入 lifecycle、TF、topic、path generation 的下一层 fail-closed 证据。

## 实际改动

- `onboard/scripts/o10_amcl_nav2_runtime_proof.py`
  - 新增 `board_source_stage_probe_command()`，单独记录 `/opt/ros/humble/setup.bash`、workspace setup、`cd` 的 exists/sourced/returncode/elapsed。
  - 新增 `board_cli_layer_probe_command()`，分别记录 `command -v ros2`、`type -a ros2`、`which ros2`、`ros2 --help >/dev/null`，并输出 `path_lookup` 与 `cli_invocation` 分层摘要。
  - `board_source_preflight()` 新增 `source_stage_ok`、`ros2_cli_path_ok`、`ros2_cli_invocation_ok`、`ros2_cli_ok`、`rclpy_import_ok`、`python_executable`、`rclpy_file`、`sys_path_head` 等字段。
  - classification 拆成 `board_source_preflight_source_failed`、`board_source_preflight_source_timeout`、`board_source_preflight_ros2_cli_path_missing`、`board_source_preflight_ros2_cli_which_timeout`、`board_source_preflight_ros2_cli_invocation_timeout`、`board_source_preflight_ros2_cli_invocation_failed`、`board_source_preflight_ready` 等更窄结果。
  - managed runtime 启动前先执行 board source preflight，避免 Nav2 进程负载污染 source/PATH/CLI 诊断。
  - `/initialpose --verbose` 订阅数补充探针改为 skipped 记录，避免该附加 CLI probe 卡住 final artifact。
  - 下游 path generation 的 ROS2 前置失败原因从旧的 `ros2_command_unavailable_after_bash_source` 收敛为 `ros2_cli_not_ready_for_path_generation`。
- `onboard/tests/test_nav2_runtime_proof_helper.py`
  - 增加 source/PATH/CLI invocation/rclpy 分层字段和 timeout 常量锁定。
  - 增加 source timeout、ros2 path missing、CLI invocation timeout 的单测。
  - 增加 `/initialpose --verbose` 不再执行的回归断言。
- `docs/navigation/field_route_evidence_preflight.md`
  - 记录 19:46 后 live artifact 读取顺序：source stage -> PATH/which -> CLI invocation -> Python/rclpy。
  - 标注旧 `ros2_command_unavailable_after_bash_source` / 泛化 `board_source_preflight_ros2_cli_unavailable` 只作为历史结论。
- `docs/navigation/fixed_route_workflow.md`
  - 同步 no-motion fixed route preflight 的新分层字段和 path generation 前置判定。
- `sprints/2026.07.11_19-46_o3_ros2_cli_source_probe_repair/artifacts/local_o10_ros2_cli_source_probe_repair.raw.json`
  - 本机 macOS fail-closed artifact。
- `sprints/2026.07.11_19-46_o3_ros2_cli_source_probe_repair/artifacts/live_o10_ros2_cli_source_probe_repair.raw.json`
  - 板端 partial/interrupted artifact。

接口影响：artifact schema 仅在 `proof.board_source_preflight` 下向后兼容扩展；no-motion safety 字段保持 false。

## 验证结果

```bash
python3 -m py_compile onboard/scripts/o10_amcl_nav2_runtime_proof.py
```

- Exit code: `0`
- 关键输出：无输出，语法检查通过。

```bash
python3 -m unittest onboard.tests.test_nav2_runtime_proof_helper
```

- Exit code: `0`
- 关键输出：

```text
Ran 65 tests in 2.221s
OK
```

```bash
python3 onboard/scripts/o10_amcl_nav2_runtime_proof.py --output sprints/2026.07.11_19-46_o3_ros2_cli_source_probe_repair/artifacts/local_o10_ros2_cli_source_probe_repair.raw.json
```

- Exit code: `2`
- 这是预期的本机 fail-closed：当前 macOS 本机没有 `/opt/ros/humble/setup.bash` 和 `/root/rober/onboard/install/setup.bash`。
- artifact 关键字段：
  - `status=blocked_with_root_cause`
  - `proof.board_source_preflight.classification=board_source_preflight_source_failed`
  - `source_stage.ros_setup.exists=false`
  - `ros2_cli_ok=false`
  - `rclpy_import_ok=false`
  - `path_generation_requested=false`
  - `path_generated=false`
  - `safe_to_control=false`

```bash
scp -P 37878 onboard/scripts/o10_amcl_nav2_runtime_proof.py root@192.168.1.11:/root/rober/onboard/scripts/o10_amcl_nav2_runtime_proof.py
```

- Exit code: `0`
- 关键输出：无输出，板端 helper 更新成功。

```bash
ssh -p 37878 root@192.168.1.11 'cd /root/rober/onboard && python3 scripts/o10_amcl_nav2_runtime_proof.py --timeout-s 18 --managed-runtime-opt-in --managed-map-yaml /root/rober/onboard/runtime/maps/trashbot_map.yaml --initialpose-opt-in --path-generation-opt-in --output /root/rober/onboard/runtime/nav2_lifecycle_latest_19_46.json'
```

- Exit code: `255`
- 结果：命令未自然收口；本地 SSH 会话在超过 helper proof 窗口后被中断，板端本轮 helper PID/PGID `476074` 和 managed runtime PGID `476166` 被限定清理。
- 影响：live artifact 是 `interrupted_before_final_artifact`，不是 final artifact；但已经保留了 source/PATH/CLI/rclpy 分层、部分 lifecycle/topic/TF 读数和中断 root cause。
- 板端残留检查：
  - `ps ... awk '$3==476074 || $3==476166 {print}'` 后续无输出，本轮进程组已清理。

```bash
ssh -p 37878 root@192.168.1.11 'cat /root/rober/onboard/runtime/nav2_lifecycle_latest_19_46.json' > sprints/2026.07.11_19-46_o3_ros2_cli_source_probe_repair/artifacts/live_o10_ros2_cli_source_probe_repair.raw.json
```

- Exit code: `0`
- 关键输出：无输出，live partial artifact 已拉取到 sprint artifacts。

## Live Artifact 结论

`live_o10_ros2_cli_source_probe_repair.raw.json` 证明本轮已修复前两轮的泛化 ROS2 CLI 误判：

- `status=interrupted_before_final_artifact`
- `last_phase=interrupted`
- `last_successful_phase=graph_discovery`
- `proof.board_source_preflight.classification=board_source_preflight_ready`
- `proof.board_source_preflight.ros2_cli_ok=true`
- `proof.board_source_preflight.rclpy_import_ok=true`
- `source_stage_ok=true`
  - ROS setup exists/sourced: `true/true`
  - workspace setup exists/sourced: `true/true`
  - source elapsed: `2979ms`
- PATH/which:
  - `command -v ros2` ok, `/opt/ros/humble/bin/ros2`, `15ms`
  - `type -a ros2` ok, `/opt/ros/humble/bin/ros2`, `14ms`
  - `which ros2` ok, `/opt/ros/humble/bin/ros2`, `16ms`
- CLI invocation:
  - `ros2 --help >/dev/null` ok, `2604ms`
- Python/rclpy:
  - `python_executable=/usr/bin/python3`
  - `python_version=3.10.12`
  - `rclpy_file=/opt/ros/humble/local/lib/python3.10/dist-packages/rclpy/__init__.py`

下游读数：

- packages: `ros2_trashbot_bringup`、`ros2_trashbot_nav`、`nav2_map_server`、`nav2_amcl`、`nav2_lifecycle_manager` 均为 true。
- graph discovery: 已到达并成功。
- lifecycle/topic:
  - `/map_server` lifecycle get 曾成功。
  - `/amcl` lifecycle get 超时。
  - `/scan`、`/map`、`/odom` echo 均 returncode `124` 或未观测消息。
- TF/root causes:
  - `/amcl_pose_once_not_observed`
  - `map_to_odom_not_observed`
  - `map_to_base_link_blocked_by_missing_map_to_odom`
- path generation:
  - `path_generation_requested=true`
  - `path_generation_attempted=false`
  - `path_generated=false`
  - `path_generation_succeeded=false`
  - 原因：localization/TF 前置未满足且 helper 未 final 收口。
- no-motion safety:
  - `safe_to_control=false`
  - `sends_motion_commands=false`
  - `publishes_cmd_vel=false`
  - `calls_base_manual=false`
  - `robot_control_executed=false`
  - `route_execution_success=false`
  - `delivery_success=false`
  - `hil_pass=false`
  - `uses_base_uart=false`

## 失败定位

本轮不再 blocked 在 `board_source_preflight_ros2_cli_unavailable` 或 `ros2_command_unavailable_after_bash_source`。板端分层显示 source、PATH/which、CLI invocation、rclpy 都可用。

新的卡点在 source preflight 之后：

1. helper 进入 managed Nav2 runtime 与 ROS graph probing；
2. lifecycle/topic/TF 读数显示 `/amcl_pose` 未出现、`map->odom` 未观测；
3. helper 后续 ROS graph/topic/lifecycle probes 没有在本轮命令窗口内自然 final，最终被记录为 `sigterm_before_final_artifact`。

因此，本轮是 source/CLI blocker repair + 下一层 AMCL/TF/graph timeout 暴露，不是 path generation success。

## 数据、样本或调试输出变化

- 新增本机 artifact：`artifacts/local_o10_ros2_cli_source_probe_repair.raw.json`
  - 用于证明本机缺 ROS setup 时的 source 层 fail-closed 分类。
- 新增板端 artifact：`artifacts/live_o10_ros2_cli_source_probe_repair.raw.json`
  - 用于证明板端 source/PATH/which/CLI invocation/rclpy 全部通过，并保留 downstream interrupted partial。
- 文档已同步说明读取这些字段时不得把 `rclpy_import_ok=true` 当成 `ros2_cli_ok=true` 的替代证据。

## 剩余风险

- live artifact 不是 final artifact；它只能证明 ROS2 CLI preflight 修复和 downstream 卡点暴露，不能证明 lifecycle/path generation 完成。
- 板端仍有历史 ROS2/managed runtime 残留进程，不属于本轮 PGID；本轮只清理了本次启动的 PID/PGID，未扩大到历史进程。
- path generation 仍未尝试成功，`path_generated=false`，不应提升 OKR 百分比。
- 下一轮应把 downstream ROS graph probes 继续分层和限时，重点处理 `/amcl` lifecycle timeout、`/scan`/`/map`/`/odom` echo 124、`map->odom` 未观测，以及 helper final artifact 的有界收口。

## Product Closeout 建议

需要 Product owner 更新 `side2side_check.md` 和 `final.md`：本轮可收口为 “ROS2 CLI source probe repair completed; downstream AMCL/TF/graph timeout exposed”。

不建议 Algorithm owner 修改 `OKR.md` 或 `docs/process/okr_progress_log.md`：本轮没有 same-run `path_generated=true`、route execution、delivery success、HIL 或生产外部证据，OKR 百分比应保持不变。
