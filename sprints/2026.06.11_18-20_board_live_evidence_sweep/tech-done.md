# sprint_type: micro

## 本轮目标与边界

本轮在真实上位机 `root@192.168.1.11:37878` 采集 live evidence readback，并只执行安全 no-motion refresh。因为 `/api/operator/report` 的现场运动材料不完整，本轮不执行非 stop motion，不调用 `/api/base/manual`，不发布 `/cmd_vel`。

## 已读资料来源

- `AGENTS.md`
- `OKR.md`
- `docs/vendor/VENDOR_INDEX.md`
- `docs/vendor/waveshare_wave_rover/ugv_rpi/base_ctrl.py`
- `docs/vendor/waveshare_wave_rover/ugv_rpi/config.yaml`
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/json_cmd.h`
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/uart_ctrl.h`
- `docs/hardware/field_hil_execution_pack.md`
- `docs/vision/board_camera_publisher.md`
- `docs/navigation/field_route_evidence_preflight.md`

采用的硬件事实仍以本地 vendor 资料为准：WAVE ROVER 上下位机是 UART newline-delimited UTF-8 JSON；vendor 示例包含 `T=1` 左右轮速度、`T=13` ROS control、`T=130` base feedback request、`T=1001` base feedback；当前实板底盘串口 readback 为 `/dev/ttyS5 @ 115200`，LiDAR readback 为 `/dev/ttyACM0 @ 150000`，这些是本板现场事实，不写成通用默认。

## 实际改动

- 新增本轮 artifact 目录：`sprints/2026.06.11_18-20_board_live_evidence_sweep/artifacts/`
  - `logs/ssh_hostname_date_service.txt`
  - `raw/api_status.json`
  - `raw/camera_health.json`
  - `raw/camera_devices.json`
  - `raw/radar_status.json`
  - `raw/map_proof_latest.json`
  - `raw/nav2_status.json`
  - `raw/operator_report.json`
  - `raw/base_status.json`
  - `raw/radar_scan_proof_refresh.json`
  - `raw/map_proof_refresh.json`
  - `raw/nav2_proof_refresh.json`
  - `raw/base_stop_smoke.json`
  - `raw/post_*` readback JSON 与对应 HTTP code
  - `logs/post_refresh_cleanup_readback.log`
- 更新本文件记录 proven/not_proven 矩阵、验证日志和剩余风险。
- 同步更新：
  - `docs/hardware/field_hil_execution_pack.md`
  - `docs/vision/board_camera_publisher.md`
  - `docs/navigation/field_route_evidence_preflight.md`
- 未改 `onboard/scripts/**`、PC UI、mobile、cloud-relay、factory firmware 或无关文件。

## 验证日志

SSH/service gate：

```text
op-z3-b6.home
Thu Jun 11 05:49:45 PM CST 2026
active
```

Robot API readback HTTP code 全部为 200：

```text
api_status=200
camera_health=200
camera_devices=200
radar_status=200
map_proof_latest=200
nav2_status=200
operator_report=200
base_status=200
base_feedback_samples_latest=200
```

安全 no-motion refresh 与 stop smoke：

```text
radar_scan_proof_refresh_http=200
map_proof_refresh_http=200
nav2_proof_refresh_http=200
base_stop_smoke_http=200
```

关键 readback：

- Radar refresh：`status=refreshed`，`proof_state=scan_once_hz_raw_packet_tf_observed`，`evidence_ref=o1-lidar-scan-proof-1781171493054`，`sends_motion_commands=false`，`sends_base_motion_commands=false`，`uses_base_uart=false`，`robot_control_executed=false`。
- Post radar status：`lifecycle_running=false`，`lifecycle_state=stopped`，`latest_proof_status=scan_once_hz_raw_packet_tf_observed`，`scan_once=true`，`scan_hz=true`，`rate=15.926`，`raw_packet=true`，`tf=true`，`freshness=fresh`。
- Map refresh：`status=map_once_artifact_metadata_observed`，`command_result.ok=true`，`map_once_observed=true`，`map_file_observed=true`，`map_metadata_observed=true`，`sends_motion_commands=false`，`calls_base_manual=false`，`uses_base_uart=false`。
- Post map latest：`evidence_ref=o3-map-lifecycle-1781171513110`，`map_once_observed=true`，`map_file_observed=true`，`map_metadata_observed=true`。
- Nav2 refresh：`status=refreshed`，`proof_state=nav2_no_motion_path_generation_runtime_observed`，`evidence_ref=o10-amcl-nav2-runtime-1781171562670`，`path_generated=true`，`path_generation_succeeded=true`，`path_point_count=31`，`planner_server_active=true`，`publishes_cmd_vel=false`，`calls_base_manual=false`，`uses_base_uart=false`。
- Camera health：`status=ready`，`active_peer_count=0`，`active_frames_read=0`，`safe_to_control=false`，`robot_control_executed=false`。
- Camera devices：`/dev/video0`、`/dev/video1`、`/dev/video2` 均存在；`v4l2-ctl --list-devices` 仍显示 `/dev/video1`、`/dev/video2` 属于 `USB Composite Device: DV20 USB`。
- Base status：`port=/dev/ttyS5`，`baudrate=115200`，`T=1001 observed by this /api/base/status non-motion T=130 readback`，`read_line_count=23`，`parsed_json_count=23`，`blocked_commands_not_sent=["T=1","T=13","T=131","cmd_vel","/api/base/manual"]`。
- Stop smoke：`stop_result.ok=true`，写入 `{"T":1,"L":0,"R":0}`，`bytes_written=20`，`safe_to_control=false`，`delivery_success=false`。
- Cleanup readback：`trashbot-upper-robot-api.service active`；`ps` 未见 `o1_lidar/o3_map/o10_amcl/nav2/slam/lidar_driver/camera_publisher/topic pub/cmd_vel` 残留；`ros2 topic info /cmd_vel` 返回 `Unknown topic '/cmd_vel'`。

## proven / not_proven 矩阵

| 项目 | 结论 | 证据 | 边界 |
| --- | --- | --- | --- |
| SSH/API | proven | hostname/date/service active；所有要求的 API readback HTTP 200 | 只证明当前 LAN/SSH/API 可达 |
| 雷达 live scan proof | proven | refresh 后 `scan_once_hz_raw_packet_tf_observed`，fresh evidence `o1-lidar-scan-proof-1781171493054`，post status rate `15.926Hz` | no-motion；不证明机械标定、运动或避障能力 |
| 摄像头 device/health | proven | camera health ready，`active_peer_count=0`；`/dev/video1` 仍是 DV20 USB UVC capture 节点 | 本轮未打开 WebRTC peer 或采样可见帧；`visible_content_proven=false` 仍成立 |
| 摄像头可见内容 | not_proven | operator report `visible_content_proven=false`，camera artifacts ref 为 `not_attached_no_motion_smoke` | 不能用于路线关键帧、视觉定位或远程可视验收 |
| 地图 no-motion proof | proven | refresh/post latest `map_once_artifact_metadata_observed`，`map_once/map_file/map_metadata=true`，evidence `o3-map-lifecycle-1781171513110` | no-motion runtime artifact；不证明地图质量、真实路线或 Nav2 执行 |
| Nav2 no-motion path proof | proven | refresh `nav2_no_motion_path_generation_runtime_observed`，path generated succeeded，31 points，evidence `o10-amcl-nav2-runtime-1781171562670` | ComputePathToPose/managed runtime proof；未执行路径、未发 `/cmd_vel` |
| Base feedback readback | proven | `/api/base/status` 发送非运动 `T=130`，读到 `T=1001`，23 行 JSON | 不是项目 robot ACK，不证明轮速非零或运动 |
| Stop smoke | proven | `/api/base/stop` 写入 `{"T":1,"L":0,"R":0}` 成功 | stop 写成功不等于 HIL pass 或物理停车视频证明 |
| 非 stop motion | not_executed | operator report 缺 `external_video_recorded`、`visible_content_proven`、`wheel_feedback_lr_nonzero_proven`、`physical_motion_lidar_delta_proven` | fail-closed；未调用 `/api/base/manual`，未发布 `/cmd_vel` |
| Delivery | not_proven | API 固定 `delivery_success=false` | 未做真实路线执行、投放或返回 |

## 失败定位

本轮没有 SSH/API/refresh/stop 的执行失败。运动未执行不是技术失败，而是安全门禁正确拦截：当前 operator report 是 no-motion smoke 材料，`external_video_recorded=false`，`visible_content_proven=false`，`wheel_feedback_lr_nonzero_proven=false`，`physical_motion_lidar_delta_proven=false`，不满足非 stop 点动前置条件。

## 剩余风险与下一步

- 相机仍未证明可见内容；下一步应现场确认镜头遮挡、光照、朝向、USB 摄像头本体，再提交带 frame artifact 的 operator report。
- 运动仍未证明；下一步必须补齐外部视频、清场、急停、可见内容、wheel feedback 非零和 LiDAR delta 材料后，才允许通过 PC/manual proxy 做 exactly one 低速短时 jog 并立即 stop。
- 本轮地图/Nav2 只提升 no-motion proof 新鲜度，不等于真实路线执行、定位稳定、controller 可控或 delivery success。
- `/api/base/status` 可读到 `T=1001`，但轮速非零仍未 proven；不能把 feedback readback 等同于真实运动。
