# Board Live Full Stack Evidence Tech Done

## sprint_type: epic

## 实际改动

本轮由 `robot-software-engineer` 继续平台层 bringup 和 evidence manifest 收口。未修改产品代码、launch 默认参数、硬件配置或协议实现。

写入/更新的文件：

- `sprints/2026.06.09_23-00_board-live-full-stack-evidence/artifacts/software_bringup_report.md`
- `sprints/2026.06.09_23-00_board-live-full-stack-evidence/artifacts/software_bringup_raw.log`
- `sprints/2026.06.09_23-00_board-live-full-stack-evidence/artifacts/preflight_ssh.json`
- `sprints/2026.06.09_23-00_board-live-full-stack-evidence/artifacts/field_evidence_manifest.json`
- `sprints/2026.06.09_23-00_board-live-full-stack-evidence/artifacts/pulled_remote_run/field_full_stack_20260609_230304/**`
- `sprints/2026.06.09_23-00_board-live-full-stack-evidence/artifacts/pulled_remote_run/software_bringup_20260609_230745/**`
- `sprints/2026.06.09_23-00_board-live-full-stack-evidence/tech-done.md`
- `sprints/2026.06.09_23-00_board-live-full-stack-evidence/side2side_check.md`
- `sprints/2026.06.09_23-00_board-live-full-stack-evidence/final.md`

## 平台 bringup 结果

远端必须用 `bash` source ROS2 和工作区：

```bash
source /opt/ros/humble/setup.bash
source /root/rober/onboard/install/setup.bash
```

`bringup.launch.py --show-args` 和 `learn.launch.py --show-args` 均成功。远端安装版本已经包含 LiDAR 参数：

- `lidar_enabled:=false`
- `lidar_serial_port:=/dev/ttyACM0`
- `lidar_serial_baudrate:=150000`
- `no_motion_static_odom_tf:=false`，仅 `learn.launch.py`

短时 bringup 使用：

```bash
ros2 launch ros2_trashbot_bringup bringup.launch.py serial_port:=/dev/ttyS5 serial_baudrate:=115200 lidar_enabled:=true
```

短时 session 内成功出现：

- `/scan [sensor_msgs/msg/LaserScan]`，publisher=`lidar_driver`
- `/odom [nav_msgs/msg/Odometry]`，publisher=`esp32_bridge`
- `/battery [sensor_msgs/msg/BatteryState]`，publisher=`esp32_bridge`
- `/imu/data [sensor_msgs/msg/Imu]`，publisher=`esp32_bridge`
- `/cmd_vel [geometry_msgs/msg/Twist]`，subscriber=`esp32_bridge`
- `/map [nav_msgs/msg/OccupancyGrid]`
- `/tf_static [tf2_msgs/msg/TFMessage]`

未出现：

- `/camera/image_raw`
- `/tf`

未执行运动：

- 没有发布 `/cmd_vel`。
- 没有调用 `/api/base/manual`。
- 没有发送直接 vendor `T=1` 或 `T=13`。

## 失败定位

平台层 ROS graph blocker 已从“没有业务 node”推进到“硬件 bridge/LiDAR 可启动，但 full bringup 仍有节点失败和 camera/tf/map artifact 缺口”。

具体失败：

- `waypoint_manager` 缺少 `nav2_simple_commander`：

```text
ModuleNotFoundError: No module named 'nav2_simple_commander'
```

- `task_orchestrator` 参数类型不匹配：

```text
InvalidParameterTypeException: Trying to set parameter 'elevator_assist_target_floor' to '1' of type 'INTEGER', expecting type 'STRING'
```

- `/camera/image_raw` 未注册，当前 bringup 没有给出 ROS camera topic。
- `/tf` 未注册，只有 `/tf_static` 的 `base_link -> laser_frame` 静态变换。
- `/map` topic 存在但未产出 `map.yaml`，不能当作建图完成证据。

## Preflight / Manifest 结果

执行：

```bash
python3 onboard/scripts/field_route_evidence_preflight.py --mode ssh --ssh-target root@192.168.1.11 --ssh-port 37878 --timeout-s 8 --output sprints/2026.06.09_23-00_board-live-full-stack-evidence/artifacts/preflight_ssh.json
```

结果：

- `schema=trashbot.board_field_evidence_preflight.v1`
- `status=blocked_ros2_cli_missing`
- `blocked_reason=blocked_ros2_cli_missing`

解释：脚本用远端默认 shell 直接执行 `command -v ros2`，没有 source ROS2 setup，因此这是脚本环境探测的假阴性；手工 `bash -lc` source 后 ROS2 和 trashbot packages 可用。

执行：

```bash
python3 onboard/scripts/field_route_evidence_manifest.py --mode local --input sprints/2026.06.09_23-00_board-live-full-stack-evidence/artifacts/pulled_remote_run --preflight-json sprints/2026.06.09_23-00_board-live-full-stack-evidence/artifacts/preflight_ssh.json --output sprints/2026.06.09_23-00_board-live-full-stack-evidence/artifacts/field_evidence_manifest.json || true
```

结果：

- `schema=trashbot.field_evidence_manifest.v1`
- `status=blocked_artifacts_missing`
- `gate_pass=false`
- `safe_to_control=false`
- `delivery_success=false`
- `primary_actions_enabled=false`
- `present_artifacts=["rosbag"]`
- `missing_artifacts=["map_yaml","route_csv","keyframes","replay_jsonl"]`

## 四个 Gate 当前状态

| Gate | 状态 | 当前证据 |
| --- | --- | --- |
| 雷达 | 部分通过 | `lidar_driver` 启动，`/scan` 注册并 echo 到 LaserScan 样本。 |
| 摄像头 | blocked | `/camera/image_raw` unknown，未发现 ROS camera driver/topic。 |
| 建图 | blocked | `/map` topic 注册，但没有 `map.yaml`、SLAM save 或 route artifact。 |
| 运动 | blocked | `/cmd_vel` 有 subscriber 且 `/odom` 可观测，但安全 gate 未通过，本轮按要求不发运动命令。 |

## 验证结果

已执行并记录关键输出：

- `git status --short --branch`
- 远端 `bringup.launch.py --show-args`
- 远端 `learn.launch.py --show-args`
- 短时 `bringup.launch.py serial_port:=/dev/ttyS5 serial_baudrate:=115200 lidar_enabled:=true`
- `field_route_evidence_preflight.py --mode ssh`
- `field_route_evidence_manifest.py --mode local`
- `rg -n "雷达|摄像头|建图|运动|/scan|/camera/image_raw|/odom|/tf|map.yaml|route.csv|rosbag|field_evidence_manifest|safe_to_control=false|delivery_success=false|primary_actions_enabled=false" ...`
- `git diff --check`

最终验证：

- `rg` 验收搜索命中 sprint 文档、hardware/algorithm/software reports、preflight、manifest、pulled run evidence，覆盖雷达、摄像头、建图、运动和 fail-closed 字段。
- `git diff --check` 无输出错误。当前 sprint 目录整体仍是 untracked，因此该命令只覆盖已跟踪 diff 的空白检查；artifact 和文档内容已通过显式 `rg` 与 JSON pretty-print 复核。

## 剩余风险

- `nav2_simple_commander` 缺失会阻断 waypoint/nav 相关节点。
- `elevator_assist_target_floor` 参数类型问题会阻断 `task_orchestrator`。
- camera ROS topic 缺失，无法生成 keyframe 或视觉证据。
- 当前 `/odom` 是 bridge 的 ROS-side command integration source；未做真实运动和轮速/里程计校验。
- graph-only bag 不是传感器 bag，manifest 必须保持 fail-closed。
