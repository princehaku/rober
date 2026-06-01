# LiDAR ROS2 Closed-loop Interface

## Package Ownership

- Driver executable: `ros2_trashbot_hardware lidar_driver`
- Parser module: `ros2_trashbot_hardware.lidar_packets`
- Launch owners: `ros2_trashbot_bringup/launch/bringup.launch.py` and `ros2_trashbot_bringup/launch/learn.launch.py`

LiDAR 当前作为传感器硬件接入和串口 reader 管理，因此 driver/parser 归属 `ros2_trashbot_hardware`。`ros2_trashbot_nav` 后续只消费 `/scan`、TF 和 SLAM/Nav2 结果，不放置重复 LiDAR driver 或 packet parser。

## Launch Contract

- `bringup.launch.py` 和 `learn.launch.py` 通过 `lidar_enabled` gate 启动 LiDAR，默认 `false`。
- `lidar_enabled:=true` 时启动 `ros2_trashbot_hardware/lidar_driver`。
- `lidar_enabled:=true` 时同步启动 `tf2_ros/static_transform_publisher`，提供 `base_link -> laser_frame` 占位 TF。
- `lidar_serial_port`、`lidar_serial_baudrate`、`lidar_frame_id`、`lidar_scan_topic`、`lidar_raw_packet_topic`、`lidar_publish_raw_packets`、range 和 timing 参数保持 launch 可配置。
- `learn.launch.py` 的参数名与 `bringup.launch.py` 对齐，真机建图 smoke 可以直接复用同一套 LiDAR/TF CLI 覆盖参数。
- `learn.launch.py` 只在显式 `lidar_enabled:=true` 时暴露 `/scan` 和 `laser_frame`，避免无雷达或未测 TF 时让 SLAM 学习阶段误消费占位输入。

## Evidence Boundary

- Vendor source: `docs/vendor/VENDOR_INDEX.md` and `docs/vendor/lidar_ros/`.
- Current evidence level: `source=software_reference`.
- Hardware status: real LiDAR, real USB path, real Orange Pi serial permission, TF measurement, Nav2/SLAM consumption, and `150000` baud stability are `not_proven`.
- Mock status: `lidar_mock_scan` and `lidar_mock_packets` can prove software conversion only; they are not HIL and cannot be marked `source=hil_pass`.

## Verification Commands

```bash
python3 -m unittest discover -s onboard/src/ros2_trashbot_hardware/test -p 'test_lidar*.py'
python3 -m unittest discover -s onboard/src/ros2_trashbot_bringup/test -p 'test_launch_contract_static.py'
python3 -m compileall -q onboard/src/ros2_trashbot_hardware onboard/src/ros2_trashbot_bringup
PYTHONDONTWRITEBYTECODE=1 bash onboard/scripts/run_smoke_tests.sh
```

真机建图 smoke 的推荐入口：

```bash
ros2 launch ros2_trashbot_bringup learn.launch.py lidar_enabled:=true lidar_serial_port:=<real_lidar_device> lidar_serial_baudrate:=150000 lidar_frame_id:=laser_frame
```

真实上车前必须补充 `ros2 topic echo --once /scan`、`ros2 topic hz /scan`、`tf2_echo base_link laser_frame` 和 SLAM/Nav2 订阅证据。Robot Software 静态验证只能证明 launch contract 可复用，不能声明真机 LiDAR、真实 TF 或建图质量已通过。
