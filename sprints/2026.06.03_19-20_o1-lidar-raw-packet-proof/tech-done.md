# O1 LiDAR Raw Packet Proof

## sprint_type

micro

## 本轮目标

在远端上位机仍缺 ROS2 Humble/install/`ros2` 的情况下，补一个 O1 前置证据切片：
通过 LiDAR 串口 raw bytes 采集和 packet parser 统计，证明 raw packet parse/material
readiness 的采集路径可执行。

本轮不尝试证明 ROS2 `/scan`、TF、SLAM/Nav2、HIL 或 `safe_to_control=true`。

## 已读 vendor 来源

- `AGENTS.md`
- `OKR.md`
- `docs/vendor/VENDOR_INDEX.md`
- `docs/vendor/lidar_pkg_ros2-main/README.md`
- `docs/vendor/lidar_pkg_ros2-main/src/lidar_node.cpp`
- `docs/vendor/lidar_pkg_ros2-main/config/lidar_params.yaml`
- `docs/vendor/lidar_pkg_ros2-main/scripts/99-lidar.rules`
- `docs/vendor/lidar_ros/README.md`
- `docs/vendor/lidar_ros/src/lidar_pkg/scripts/lidar_driver.py`
- `onboard/src/ros2_trashbot_hardware/ros2_trashbot_hardware/lidar_packets.py`

## 已证实的硬件结论

- 本轮采用当前 LiDAR vendor 边界：`/dev/ttyACM0 @150000`、start bytes
  `A5 60`、stop bytes `A5 00 A5 65 A5 65`、sync header `0xAA55`。
- `onboard/scripts/o1_lidar_raw_packet_proof_collector.py` 会打开 LiDAR 串口并
  发送 LiDAR start/stop bytes；这是本轮允许的目标行为。
- collector 不发送 WAVE ROVER 底盘 `T=1/T=13/T=130/T=131`，不发布
  `/cmd_vel`，不调用 `/api/base/manual`。
- collector 不启动 ROS2 driver，不启动 launch，不读取 ROS2 `/scan` topic。
- artifact 只能证明 raw bytes/packet/point parse material readiness，不能证明
  ROS2 `/scan`、TF、SLAM/Nav2、HIL、ACK、真实 manual 或 `safe_to_control=true`。

## 实际改动

- 新增 `onboard/scripts/o1_lidar_raw_packet_proof_collector.py`
  - 支持 `python3 -s - --once-json ... < script.py` 远端 stdin 运行。
  - 优先复用 `ros2_trashbot_hardware.lidar_packets`，无法 import 时使用内置
    fallback parser，并在 artifact 记录 `parser_source`。
  - 支持 pyserial；目标机无 pyserial 时使用 Linux termios fallback。
  - 输出 `trashbot.o1.lidar_raw_packet_proof.v1` artifact。
  - 记录 `serial_open`、`lidar_commands_sent`、`base_commands_sent=[]`、
    `packet_stats`、`proof` 和 fail-closed 安全字段。
- 新增 `onboard/scripts/test_o1_lidar_raw_packet_proof_collector.py`
  - 覆盖 mock packet parse、fake serial start/stop 写入、串口失败 fail-closed、
    artifact 原子写入。
- 新增 `docs/hardware/o1_lidar_raw_packet_proof.md`
  - 记录 contract、runbook、artifact 字段、验收口径和边界。
- 更新 `OKR.md`
  - 增加 `2026.06.03_19-20_o1-lidar-raw-packet-proof` O1 补充材料说明。
  - 明确 O1 百分比不变，不夸大为 `/scan` 或 HIL。
- 新增本文件作为 micro sprint 留档。

## 验证结果

### 本地 unittest

命令：

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest onboard/scripts/test_o1_lidar_raw_packet_proof_collector.py
```

结果：

```text
....
----------------------------------------------------------------------
Ran 4 tests in 0.259s

OK
```

### py_compile

命令：

```bash
python3 -m py_compile onboard/scripts/o1_lidar_raw_packet_proof_collector.py onboard/scripts/test_o1_lidar_raw_packet_proof_collector.py
```

结果：

```text
passed
```

### 远端受限 smoke

命令：

```bash
ssh -o BatchMode=yes -o ConnectTimeout=8 -p 37878 root@192.168.1.11 'python3 -s - --once-json --output /tmp/o1_lidar_raw_packet_proof_latest.json --timeout-s 3 --port /dev/ttyACM0 --baudrate 150000' < onboard/scripts/o1_lidar_raw_packet_proof_collector.py
```

结果：

```text
serial_open.ok=true
port=/dev/ttyACM0
baudrate=150000
lidar_start bytes_written=2 hex="a5 60"
lidar_stop bytes_written=6 hex="a5 00 a5 65 a5 65"
bytes_read=9086
sync_header_count=275
packets_found=275
packets_parse_ok=275
packet_parse_errors=0
points_total=1923
artifact_write.ok=true
artifact=/tmp/o1_lidar_raw_packet_proof_latest.json
base_commands_sent=[]
safe_to_control=false
ros2_scan_proven=false
hil_pass=false
```

## 剩余风险和下一步

- 远端 raw packet artifact 已通过，但只证明 LiDAR raw bytes、`0xAA55`
  sync header、packet parse 和 point 统计材料路径可用。
- 该结果仍不证明真实 ROS2 `/scan`、
  `/lidar/raw_packet` topic、TF、SLAM/Nav2、HIL、ACK 或 `safe_to_control=true`。
- 下一步仍是补齐上位机 ROS2 Humble/install/`ros2`，再采集真实 `/scan`、
  `/lidar/raw_packet`、`ros2 topic hz /scan` 和 `tf2_echo base_link laser_frame`。
