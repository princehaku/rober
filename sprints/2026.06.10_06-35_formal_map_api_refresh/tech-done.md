# 2026-06-10 06:35 formal API map proof refresh

sprint_type: micro

## 实际改动/部署

- 本地改动：
  - `docs/hardware/board_sensor_stack_smoke.md`
  - `sprints/2026.06.10_06-35_formal_map_api_refresh/tech-done.md`
  - `sprints/2026.06.10_06-35_formal_map_api_refresh/artifacts/**`
- 远端部署：
  - 远端 `root@192.168.1.11:37878` 可达，hostname 为 `op-z3-b6.home`，远端时间为 `Wed Jun 10 04:59:38 AM CST 2026`。
  - `/root/rober` 和 `/root/rober/onboard` 均无 git 元数据，无法用 `git pull --ff-only` 部署到 `acccb06`。
  - 已备份正式 helper 到 `/tmp/rober_o3_map_lifecycle_proof_before_20260610_050003.py`，备份 sha256 为 `f8cffd9830ee66b5344985475c32665184a05a9ed4fb77df3ae21244c184fea3`。
  - 已用本地 `acccb06 Fix map lifecycle laser TF proof` 的 committed script 覆盖 `/root/rober/onboard/scripts/o3_map_lifecycle_proof.py`，覆盖后 sha256 为 `cd40b1a73c1c3c936f8a08ac96fa5b8d7ff15b0ea5c47e4bb2c0452cefa6f2a6`。
  - 正式 helper 已确认包含 `static_laser_tf_enabled:=true` 与 `no_motion_static_odom_tf:=true`。

## 验证结果

远端初始状态：

```text
op-z3-b6.home
Wed Jun 10 04:59:38 AM CST 2026
fatal: not a git repository (or any of the parent directories): .git
119:            "no_motion_static_odom_tf:=true",
```

部署后 helper 检查：

```text
cd40b1a73c1c3c936f8a08ac96fa5b8d7ff15b0ea5c47e4bb2c0452cefa6f2a6  /root/rober/onboard/scripts/o3_map_lifecycle_proof.py
125:            "static_laser_tf_enabled:=true",
126:            "no_motion_static_odom_tf:=true",
```

helper 基础验证：

```text
---PYC_COMPILE---
py_compile_rc:0
---HELP---
usage: o3_map_lifecycle_proof.py [-h] [--output OUTPUT] [--map-dir MAP_DIR]
                                 [--map-name MAP_NAME]
                                 [--serial-port SERIAL_PORT]
                                 [--serial-baudrate SERIAL_BAUDRATE]
                                 [--frame-id FRAME_ID] [--startup-s STARTUP_S]
                                 [--timeout-s TIMEOUT_S]
```

正式 API proof refresh：

```text
POST /api/map/proof/refresh {"timeout_s":60}
HTTP 200
top-level status=not_proven
latest runtime proof status=map_once_artifact_metadata_observed
evidence_ref=o3-map-lifecycle-1781038819987
scan_once_observed=true
map_once_observed=true
map_metadata_observed=true
map_file_observed=true
publishes_cmd_vel=false
calls_base_manual=false
uses_base_uart=false
sends_base_motion_commands=false
delivery_success=false
```

canonical artifact 摘要：

```json
{
  "status": "map_once_artifact_metadata_observed",
  "proof_status": "map_once_artifact_metadata_observed",
  "evidence_ref": "o3-map-lifecycle-1781038819987",
  "scan_once_observed": true,
  "map_once_observed": true,
  "map_metadata_observed": true,
  "map_file_observed": true,
  "publishes_cmd_vel": false,
  "calls_base_manual": false,
  "uses_base_uart": false,
  "sends_base_motion_commands": false,
  "map_metadata": {
    "frame_id": "map",
    "height": 126,
    "resolution": 0.05000000074505806,
    "width": 237
  }
}
```

runtime log 关键片段：

```text
[static_laser_tf]: Spinning until stopped - publishing transform
from 'base_link' to 'laser_frame'
[no_motion_static_odom_tf]: Spinning until stopped - publishing transform
from 'odom' to 'base_link'
[lidar_driver]: LiDAR serial started: /dev/ttyACM0 @ 150000
Registering sensor: [Custom Described Lidar]
```

`GET /api/map/proof/latest`：

```text
endpoint=/api/map/proof/latest
source=map_lifecycle_runtime_artifact
artifact.canonical_path=/root/rober/onboard/runtime/map_lifecycle_latest.json
latest_result.status=map_once_artifact_metadata_observed
status=not_proven
proof_state=not_proven
boundary=software_guard_only_not_real_slam_map_or_nav2_consumption
```

`GET /api/nav2/status`：

```text
status=not_proven
latest_proof_status=blocked_with_root_cause
amcl_nav2_readiness.status=map_inputs_ready_for_no_motion_nav2_collector
source_latest_status=map_once_artifact_metadata_observed
map_yaml_candidates=/root/rober/onboard/runtime/maps/trashbot_map.yaml
map_image_candidates=/root/rober/onboard/runtime/maps/trashbot_map.pgm
publishes_cmd_vel=false
uses_base_uart=false
delivery_success=false
```

serial occupancy：

```text
pre lsof /dev/ttyS5 /dev/ttyACM0: no output
pre fuser -v /dev/ttyS5 /dev/ttyACM0: no output
post lsof /dev/ttyS5 /dev/ttyACM0: no output
post fuser -v /dev/ttyS5 /dev/ttyACM0: no output
final lsof /dev/ttyS5 /dev/ttyACM0: no output
final fuser -v /dev/ttyS5 /dev/ttyACM0: no output
```

本地验证：

```text
git diff --check: passed
rg docs/sprint proof keywords: passed
```

关键 artifacts：

- `sprints/2026.06.10_06-35_formal_map_api_refresh/artifacts/remote_initial_state.log`
- `sprints/2026.06.10_06-35_formal_map_api_refresh/artifacts/remote_helper_backup.log`
- `sprints/2026.06.10_06-35_formal_map_api_refresh/artifacts/remote_helper_deploy.log`
- `sprints/2026.06.10_06-35_formal_map_api_refresh/artifacts/remote_helper_validate.log`
- `sprints/2026.06.10_06-35_formal_map_api_refresh/artifacts/api_map_proof_refresh_response.json`
- `sprints/2026.06.10_06-35_formal_map_api_refresh/artifacts/api_map_proof_refresh_response_pure.json`
- `sprints/2026.06.10_06-35_formal_map_api_refresh/artifacts/api_map_proof_latest_response.json`
- `sprints/2026.06.10_06-35_formal_map_api_refresh/artifacts/api_nav2_status_response.json`
- `sprints/2026.06.10_06-35_formal_map_api_refresh/artifacts/map_lifecycle_latest.json`
- `sprints/2026.06.10_06-35_formal_map_api_refresh/artifacts/map_lifecycle_latest_summary_corrected.json`
- `sprints/2026.06.10_06-35_formal_map_api_refresh/artifacts/remote_post_api_state.log`
- `sprints/2026.06.10_06-35_formal_map_api_refresh/artifacts/remote_final_serial_occupancy.log`
- `sprints/2026.06.10_06-35_formal_map_api_refresh/artifacts/trashbot_map.yaml`
- `sprints/2026.06.10_06-35_formal_map_api_refresh/artifacts/trashbot_map.pgm`

## 失败定位

- 无 helper 部署或 API 执行失败。
- 远端正式 repo 路径没有 git 元数据，所以不能用 `git pull --ff-only`；已按任务边界备份并覆盖单个正式 helper 文件。
- API 外层 `status=not_proven` 不是本轮 map evidence 失败，而是正式 API 的软件护栏：本轮只证明 no-motion `/scan`、`/map`、map metadata 和 map file，不证明地图质量、AMCL/Nav2 runtime、固定路线或 HIL delivery。
- runtime 停止时 `lidar_driver` 和 `map_recorder` 在 SIGINT 关闭路径打印 traceback；最终串口占用为空，也未发现本轮 helper/launch/lidar/slam 残留。

## 剩余风险

- refresh 前 default ROS domain 已有 `/map` 和多组 `waypoint_manager`、`map_recorder`、`task_orchestrator` 进程；无法确认它们是否是上一轮残留，因此本轮只记录，没有清理。
- `static_laser_tf_enabled` 和 `no_motion_static_odom_tf` 仍是 no-motion smoke 拓扑，不是机械外参标定或可导航地图结论。
- `/api/nav2/status` 仍为 `not_proven`；后续还要单独验证地图质量、AMCL/Nav2 lifecycle、fixed route replay/real route 和 delivery_success。
- 本轮没有 Product、Hardware、Autonomy 或 Full-Stack 强协同需求；下一步若要把 map artifact 升级为 Nav2 readiness，需要 Robot Algorithm Engineer 介入地图质量与 AMCL/Nav2 proof。
