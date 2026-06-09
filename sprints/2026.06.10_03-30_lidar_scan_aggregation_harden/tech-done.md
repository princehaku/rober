# LiDAR Scan Aggregation Harden

## sprint_type

micro

## 设计决策

- 本轮只硬化 `ros2_trashbot_hardware/lidar_driver.py` 的 `/scan` 发布形态，不改底盘控制、不改 launch 默认、不发送 `/cmd_vel`。
- 保留 `scan_dict_from_packet()` 旧函数兼容既有测试；新增纯 Python 聚合 helper，把多个 parsed `LidarPoint` 累积后按角度排序，再发布一帧覆盖更宽角度的 `LaserScan` 字典。
- 聚合触发采用保守策略：后一个 packet 首角小于前一个 packet 首角时认为发生角度回绕；同时保留最大 packet 数和最小点数 fallback，避免现场 packet 异常或长期不回绕时 `/scan` 停止发布。
- 聚合帧只发布已有采样点，不伪造 360 度，不给未覆盖角度填虚假距离；因此本轮提升的是 motion-delta 证据的角度覆盖，不等同于完成机械标定或真实运动证明。

## 验收口径

1. 本地纯 Python 单测必须覆盖旧单包转换、聚合回绕发布、最大 packet 数 fallback、mock packet 路径。
2. Docker/Humble 工作区构建必须通过：`bash onboard/scripts/docker_humble_build.sh`。
3. 如真实上位机 SSH 可达，只做 no-motion LiDAR smoke：同步最小改动、只构建 `ros2_trashbot_hardware`、启动 `/dev/ttyACM0 @ 150000` 的 `lidar_driver`、采样 `/scan` 的 ranges 数、finite 数和 angle span；禁止 `/cmd_vel`。

## 已读 vendor 与现场来源

- `AGENTS.md`：硬件相关必须先读 `docs/vendor/VENDOR_INDEX.md`，真实集成阶段需明确 vendor 来源；缺真实硬件时允许 mock/stub 推进。
- `OKR.md`：当前 O1 仍缺真实 WAVE ROVER/HIL 准入；本轮属于 O1/O3 现场传感器证据硬化，不提升为底盘真实运动证明。
- `docs/vendor/VENDOR_INDEX.md`：本地 vendor 是硬件事实优先来源；WAVE ROVER 上位/下位链路为 UART newline-delimited JSON，Orange Pi 串口路径必须现场确认。
- `docs/vendor/waveshare_wave_rover/ugv_rpi/base_ctrl.py`：厂商上位机参考中 LiDAR 使用 `/dev/ttyACM*`，并以 start angle 回绕作为一轮 LiDAR 数据输出触发。
- `docs/vendor/waveshare_wave_rover/ugv_rpi/config.yaml`：`base_config.use_lidar: false`，说明厂商默认应用未强制启用 LiDAR。
- `docs/hardware/board_sensor_stack_smoke.md`：项目现场事实为 `root@192.168.1.11:37878` 上 `/dev/ttyACM0 @ 150000` 可发布 `/scan`；该波特率来自现场 smoke，不是 WAVE ROVER 底盘 UART vendor 默认。

## 功能点

- 已实现：`lidar_driver.py` 新增 `scan_dict_from_points()` 与 `LidarScanAggregator`，聚合多个 parsed `LidarPoint` 后再形成 LaserScan 字典。
- 已实现：`lidar_driver` ROS runtime 默认使用聚合路径发布 `/scan`；`scan_dict_from_packet()` 保持旧入口兼容测试。
- 已实现：新增 `scan_aggregation_max_packets` / `scan_aggregation_min_points` 参数，默认 `24` / `48`，避免单个窄角度 packet 直接发布，同时保留 no-wrap 兜底。
- 已实现：`make_mock_packet()` 支持传入 start/end angle，用于构造回绕单测；默认参数保持原 mock 行为。
- 已实现：更新 `docs/hardware/board_sensor_stack_smoke.md`，记录聚合发布形态、no-motion smoke 指标和风险边界。

## 实际改动文件

- `onboard/src/ros2_trashbot_hardware/ros2_trashbot_hardware/lidar_driver.py`
- `onboard/src/ros2_trashbot_hardware/ros2_trashbot_hardware/lidar_packets.py`
- `onboard/src/ros2_trashbot_hardware/test/test_lidar_driver_stubs.py`
- `onboard/src/ros2_trashbot_hardware/test/test_lidar_packets.py`
- `docs/hardware/board_sensor_stack_smoke.md`
- `sprints/2026.06.10_03-30_lidar_scan_aggregation_harden/tech-done.md`
- `sprints/2026.06.10_03-30_lidar_scan_aggregation_harden/artifacts/no_motion_lidar_smoke_2026-06-10.txt`

## 验证结果

- 本地单测：

```text
$ python3 -m unittest onboard/src/ros2_trashbot_hardware/test/test_lidar_driver_stubs.py onboard/src/ros2_trashbot_hardware/test/test_lidar_packets.py
...............
----------------------------------------------------------------------
Ran 15 tests in 0.001s

OK
```

- Docker/Humble 构建：

```text
$ bash onboard/scripts/docker_humble_build.sh
Finished <<< ros2_trashbot_bringup [6.08s]

Summary: 6 packages finished [52.9s]
```

- 真实上位机 SSH：

```text
$ ssh root@192.168.1.11 -p 37878 'echo connected'
connected
```

- 真实上位机只构建硬件包：

```text
$ colcon build --symlink-install --packages-select ros2_trashbot_hardware
Starting >>> ros2_trashbot_hardware
Finished <<< ros2_trashbot_hardware [5.91s]

Summary: 1 package finished [7.19s]
```

- 真实上位机 no-motion LiDAR smoke：启动 `lidar_driver --ros-args -p serial_port:=/dev/ttyACM0 -p serial_baudrate:=150000` 后采样 `/scan`，未发布 `/cmd_vel`。

```text
{"angle_max": 6.267913818359375, "angle_min": 3.1421380043029785, "angle_span_deg": 179.0937618495007, "finite_count": 161, "range_max": 8.0, "range_min": 0.05000000074505806, "ranges_count": 161}
--- lidar_driver.log tail ---
[INFO] [1781033689.357307401] [lidar_driver]: LiDAR serial started: /dev/ttyACM0 @ 150000
```

- 真实上位机清理检查：

```text
$ pgrep -af "[r]os2 run ros2_trashbot_hardware lidar_driver" || true
# no output
```

## 失败定位与修复

- 远端首次构建使用 SSH 默认 shell 直接 `source /opt/ros/humble/setup.bash`，失败于 `/root/rober/onboard/setup.sh`；改用远端 `bash -lc` 后构建通过。
- 远端 smoke 脚本第一次本地引号未闭合，未触达远端执行；改用 SSH heredoc。
- 远端 smoke 脚本第二次在 `set -u` 下 source ROS setup，失败于 `AMENT_TRACE_SETUP_FILES` 未定义；将 ROS setup 放在 `set -u` 前后 smoke 通过。

## 剩余风险

- 本轮证明 `/scan` 不再由单个窄角 packet 直接发布，并在真实上位机 no-motion 场景取得 `ranges_count=161`、`finite_count=161`、`angle_span_deg≈179.09` 的聚合帧。
- 本轮没有发送 `/cmd_vel`，因此不证明真实底盘运动、LiDAR motion-delta、机械标定、实测里程计或 WAVE ROVER HIL 准入。
- 聚合后的 `angle_increment` 是当前真实点集的平均步长；未覆盖角度不会填虚假距离，上层 motion-delta 仍应按实际 `angle_min/max/ranges` 做保守判断。
- 现场 LiDAR 波特率 `150000` 仍是实板 smoke 事实，不是 WAVE ROVER 底盘 UART vendor 默认；后续换硬件或固件时需重新确认。
