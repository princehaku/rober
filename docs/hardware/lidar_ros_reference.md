# LiDAR ROS Reference

## Sources

- `docs/vendor/VENDOR_INDEX.md`
- `docs/vendor/lidar_ros/SOURCE.md`
- `docs/vendor/lidar_ros/README.md`
- `docs/vendor/lidar_ros/plot.py`
- `docs/vendor/lidar_ros/src/lidar_pkg/package.xml`
- `docs/vendor/lidar_ros/src/lidar_pkg/CMakeLists.txt`
- `docs/vendor/lidar_ros/src/lidar_pkg/launch/lidar_vi.xml`
- `docs/vendor/lidar_ros/src/lidar_pkg/scripts/lidar_driver.py`
- `docs/vendor/lidar_ros/src/lidar_pkg/src/lidar_driver.cpp`
- `docs/vendor/lidar_ros/src/lidar_pkg/rviz/lidar_config.rviz`

本文件只记录 LiDAR 参考资料入库与 ROS2 闭环接入前置事实。当前结论属于 `source=software_reference`，不能替代真实上车 `source=hil_pass`。

## Source Snapshot

- Upstream URL: `https://github.com/sudreamcarver/lidar_ros`
- Snapshot commit: `a88fcec0a207e0a2765fb4542ffbc8b1913f60ee`
- Retrieved at: `2026-06-01T01:46:25Z`
- Local directory: `docs/vendor/lidar_ros/`
- Snapshot boundary: excludes upstream `.git/`, `.clangd/`, `compile_commands.json`, and `.catkin_workspace`.

## Confirmed Facts From Reference

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
| Declared build deps | `roscpp`, `rospy`, `sensor_msgs`, `serial`, `boost` | `package.xml`, `CMakeLists.txt` |

## ROS2 Closed-loop接入建议

后续 Robot Platform Engineer 接入 ROS2 时，不应直接把 ROS1 包复制到 `onboard/` 运行，而应显式移植为 ROS2 Humble 节点。推荐闭环如下：

1. ROS2 LiDAR driver 打开可配置串口，例如 `serial_port`，默认值只可作为开发占位，真实上车前必须现场确认 USB 设备名。
2. 串口波特率保留为可配置参数 `serial_baudrate`，参考值为 `150000`。
3. raw reader 使用 `0xAA 0x55` 同步帧头，按 `LSN` 计算包长度，先发布或内部传递原始 packet。
4. parser 将 packet 转为 `sensor_msgs/msg/LaserScan`，默认 `frame_id=laser_frame`，但 launch/config 必须允许覆盖。
5. 与 Nav2/SLAM 闭环时，统一 scan topic 到项目约定，例如 `/scan`，并用 TF 明确 `base_link -> laser_frame`。
6. RViz/SLAM 验收以 `LaserScan` 话题连续发布、TF 可解析、Nav2/SLAM 能订阅为准。

建议 ROS2 参数至少包含：

- `serial_port`
- `serial_baudrate`
- `frame_id`
- `raw_packet_topic`
- `scan_topic`
- `range_min`
- `range_max`
- `scan_time`
- `time_increment`
- `publish_raw_packets`

## 闭环验收命令建议

这些命令是 ROS2 软件闭环和真实上车阶段的验收口径。第二阶段软件接入状态见下方 `Stage 2 ROS2 Closed-loop Status`，真实硬件 run 仍需额外记录实机 topic、TF 和 RViz/SLAM 证据。

```bash
source /opt/ros/humble/setup.bash
colcon build --symlink-install
source install/setup.bash
ros2 launch ros2_trashbot_bringup bringup.launch.py lidar_enabled:=true lidar_serial_port:=/dev/ttyUSB0 lidar_serial_baudrate:=150000 lidar_frame_id:=laser_frame
ros2 topic list | grep -E '(^/scan$|/lidar/raw_packet)'
ros2 topic echo --once /scan
ros2 topic hz /scan
ros2 interface show sensor_msgs/msg/LaserScan
ros2 run tf2_ros tf2_echo base_link laser_frame
```

Mock/软件验证建议：

```bash
python3 -m compileall <ros2_lidar_package_path>
python3 -m unittest discover -s <ros2_lidar_package_path> -p 'test_*.py'
```

## Mock 和软件验证边界

- 当前已完成资料入库、静态事实梳理和 ROS2/Humble 软件骨架，未接入真实雷达串口。
- 参考仓库能证明其作者记录的 packet 格式、ROS1 topic 结构和解析意图，但不能证明当前机器人上的雷达 USB 设备、供电、线缆、安装角度或数据质量。
- 当前 parser 单元测试和 ROS message stub 测试只能证明软件逻辑，不能标记为真实上车通过。
- 真实闭环需要 LiDAR 实机输出 `/scan`，并与 TF、SLAM/Nav2 消费链路一起验证。

## Real Robot Risks

- `/dev/ttyUSB0` 只是参考仓库默认值；机器人上可能因为 WAVE ROVER、4G 模块、调试串口或其他 USB 设备变化而漂移。
- `150000` 是非标准波特率；需要确认 Orange Pi Ubuntu 内核、USB-UART 芯片和容器/宿主设备透传均支持。
- 参考代码是 ROS1/catkin，迁移到 ROS2 需要重写 node、parameter、launch 和 message import。
- `sensor_msgs/LaserScan` 的角度方向、`angle_min/max/increment`、`scan_time`、`range_min/max` 仍需用实测点云和 RViz/SLAM 行为校验。
- `laser_frame` 到 `base_link` 的安装位姿没有在该参考仓库中给出；上车必须测量安装位置和朝向，不能从代码猜。
- 参考 README 说明“本测试无角度修正”，因此导航使用前需要评估角度误差对建图和避障的影响。

## Stage 2 ROS2 Closed-loop Status

- Hardware Infra Engineer 已完成参考资料入库和事实边界声明。
- Robot Platform Engineer 已把 ROS2 LiDAR 软件闭环收敛在 `ros2_trashbot_nav`，避免在 `ros2_trashbot_hardware` 重复放置 LiDAR driver/parser。
- 新增 ROS2 console script：`ros2_trashbot_nav/lidar_driver`。
- 新增纯软件 parser：`ros2_trashbot_nav.lidar_packets`，按 `0xAA 0x55` 帧头和 `LSN` 长度解析 vendor packet。
- 默认输出：`sensor_msgs/msg/LaserScan` 到 `/scan`，frame 为 `laser_frame`。
- 可选输出：`std_msgs/msg/UInt8MultiArray` 到 `/lidar/raw_packet`。
- `bringup.launch.py` 新增 `lidar_enabled`，默认 `false`；本轮不改 `learn.launch.py` 或 `autonomous.launch.py`。
- `bringup.launch.py` 在 `lidar_enabled:=true` 时启动 `tf2_ros static_transform_publisher`，发布 `base_link -> laser_frame` 占位 TF。
- `bringup.launch.py` 暴露 `lidar_range_min`、`lidar_range_max`、`lidar_scan_time`、`lidar_time_increment`，避免把未实测的 LaserScan 范围和时序写死。
- TF 的 `lidar_tf_x/y/z/roll/pitch/yaw` 默认全零，只是软件闭环占位；真实导航前必须用实测安装位姿覆盖。
- mock 边界：支持 `lidar_mock_scan:=true` 或 `lidar_mock_packets:=<hex>` 做软件闭环验证；该证据不能替代真实串口/HIL。

## Stage 2 Verification Scope

- 已覆盖 packet parser 单测：LSN 长度、mock packet、坏包错误、mock hex 参数。
- 已覆盖 driver stub 单测：LaserScan-shaped 字段转换、launch 风格 bool 字符串、串口流分包。
- 已覆盖 launch static contract：`bringup.launch.py` 的 LiDAR 参数、默认关闭、nav 包节点、TF 节点和 `base_link -> laser_frame` contract。
- 真实硬件 run 前必须再次查阅 `docs/vendor/VENDOR_INDEX.md` 和本文件，并把 `serial_port`、`serial_baudrate`、`frame_id`、scan topic、TF、实测命令输出写入 sprint 证据。
