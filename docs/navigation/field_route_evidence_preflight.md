# Field Route Evidence Preflight

`onboard/scripts/field_route_evidence_preflight.py` 是现场路线证据采集前的预检入口。它只生成 JSON evidence packet、只读探测 ROS2/SSH/topic 状态，并输出下一步 map、route、keyframe、rosbag、replay 采集命令模板；它不是路线成功、送达成功或 Nav2 实跑通过证明。

## 本地 dry-run

在 macOS 开发机、无 ROS2、无真实 SSH 时也应稳定运行：

```bash
python3 onboard/scripts/field_route_evidence_preflight.py \
  --mode local \
  --dry-run \
  --output /tmp/trashbot_field_preflight.json
```

dry-run 输出状态固定为 `dry_run_template_only_not_proven`，并保持：

- `not_proven=true`
- `delivery_success=false`
- `primary_actions_enabled=false`

## 上位机或本机真实预检

在已经 source ROS2 工作区的上位机上运行：

```bash
python3 onboard/scripts/field_route_evidence_preflight.py \
  --mode local \
  --output "$HOME/.ros/trashbot_runs/field_preflight.json"
```

通过 SSH 从开发机探测上位机：

```bash
python3 onboard/scripts/field_route_evidence_preflight.py \
  --mode ssh \
  --ssh-target root@192.168.1.11 \
  --ssh-port 37878 \
  --timeout-s 5 \
  --output /tmp/trashbot_field_preflight_ssh.json
```

从 2026-06-09 的 board bringup blocker 修复开始，SSH 模式下所有远端 ROS2 命令都通过
`bash -lc` 执行，并先 source：

- `/opt/ros/humble/setup.bash`
- `/root/rober/onboard/install/setup.bash`（优先）
- 若不存在，再回退到脚本内候选 workspace setup

这样做是为了修复此前 `command -v ros2` / `ros2 topic list` 在非登录 SSH shell 中的假阴性
`blocked_ros2_cli_missing`。

SSH 不可达时，工具仍会写出 JSON，状态为 `blocked_ssh_unreachable`。这份 JSON 只能证明预检入口可用和网络 blocker 已分层，不能证明现场路线材料已经产生。

## JSON contract

输出 schema 为 `trashbot.board_field_evidence_preflight.v1`，关键字段包括：

- `status`
- `source`
- `mode`
- `dry_run`
- `generated_at`
- `target`
- `checks`
- `commands`
- `next_required_evidence`
- `blocked_reason`
- `not_proven`
- `delivery_success=false`
- `primary_actions_enabled=false`

失败状态采用 fail closed 分层：

- `blocked_ssh_unreachable`
- `blocked_ros2_cli_missing`
- `blocked_setup_missing`
- `blocked_trashbot_packages_missing`
- `blocked_required_topics_missing`
- `blocked_topic_smoke_failed`
- `ready_for_live_route_capture_not_proven`
- `dry_run_template_only_not_proven`

`checks.setup_candidates.candidates` 现在也会优先列出 `/root/rober/onboard/install/setup.bash`，
便于现场确认真实上位机工作区是否已完成 build 并可被 SSH 采样。

## 安全边界

工具不发布 `/cmd_vel`，不启动运动任务，不修改 WAVE ROVER、ESP32、UART、串口、底盘协议或 launch 默认硬件参数。命令输出进入 JSON 前会做长度裁剪和常见凭证脱敏，避免把 token、password、private key 片段带入证据包。

真实路线验收仍需要补齐上位机 SSH 可达、ROS2 topic smoke、`map.yaml`、`route.csv`、`keyframes/`、`route_bag/` 或 fixed-route replay JSONL。

## 2026-06-09 实板 topic gate 补充

对 `root@192.168.1.11:37878` 的短时 bringup smoke 说明，当前 `ros2_trashbot_bringup/bringup.launch.py` 只覆盖基础硬件桥、地图记录、航点、行为和可选相机，不包含：

- `lidar_driver`
- `robot_state_publisher`
- `static_transform_publisher`

因此：

1. 仅运行当前 `bringup.launch.py` 时，`/scan` 缺失不能直接判定为 LiDAR 硬件坏；更常见原因是该 launch 根本没有把 LiDAR node 拉起。
2. `/tf_static` 缺失在当前 bringup 下也是预期现象，因为 launch 组成里没有静态 TF 发布者。
3. 2026-06-09 的实板 smoke 还额外暴露：`esp32_bridge` 默认串口仍指向 `/dev/ttyUSB0`，而实板实际观察到的入口是 `/dev/ttyS5` 与 `/dev/ttyACM0`。这会让 topic 观察窗口进一步变差。

所以现场预检里对 `/scan` / `/tf_static` 的 gate 应明确区分：

- `bringup 基础 topic gate`：例如 `/map`、参数面、节点存活。
- `LiDAR no-motion smoke gate`：单独运行 `ros2 run ros2_trashbot_hardware lidar_driver --ros-args -p serial_port:=/dev/ttyACM0` 采样 `/scan`。
- `full field stack gate`：从 2026-06-09 当晚开始，`bringup.launch.py` 已支持 `base_enabled:=false`、`lidar_enabled:=true` 和 `static_laser_tf_enabled:=true` 的 sensor-only 组合；只有显式使用这组参数时，才把 `/scan` 与 `/tf_static` 作为同一条 bringup gate。

推荐的 no-motion full sensor stack gate：

```bash
ros2 launch ros2_trashbot_bringup bringup.launch.py \
  base_enabled:=false \
  lidar_enabled:=true \
  lidar_serial_port:=/dev/ttyACM0 \
  lidar_serial_baudrate:=150000 \
  static_laser_tf_enabled:=true \
  camera_enabled:=true \
  camera_device:=/dev/video1
```

该 gate 仍然只证明 topic 链路，不证明：

- `/dev/ttyS5` 底盘串口冲突已解决；
- `base_link -> laser_frame` 已标定；
- 运动、建图和固定路线已完成 HIL。

## 2026-06-10 no-motion 现场补充

在 `root@192.168.1.11:37878` 上继续执行 no-motion evidence capture 后，现场边界进一步收敛：

1. `topic list` 里可见 `/map`，但 `ros2 topic echo --once /map` 没有拿到消息，额外执行 `ros2 topic info /map` 还会返回 `Unknown topic '/map'`。
2. `/trashbot/save_map` service 虽然存在，但在单独重试时明确返回：

```text
std_srvs.srv.Trigger_Response(success=False, message='No map data received')
```

3. 这说明当前 sensor-only bringup 的 no-motion 组合里，`map_recorder` 只是被启动了；它并不等于现场已经有持续发布的 mapping source。若要收集 `map.yaml`，必须把真实 mapping node（例如 `learn.launch.py` 中的 `slam_toolbox`）明确纳入现场链路。
4. `route_data_recorder` 本轮在板上先失败于 Python 依赖：

```text
ModuleNotFoundError: No module named 'cv_bridge'
```

5. 即使补齐 `cv_bridge`，当前 no-motion sensor-only bringup 依然没有 `/odom`，因此也不会生成有效 `route.csv` 轨迹点。

因此 2026-06-10 这轮现场 no-motion 采集的正确定位应是：

- **已证明**：`/scan`、`/camera/image_raw`、`/tf_static`、短 rosbag、相机单帧 keyframe fallback。
- **未证明**：`map.yaml`、`route.csv`、keyframe manifest、fixed-route replay JSONL。

## 下游 artifact gate

预检 JSON 生成后，使用 `onboard/scripts/field_route_evidence_manifest.py` 继续生成 `trashbot.field_evidence_manifest.v1`。manifest gate 会校验 `map.yaml`、`route.csv`、`keyframes/`、rosbag 和 fixed-route replay JSONL 是否存在且非空，并记录 sha256 或目录摘要。

示例：

```bash
python3 onboard/scripts/field_route_evidence_manifest.py \
  --mode local \
  --artifact-root /tmp/trashbot_field_manifest_fixture_complete \
  --preflight-json /tmp/trashbot_field_preflight_ssh.json \
  --output /tmp/trashbot_field_manifest_complete.json
```

如果 SSH 仍不可达，必须保留 `blocked_ssh_unreachable` 与 `not_proven=true`，但可以用本地完整 fixture 和缺失 fixture 验证 manifest 功能，确保不再次只消费同一 SSH blocker。无论 artifact gate 是否通过，manifest 仍保持 `delivery_success=false` 和 `primary_actions_enabled=false`，直到真实现场路线和送达验收另行证明。
