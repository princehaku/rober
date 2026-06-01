# O1 Readiness Probe Hardening

sprint_type: micro

## 实际改动

- `onboard/scripts/o1_upper_computer_readiness_probe.py`
  - 将 LiDAR readiness JSON 从历史 ROS1/protocol reference 口径收敛为当前 ROS2 source-of-truth：`docs/vendor/lidar_pkg_ros2-main/`。
  - 在 JSON 中显式输出 ROS2 LiDAR reference：`150000` baud、`A5 60` 启动命令、`A5 00 A5 65 A5 65` 停止序列、`0xAA 0x55` 包头、`/dev/lidar`、`/scan`、`laser` frame、STC udev `34bf:ff0a`。
  - 保留 `docs/vendor/lidar_ros/` 作为 `historical_protocol_reference`，避免误删历史对照资料，但不再把它写成当前 ROS2 source-of-truth。
  - `_is_pyserial_available()` 改为异常 fail-closed，半初始化/stub `serial` 或异常 import spec 不会导致 readiness JSON 崩溃。
- `onboard/src/ros2_trashbot_hardware/test/test_o1_upper_computer_readiness_probe.py`
  - 增加 ROS2 LiDAR vendor source 覆盖测试。
  - 增加 LiDAR readiness contract 测试，锁住 source-of-truth、启动/停止命令、udev、topic 和 not-HIL 边界。
  - 增加 pyserial 半初始化/stub 与异常 import spec 回归测试。
- `docs/hardware/o1_upper_computer_readiness_probe.md`
  - 同步说明当前 ROS2 LiDAR vendor source-of-truth、历史 ROS1/protocol comparison 边界和 pyserial fail-closed 行为。

## 验证结果

- `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s onboard/src/ros2_trashbot_hardware/test -p 'test_o1_upper_computer_readiness_probe.py'`
  - 结果：`Ran 7 tests in 0.193s`，`OK`。
- `python3 -m py_compile onboard/scripts/o1_upper_computer_readiness_probe.py`
  - 结果：通过，无输出。
- `git diff --check -- onboard/scripts/o1_upper_computer_readiness_probe.py onboard/src/ros2_trashbot_hardware/test/test_o1_upper_computer_readiness_probe.py docs/hardware/o1_upper_computer_readiness_probe.md sprints/2026.06.02_04-05_o1-readiness-probe-hardening/tech-done.md`
  - 结果：通过，无输出。
- `python3 onboard/scripts/o1_upper_computer_readiness_probe.py --once-json | python3 -m json.tool >/tmp/o1_readiness_probe_local_check.json`
  - 结果：本地只读 JSON 可解析；`schema=trashbot.o1.upper_computer_readiness.v1`，`safe_to_control=false`，`sends_commands=false`，`opens_serial_devices=false`，`lidar_reference_readiness.source_of_truth=docs/vendor/lidar_pkg_ros2-main/`，`pyserial.opened=false`。
- `timeout 12 ssh -o BatchMode=yes -o ConnectTimeout=5 -p 37878 root@192.168.1.11 'python3 -s - --once-json' < onboard/scripts/o1_upper_computer_readiness_probe.py`
  - 结果：未连通，`ssh: connect to host 192.168.1.11 port 37878: No route to host`。这是 SSH 网络层不可达边界，不是 probe 逻辑失败；未执行远端串口或控制动作。

## 剩余风险

- 本轮 probe 仍严格 read-only：不打开串口、不发送 WAVE ROVER JSON、不启动 LiDAR、不启动 ROS2 控制链路、不发送 `/cmd_vel`，因此不构成 HIL pass。
- ROS2 LiDAR `/scan` 连续输出、TF/Nav2/SLAM 消费链路、目标硬件 `150000` 长时间稳定性仍未验证。
- WAVE ROVER 真实 UART、真实 `T=1001` feedback、真实底盘控制、IMU/battery/odom 标定仍未验证。
- O1 仍是最低完成度 Objective，本 micro sprint 只推进 readiness artifact 的 vendor 覆盖与 fail-closed 稳健性，不改变真实硬件完成度边界。
