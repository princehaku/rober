# O1 Upper Computer Readiness Probe Tech Done

## sprint_type

micro

## 实际改动

- 新增 `onboard/scripts/o1_upper_computer_readiness_probe.py`：dependency-free 只读 readiness probe，输出 `trashbot.o1.upper_computer_readiness.v1` JSON，固定 `safe_to_control=false`、`sends_commands=false`、`robot_control_executed=false`、`delivery_success=false`。
- 新增 `onboard/src/ros2_trashbot_hardware/test/test_o1_upper_computer_readiness_probe.py`：覆盖输出 contract、串口候选 glob 注入、fail-closed 字段、vendor source/boundary、safe command list 不包含 move/turn/control/cmd_vel/T=1/T=13/T=131。
- 新增 `docs/hardware/o1_upper_computer_readiness_probe.md`：记录 vendor 来源、运行命令、输出 contract、远端采集方式和 not_proven 边界。

## 已读 vendor 来源

- `docs/vendor/VENDOR_INDEX.md`
- `docs/vendor/waveshare_wave_rover/ugv_rpi/base_ctrl.py`
- `docs/vendor/waveshare_wave_rover/ugv_rpi/config.yaml`
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/json_cmd.h`
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/uart_ctrl.h`
- `docs/vendor/lidar_pkg_ros2-main/README.md`
- `docs/vendor/lidar_pkg_ros2-main/src/lidar_node.cpp`
- `docs/vendor/lidar_pkg_ros2-main/config/lidar_params.yaml`
- `docs/vendor/lidar_pkg_ros2-main/scripts/99-lidar.rules`

## 已证实的硬件结论

- WAVE ROVER vendor reference 是 UART + UTF-8 newline-delimited JSON；Raspberry Pi reference 路径 `/dev/ttyAMA0`、baud `115200` 不能直接当 Orange Pi 真实路径。
- `T=1`、`T=13`、`T=131` 都可能改变底盘或反馈流状态，本轮 probe 只列入 `blocked_commands_not_sent`，未发送。
- LiDAR `150000` baud、`A5 60` 启动命令、`0xAA 0x55`、`/scan`、`/lidar/raw_packet` 仍是 vendor/software reference 加用户手动启动观察，不是 HIL。

## 验证结果

- `python3 -m py_compile onboard/scripts/o1_upper_computer_readiness_probe.py`
  - 通过，无输出。
- `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest onboard/src/ros2_trashbot_hardware/test/test_o1_upper_computer_readiness_probe.py`
  - 通过：`Ran 6 tests in 0.157s`，`OK`。
- `python3 onboard/scripts/o1_upper_computer_readiness_probe.py --once-json`
  - 通过，输出 `schema=trashbot.o1.upper_computer_readiness.v1`，本地 `safe_to_control=false`、`sends_commands=false`、`robot_control_executed=false`、`delivery_success=false`；本地 `/opt/ros/humble/setup.bash` 不存在；本地串口候选总数为 `0`；本地 `pyserial.available=true`。
- `ssh -p 37878 root@192.168.1.11 'python3 -s -- --once-json' < onboard/scripts/o1_upper_computer_readiness_probe.py`
  - 按验收原命令运行，失败：`python3: can't open file '/root/--once-json': [Errno 2] No such file or directory`。定位：远端 Python 把 `--once-json` 当成脚本路径；这不是 SSH 连通性失败，也不是 probe 行为失败。
  - 使用等价 stdin 语法补采：`ssh -p 37878 root@192.168.1.11 'python3 -s - --once-json' < onboard/scripts/o1_upper_computer_readiness_probe.py`，通过。
- `git diff --check -- onboard/scripts/o1_upper_computer_readiness_probe.py onboard/src/ros2_trashbot_hardware/test/test_o1_upper_computer_readiness_probe.py docs/hardware/o1_upper_computer_readiness_probe.md sprints/2026.06.01_15-16_o1-upper-computer-readiness-probe/tech-done.md`
  - 通过，无输出。
- 中文技术注释比例检查：
  - `onboard/scripts/o1_upper_computer_readiness_probe.py`：`46/211=21.80%`
  - `onboard/src/ros2_trashbot_hardware/test/test_o1_upper_computer_readiness_probe.py`：`24/97=24.74%`

## 远端 SSH 脱敏摘要

- `schema=trashbot.o1.upper_computer_readiness.v1`
- fail-closed 字段：`safe_to_control=false`、`sends_commands=false`、`robot_control_executed=false`、`delivery_success=false`
- host 脱敏摘要：Linux `aarch64`，kernel `6.1.31-sun50iw9`，Python `3.10.12`
- `pyserial.available=false`，未 import/open 串口
- `/opt/ros/humble/setup.bash` 不存在，`ROS_DISTRO` 为空
- repo root 未发现，stdin 执行时 cwd 为 `/root`
- 串口候选只枚举不打开：`/dev/ttyACM0`、`/dev/serial`、`/dev/serial/by-id/usb-STC_STC_USB_Serial-if00`、`/dev/serial/by-path/platform-5311400.usb-usb-0:1:1.0`
- LiDAR readiness 仍为 `software_reference_not_hil`
- WAVE ROVER readiness 仍为 `not_ready_for_control`
- 仓库未保存远端原始 artifact。

## 剩余风险

- 真实 WAVE ROVER UART/HIL、真实 `T=1001` feedback、真实 Orange Pi 串口路径、真实 LiDAR USB path 和 `150000` 稳定性仍 `not_proven`。
- 本轮只证明可以安全采集上位机 readiness 材料，不证明底盘可控、LiDAR 可用、Nav2/SLAM ready 或送达闭环。

## O1 进度建议

若本地验证和 SSH 远端只读快照均通过，可建议 O1 从 91% 调整到 92%：理由是新增了真实上位机材料采集入口和一次 fail-closed 环境快照。但不能写成 HIL pass，因为没有打开串口、没有 WAVE ROVER feedback、没有发送控制命令、没有真实 LiDAR `/scan`。

## Product Closeout

- 用户价值和产品北极星：本轮把 O1 从纯 software_reference / mock skeleton 推进到真实上位机 readiness 可观测，帮助后续按证据安排 UART/HIL、LiDAR `/scan`、ROS Humble runtime、pyserial 和 Nav2/SLAM 实机补齐；仍服务于低成本自主垃圾投递机器人“可信底盘控制层”。
- OKR 映射和方向判断：Objective 1 从约 91% 调整为约 92% `software_reference + upper-computer readiness observed`；方向为**继续**，不替换、不暂停。
- KR 更新：O1 KR1-KR6 仍在当前推进区，不归档；本轮只补强上位机 readiness 证据链，不把任何 KR 标记为真实 HIL 完成。
- 本轮核心抓手：只读 probe + 远端 SSH fail-closed 快照，确认真实上位机 Linux/Python/串口候选状态，以及 `pyserial.available=false`、`/opt/ros/humble/setup.bash` 不存在等缺口。
- 需要做什么：下一轮由 Hardware Infra Engineer 继续补真实 WAVE ROVER UART/HIL、真实串口打开、真实 `T=1001` feedback；Robot Software Engineer 补 ROS Humble runtime 与硬件桥实机启动证据；Robot Algorithm Engineer 在 LiDAR `/scan` 可用后补 TF、Nav2/SLAM 消费链路。
- 优先级和验收口径：O1 已不再与 O5/O6 并列最低，下一轮 OKR 最低优先级优先看 O5/O6；若继续推进 O1，验收必须包含真实设备串口打开、真实反馈包或真实 `/scan`，并明确 `safe_to_control` 何时仍需保持 false。
- 对应责任 Engineer：主责 `rober-hardware-engineer`；ROS runtime 和 bringup 证据由 `robot-software-engineer` 协作；LiDAR 到 Nav2/SLAM 证据由 `robot-algorithm-engineer` 协作。
- 风险、阻塞和证据链缺口：真实 WAVE ROVER UART/HIL、真实 `T=1001`、真实 LiDAR `/scan`、ROS Humble runtime、pyserial、Nav2/SLAM、真实串口打开仍 `not_proven`；本轮不是 HIL pass。
- 已完成 KR 历史记录：无 KR 完成归档；历史记录追加到 `docs/process/okr_progress_log.md` 的 `2026-06-01 15-16｜o1-upper-computer-readiness-probe` 小节，证据来源为本文件和 `docs/hardware/o1_upper_computer_readiness_probe.md`。
- Sprint 文档：本 micro sprint 保持 `tech-done.md` 作为唯一必需留档；Product closeout 已同步 `OKR.md` 和 `docs/process/okr_progress_log.md`。
