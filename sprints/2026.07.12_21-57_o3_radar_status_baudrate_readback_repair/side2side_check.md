# Side-by-Side Check - O3 Radar Status Baudrate Readback Repair

## Sprint Metadata

- sprint_type: epic
- Sprint: `sprints/2026.07.12_21-57_o3_radar_status_baudrate_readback_repair/`
- Product owner: `product-okr-owner`
- Product status: accepted as O3/O1 strict no-motion same-run planner-only path proof
- Proof boundary: `software_proof_o3_o1_strict_no_motion_planner_only_path_proof`

## 用户价值和产品北极星

北极星仍是普通手机用户一键发车后，小车能沿固定路线完成可验证送达或给出清楚失败原因。本轮没有交付发车或送达能力；它把真实上位机路线执行前的关键链路从 radar status / baudrate drift 推进到 same-run planner-only path generation success，减少下一轮继续猜 `/scan`、AMCL 或 TF 的成本。

## Side-by-Side 验收

| 验收项 | 20-57 基线 | 21-57 结果 | Product 判断 |
| --- | --- | --- | --- |
| radar status baudrate | `/api/radar/status` top-level 仍报告 `baudrate=230400`，但实际 commands 用 `150000` | `board_radar_status_after_deploy.json` 为 `baudrate=150000`，`baudrate_readback_source=driver_diagnostics_latest.serial.serial_baudrate`，start/scan-proof controls 都含 `--serial-baudrate 150000` | 接受，radar status readback drift 已修复 |
| LiDAR lifecycle policy | 已有 `150000` holder，不能随意 stop/start | `managed_lidar_policy=reuse_existing_lidar_lifecycle_no_driver_start`，`managed_lidar_driver_started_by_helper=false`，`managed_lidar_serial_baudrate=150000` | 接受，未启动第二个 LiDAR driver |
| Localization inputs | 之前只证明 `/scan` once/hz、raw packet、TF，尚未同轮 planner success | `scan_once_observed=true`，`map_once_observed=true`，`amcl_pose_observed=true`，`initialpose_published=true`，`map_to_odom=true` | 接受，同轮 planner 输入条件足够 |
| Path proof | 20-57 无 same-run path generation | `status=nav2_no_motion_path_generation_runtime_observed`，`path_generation_attempted=true`，`path_generated=true`，`path_point_count=21`，`fallback_used=true`，`fallback_mode=ros2_cli_action_send_goal` | 接受为 planner-only path proof |
| Motion / mission safety | 必须继续 fail-closed | `safe_to_control=false`，`publishes_cmd_vel=false`，`calls_base_manual=false`，`uses_base_uart=false`，`route_execution_success=false`，`delivery_success=false`，`hil_pass=false` | 接受，未越过安全边界 |

## OKR 映射和方向判断

- Direction: continue O3/O1 strict no-motion path-to-route lane.
- O1: 保守从约 `93%` 上调到约 `94%`，原因是本轮补齐了之前缺失的 current same-run planner-only path generation success slice。
- O5: 继续约 `85%`，因为本轮没有真实 HTTPS/TLS、公网入口、production DB/queue、worker cutover、OSS/CDN live traffic、真实手机/browser 或 external production evidence。
- O6/O7: 继续约 `93%`，因为本轮尚未产生 live route execution、delivery/operator acceptance 或 production readback。
- KR archive decision: `不归档`。本轮没有完成 current live HIL、Nav2 route execution、delivery success、operator acceptance 或 production external evidence。

## Product Acceptance

Product accepts Gate 1 Robot Software and Gate 2 Algorithm after fallback as a real O3/O1 strict no-motion same-run planner-only path proof.

Accepted evidence:

- `artifacts/robot_software/board_radar_status_after_deploy.json`: `baudrate=150000`，`baudrate_readback_source=driver_diagnostics_latest.serial.serial_baudrate`，start/scan-proof controls 都含 `--serial-baudrate 150000`。
- `artifacts/algorithm/live_o10_reuse_existing_lidar_lifecycle_path_proof_after_fallback.raw.json`: `status=nav2_no_motion_path_generation_runtime_observed`，`evidence_type=robot_runtime_material`。
- Same-run path proof: `scan_once_observed=true`，`map_once_observed=true`，`amcl_pose_observed=true`，`initialpose_published=true`，`map_to_odom=true`，`path_generation_attempted=true`，`path_generated=true`，`path_point_count=21`。
- Fallback proof: `fallback_used=true`，`fallback_mode=ros2_cli_action_send_goal`，`path_generation_boundary=explicit_opt_in_compute_path_to_pose_cli_action_no_motion`，`root_causes=[]`。
- Safety proof: `safe_to_control=false`，`publishes_cmd_vel=false`，`calls_base_manual=false`，`uses_base_uart=false`，`route_execution_success=false`，`delivery_success=false`，`hil_pass=false`。

Rejected scope:

- Not route execution.
- Not NavigateToPose.
- Not controller / BT execution.
- Not `/cmd_vel`.
- Not `/api/base/manual`.
- Not WAVE ROVER UART.
- Not delivery/operator acceptance.
- Not current live HIL.
- Not safe-to-control.
- Not production external evidence.

## 优先级和验收口径

Next P0 owner: `robot-algorithm-engineer` with `robot-software-engineer` support if action/runtime readback regresses.

Next acceptance:

- Keep strict no-motion by default.
- Convert this same-run planner-only path proof into a fixed-route replay gate or route intent proof.
- Do not claim route execution until a Nav2 route/goal execution record exists.
- Do not claim delivery until route execution, dropoff/delivery record, and operator/production readback are present.
- Keep `safe_to_control=false` and `hil_pass=false` until current live HIL acceptance evidence exists.

## 风险、阻塞和证据链缺口

- Planner-only path proof does not prove controller, BT, route execution, wheel motion, delivery, operator acceptance, or production cloud.
- `fallback_mode=ros2_cli_action_send_goal` is acceptable for path proof, but it is not a product motion interface.
- Existing LiDAR lifecycle reuse remains correct; future exclusive baud/USB/power checks must be owned by Hardware and read vendor docs first.
- Next missing evidence chain: fixed-route replay or route intent material -> Nav2 route execution -> delivery/operator acceptance -> current live HIL or production external readback.

## Sprint 文档

Created or updated in Product closeout:

- `sprints/2026.07.12_21-57_o3_radar_status_baudrate_readback_repair/side2side_check.md`
- `sprints/2026.07.12_21-57_o3_radar_status_baudrate_readback_repair/final.md`
- `OKR.md`
- `docs/process/okr_progress_log.md`
