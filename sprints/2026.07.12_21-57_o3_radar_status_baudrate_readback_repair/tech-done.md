# Tech Done - O3 Radar Status Baudrate Readback Repair

## Sprint Metadata

- sprint_type: epic
- Sprint: `sprints/2026.07.12_21-57_o3_radar_status_baudrate_readback_repair/`
- Owner: `robot-software-engineer`
- Scope: Gate 1 Robot Software 单线闭环，修复 `GET /api/radar/status` baudrate current readback。
- Proof boundary: `software_proof_o3_o1_strict_no_motion_radar_status_readback_only`
- OKR handling: 本轮只修 readback drift，不声明 mission progress，不调整 O5/O1/O6/O7 百分比，不归档 KR。

## 实际改动

- `onboard/scripts/upper_robot_api.py`
  - 新增 `LIDAR_VENDOR_REFERENCE_BAUDRATE=230400` 与 `LIDAR_HISTORICAL_FIELD_BAUDRATE_CANDIDATE=150000`。
  - 新增 `parse_lidar_baudrate()`、`radar_baudrate_from_command_info()` 和 `build_radar_baudrate_readback()`。
  - `radar_status()` 不再 hard-code top-level `baudrate=230400`，改为按 current readback 选择：
    1. 可信 lifecycle/status readback。
    2. driver diagnostics `serial.serial_baudrate` / `serial.baudrate` / `runtime.serial_baudrate`。
    3. `controls.start.command.argv` 或 `controls.scan_proof_refresh.runtime_command.argv` 的 `--serial-baudrate`。
    4. 只有 reference/default `230400` 时 fail-closed 为 `baudrate=null`。
  - 新增响应字段 `baudrate_readback_source`、`baudrate_readback_status`、`baudrate_candidates`、`vendor_reference_baudrate`、`historical_field_baudrate_candidate`。
  - top-level 补齐并固定 `uses_base_uart=false`、`route_execution_success=false`、`hil_pass=false`。
- `onboard/tests/test_upper_robot_api.py`
  - 新增 diagnostics 纠正 stale lifecycle `230400` 的回归测试。
  - 新增 configured start argv `150000` fallback 回归测试。
  - 新增只有 reference `230400` 时 `baudrate=null` 的 fail-closed 回归测试。
- `docs/hardware/board_sensor_stack_smoke.md`
  - 增加 2026-07-12 radar status baudrate readback repair 小节，记录字段语义、选择顺序和 strict no-motion 边界。
- Artifacts:
  - `artifacts/robot_software/board_radar_status_before_deploy.json`
  - `artifacts/robot_software/board_radar_status_after_deploy.json`
  - `artifacts/robot_software/board_radar_status_after_deploy.pretty.json`
  - `artifacts/robot_software/board_radar_status_after_deploy.filtered.txt`

## 验证结果

Python compile:

```text
python3 -m py_compile onboard/scripts/upper_robot_api.py
exit 0
```

Unit tests:

```text
python3 -m unittest onboard.tests.test_upper_robot_api onboard.tests.test_lidar_lifecycle_script
Ran 113 tests in 0.333s
OK (skipped=1)
exit 0
```

Scoped diff check:

```text
git diff --check -- onboard/scripts/upper_robot_api.py onboard/tests/test_upper_robot_api.py docs/hardware/board_sensor_stack_smoke.md sprints/2026.07.12_21-57_o3_radar_status_baudrate_readback_repair/tech-done.md
exit 0
```

本机只读 curl:

```text
curl -s --max-time 5 http://127.0.0.1:8787/api/radar/status | python3 -m json.tool
failed: Expecting value: line 1 column 1 (char 0)
```

定位：本机 127.0.0.1:8787 没有返回 JSON，按 tech-plan 转为板端 SSH 只读验证。

True-board deployment/readback:

```text
ssh -p 37878 root@192.168.1.11 'echo ssh_ok'
ssh_ok

scp -P 37878 onboard/scripts/upper_robot_api.py root@192.168.1.11:/root/rober/onboard/scripts/upper_robot_api.py
exit 0

ssh -p 37878 root@192.168.1.11 'systemctl restart trashbot-upper-robot-api.service && sleep 2 && systemctl is-active trashbot-upper-robot-api.service'
active
```

只读 `/api/radar/status` summary after deploy:

```json
{
  "baudrate": 150000,
  "baudrate_readback_source": "driver_diagnostics_latest.serial.serial_baudrate",
  "baudrate_readback_status": "current_with_reference_conflict",
  "vendor_reference_baudrate": 230400,
  "historical_field_baudrate_candidate": 150000,
  "start_serial_baudrate": "150000",
  "scan_proof_serial_baudrate": "150000",
  "safe_to_control": false,
  "publishes_cmd_vel": false,
  "calls_base_manual": false,
  "uses_base_uart": false,
  "robot_control_executed": false,
  "route_execution_success": false,
  "delivery_success": false,
  "hil_pass": false
}
```

Artifact grep anchors:

```text
board_radar_status_after_deploy.pretty.json:1498:    "baudrate": 150000,
board_radar_status_after_deploy.pretty.json:1499:    "baudrate_readback_source": "driver_diagnostics_latest.serial.serial_baudrate",
board_radar_status_after_deploy.pretty.json:1500:    "baudrate_readback_status": "current_with_reference_conflict",
board_radar_status_after_deploy.pretty.json:1503:            "source": "lifecycle_status_readback.latest_result.baudrate",
board_radar_status_after_deploy.pretty.json:1504:            "baudrate": 230400,
board_radar_status_after_deploy.pretty.json:1511:            "source": "driver_diagnostics_latest.serial.serial_baudrate",
board_radar_status_after_deploy.pretty.json:1512:            "baudrate": 150000,
board_radar_status_after_deploy.pretty.json:1535:    "vendor_reference_baudrate": 230400,
board_radar_status_after_deploy.pretty.json:1536:    "historical_field_baudrate_candidate": 150000,
board_radar_status_after_deploy.pretty.json:2503:                    "--serial-baudrate",
board_radar_status_after_deploy.pretty.json:2548:                    "--serial-baudrate",
board_radar_status_after_deploy.pretty.json:2573:    "calls_base_manual": false,
board_radar_status_after_deploy.pretty.json:2574:    "publishes_cmd_vel": false,
board_radar_status_after_deploy.pretty.json:2575:    "uses_base_uart": false,
board_radar_status_after_deploy.pretty.json:2576:    "route_execution_success": false,
board_radar_status_after_deploy.pretty.json:2577:    "hil_pass": false,
board_radar_status_after_deploy.pretty.json:2578:    "safe_to_control": false,
board_radar_status_after_deploy.pretty.json:2579:    "delivery_success": false
```

## 安全边界

- 未发布 `/cmd_vel`。
- 未调用 `/api/base/manual`。
- 未调用 NavigateToPose。
- 未打开 WAVE ROVER UART 或 `/dev/ttyS5`。
- 未执行 radar stop/start，未 stop/start 当前 LiDAR holder。
- 仅 scp API 脚本并重启 `trashbot-upper-robot-api.service`，随后只读 `/api/radar/status`。

## 剩余风险和 Gate 2

- `lifecycle_status_readback.latest_result.baudrate` 仍报告 reference/stale `230400`，本轮在 API 层用 diagnostics/controls provenance 纠正 top-level；后续若要消除底层 drift，需要另行修 `o1_lidar_lifecycle.sh status`。
- `latest_scan_proof_fresh=false`、`continuous_scan_status=latest_proof_stale_while_lifecycle_running` 仍存在；这不阻塞 baudrate readback gate，但 Algorithm Gate 2 应重新采集 no-motion `/scan` / `/amcl_pose` / dynamic `map->odom` / planner-only path proof。
- Gate 1 已通过，可以进入 Algorithm Gate 2。最窄下一步：复用现有 `150000` lifecycle，不启动第二个 LiDAR driver，重跑 strict no-motion path proof。

## Gate 2 - Algorithm 实际改动

- `onboard/scripts/o10_amcl_nav2_runtime_proof.py`
  - 新增 `--reuse-existing-lidar-lifecycle` 参数。默认仍保持旧 managed runtime 行为；显式传入该参数时，helper 只启动 map_server、AMCL、planner_server 和静态 TF，不再启动第二个 `ros2_trashbot_hardware lidar_driver`。
  - Gate 2 artifact 新增 `managed_lidar_policy`、`managed_lidar_serial_port`、`managed_lidar_serial_baudrate`、`managed_lidar_driver_started_by_helper`，用于证明本轮复用现有 `/dev/ttyACM0 @ 150000` lifecycle。
- `onboard/tests/test_nav2_runtime_proof_helper.py`
  - 新增回归测试，锁定 `--reuse-existing-lidar-lifecycle --managed-lidar-serial-baudrate 150000` 不生成 `lidar_driver` 启动命令，并保留 no-motion Nav2/TF runtime。
- `docs/navigation/field_route_evidence_preflight.md`
  - 补充 21:57 Gate 2 读取规则：Algorithm path proof 必须显式复用现有 LiDAR lifecycle，并回写 no-start policy。
- `docs/navigation/fixed_route_workflow.md`
  - 补充 fixed-route/no-motion 工作流里的 Gate 2 命令边界和 same-run path generation 判定条件。
- `artifacts/algorithm/live_o10_reuse_existing_lidar_lifecycle_path_proof.raw.json`
  - 板端 true-board strict no-motion raw artifact，已从 `/root/rober/onboard/runtime/o3_radar_status_baudrate_readback_repair.raw.json` 拉回。

## Gate 2 验证结果

Python compile:

```text
python3 -m py_compile onboard/scripts/o10_amcl_nav2_runtime_proof.py
exit 0
```

Unit tests:

```text
python3 -m unittest onboard.tests.test_nav2_runtime_proof_helper
Ran 134 tests in 2.305s
OK
exit 0
```

Scoped diff check:

```text
git diff --check -- onboard/scripts/o10_amcl_nav2_runtime_proof.py onboard/tests/test_nav2_runtime_proof_helper.py docs/navigation/field_route_evidence_preflight.md docs/navigation/fixed_route_workflow.md sprints/2026.07.12_21-57_o3_radar_status_baudrate_readback_repair/tech-done.md
exit 0
```

Board deployment check:

```text
ssh -p 37878 root@192.168.1.11 'echo ssh_ok && hostname && date'
ssh_ok
op-z3-b6.home
Sun Jul 12 10:21:56 PM CST 2026

scp -P 37878 onboard/scripts/o10_amcl_nav2_runtime_proof.py root@192.168.1.11:/root/rober/onboard/scripts/o10_amcl_nav2_runtime_proof.py
exit 0

ssh -p 37878 root@192.168.1.11 'python3 -m py_compile /root/rober/onboard/scripts/o10_amcl_nav2_runtime_proof.py'
exit 0
```

True-board strict no-motion command used:

```bash
python3 /root/rober/onboard/scripts/o10_amcl_nav2_runtime_proof.py \
  --strict-no-motion \
  --no-base-uart \
  --managed-runtime-opt-in \
  --reuse-existing-lidar-lifecycle \
  --managed-lidar-serial-port /dev/ttyACM0 \
  --managed-lidar-serial-baudrate 150000 \
  --initialpose-opt-in \
  --path-generation-opt-in \
  --output /root/rober/onboard/runtime/o3_radar_status_baudrate_readback_repair.raw.json
```

True-board command result:

```text
exit 2
status=blocked_with_root_cause
evidence_type=blocked_with_root_cause
managed_runtime_started=true
managed_lidar_policy=reuse_existing_lidar_lifecycle_no_driver_start
managed_lidar_serial_baudrate=150000
managed_lidar_driver_started_by_helper=false
map_server_active=true
amcl_active=true
scan_once_observed=true
map_once_observed=true
amcl_pose_observed=true
initialpose_published=true
path_generation_requested=true
path_generation_attempted=true
path_generated=false
path_generation_boundary=path_generation_python_runtime_unavailable
path_point_count=0
safe_to_control=false
publishes_cmd_vel=false
calls_base_manual=false
uses_base_uart=false
route_execution_success=false
delivery_success=false
hil_pass=false
```

Path generation result:

```json
{
  "attempted": true,
  "ok": false,
  "boundary": "path_generation_python_runtime_unavailable",
  "error": {
    "type": "ImportError",
    "message": "librcl_action.so: cannot open shared object file ... _rclpy_pybind11 ... failed to be imported"
  }
}
```

Artifact anchor grep:

```text
rg -n '"baudrate"|150000|"/scan"|"/amcl_pose"|map_to_odom|path_generation_attempted|path_generated|safe_to_control|publishes_cmd_vel|calls_base_manual|uses_base_uart|route_execution_success|delivery_success|hil_pass' sprints/2026.07.12_21-57_o3_radar_status_baudrate_readback_repair/artifacts/algorithm
exit 0
```

Key anchor lines include:

```text
live_o10_reuse_existing_lidar_lifecycle_path_proof.raw.json:8:  "path_generated": false,
live_o10_reuse_existing_lidar_lifecycle_path_proof.raw.json:9:  "path_generation_attempted": true,
live_o10_reuse_existing_lidar_lifecycle_path_proof.raw.json:41:      "source": "/amcl_pose",
live_o10_reuse_existing_lidar_lifecycle_path_proof.raw.json:1074:        "managed_lidar_serial_baudrate": 150000,
live_o10_reuse_existing_lidar_lifecycle_path_proof.raw.json:3231:      "/scan": {
live_o10_reuse_existing_lidar_lifecycle_path_proof.raw.json:3445:      "map_to_odom": true
```

Board post-run process check:

```text
550851 bash /root/rober/onboard/scripts/o1_lidar_lifecycle.sh __run --serial-port /dev/ttyACM0 --serial-baudrate 150000 ...
550914 /usr/bin/python3 /opt/ros/humble/bin/ros2 run ros2_trashbot_hardware lidar_driver ... -p serial_baudrate:=150000 ...
550922 /usr/bin/python3 /root/rober/onboard/install/ros2_trashbot_hardware/lib/ros2_trashbot_hardware/lidar_driver ... -p serial_baudrate:=150000 ...
```

该 post-run `ps` 只显示既有 `o1_lidar_lifecycle.sh` holder 与其 LiDAR driver；没有本轮 helper 启动的第二个 LiDAR driver，也没有残留 `rober_nav2_localization` runtime 进程组。

## Gate 2 失败定位

- 本轮已经越过 Gate 1 stale readback blocker，且没有回退到 generic `/scan` timeout。
- 同 run artifact 已证明 `/scan`、`/map`、`/amcl_pose`、map_server/amcl lifecycle active、`initialpose_published=true`，并进入 planner-only path generation gate。
- same-run path generation 尚未证明：`path_generation_attempted=true` 但 `path_generated=false`，`path_point_count=0`。
- 下一最窄 blocker 是 `path_generation_python_runtime_unavailable`：板端 path generation Python/action runtime 在 import `rclpy` action binding 时命中 `librcl_action.so` / `_rclpy_pybind11` ImportError。
- Secondary diagnostic：`artifact_closeout.primary_root_cause` 仍保留 `Managed runtime wait: ros2_node_list_timeout`，但本轮下游事实已经足够说明 path gate 卡在 Python action runtime，不应回退到 radar status、baudrate、generic `/scan` 或 map_server lifecycle blocker。

## Gate 2 安全边界

- 未发布 `/cmd_vel`。
- 未调用 `/api/base/manual`。
- 未调用 NavigateToPose；仅尝试 planner-only ComputePathToPose path proof。
- 未打开 WAVE ROVER UART 或 `/dev/ttyS5`。
- 未 stop/start 当前 LiDAR holder。
- 未启动第二个 LiDAR driver；helper 以 `--reuse-existing-lidar-lifecycle` 复用现有 `/dev/ttyACM0 @ 150000` lifecycle。
- 未声明 route execution、delivery、safe-to-control 或 HIL pass。

## Gate 2 剩余风险和下一步

- OKR 处理仍为 `不调整`、`不归档`：本轮是 O3/O1 strict no-motion path gate narrowing，不是 route execution、delivery/operator acceptance、current live HIL 或 production external evidence。
- 下一步最窄 owner 是 Algorithm/Robot Software 交界：修板端 Python/action runtime 的 `librcl_action.so` / `_rclpy_pybind11` import 环境，或给 planner-only path proof 增加不依赖 broken Python action binding 的 ROS2 CLI/action fallback。
- 修复后复跑同一命令，继续保持 `--reuse-existing-lidar-lifecycle`，接受标准是 `path_generation_attempted=true` 且 `path_generated=true`、`path_point_count>0`，同时所有 motion/control/HIL/delivery 字段继续 false。

## Gate 2 返工 - CLI action fallback 与 same-run path proof

### 返工实际改动

- `onboard/scripts/o10_amcl_nav2_runtime_proof.py`
  - 为 `path_generation_python_runtime_unavailable` 增加 `ros2 action send_goal` fallback；fallback 仅调用 `nav2_msgs/action/ComputePathToPose`，不触发 NavigateToPose、controller、BT、`/cmd_vel`、`/api/base/manual`、WAVE ROVER UART 或 `/dev/ttyS5`。
  - 新增 CLI action list 解析、ComputePathToPose goal payload、CLI result path point count 解析和 fallback root cause 分类。
  - 当 path 已在同一 run 成功生成时，把 `Managed runtime wait: ros2_node_list_timeout` 降级为 `root_cause_filtering.suppressed_root_causes`，避免旧 graph wait blocker 覆盖更强的下游 planner 事实。
  - 合并 `planner_lifecycle_recheck` 的 graph visibility 到 `planner_server_observed`，避免 planner 节点已可见但 lifecycle CLI readback 抖动时提前挡住 action fallback。
  - 当 `/amcl_pose` 已同轮观测且 frame 为 `map` 时，将 ComputePathToPose `start` 改为该 AMCL pose，并记录 `start_source=amcl_pose_observed_for_planner_only_start`、`use_start=true`，避免 `use_start=false` 时 planner 回查当前 TF 时间窗产生 extrapolation。
- `onboard/tests/test_nav2_runtime_proof_helper.py`
  - 新增 CLI fallback 成功路径、planner-only goal payload、managed wait demotion、lifecycle recheck graph visibility 和 AMCL pose explicit start 回归测试。
- `docs/navigation/field_route_evidence_preflight.md`
  - 记录 21:57 Gate 2 fallback、150000 lifecycle no-start policy 和 same-run path proof 读取规则。
- `docs/navigation/fixed_route_workflow.md`
  - 记录 fixed-route 侧只能消费 planner-only path evidence，不能升级成 route execution、delivery 或 HIL。
- `artifacts/algorithm/live_o10_reuse_existing_lidar_lifecycle_path_proof_after_fallback.raw.json`
  - 板端 true-board strict no-motion 成功 artifact，已从 `/root/rober/onboard/runtime/o3_radar_status_baudrate_readback_repair_after_fallback.raw.json` 拉回。

### 返工验证结果

Python compile:

```text
python3 -m py_compile onboard/scripts/o10_amcl_nav2_runtime_proof.py
exit 0
```

Unit tests:

```text
python3 -m unittest onboard.tests.test_nav2_runtime_proof_helper
Ran 139 tests in 2.275s
OK
exit 0
```

Board deployment check:

```text
scp -P 37878 onboard/scripts/o10_amcl_nav2_runtime_proof.py root@192.168.1.11:/root/rober/onboard/scripts/o10_amcl_nav2_runtime_proof.py
ssh -p 37878 root@192.168.1.11 'python3 -m py_compile /root/rober/onboard/scripts/o10_amcl_nav2_runtime_proof.py'
remote sha256=ebf7390c529398549ea52f5ef84cf21e782f279b232275cbbfd50e24a8fdc22c
exit 0
```

True-board strict no-motion command used:

```bash
python3 /root/rober/onboard/scripts/o10_amcl_nav2_runtime_proof.py \
  --strict-no-motion \
  --no-base-uart \
  --managed-runtime-opt-in \
  --reuse-existing-lidar-lifecycle \
  --managed-lidar-serial-port /dev/ttyACM0 \
  --managed-lidar-serial-baudrate 150000 \
  --initialpose-opt-in \
  --path-generation-opt-in \
  --output /root/rober/onboard/runtime/o3_radar_status_baudrate_readback_repair_after_fallback.raw.json
```

Final true-board result:

```text
exit 0
status=nav2_no_motion_path_generation_runtime_observed
evidence_type=robot_runtime_material
managed_lidar_policy=reuse_existing_lidar_lifecycle_no_driver_start
managed_lidar_serial_port=/dev/ttyACM0
managed_lidar_serial_baudrate=150000
managed_lidar_driver_started_by_helper=false
scan_once_observed=true
map_once_observed=true
amcl_pose_observed=true
map_server_active=true
amcl_active=true
planner_server_active=true
planner_server_observed=true
path_generation_requested=true
path_generation_attempted=true
path_generation_succeeded=true
path_generated=true
path_generation_boundary=explicit_opt_in_compute_path_to_pose_cli_action_no_motion
path_point_count=21
fallback_used=true
fallback_mode=ros2_cli_action_send_goal
path_goal_request.start_source=amcl_pose_observed_for_planner_only_start
path_goal_request.use_start=true
root_causes=[]
safe_to_control=false
publishes_cmd_vel=false
calls_base_manual=false
uses_base_uart=false
route_execution_success=false
delivery_success=false
hil_pass=false
```

Artifact anchor grep:

```text
rg -n '"baudrate"|150000|"/scan"|"/amcl_pose"|map_to_odom|path_generation_attempted|path_generated|path_point_count|fallback_used|fallback_mode|safe_to_control|publishes_cmd_vel|calls_base_manual|uses_base_uart|route_execution_success|delivery_success|hil_pass' \
  sprints/2026.07.12_21-57_o3_radar_status_baudrate_readback_repair/artifacts/algorithm
exit 0
```

Board post-run process check:

```text
550851 bash /root/rober/onboard/scripts/o1_lidar_lifecycle.sh __run --serial-port /dev/ttyACM0 --serial-baudrate 150000 ...
550914 /usr/bin/python3 /opt/ros/humble/bin/ros2 run ros2_trashbot_hardware lidar_driver ... -p serial_baudrate:=150000 ...
550922 /usr/bin/python3 /root/rober/onboard/install/ros2_trashbot_hardware/lib/ros2_trashbot_hardware/lidar_driver ... -p serial_baudrate:=150000 ...
```

该 post-run `ps` 只显示既有 `o1_lidar_lifecycle.sh` holder 与其 LiDAR driver；没有本轮 helper 启动的第二个 LiDAR driver，也没有残留 `rober_nav2_localization` runtime 进程组。

### 返工失败定位和最终结论

- 首轮 blocker `path_generation_python_runtime_unavailable` 已通过 CLI action fallback 越过；fallback 实际执行，`fallback_used=true`、`fallback_mode=ros2_cli_action_send_goal`。
- 中间一次复验进入 action 但返回 `path_generation_cli_action_empty_path`，最窄原因是 `use_start=false` 让 planner 回查当前 TF 时间窗并触发 extrapolation；已通过同轮 `/amcl_pose` explicit start 修复。
- 最终 artifact 已证明 same-run planner-only path generation：`path_generation_attempted=true`、`path_generated=true`、`path_point_count=21`。
- `root_cause_filtering.suppressed_root_causes` 仍记录 `Managed runtime wait: ros2_node_list_timeout`，但它已被 same-run ComputePathToPose 成功证据降级为 secondary diagnostic，不再是 blocker。

### 返工安全边界和剩余风险

- 本轮未发布 `/cmd_vel`，未调用 `/api/base/manual`，未调用 NavigateToPose，未进入 controller/BT，未打开 WAVE ROVER UART 或 `/dev/ttyS5`。
- 未 stop/start 当前 LiDAR holder，未启动第二个 LiDAR driver；helper 显式复用 `/dev/ttyACM0 @ 150000` lifecycle。
- 未声明 route execution、delivery、safe-to-control 或 HIL pass；所有对应字段继续为 false。
- 剩余风险：这是 planner-only path proof，不是固定路线 replay、Nav2 goal execution、控制层输出、路线执行、送达或 HIL。下一步最窄能力建设是把该 same-run path proof 接到 fixed-route replay gate，仍需保持 route execution 与 delivery claim fail-closed。
