# O1 LiDAR Scan Proof Artifact

## 目标

`onboard/scripts/o1_lidar_scan_proof_collector.py` 用于把 O1 LiDAR `/scan`
ready/proof/blocker 写成机器可读 artifact。它服务后续现场复跑和 8787 只读
回放，不替代 ROS2 driver、TF、SLAM/Nav2 或 HIL 验收。

## Vendor 来源

本 artifact 的硬件事实来自：

- `docs/vendor/VENDOR_INDEX.md`
- `docs/vendor/lidar_pkg_ros2-main/README.md`
- `docs/vendor/lidar_pkg_ros2-main/src/lidar_node.cpp`
- `docs/vendor/lidar_pkg_ros2-main/config/lidar_params.yaml`
- `docs/vendor/lidar_pkg_ros2-main/launch/lidar.launch.py`
- `docs/vendor/lidar_pkg_ros2-main/scripts/99-lidar.rules`

已采用的本地 vendor 事实：

- 当前 LiDAR source-of-truth 是 `docs/vendor/lidar_pkg_ros2-main/`，不是历史 ROS1 snapshot。
- ROS2 参考环境是 Humble。
- 参考串口波特率是 `150000`。
- 参考 driver 启动时发送 `A5 60`，退出时发送 `A5 00 A5 65 A5 65`。
- 包同步头是 `0xAA 0x55`。
- ROS2 LaserScan 目标 topic 是 `/scan`。
- raw packet 目标 topic 是 `/lidar/raw_packet`。
- vendor udev 目标是 `/dev/lidar`；当前现场观察候选是 `/dev/ttyACM0` 与 STC by-id。

## 安全边界

collector 默认只读：

- 检查 `/opt/ros/humble/setup.bash`。
- 检查 `/root/rober/onboard/install/setup.bash`。
- 检查 `/dev/lidar`、`/dev/ttyACM0`、`/dev/serial/by-id/usb-STC_STC_USB_Serial-if00` 元数据。
- GET 8787 `/health` 与 `/api/radar/status`。
- 可选写入 JSON artifact。

collector 禁止：

- 不启动 LiDAR driver。
- 不发送 `A5 60`。
- 不打开 `/dev/ttyACM0` 或 `/dev/lidar`。
- 不读取或写入 WAVE ROVER `/dev/ttyS5`。
- 不发送 `T=1/T=13/T=130/T=131`。
- 不发布 `/cmd_vel`。
- 不声明 `safe_to_control=true`、HIL pass 或 delivery success。

只有显式 `--expect-existing-topics` 且 ROS2 runtime ready 时，collector 才会只读
运行：

```bash
ros2 topic echo --once /scan
ros2 topic echo --once /lidar/raw_packet
ros2 topic hz /scan
```

这些命令只观察已有 topic，不启动 driver，不发送底盘控制命令。

## 运行

本地：

```bash
python3 onboard/scripts/o1_lidar_scan_proof_collector.py --once-json --output runtime/lidar_scan_proof_latest.json
```

远端 stdin：

```bash
ssh -p 37878 root@192.168.1.11 'python3 -s - --once-json --output /tmp/o1_lidar_scan_proof_latest.json --timeout-s 3' < onboard/scripts/o1_lidar_scan_proof_collector.py
```

读取已经存在的 ROS2 topic：

```bash
python3 onboard/scripts/o1_lidar_scan_proof_collector.py --once-json --expect-existing-topics --output runtime/lidar_scan_proof_latest.json
```

## Artifact contract

关键字段：

- `schema=trashbot.o1.lidar_scan_proof.v1`
- `proof.status=blocked_or_not_observed | scan_and_raw_packet_observed`
- `proof.scan_once_observed`
- `proof.raw_packet_once_observed`
- `proof.driver_started_by_collector=false`
- `proof.lidar_start_command_sent_by_collector=false`
- `topic_reads.attempted`
- `blockers[].code`
- `blocked_commands_not_sent[]`
- `safe_to_control=false`
- `sends_commands=false`
- `sends_motion_commands=false`
- `robot_control_executed=false`
- `hil_pass=false`

8787 只读回放：

```text
GET /api/radar/scan-proof/latest
```

该 endpoint 只读取 `ROBER_LIDAR_SCAN_PROOF_ARTIFACT_PATH` /
`--lidar-scan-proof-artifact-path` 指向的 JSON，默认
`runtime/lidar_scan_proof_latest.json`。artifact 缺失、坏 JSON 或根节点不是对象时
fail-closed 返回，不启动 ROS2，不打开串口，不发送 `A5 60` 或任何底盘命令。

## 本轮结果

2026-06-03 17-18 远端 no-motion collector 成功写入
`/tmp/o1_lidar_scan_proof_latest.json`，但 proof 仍为 blocked：

- `/dev/ttyACM0` 存在。
- `/dev/serial/by-id/usb-STC_STC_USB_Serial-if00 -> ../../ttyACM0` 存在。
- `/dev/lidar` 不存在。
- 8787 `/health` ready。
- 8787 `/api/radar/status` 返回 `scan_status=not_proven`。
- `/opt/ros/humble/setup.bash` 不存在。
- `/root/rober/onboard/install/setup.bash` 不存在。
- `ros2` 不可用。
- `proof.status=blocked_or_not_observed`。
- `topic_reads.attempted=false`。

因此本轮没有证明真实 ROS2 `/scan`、`/lidar/raw_packet`、TF、SLAM/Nav2 消费链路、
LiDAR continuous scan、HIL pass 或 `safe_to_control=true`。
