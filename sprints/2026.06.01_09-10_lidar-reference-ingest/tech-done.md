# 2026.06.01 09-10 LiDAR Reference Ingest

sprint_type: micro

## 实际改动

- 新增 `docs/vendor/lidar_ros/` 参考快照，来源为 `https://github.com/sudreamcarver/lidar_ros`，commit `a88fcec0a207e0a2765fb4542ffbc8b1913f60ee`，获取时间 `2026-06-01T01:46:25Z`。
- 快照保留 `README.md`、`LICENSE`、`plot.py`、`src/lidar_pkg` 下 package/launch/rviz/scripts/src 文件；排除 `.git/`、`.clangd/`、`compile_commands.json`、`.catkin_workspace`。
- 更新 `docs/vendor/VENDOR_INDEX.md`，新增 LiDAR 参考资料入口、已证实事实和后续 Agent 使用规则。
- 新增 `docs/hardware/lidar_ros_reference.md`，梳理 ROS2 闭环接入前置事实、建议接入方式、验收命令、Mock 边界和真实上车风险。

## 验证结果

本轮按任务要求执行以下验收：

```bash
git status --short
test -d docs/vendor/lidar_ros && find docs/vendor/lidar_ros -maxdepth 3 -type f | head -80
python3 - <<'PY'
from pathlib import Path
for p in ['docs/vendor/VENDOR_INDEX.md','docs/hardware/lidar_ros_reference.md','sprints/2026.06.01_09-10_lidar-reference-ingest/tech-done.md']:
    text=Path(p).read_text(encoding='utf-8')
    assert 'lidar_ros' in text or 'LiDAR' in text or '雷达' in text, p
print('lidar reference docs ok')
PY
```

结果：

- `git status --short`：

```text
 M docs/vendor/VENDOR_INDEX.md
?? docs/hardware/lidar_ros_reference.md
?? docs/vendor/lidar_ros/
?? sprints/2026.06.01_09-10_lidar-reference-ingest/
```

- `find docs/vendor/lidar_ros -maxdepth 3 -type f | head -80`：

```text
docs/vendor/lidar_ros/LICENSE
docs/vendor/lidar_ros/plot.py
docs/vendor/lidar_ros/README.md
docs/vendor/lidar_ros/SOURCE.md
docs/vendor/lidar_ros/src/lidar_pkg/CMakeLists.txt
docs/vendor/lidar_ros/src/lidar_pkg/package.xml
```

- 文档关键字检查：

```text
lidar reference docs ok
```

- `docs/vendor/lidar_ros` 目录存在，且包含 `SOURCE.md`、上游 README、plot 脚本和 ROS1 `lidar_pkg` 参考文件。
- 三份文档均包含 `lidar_ros` / `LiDAR` / `雷达` 关键内容。
- 本轮未运行 ROS2 build 或 launch，因为任务明确禁止修改 `onboard/`，本阶段只做参考资料入库和事实梳理。

## 已证实硬件/软件事实

- 该上游仓库是 ROS1/catkin 参考，不是 ROS2/ament 包。
- 包名为 `lidar_pkg`，launch 文件为 `src/lidar_pkg/launch/lidar_vi.xml`。
- README 说明雷达为拆机 YDLIDAR，使用 `150000` 非标准波特率。
- Python reader 默认串口为 `/dev/ttyUSB0`，默认波特率为 `150000`。
- packet 同步头为 `0xAA 0x55`，以 `LSN` 推导剩余 payload 长度。
- Python reader 发布 `/lidar/raw_packet`，消息为 `std_msgs/UInt8MultiArray`。
- C++ parser 订阅 `/lidar/raw_packet`，发布 `sensor_msgs/LaserScan`，默认 `frame_id=laser_frame`。
- RViz 配置固定帧为 `laser_frame`，显示话题为 `/lidar_parser_node/scan`。

## 剩余风险

- 尚未确认机器人真实 LiDAR USB 设备路径、权限、供电、安装角度和线缆稳定性。
- 尚未验证 Orange Pi Ubuntu、Docker 设备透传和目标 USB-UART 对 `150000` 波特率的支持。
- 尚未完成 ROS2 Humble 移植；参考仓库不能直接作为 `onboard/` 生产代码使用。
- 尚未验证 `/scan` 与 TF、SLAM/Nav2 的真实闭环；本轮没有 `source=hil_pass`。
- 参考 README 明确“本测试无角度修正”，后续导航使用前必须评估角度误差影响。

## 下一步履约动作

- Robot Platform Engineer 基于本参考资料实现 ROS2 LiDAR package/launch，不直接拷贝 ROS1 包进入生产路径。
- 参数必须暴露 `serial_port`、`serial_baudrate`、`frame_id`、`raw_packet_topic`、`scan_topic` 等配置入口。
- 真实上车前再次查阅 `docs/vendor/VENDOR_INDEX.md` 与 `docs/hardware/lidar_ros_reference.md`，并记录 `ros2 topic hz /scan`、`ros2 topic echo --once /scan`、TF 和 RViz/SLAM 证据。

## 当前 Hardware Infra 复核补充（2026-06-01 11:45）

- 已读来源：`AGENTS.md`、`OKR.md`、`docs/vendor/VENDOR_INDEX.md`、`docs/vendor/lidar_ros/SOURCE.md`、`README.md`、`plot.py`、ROS1 `scripts/lidar_driver.py`、C++ parser、`launch/lidar_vi.xml`。
- 确认事实：上游是 ROS1/catkin reference；LiDAR 软件参考参数为 `/dev/ttyUSB0`、`150000` baud、`0xAA 0x55` header、按 `LSN` 计算长度、`/lidar/raw_packet` raw topic、LaserScan 输出和 `laser_frame`。这些仍是 `source=software_reference`，不是 HIL。
- 本轮曾在允许路径补齐 `ros2_trashbot_hardware` LiDAR parser/driver/test、`bringup.launch.py` gated node 和 range/timing 参数，并通过 focused tests；但随后工作区发生并发/外部改动，当前 LiDAR 源码/测试不在 `ros2_trashbot_hardware`，而在范围外 `ros2_trashbot_nav` 未跟踪文件中。按本轮文件范围，不继续搬动或回滚范围外内容。
- 已通过验证：`python3 -m unittest discover -s onboard/src/ros2_trashbot_hardware/test -p 'test_lidar_*.py'` 曾返回 `Ran 7 tests OK`；`python3 -m unittest discover -s onboard/src/ros2_trashbot_bringup/test -p 'test_launch_contract_static.py'` 返回 `Ran 11 tests OK`；`python3 -m py_compile ...lidar_packets.py ...lidar_driver.py ...bringup.launch.py` 通过；`git diff --check` 通过。
- Smoke 结果：任务指定的 `scripts/run_smoke_tests.sh` 不存在；实际存在的是 `onboard/scripts/run_smoke_tests.sh`。运行 `PYTHONDONTWRITEBYTECODE=1 bash onboard/scripts/run_smoke_tests.sh` 通过：interfaces 6 OK、hardware 26 OK、nav 52 OK、bringup 11 OK、behavior 841 OK、vision 13 OK。
- Docker 结果：`docker --version` 失败，当前 WSL 发行版没有 Docker CLI / Docker Desktop WSL integration，未运行 `bash onboard/scripts/docker_humble_build.sh`。
- 当前阻塞/风险：工作区存在范围外并发改动（OKR、process log、bringup package、nav package/setup、nav LiDAR files、额外 sprint 等）；真实 LiDAR USB、供电、线缆、150000 波特率、TF 安装位姿、Nav2/SLAM 消费和 HIL 仍未验证。
