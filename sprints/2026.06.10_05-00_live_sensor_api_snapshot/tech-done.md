# 2026-06-10 05:00 Live Sensor/API Snapshot

## sprint_type

micro

## 本轮目标

在不让底盘运动的前提下，对真实上位机 `root@192.168.1.11:37878`
做一次 live sensor/API snapshot，补齐 SSH、API service、operator report readback、
设备枚举、camera、LiDAR `/scan`、map/route 和 motion gate 的当前事实边界。

本轮采用资料来源：

- `AGENTS.md`
- `OKR.md`
- `docs/vendor/VENDOR_INDEX.md`
- `docs/vendor/waveshare_wave_rover/ugv_rpi/base_ctrl.py`
- `docs/vendor/waveshare_wave_rover/ugv_rpi/config.yaml`
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/json_cmd.h`
- `docs/hardware/field_hil_execution_pack.md`
- `docs/hardware/field_hil_operator_report_template.md`
- `onboard/scripts/upper_robot_api.py`

WAVE ROVER 事实仍按 vendor 文件和既有实板证据处理：UART 是一行 UTF-8 JSON
以 `\n` 结束；vendor Raspberry Pi 示例为 `/dev/ttyAMA0 @ 115200`，但当前
Orange Pi 实板枚举使用 `/dev/ttyS5`；`/dev/ttyACM0` 是当前 LiDAR 设备。

## 实际改动

- 新增 `sprints/2026.06.10_05-00_live_sensor_api_snapshot/artifacts/`，
  保存远端只读采集结果和 camera frame 样本。
- 新增本文件，记录 live sensor/API snapshot 证据、失败定位和剩余风险。
- 更新 `docs/hardware/board_sensor_stack_smoke.md`，同步本轮 no-motion live snapshot
  结果和下一步现场 HIL gate。

## 远端采集证据

artifact 根目录：

- `sprints/2026.06.10_05-00_live_sensor_api_snapshot/artifacts/remote_capture/`

关键文件：

- `ssh_service_status.log`
- `device_enumeration.log`
- `api/operator_report_get.json`
- `api/camera_health.json`
- `api/camera_devices.json`
- `api/radar_status.json`
- `api/radar_scan_proof_latest.json`
- `api/map_list.json`
- `api/map_proof_latest.json`
- `api/nav2_status.json`
- `api/nav2_proof_latest.json`
- `camera/camera_metrics.json`
- `camera/camera_frame_video1.jpg`
- `ros/topic_list_retry.log`
- `ros/scan_once.log`
- `map_route/recent_map_route_artifacts.log`
- `motion_gate/no_motion_gate_readback.txt`

### SSH / API service

`ssh_service_status.log` 显示 SSH 可达，远端主机为 `op-z3-b6.home`，
采集时间 `2026-06-10T04:22:26+08:00`。`trashbot-upper-robot-api.service`
为 `active (running)`，主进程命令包含：

```text
python3 /root/rober/onboard/scripts/upper_robot_api.py --host 0.0.0.0 --port 8787 --camera-base-url http://127.0.0.1:8088 --base-port /dev/ttyS5 --base-baudrate 115200 --max-speed 0.12
```

`/api/operator/report` readback 返回 HTTP `404`，原因是
`runtime/operator_report_latest.json` 缺失；但 guard 字段符合预期：
`operator_report_material_only=true`、`readback_sends_commands=false`、
`sends_motion_commands=false`、`opens_serial=false`、`hil_pass=false`、
`safe_to_control=false`、`delivery_success=false`。

### 设备枚举

`device_enumeration.log` 显示：

```text
/dev/ttyACM0
/dev/ttyS5
/dev/video0
/dev/video1
/dev/video2
/dev/serial/by-id/usb-STC_STC_USB_Serial-if00 -> ../../ttyACM0
USB Composite Device: DV20 USB  (usb-5310000.usb-1):
    /dev/video1
    /dev/video2
```

结论：`/dev/video1` 仍是 DV20 USB 的 capture 候选；`/dev/ttyS5` 和
`/dev/ttyACM0` 当前存在，但本轮未打开 `/dev/ttyS5` 写 UART。

### Camera

`camera/camera_metrics.json` 显示 OpenCV 成功读取 `/dev/video1` 一帧，并保存到
`camera/camera_frame_video1.jpg`：

```json
{
  "selected_device": "/dev/video1",
  "read_ok": true,
  "width": 640,
  "height": 480,
  "mean": 0.9961740451388889,
  "std": 1.5225192245593269,
  "min": 0,
  "max": 8,
  "non_black_ratio": 0.0,
  "non_dark_ratio": 0.0,
  "edge_count": 0,
  "visible_content_proven": false
}
```

结论：camera device read 仍为真，但 frame 近黑，`visible_content_proven=false`。
本轮不修改 v4l2 持久配置。

### LiDAR / `/scan`

`api/radar_status.json` 的 latest artifact readback 显示历史/latest LiDAR proof
存在，`/dev/ttyACM0` 存在，API readback 中 `latest_scan_proof_state` 为
`scan_once_hz_raw_packet_tf_observed`，`latest_scan_hz_average_rate_hz=277.908`，
且 `sends_motion_commands=false`。

但本轮 live ROS graph 只读结果不同：

```text
/amcl_pose [geometry_msgs/msg/PoseWithCovarianceStamped]
/map [nav_msgs/msg/OccupancyGrid]
/parameter_events [rcl_interfaces/msg/ParameterEvent]
/rosout [rcl_interfaces/msg/Log]
/trashbot/waypoints [ros2_trashbot_interfaces/msg/WaypointList]
```

`ros/scan_once.log` 显示：

```text
Unknown topic '/scan'
WARNING: topic [/scan] does not appear to be published yet
Could not determine the type for the passed topic
```

结论：本轮不能证明当前 live `/scan` 正在发布；只证明 API 内有历史/latest
LiDAR proof artifact，且 `/dev/ttyACM0` 当前枚举存在。按本轮约束，未启动会接触
底盘或扩大运行面的 ROS bringup。

### Map / route

`api/map_list.json` 显示 `/root/rober/onboard/runtime/maps` 存在，包含：

- `/root/rober/onboard/runtime/maps/trashbot_map.yaml`
- `/root/rober/onboard/runtime/maps/trashbot_map.pgm`

`map_route/recent_map_route_artifacts.log` 只找到 2026-06-05 的
`map_lifecycle_latest.json`、`trashbot_map.yaml` 和 `trashbot_map.pgm`；
未找到本轮或近期真实移动的 `route.csv`、keyframe 或同轮 manifest。

`api/nav2_status.json` 显示 `status=not_proven`，latest Nav2 proof 为
`blocked_with_root_cause`，`latest_path_generated=false`，
`latest_scan_consumed=false`，`delivery_success=false`。

结论：map artifact 存在，但 `real_route_map_proven=false`；本轮没有真实 route/map
移动证据，不能提升 Nav2、固定路线或送达闭环状态。

### Motion gate

`motion_gate/no_motion_gate_readback.txt` 记录：

```text
No /cmd_vel published. No direct T=1/T=13 sent. No manual/control/nav motion endpoint invoked.
Skipped endpoints: /api/base/manual, /api/base/stop, /api/base/status, /api/radar/start, /api/radar/scan-proof/refresh, /api/map/start, /api/map/proof/refresh, /api/nav2/start, /api/nav2/proof/refresh.
/api/base/status skipped because current implementation sends non-motion T=130 feedback readback on /dev/ttyS5; this no-motion snapshot avoids UART writes entirely.
```

本轮 no motion command 边界成立：没有发布非零 `/cmd_vel`，没有 direct UART
`T=1`/`T=13`，没有调用 manual/control/nav motion endpoint，也没有调用会启动
LiDAR/map/Nav2 runtime 的 refresh/start endpoint。

## Proof 状态

| proof | 本轮状态 | 说明 |
| --- | --- | --- |
| SSH reachable | true | `root@192.168.1.11:37878` 可达，service status 已采集 |
| API service active | true | `trashbot-upper-robot-api.service` active |
| `/api/operator/report` readback | boundary | HTTP 404 missing latest artifact；guard 字段 fail-closed |
| `/dev/video*` | true | `/dev/video0/1/2` 存在，`/dev/video1` 为 DV20 USB |
| `/dev/ttyS5` | true | 当前枚举存在；本轮未写 UART |
| `/dev/ttyACM0` | true | 当前枚举存在，serial symlink 指向它 |
| camera frame read | true | `/dev/video1` OpenCV read 成功 |
| `visible_content_proven` | false | frame 近黑，`non_dark_ratio=0.0`、`edge_count=0` |
| live `/scan` topic | false | 当前 ROS graph 无 `/scan` |
| latest LiDAR API artifact | boundary | 历史/latest proof loaded，不等于当前 live `/scan` |
| `real_route_map_proven` | false | 只有旧 map yaml/pgm，未见真实移动 route/keyframe |
| `physical_motion_lidar_delta_proven` | false | 本轮无运动，不做 delta |
| `wheel_feedback_lr_nonzero_proven` | false | 本轮未采底盘运动/反馈窗口 |
| `delivery_success` | false | 无导航、路线执行或投放闭环 |

## 验证结果

已运行：

```bash
git status --short --branch --untracked-files=all
rg -n "live sensor|SSH|/api/operator/report|/dev/video|/dev/ttyS5|/dev/ttyACM0|/scan|visible_content_proven|physical_motion_lidar_delta_proven|wheel_feedback_lr_nonzero_proven|real_route_map_proven|delivery_success|no motion command" docs/hardware/board_sensor_stack_smoke.md sprints/2026.06.10_05-00_live_sensor_api_snapshot/tech-done.md
find sprints/2026.06.10_05-00_live_sensor_api_snapshot/artifacts -maxdepth 3 -type f | sort
git diff --check
```

验证日志见最终聊天摘要；本文件写入后已完成 `rg`、artifact `find` 和
`git diff --check`。

## 失败定位

- camera：`/dev/video1` 可打开可读，但 frame 仍为黑场，`max=8`、`edge_count=0`。
  这更像现场镜头盖/保护膜/遮挡/朝向/补光/相机本体问题，不能靠本轮远端只读命令翻证据。
- LiDAR：API latest proof artifact 仍可读，但当前 live ROS graph 没有 `/scan`。
  本轮按 no-motion 约束没有启动 LiDAR runtime，因此只能记录边界。
- route/map：已有旧 map 文件，但没有本轮或近期真实移动 route/keyframe/manifest；
  不能证明真实路线或地图质量。
- operator report：latest artifact 缺失，readback HTTP 404；需要现场人员按模板提交。

## 剩余风险

- `visible_content_proven=false`，下一步现场必须检查镜头盖、保护膜、遮挡、朝向和补光。
- `physical_motion_lidar_delta_proven=false`，本轮没有运动，不能证明物理位移。
- `wheel_feedback_lr_nonzero_proven=false`，本轮避免 UART 写入，未刷新 `T=1001` 运动窗口。
- `real_route_map_proven=false`，缺真实移动 route、keyframe、manifest 与外部视频对齐。
- `delivery_success=false`，未进入导航、投放或返回闭环。
- 下一步现场 HIL 前，仍必须按 `docs/hardware/field_hil_execution_pack.md` 的 gate：
  operator report、外部视频、camera 可见性、stop gate、LiDAR scan、feedback 和清场全部通过后，
  才能讨论任何受控运动。
