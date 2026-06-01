# Tech Done

sprint_type: micro

## 实际改动

- `onboard/src/ros2_trashbot_hardware/ros2_trashbot_hardware/lidar_driver.py`
  - 增加 `LidarRuntimeConfig` 和 `LidarSerialSession`，把真实串口打开、启动命令、读 bytes、packet 重同步和关闭流程从 ROS2 Node 中拆出，便于无硬件 fake serial 单测。
  - 增加 `LIDAR_START_COMMAND = A5 60` 和 `LIDAR_STOP_COMMAND = A5 00 A5 65 A5 65`；真实串口模式打开后立即发送启动命令，节点销毁时 best-effort 发送停止序列并关闭串口。
  - 保持 `mock_scan` 和 `mock_packets` 软件验证路径：任一 mock 路径启用时不打开串口、不发送 `A5 60`，避免 CI 或无硬件环境误控设备。
  - 真实串口模式条件为 `mock_scan=false` 且 `mock_packets` 为空；读取串口 bytes 后继续复用 `find_packets` / `scan_dict_from_packet` 发布 `LaserScan`，`publish_raw_packets=true` 时同步发布 raw packet。
- `onboard/src/ros2_trashbot_hardware/test/test_lidar_driver_stubs.py`
  - 增加 `FakeSerial`，验证 `/dev/ttyACM0`、`150000` 配置会传入串口工厂。
  - 覆盖 fake serial 收到 `A5 60` 启动和 `A5 00 A5 65 A5 65` 停止字节。
  - 覆盖 `mock_scan` 和 `mock_packets` 路径不会打开串口。
- `docs/hardware/lidar_ros_reference.md`
  - 补充 `docs/vendor/lidar_pkg_ros2-main/` 参考来源、启动/停止命令和 STC udev 规则事实。
  - 保留 `docs/vendor/lidar_ros/` 为历史 ROS1/protocol comparison，避免破坏旧证据链。
  - 更新 Stage 2 状态：ROS2 driver 已具备真实串口启动路径，但真实 `/scan` 连续输出、TF、SLAM/Nav2 消费仍未证明。
- `docs/interfaces/lidar_ros2_closed_loop.md`
  - 新增 Driver Runtime Contract，明确 mock、真实串口、raw packet、停止序列和证据边界。
  - 真机 smoke 示例更新为用户已手动验证的 `/dev/ttyACM0`、`150000`，但仍要求上车时显式传参。
- `docs/vendor/VENDOR_INDEX.md`
  - 新增双快照口径：`lidar_pkg_ros2-main` 是当前 ROS2/STC source of truth，旧 `lidar_ros` 只作为历史 ROS1/protocol comparison。
- `onboard/scripts/o1_wave_rover_serial_feedback_probe.py`
  - 同步补充设备清单、`root_cause_hints`、`t1001_feedback_status` 和 `next_required_checks[]`，让无 `T=1001` 的下一步现场检查可机器读取。
- `docs/hardware/o1_wave_rover_serial_feedback_probe.md`
  - 同步诊断合同字段和 2026-06-02 远端 SSH `No route to host` 边界。

## 验证结果

- `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s onboard/src/ros2_trashbot_hardware/test -p 'test_lidar*.py'`
  - 结果：`Ran 11 tests in 0.001s`，`OK`。
- `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest onboard/src/ros2_trashbot_hardware/test/test_o1_wave_rover_serial_feedback_probe.py`
  - 结果：`Ran 9 tests in 0.260s`，`OK`。
- `python3 -m compileall -q onboard/src/ros2_trashbot_hardware onboard/scripts/o1_wave_rover_serial_feedback_probe.py`
  - 结果：通过，无输出。
- `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s onboard/src/ros2_trashbot_bringup/test -p 'test_launch_contract_static.py'`
  - 结果：`Ran 11 tests in 0.089s`，`OK`。
- `git diff --check -- docs/vendor/VENDOR_INDEX.md docs/hardware/lidar_ros_reference.md docs/interfaces/lidar_ros2_closed_loop.md onboard/src/ros2_trashbot_hardware/ros2_trashbot_hardware/lidar_driver.py onboard/src/ros2_trashbot_hardware/test/test_lidar_driver_stubs.py onboard/scripts/o1_wave_rover_serial_feedback_probe.py onboard/src/ros2_trashbot_hardware/test/test_o1_wave_rover_serial_feedback_probe.py sprints/2026.06.02_01-02_lidar-start-command/tech-done.md`
  - 结果：通过，无输出。
- `PYTHONDONTWRITEBYTECODE=1 bash onboard/scripts/run_smoke_tests.sh`
  - 首轮失败：`o1_upper_computer_readiness_probe.py` 在测试 stub 场景下调用 `importlib.util.find_spec("serial")` 抛出 `ValueError: serial.__spec__ is None`。
  - 修复：新增 `_is_pyserial_available()`，把 `ImportError`、`AttributeError`、`ValueError` 都按 pyserial unavailable fail-closed 处理，并补充 LiDAR ROS2/STC vendor source contract。
  - 复验结果：interfaces 6 OK、hardware 53 OK、nav 52 OK、bringup 11 OK、behavior 841 OK、vision 13 OK。behavior 段出现 Python `ResourceWarning: unclosed <socket.socket ...>`，但 unittest 退出码为 0。
- 临时文档漂移检查：
  - `docs/hardware/lidar_pkg_ros2_reference.md` 和 `docs/interfaces/lidar_pkg_ros2_closed_loop.md` 已删除；内容合并回原路径。
  - `docs/vendor/lidar_ros/` 已恢复并保留为历史 ROS1/protocol comparison。

## 失败定位

- 首轮完整 smoke 失败根因是 readiness probe 的 pyserial import-spec 检测不兼容测试 stub，不是 LiDAR runtime、WAVE ROVER vendor 协议或 ROS2 launch contract 失败。
- 子 agent 曾多次超时未完成最终结果，主会话接手完成文档纠偏、临时新文档删除和验证收口。

## 剩余风险

- 本轮未接入真实 LiDAR 跑 ROS2 runtime，fake serial 只能证明软件发送了启动/停止 bytes，不能证明真实电机停止、raw packet 稳定、`/scan` 连续发布或 SLAM/Nav2 可消费。
- `/dev/ttyACM0` 和 `150000` 来自用户手动 Python 串口测试与 vendor 参考；真实上车仍需确认容器设备透传、权限、udev/by-id 稳定性和长时间运行。
- `laser_frame` 到 `base_link` 的真实安装位姿仍未测量，当前 launch TF 默认全零只是软件占位。

## 协同需求

- Hardware：需要后续上车确认 udev/by-id、容器设备透传、物理停止效果和长时间 `150000` 稳定性。
- Autonomy：需要在真实 `/scan` 连续输出后验证 SLAM/Nav2 消费、TF 和建图质量。
- Product / Full-Stack：本 micro sprint 暂不需要。

## OKR 最低优先级提示

本 micro sprint 针对当前最低 Objective O1：硬件协议可信底盘中的真实 LiDAR `/scan` 缺口，把用户已验证的启动命令落到 ROS2 driver 软件路径。
