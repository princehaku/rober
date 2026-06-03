# O1 LiDAR Raw Packet Proof

## 目标

`onboard/scripts/o1_lidar_raw_packet_proof_collector.py` 用于在远端上位机缺
ROS2 Humble/install/`ros2` 时，先采集 LiDAR 串口原始 bytes，并用现有
`lidar_packets.py` parser 或脚本内置 fallback 生成 packet/point 统计 artifact。

该 artifact 的结论只允许写成：

- LiDAR 串口可打开或不可打开。
- collector 是否发送了 vendor LiDAR start/stop bytes。
- 是否观察到 `0xAA55` sync header。
- 是否能把 raw bytes 解析成 packet。
- 是否能从 packet 解析出非零 point 统计。

该 artifact 不能写成真实 ROS2 `/scan`、`/lidar/raw_packet` topic、TF、
SLAM/Nav2、HIL、底盘安全控制、`safe_to_control=true` 或送达闭环。

## Vendor 来源

本轮已读并采用的本地来源：

- `AGENTS.md`
- `OKR.md`
- `docs/vendor/VENDOR_INDEX.md`
- `docs/vendor/lidar_pkg_ros2-main/README.md`
- `docs/vendor/lidar_pkg_ros2-main/src/lidar_node.cpp`
- `docs/vendor/lidar_pkg_ros2-main/config/lidar_params.yaml`
- `docs/vendor/lidar_pkg_ros2-main/scripts/99-lidar.rules`
- `docs/vendor/lidar_ros/README.md`
- `onboard/src/ros2_trashbot_hardware/ros2_trashbot_hardware/lidar_packets.py`

已采用的硬件/协议事实：

- 当前 LiDAR source-of-truth 是 `docs/vendor/lidar_pkg_ros2-main/`。
- 当前现场候选串口是 `/dev/ttyACM0`，稳定部署后仍应优先验证 `/dev/lidar` 或
  `/dev/serial/by-id/...`。
- 当前 baudrate 是 `150000`。
- ROS2 vendor driver startup bytes 是 `A5 60`。
- ROS2 vendor driver shutdown bytes 是 `A5 00 A5 65 A5 65`。
- packet sync header 是 `0xAA55`。
- packet length 由 `LSN` 推导：`8 + LSN * 3` bytes。
- 现有项目 parser 是
  `onboard/src/ros2_trashbot_hardware/ros2_trashbot_hardware/lidar_packets.py`。

## 运行方式

远端 stdin smoke：

```bash
ssh -o BatchMode=yes -o ConnectTimeout=8 -p 37878 root@192.168.1.11 'python3 -s - --once-json --output /tmp/o1_lidar_raw_packet_proof_latest.json --timeout-s 3 --port /dev/ttyACM0 --baudrate 150000' < onboard/scripts/o1_lidar_raw_packet_proof_collector.py
```

本地或已同步脚本后运行：

```bash
python3 onboard/scripts/o1_lidar_raw_packet_proof_collector.py --once-json --output /tmp/o1_lidar_raw_packet_proof_latest.json --timeout-s 3 --port /dev/ttyACM0 --baudrate 150000
```

## 明确会做的事

- 打开 `--port` 指定的 LiDAR 串口。
- 使用 `--baudrate`，默认 `150000`。
- 写入 LiDAR start bytes：`A5 60`。
- 在 `--timeout-s` 窗口内读取 raw bytes。
- 使用项目 parser 或内置 fallback 统计 packet/point。
- 退出前写入 LiDAR stop bytes：`A5 00 A5 65 A5 65`。
- 原子写入 JSON artifact。

## 明确不会做的事

- 不发送 WAVE ROVER 底盘 JSON 命令：`T=1/T=13/T=130/T=131`。
- 不发布 `/cmd_vel`。
- 不调用 `/api/base/manual`。
- 不启动 ROS2 driver。
- 不启动 launch。
- 不读取 ROS2 `/scan` 或 `/lidar/raw_packet` topic。
- 不声明 `safe_to_control=true`、HIL pass 或 delivery success。

## Artifact contract

关键字段：

- `schema=trashbot.o1.lidar_raw_packet_proof.v1`
- `evidence_boundary=lidar_raw_packet_parse_material_readiness_only`
- `target.port`
- `target.baudrate`
- `serial_open.ok`
- `lidar_commands_sent[]`
- `base_commands_sent=[]`
- `forbidden_base_actions_not_sent[]`
- `packet_stats.bytes_read`
- `packet_stats.sync_header_count`
- `packet_stats.packets_found`
- `packet_stats.packets_parse_ok`
- `packet_stats.points_total`
- `proof.status=raw_packets_parsed | blocked_or_not_observed`
- `proof.raw_bytes_observed`
- `proof.sync_header_observed`
- `proof.packet_parse_ok`
- `proof.points_observed`
- `proof.ros2_driver_started_by_collector=false`
- `safe_to_control=false`
- `ros2_scan_proven=false`
- `tf_proven=false`
- `slam_nav2_proven=false`
- `hil_pass=false`

## 验收口径

通过标准：

- artifact 中 `serial_open.ok=true`。
- `lidar_commands_sent` 包含 `lidar_start` 和 `lidar_stop`。
- `packet_stats.bytes_read > 0`。
- `packet_stats.sync_header_count > 0`。
- `packet_stats.packets_parse_ok > 0`。
- `packet_stats.points_total > 0`。
- 所有安全边界字段保持 fail-closed。

未通过但有价值的材料：

- 串口打不开：说明设备路径、权限、占用或接线仍需处理。
- 有 bytes 但无 sync header：说明波特率、启动命令、设备身份或数据流异常。
- 有 sync header 但 parser 失败：说明 packet 边界、LSN 或 parser 兼容性需要继续定位。

## 下一步

raw packet artifact 通过后，下一步仍是补齐上位机 ROS2 Humble/install/`ros2`，
再采集真实：

- `ros2 topic echo --once /scan`
- `ros2 topic hz /scan`
- `/lidar/raw_packet`
- `tf2_echo base_link laser_frame`

这些后续材料完成前，不得把本 artifact 提升为 `/scan` proof、HIL 或
`safe_to_control=true`。
