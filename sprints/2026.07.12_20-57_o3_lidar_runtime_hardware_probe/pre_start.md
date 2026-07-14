# Pre Start - O3 LiDAR Runtime Hardware Probe

## Sprint Metadata

- sprint_type: epic
- Sprint: `sprints/2026.07.12_20-57_o3_lidar_runtime_hardware_probe/`
- Planned start: `2026-07-12 20:57 CST`
- Product owner: `product-okr-owner`
- P0 owner: `robot-hardware-engineer`
- Secondary support: `robot-software-engineer` only if the helper contract needs a bounded readback change.
- Waiting owner: `robot-algorithm-engineer` waits until `/scan`, `/amcl_pose`, and dynamic `map->odom` are clean enough for planner-only path proof.
- Sprint boundary: O3/O1 strict no-motion LiDAR serial/runtime/wiring diagnosis and artifact only.
- Proof boundary target: `software_proof_o3_o1_strict_no_motion_lidar_runtime_hardware_probe_only`

## 用户价值和产品北极星

产品北极星仍是普通手机用户把垃圾交给小车后，一键发车并得到可验证的送达或失败结果。当前 sprint 不交付用户可见发车能力；它要把 fixed-route delivery 前的最近现场 blocker 从 LiDAR runtime exception 候选推进成可执行修复、配置、接线结论，或产出更窄的 no-motion live artifact。

用户价值是减少现场定位链路的不确定性。只有 `/scan` 能稳定产生样本，AMCL 才可能形成 `/amcl_pose`，dynamic `map->odom` 才可能出现，后续 planner-only path、route execution、delivery/operator evidence 才有进入条件。

## Read First Evidence

- `AGENTS.md`: 硬件、线路、串口、底盘协议、Orange Pi、WAVE ROVER、固件或电气相关任务必须先读 `docs/vendor/VENDOR_INDEX.md`，并保持 strict no-motion 边界。
- `OKR.md`: O5 仍是最低 Objective，约 `85%`；但 O5 缺真实 external production evidence，继续 support-only 不计分。
- `docs/vendor/VENDOR_INDEX.md`: 本轮 Hardware 必须先读的本地硬件事实入口；Orange Pi 串口/电气需要继续打开 Orange Pi manual/schematic；WAVE ROVER/base UART 只允许读资料，不允许打开或使用。
- `sprints/2026.07.12_18-56_o3_lifecycle_active_graph_readback_repair/final.md`: 最近两轮 blocker 扫描的第一轮，primary reason 为 `/scan_reliable_and_best_effort_timeout`。
- `sprints/2026.07.12_19-56_o3_scan_qos_endpoint_readback_split/final.md`: 最近两轮 blocker 扫描的第二轮，primary reason 已收窄为 `/scan_lidar_runtime_exception_after_endpoint_visible_qos_compatible_timeout`，next_owner=`hardware_after_vendor_doc_review`。

## 最近两轮 Blocker 扫描

- 18:56: `/scan_reliable_and_best_effort_timeout`。当时已经证明 `map_server_active=true`、`amcl_active=true`、`managed_runtime_log_lifecycle_readback.clean=true`、`map_once_observed=true`，但 `/scan` 样本仍未读到。
- 19:56: `/scan_lidar_runtime_exception_after_endpoint_visible_qos_compatible_timeout`。上一轮进一步证明 `/scan` endpoint visible/stable、publisher node 为 `lidar_driver`、topic type 为 `sensor_msgs/msg/LaserScan`、QoS compatible，但 BEST_EFFORT / RELIABLE readback 都是 `sample_count=0`，并观察到 `serial.serialutil.SerialException`。
- Product 判断：这不是重复消费同一 blocker。18:56 是 generic sensor-input timeout；19:56 已把 endpoint/QoS/readback 排开一层，转成 Hardware after vendor-doc review 的更窄 LiDAR runtime 诊断。

## OKR Mapping And Direction

- O5：继续约 `85%`，本轮不做 O5 support-only。原因是没有真实公网 HTTPS/TLS、4G/SIM、production DB/queue、worker cutover、OSS/CDN live traffic、真实手机/browser 或 external production evidence；继续 readiness packet、handoff、review、surface、checklist 不产生 `external_artifact_delta`。
- O1/O3：继续 strict no-motion 现场链路。本轮把 LiDAR runtime exception 候选落到 vendor-doc-backed serial/runtime/wiring 诊断，不碰底盘运动。
- O6/O7：继续约 `93%`，等待 live route execution、delivery/operator acceptance 或 production readback；独立 UI/API/readback surface 本轮冻结。
- 方向判断：继续 O3/O1，暂停 O5 support-only；不调整百分比，不归档 KR。若 Hardware 产出 clean `/scan` sample 或更窄 root cause，Product 后续再判断是否进入 Algorithm planner-only path proof。

## 本轮核心抓手

P0 抓手是 Hardware 在 vendor docs 后做 no-motion LiDAR runtime probe：

- 复核 LiDAR driver/runtime 是否实际打开 `/dev/ttyACM0`，并确认该路径没有被其他进程抢占。
- 对比 `150000` vs `230400` baudrate drift：既有导航文档和历史 smoke 出现 `/dev/ttyACM0 @ 150000`，当前 `o1_lidar_lifecycle.sh`、`o1_lidar_ros2_scan_smoke.sh` 与 `o10_amcl_nav2_runtime_proof.py` 默认存在 `230400` 路径。Product 不预判哪个值正确，要求 Hardware 用 vendor docs、现场 readback 和 no-motion smoke 证明。
- 收集 `lidar_driver` diagnostics、raw bytes/empty-read counters、`serial.serialutil.SerialException` message hint、`/scan` sample 或明确的 fail-closed artifact。
- 只允许 LiDAR 串口和 ROS2 scan readback，不允许 WAVE ROVER UART、`/cmd_vel`、`/api/base/manual`、NavigateToPose 或 route execution。

## Strict No-Motion Safety Boundary

This sprint is strict no-motion:

- no `/cmd_vel`.
- no `/api/base/manual`.
- no NavigateToPose.
- no WAVE ROVER UART.
- no `/dev/ttyS5` base UART open.
- no base manual relay.
- no route execution.
- no safe-to-control claim.

Required false fields or equivalent summary:

- `safe_to_control=false`
- `publishes_cmd_vel=false`
- `calls_base_manual=false`
- `uses_base_uart=false`
- `robot_control_executed=false`
- `route_execution_success=false`
- `delivery_success=false`
- `hil_pass=false`

## Required Sprint Documents

This planning pass creates:

- `pre_start.md`
- `prd.md`
- `tech-plan.md`

After Hardware implementation, the owner must update:

- `tech-done.md`

Product acceptance, if implementation completes, must then update:

- `side2side_check.md`
- `final.md`
