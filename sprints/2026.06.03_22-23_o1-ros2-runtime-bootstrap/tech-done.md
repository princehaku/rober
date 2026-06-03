# O1 ROS2 Runtime Bootstrap Micro Sprint

## sprint_type

sprint_type: micro

## 已读 vendor 来源

- `AGENTS.md`
- `OKR.md`
- `docs/vendor/VENDOR_INDEX.md`
- `docs/vendor/lidar_pkg_ros2-main/README.md`
- `docs/vendor/lidar_pkg_ros2-main/src/lidar_node.cpp`
- `docs/vendor/lidar_pkg_ros2-main/config/lidar_params.yaml`
- `docs/vendor/lidar_pkg_ros2-main/launch/lidar.launch.py`
- `docs/vendor/lidar_ros/src/lidar_pkg/scripts/lidar_driver.py`（仅历史 ROS1 raw packet topic 对照）

## 已证实的硬件结论

- 当前 LiDAR ROS2/STC vendor source-of-truth 是 `docs/vendor/lidar_pkg_ros2-main/`。
- LiDAR reference：`150000` baud、启动命令 `A5 60`、停止序列
  `A5 00 A5 65 A5 65`、packet sync `0xAA 0x55`、ROS2 scan topic `/scan`。
- `/lidar/raw_packet` 是项目 driver 为真机 bringup 保留的 raw packet 证据 topic，
  其历史形态可从 `docs/vendor/lidar_ros/` 对照；当前 ROS2 vendor driver 默认只发布
  `sensor_msgs/msg/LaserScan`。
- 远端上位机只读证据：Ubuntu 22.04.5 LTS `aarch64`，`/dev/ttyACM0` 与
  `usb-STC_STC_USB_Serial-if00 -> ../../ttyACM0` 存在，pyserial 可用。
- 远端仍缺 ROS2 Humble runtime、当前 `/root/rober/onboard/install` 和构建后的
  `lidar_driver` entrypoint；真实 `/scan` 仍未证明。

## 实际改动

- `onboard/scripts/o1_upper_computer_readiness_probe.py`
  - remediation 从泛化文本改为指向可执行脚本：
    `o1_ros2_humble_arm64_bootstrap.sh` 与 `o1_lidar_ros2_scan_smoke.sh`。
- `onboard/scripts/test_o1_upper_computer_readiness_probe.py`
  - 新增测试，确认 runtime 缺失时输出 bootstrap 脚本，topic 未运行时输出
    LiDAR-only smoke 脚本，且命令不包含底盘运动入口。
- `onboard/scripts/o1_ros2_humble_arm64_bootstrap.sh`
  - 新增 Ubuntu 22.04 arm64 ROS2 Humble runtime/install/build bootstrap。
  - 不打开串口、不写 `/dev/ttyS5`、不调用 8787 控制 API、不启动 driver。
- `onboard/scripts/o1_lidar_ros2_scan_smoke.sh`
  - 新增 LiDAR-only `/scan`、`/lidar/raw_packet`、TF 证据采集脚本。
  - 显式拒绝 `/dev/ttyS5`，不发布 `/cmd_vel`，不调用 `/api/base/manual`。
- `docs/hardware/o1_upper_computer_readiness_probe.md`
  - 记录两个脚本、远端 OS/arch/runtime/docker/apt/source 证据和 blocker。
- `docs/interfaces/lidar_ros2_closed_loop.md`
  - 记录 bootstrap/smoke 脚本在 LiDAR ROS2 closed-loop 中的职责与安全边界。
- `docs/process/okr_progress_log.md`
  - 追加 2026-06-03 22-23 O1 进展，O1 百分比不调整。
- `OKR.md`
  - 追加本轮 O1 进展，并更新当前最高优先级 next action。

## 远端证据

执行的远端命令均为 SSH shell 检查或源码同步，没有 apt install、colcon build、
ROS2 driver 启动或 topic 采集。

关键摘要：

```text
PRETTY_NAME="Ubuntu 22.04.5 LTS"
uname -m -> aarch64
apt-get -> /usr/bin/apt-get
ROS_SETUP_MISSING
ROBER_INSTALL_MISSING
ONBOARD_PRESENT
LIDAR_DRIVER_SOURCE_MISSING
Python 3.10.12
pyserial_available True
docker server_arch=arm64
osrf/ros:humble-desktop -> amd64
/dev/serial/by-id/usb-STC_STC_USB_Serial-if00 -> ../../ttyACM0
/dev/ttyACM0 present
trashbot-upper-robot-api.service -> active
```

后续 `rsync` 只同步当前 `onboard/src` 与 `onboard/scripts` 到
`/root/rober/onboard/`，没有 `--delete`，没有运行 bootstrap 安装或 scan smoke。

## 验证结果

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest onboard/scripts/test_o1_upper_computer_readiness_probe.py
# Ran 9 tests in 1.020s
# OK

python3 -m py_compile onboard/scripts/o1_upper_computer_readiness_probe.py onboard/scripts/test_o1_upper_computer_readiness_probe.py
# passed

bash -n onboard/scripts/o1_ros2_humble_arm64_bootstrap.sh
# passed

bash -n onboard/scripts/o1_lidar_ros2_scan_smoke.sh
# passed

git diff --check -- onboard/scripts/o1_upper_computer_readiness_probe.py onboard/scripts/test_o1_upper_computer_readiness_probe.py onboard/scripts/o1_ros2_humble_arm64_bootstrap.sh onboard/scripts/o1_lidar_ros2_scan_smoke.sh docs/hardware/o1_upper_computer_readiness_probe.md docs/interfaces/lidar_ros2_closed_loop.md docs/process/okr_progress_log.md OKR.md sprints/2026.06.03_22-23_o1-ros2-runtime-bootstrap/tech-done.md
# passed
```

## 剩余风险

- 真实 ROS2 `/scan` once/hz、`/lidar/raw_packet` once 和 TF 仍未采集。
- 远端 ROS2 Humble runtime 尚未安装，`onboard/install` 尚未重建。
- 远端 apt ROS2 source/key 尚未配置；Docker 现有 ROS image 架构不匹配。
- 新脚本尚未在远端执行安装/build/smoke，因此不能写为 HIL、LiDAR ready、
  `safe_to_control=true`、ACK 或 delivery success。

## 安全声明

本轮没有发送任何底盘运动命令：没有调用 `/api/base/manual`，没有写 `/dev/ttyS5`，
没有发送 WAVE ROVER `T=1/T=13/T=130/T=131`，没有发布 `/cmd_vel`。本轮也没有运行
LiDAR smoke 脚本，因此没有在本轮新增发送 `A5 60`。
