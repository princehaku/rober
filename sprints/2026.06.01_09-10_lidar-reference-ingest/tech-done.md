# 2026.06.01 09-10 LiDAR Reference Ingest

## 2026-06-02 纠偏说明

本 sprint 的原始 LiDAR 来源判断已被后续真实设备观察修正：旧 `lidar_ros`
快照保留为历史 ROS1/protocol comparison，不作为当前机器人 ROS2/STC driver
source-of-truth。当前实现依据是 `docs/vendor/lidar_pkg_ros2-main/`；后续以
`docs/hardware/lidar_ros_reference.md` 和 `docs/interfaces/lidar_ros2_closed_loop.md`
为准。

sprint_type: micro

## 实际改动

- 当前 ROS2/STC 参考快照为 `docs/vendor/lidar_pkg_ros2-main/`，来源为
  `https://github.com/zhangwanjie/lidar_pkg_ros2`。
- 快照保留 `README.md`、ROS2 package/launch/config/rviz/URDF/STL 和
  `src/lidar_node.cpp`。
- 原 `docs/vendor/lidar_ros/` 快照继续保留，用于历史 ROS1/protocol 对照。
- 更新 `docs/vendor/VENDOR_INDEX.md`，新增 LiDAR 参考资料入口、已证实事实和后续 Agent 使用规则。
- 新增 `docs/hardware/lidar_ros_reference.md`，梳理 ROS2 闭环接入前置事实、建议接入方式、验收命令、Mock 边界和真实上车风险。

## 验证结果

本轮按任务要求执行以下验收：

```bash
git status --short
test -d docs/vendor/lidar_pkg_ros2-main && find docs/vendor/lidar_pkg_ros2-main -maxdepth 3 -type f | head -80
python3 - <<'PY'
from pathlib import Path
for p in ['docs/vendor/VENDOR_INDEX.md','docs/hardware/lidar_ros_reference.md','sprints/2026.06.01_09-10_lidar-reference-ingest/tech-done.md']:
    text=Path(p).read_text(encoding='utf-8')
    assert 'lidar_pkg_ros2-main' in text or 'LiDAR' in text or '雷达' in text, p
print('lidar reference docs ok')
PY
```

结果：

- `git status --short`：

```text
 M docs/vendor/VENDOR_INDEX.md
?? docs/hardware/lidar_ros_reference.md
?? docs/vendor/lidar_pkg_ros2-main/
?? sprints/2026.06.01_09-10_lidar-reference-ingest/
```

- `find docs/vendor/lidar_pkg_ros2-main -maxdepth 3 -type f | head -80`：

```text
docs/vendor/lidar_pkg_ros2-main/LICENSE
docs/vendor/lidar_pkg_ros2-main/README.md
docs/vendor/lidar_pkg_ros2-main/CMakeLists.txt
docs/vendor/lidar_pkg_ros2-main/package.xml
docs/vendor/lidar_pkg_ros2-main/config/lidar_params.yaml
docs/vendor/lidar_pkg_ros2-main/launch/lidar.launch.py
docs/vendor/lidar_pkg_ros2-main/launch/monitor.launch.py
docs/vendor/lidar_pkg_ros2-main/scripts/99-lidar.rules
docs/vendor/lidar_pkg_ros2-main/src/lidar_node.cpp
```

- 文档关键字检查：

```text
lidar reference docs ok
```

- `docs/vendor/lidar_pkg_ros2-main` 目录存在，且包含上游 README、ROS2 launch/config、
  udev 规则、RViz、URDF、STL 和 `src/lidar_node.cpp`。
- 三份文档均包含 `lidar_pkg_ros2-main` / `LiDAR` / `雷达` 关键内容。
- 本轮未运行 ROS2 build 或 launch，因为任务明确禁止修改 `onboard/`，本阶段只做参考资料入库和事实梳理。

## 已证实硬件/软件事实

- 该上游仓库是 ROS2 Humble / ament CMake 参考。
- 包名为 `lidar_pkg`，launch 文件为 `launch/lidar.launch.py` 和 `launch/monitor.launch.py`。
- 默认 config 使用 `/dev/lidar`，udev 规则把 STC USB Serial `34bf:ff0a` 映射为 `lidar`。
- `src/lidar_node.cpp` 使用 `150000` baud，启动时发送 `A5 60`，退出时发送
  `A5 00 A5 65 A5 65`。
- packet 同步头为 `0xAA 0x55`，以 `LSN` 推导剩余 payload 长度。
- C++ node 发布 `sensor_msgs/msg/LaserScan`，RViz 显示 `/scan`。

## 剩余风险

- 尚未确认机器人真实 LiDAR USB 设备路径、权限、供电、安装角度和线缆稳定性。
- 尚未验证 Orange Pi Ubuntu、Docker 设备透传和目标 USB-UART 对 `150000` 波特率的支持。
- 项目已在 `ros2_trashbot_hardware/lidar_driver` 中移植必要 runtime 行为；
  真机 `/scan` 连续输出和 SLAM 消费仍需验证。
- 尚未验证 `/scan` 与 TF、SLAM/Nav2 的真实闭环；本轮没有 `source=hil_pass`。
- 参考 README 明确“本测试无角度修正”，后续导航使用前必须评估角度误差影响。

## 下一步履约动作

- Robot Platform Engineer 基于本参考资料实现 ROS2 LiDAR package/launch，不直接拷贝 ROS1 包进入生产路径。
- 参数必须暴露 `serial_port`、`serial_baudrate`、`frame_id`、`raw_packet_topic`、`scan_topic` 等配置入口。
- 真实上车前再次查阅 `docs/vendor/VENDOR_INDEX.md` 与 `docs/hardware/lidar_ros_reference.md`，并记录 `ros2 topic hz /scan`、`ros2 topic echo --once /scan`、TF 和 RViz/SLAM 证据。

## 当前 Hardware Infra 复核补充（2026-06-01 11:45）

- 已读来源已纠偏为：`AGENTS.md`、`OKR.md`、`docs/vendor/VENDOR_INDEX.md`、
  `docs/vendor/lidar_pkg_ros2-main/README.md`、`src/lidar_node.cpp`、
  `config/lidar_params.yaml`、`scripts/99-lidar.rules`、`launch/*.py`。
- 确认事实：上游是 ROS2 Humble reference；LiDAR 软件参考参数为 `/dev/lidar`
  或实测 `/dev/ttyACM0`、`150000` baud、`A5 60` 启动、`0xAA 0x55` header、
  按 `LSN` 计算长度、`/scan` LaserScan 输出。这些仍是
  `source=software_reference + user_manual_serial_observed_start`，不是 HIL。
- 后续 `2026.06.01_10-11_lidar-ros2-driver-skeleton` 已把 LiDAR parser/driver/test 收敛到 `ros2_trashbot_hardware`，`bringup.launch.py` gated node 也指向 `ros2_trashbot_hardware/lidar_driver`；`ros2_trashbot_nav` 只消费 `/scan`、TF 和 SLAM/Nav2 结果，不承载重复 driver/parser。
- 已通过验证：`python3 -m unittest discover -s onboard/src/ros2_trashbot_hardware/test -p 'test_lidar_*.py'` 曾返回 `Ran 7 tests OK`；`python3 -m unittest discover -s onboard/src/ros2_trashbot_bringup/test -p 'test_launch_contract_static.py'` 返回 `Ran 11 tests OK`；`python3 -m py_compile ...lidar_packets.py ...lidar_driver.py ...bringup.launch.py` 通过；`git diff --check` 通过。
- Smoke 结果：任务指定的 `scripts/run_smoke_tests.sh` 不存在；实际存在的是 `onboard/scripts/run_smoke_tests.sh`。运行 `PYTHONDONTWRITEBYTECODE=1 bash onboard/scripts/run_smoke_tests.sh` 通过：interfaces 6 OK、hardware 26 OK、nav 52 OK、bringup 11 OK、behavior 841 OK、vision 13 OK。
- Docker 结果：`docker --version` 失败，当前 WSL 发行版没有 Docker CLI / Docker Desktop WSL integration，未运行 `bash onboard/scripts/docker_humble_build.sh`。
- 当前阻塞/风险：工作区存在范围外并发改动（OKR、process log、bringup package、nav package/setup、nav LiDAR files、额外 sprint 等）；真实 LiDAR USB、供电、线缆、150000 波特率、TF 安装位姿、Nav2/SLAM 消费和 HIL 仍未验证。
