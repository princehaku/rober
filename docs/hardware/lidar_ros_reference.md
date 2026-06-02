# LiDAR ROS Reference

## Sources

Current ROS2/STC source of truth:

- `docs/vendor/VENDOR_INDEX.md`
- `docs/vendor/lidar_pkg_ros2-main/README.md`
- `docs/vendor/lidar_pkg_ros2-main/src/lidar_node.cpp`
- `docs/vendor/lidar_pkg_ros2-main/config/lidar_params.yaml`
- `docs/vendor/lidar_pkg_ros2-main/scripts/99-lidar.rules`
- `docs/vendor/lidar_pkg_ros2-main/launch/lidar.launch.py`
- `docs/vendor/lidar_pkg_ros2-main/launch/monitor.launch.py`
- `docs/vendor/lidar_pkg_ros2-main/rviz/lidar.rviz`
- `docs/vendor/lidar_pkg_ros2-main/urdf/lidar.urdf`
- `docs/vendor/lidar_pkg_ros2-main/models/lidar_mount.stl`

Historical ROS1/protocol reference retained for comparison:

- `docs/vendor/lidar_ros/SOURCE.md`
- `docs/vendor/lidar_ros/README.md`
- `docs/vendor/lidar_ros/plot.py`
- `docs/vendor/lidar_ros/src/lidar_pkg/package.xml`
- `docs/vendor/lidar_ros/src/lidar_pkg/CMakeLists.txt`
- `docs/vendor/lidar_ros/src/lidar_pkg/launch/lidar_vi.xml`
- `docs/vendor/lidar_ros/src/lidar_pkg/scripts/lidar_driver.py`
- `docs/vendor/lidar_ros/src/lidar_pkg/src/lidar_driver.cpp`
- `docs/vendor/lidar_ros/src/lidar_pkg/rviz/lidar_config.rviz`

本文件合并当前 ROS2/STC 参考与历史 ROS1/protocol 快照。当前实现依据是
`docs/vendor/lidar_pkg_ros2-main/`；`docs/vendor/lidar_ros/` 保留为历史协议和
ROS1 topic 行为参考，不得写成已删除，也不得作为当前 ROS2 driver source of
truth。

当前结论属于 `source=software_reference + user_manual_serial_observed_start`，
不能替代真实 `/scan`、TF、SLAM/Nav2 或长期稳定性已经 `source=hil_pass`。

## Source Snapshots

### Current ROS2/STC Snapshot

- Local directory: `docs/vendor/lidar_pkg_ros2-main/`
- ROS generation: ROS2 Humble / ament CMake.
- Package name: `lidar_pkg`.
- Runtime executable: `lidar_node`.
- Evidence boundary: `source=software_reference + user_manual_serial_observed_start`。

### Historical ROS1/protocol Snapshot

- Upstream URL: `https://github.com/sudreamcarver/lidar_ros`
- Snapshot commit: `a88fcec0a207e0a2765fb4542ffbc8b1913f60ee`
- Retrieved at: `2026-06-01T01:46:25Z`
- Local directory: `docs/vendor/lidar_ros/`
- Snapshot boundary: excludes upstream `.git/`, `.clangd/`, `compile_commands.json`, and `.catkin_workspace`.
- Usage boundary: historical ROS1/protocol comparison only.

## Confirmed Facts From Current ROS2/STC Reference

| Item | Fact | Source |
| --- | --- | --- |
| ROS generation | ROS2 Humble / ament CMake | `README.md`, `CMakeLists.txt`, `package.xml` |
| Vendor config port | `/dev/lidar` | `config/lidar_params.yaml` |
| Observed USB bridge | STC USB Serial, `idVendor=34bf`, `idProduct=ff0a` | `scripts/99-lidar.rules`, user dmesg |
| Observed runtime path | `/dev/ttyACM0` during manual test | user dmesg and manual Python test |
| Baud rate | `150000` | `src/lidar_node.cpp`, manual test |
| Start command | `A5 60` | `src/lidar_node.cpp`, manual test confirmed motor starts |
| Stop sequence | `A5 00 A5 65 A5 65` | `src/lidar_node.cpp` |
| Packet header | `0xAA 0x55` | `src/lidar_node.cpp` |
| Packet length | `8 + LSN * 3` | `src/lidar_node.cpp` |
| Parser output | `sensor_msgs/msg/LaserScan` | `src/lidar_node.cpp` |
| ROS2 scan topic | `scan`, normally visible as `/scan` | `src/lidar_node.cpp`, `rviz/lidar.rviz` |
| Vendor frame id | `laser` | `config/lidar_params.yaml` |
| Project frame id | `laser_frame` by launch default | `bringup.launch.py`, `learn.launch.py` |

## Historical ROS1/protocol Facts

| Item | Fact | Source |
| --- | --- | --- |
| ROS generation | ROS1/catkin reference, not ROS2/ament | `package.xml`, `CMakeLists.txt`, `launch/lidar_vi.xml` |
| Package name | `lidar_pkg` | `package.xml` |
| Launch file | `src/lidar_pkg/launch/lidar_vi.xml` | `lidar_vi.xml` |
| LiDAR type | Upstream README calls it拆机 `YDLIDAR` | `README.md` |
| Serial port default | `/dev/ttyUSB0` | `plot.py`, `scripts/lidar_driver.py` |
| Baud rate | `150000` | `README.md`, `plot.py`, `scripts/lidar_driver.py` |
| Packet header | `0xAA 0x55` | `README.md`, `plot.py`, `scripts/lidar_driver.py` |
| Raw packet topic | `/lidar/raw_packet` | `scripts/lidar_driver.py`, `src/lidar_driver.cpp` |
| Raw packet message | `std_msgs/UInt8MultiArray` | `scripts/lidar_driver.py`, `src/lidar_driver.cpp` |
| Parser output | `sensor_msgs/LaserScan` | `src/lidar_driver.cpp` |
| Default frame | `laser_frame` | `src/lidar_driver.cpp`, `launch/lidar_vi.xml`, `rviz/lidar_config.rviz` |
| RViz scan topic reference | `/lidar_parser_node/scan` | `rviz/lidar_config.rviz` |
| Parser advertised topic | private `scan` under `ros::NodeHandle("~")` | `src/lidar_driver.cpp` |

## Project ROS2 Integration

Project driver ownership:

- Driver executable: `ros2_trashbot_hardware lidar_driver`
- Parser module: `ros2_trashbot_hardware.lidar_packets`
- Launch owners: `ros2_trashbot_bringup/launch/bringup.launch.py` and
  `ros2_trashbot_bringup/launch/learn.launch.py`
- Interface doc: `docs/interfaces/lidar_ros2_closed_loop.md`

Runtime contract:

1. `mock_scan=true` uses a built-in packet and does not open serial.
2. `mock_packets` replays hex packets and does not open serial.
3. Real serial mode is selected only when `mock_scan=false` and `mock_packets`
   is empty.
4. Real serial mode opens `serial_port` at `serial_baudrate`, writes `A5 60`,
   reads bytes, resynchronizes complete packets on `0xAA 0x55`, and publishes
   `sensor_msgs/msg/LaserScan`; if the startup write fails, the driver closes
   the just-opened handle before surfacing the error.
5. If `publish_raw_packets=true`, complete packets are also published as
   `std_msgs/msg/UInt8MultiArray` on `raw_packet_topic`.
6. Node shutdown writes `A5 00 A5 65 A5 65` best-effort, then closes serial;
   stop-write failure must not prevent close, and physical stop still requires
   robot observation.
7. `o1_upper_computer_readiness_probe.py` now emits
   `lidar_runtime_readiness` as a no-motion smoke gate. It only marks
   `ready_for_no_motion_lidar_smoke` when ROS2 Humble setup exists, pyserial is
   importable, a rober workspace is visible, and a `/dev/lidar` / STC / ttyACM
   LiDAR candidate is listed by the read-only probe.
8. 2026-06-03 现场事实更新：`/dev/ttyACM0` 是当前雷达口，不是底盘控制口。项目
   ROS2 LiDAR 默认配置已对齐 `/dev/ttyACM0 @150000`；WAVE ROVER 底盘写入口另行
   记录为 `/dev/ttyS5 @115200`，两者不得混用。

## Launch Parameters

The ROS2 launch files keep these configurable:

- `lidar_enabled`
- `lidar_serial_port`
- `lidar_serial_baudrate`
- `lidar_frame_id`
- `lidar_scan_topic`
- `lidar_raw_packet_topic`
- `lidar_publish_raw_packets`
- `lidar_range_min`
- `lidar_range_max`
- `lidar_scan_time`
- `lidar_time_increment`
- `lidar_tf_x`
- `lidar_tf_y`
- `lidar_tf_z`
- `lidar_tf_roll`
- `lidar_tf_pitch`
- `lidar_tf_yaw`
- `lidar_mock_packets`
- `lidar_mock_scan`

`lidar_enabled` defaults to `false` so learning/bringup still work when no
LiDAR is attached. `lidar_serial_port` now defaults to the confirmed Orange Pi
runtime device `/dev/ttyACM0`. Real robot smoke may still pass the udev-stable
device explicitly, for example `/dev/lidar` or a by-id path, after verifying it
resolves to the same LiDAR.

## Verification Commands

Software verification:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s onboard/src/ros2_trashbot_hardware/test -p 'test_lidar*.py'
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s onboard/src/ros2_trashbot_bringup/test -p 'test_launch_contract_static.py'
PYTHONDONTWRITEBYTECODE=1 python3 onboard/scripts/test_upper_robot_api.py
python3 -m compileall -q onboard/src/ros2_trashbot_hardware onboard/src/ros2_trashbot_bringup
```

Real robot no-motion smoke:

```bash
timeout 20 ssh -o BatchMode=yes -o ConnectTimeout=8 -p 37878 root@192.168.1.11 'python3 -s - --once-json' < onboard/scripts/o1_upper_computer_readiness_probe.py
ssh -p 37878 root@192.168.1.11 'modprobe ch341; modprobe cp210x; modprobe ftdi_sio; modprobe pl2303; modprobe cdc_acm; ls -l /dev/ttyACM0 /dev/lidar 2>/dev/null || true'
source /opt/ros/humble/setup.bash
source install/setup.bash
ros2 launch ros2_trashbot_bringup learn.launch.py lidar_enabled:=true lidar_serial_port:=/dev/ttyACM0 lidar_serial_baudrate:=150000 lidar_frame_id:=laser_frame lidar_publish_raw_packets:=true
ros2 topic echo --once /scan
ros2 topic hz /scan
ros2 topic echo --once /lidar/raw_packet
ros2 run tf2_ros tf2_echo base_link laser_frame
```

## Mock And Software Verification Boundary

- 当前已完成双快照资料整理、ROS2/STC current source-of-truth 收口和软件启动命令路径记录。
- 当前 parser 和 fake serial 单元测试只能证明软件逻辑，不能标记为真实上车通过。
- `docs/vendor/lidar_ros/` 能证明历史 ROS1/protocol 参考事实，不能证明当前机器人 USB 设备、供电、线缆、安装角度或数据质量。
- 真实闭环需要 LiDAR 实机输出 `/scan`，并与 TF、SLAM/Nav2 消费链路一起验证。

## Real Robot Risks

- `/dev/ttyACM0` 是用户手动测试观测值；生产应验证 `/dev/lidar` udev 或 `/dev/serial/by-id/...` 稳定命名。
- `150000` 是非标准波特率；需要确认 Orange Pi Ubuntu 内核、USB-UART 芯片和容器/宿主设备透传均支持。
- 停止序列是软件 best-effort；物理电机停转仍需上车观察。
- `sensor_msgs/msg/LaserScan` 的角度方向、`angle_min/max/increment`、`scan_time`、`range_min/max` 仍需用实测点云和 RViz/SLAM 行为校验。
- `laser_frame` 到 `base_link` 的安装位姿没有在 vendor reference 中给出；上车必须测量安装位置和朝向，不能从代码猜。

## Current Status

- 当前 LiDAR ROS2/STC source of truth 是 `docs/vendor/lidar_pkg_ros2-main/`。
- 历史 `docs/vendor/lidar_ros/` 已保留，只作为 ROS1/protocol reference。
- 项目 ROS2 driver 已实现用户手动确认可启动电机的 `A5 60` start command。
- 项目 ROS2 driver、`bringup.launch.py` 和 `learn.launch.py` 的默认 LiDAR 端口已对齐现场雷达 `/dev/ttyACM0 @150000`。
- Fake serial tests 证明 driver 发送 start/stop bytes、mock 路径不碰串口、split packet 可重同步、启动写失败会 close、停止写失败仍会 close。
- `2026.06.02_06-07_o1-lidar-upper-runtime-readiness` 远端只读 SSH readiness probe 未进入上位机，错误为 `No route to host`；因此本轮没有采到真实 `/scan` 或 LiDAR runtime 证据。
- 下一轮必须先恢复 SSH 可达性并检查 `lidar_runtime_readiness.status`；只有它为 `ready_for_no_motion_lidar_smoke` 时，才允许继续执行不含底盘运动命令的 LiDAR driver 与 `/scan` 观察。
- 真实 `/scan` 连续输出、raw packet 质量、TF、SLAM/Nav2 消费和长时间稳定性仍未证明。
