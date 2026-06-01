# O1 Upper Computer Readiness Probe

## 目标

`onboard/scripts/o1_upper_computer_readiness_probe.py` 是 O1 的只读上位机 readiness probe。它只采集本机环境、候选串口路径、ROS 环境提示和 repo 路径提示，不打开串口、不写 `/dev/*`、不发送 WAVE ROVER JSON 命令、不启动 ROS2 控制链路、不发送 `/cmd_vel`。

输出固定 fail-closed：

- `safe_to_control=false`
- `sends_commands=false`
- `robot_control_executed=false`
- `delivery_success=false`

## Vendor 来源

本 probe 的硬件边界来自以下本地资料：

- `docs/vendor/VENDOR_INDEX.md`
- `docs/vendor/waveshare_wave_rover/ugv_rpi/base_ctrl.py`
- `docs/vendor/waveshare_wave_rover/ugv_rpi/config.yaml`
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/json_cmd.h`
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/uart_ctrl.h`
- `docs/vendor/lidar_pkg_ros2-main/README.md`
- `docs/vendor/lidar_pkg_ros2-main/src/lidar_node.cpp`
- `docs/vendor/lidar_pkg_ros2-main/config/lidar_params.yaml`
- `docs/vendor/lidar_pkg_ros2-main/scripts/99-lidar.rules`
- `docs/vendor/lidar_ros/README.md`（仅历史 ROS1/protocol comparison，不作为当前 ROS2 source-of-truth）

已证实的软件 reference 边界：

- WAVE ROVER 上位机参考使用 UART、UTF-8 JSON、每行一个 JSON 对象并以 `\n` 结束。
- vendor Raspberry Pi reference 提到 `/dev/ttyAMA0`、`115200`；Orange Pi 实际设备名必须上机确认，不能直接继承 Raspberry Pi 路径。
- WAVE ROVER `T=1`、`T=13`、`T=131` 都属于会改变底盘或反馈流状态的命令，本 probe 只把它们列为 `blocked_commands_not_sent`，不发送。
- LiDAR 当前 source-of-truth 是 `docs/vendor/lidar_pkg_ros2-main/` ROS2 snapshot；历史 `docs/vendor/lidar_ros/` 只保留 ROS1/protocol comparison。
- ROS2 LiDAR reference 固定记录 `150000` baud、`A5 60` 启动命令、`A5 00 A5 65 A5 65` 停止序列、`0xAA 0x55` 包头、默认 `port_name="/dev/lidar"`、udev `idVendor=34bf`/`idProduct=ff0a`/symlink `lidar`、`/scan` 和可选 `/lidar/raw_packet`。这些只代表 `software_reference_not_hil` 加用户手动启动观察，不等于真实 ROS2 `/scan`、TF 或 SLAM 已跑通。

## 运行命令

本地只读 JSON：

```bash
python3 onboard/scripts/o1_upper_computer_readiness_probe.py --once-json
```

写入脱敏 artifact：

```bash
python3 onboard/scripts/o1_upper_computer_readiness_probe.py --once-json --output /tmp/o1_upper_computer_readiness.json
```

通过用户提供的上位机 SSH 入口以 stdin 方式执行：

```bash
ssh -p 37878 root@192.168.1.11 'python3 -s - --once-json' < onboard/scripts/o1_upper_computer_readiness_probe.py
```

## 输出 contract

关键字段：

- `schema=trashbot.o1.upper_computer_readiness.v1`
- `source.mode=read_only_once`
- `boundary.*` 固定 fail-closed，且 `opens_serial_devices=false`
- `vendor_sources[]` 固定列出本地 vendor 文件
- `host` 只包含 hostname、OS、kernel、machine、Python version，不包含完整网卡 MAC/IP 列表
- `serial_candidates` 只枚举 `/dev/ttyUSB*`、`/dev/ttyAMA*`、`/dev/ttyACM*`、`/dev/serial*`、`/dev/serial/by-id/*`、`/dev/serial/by-path/*`，不打开设备
- `pyserial.available` 只通过 import spec 判断，不 import 并打开串口
- 半初始化/stub `serial` 模块或异常 import spec 会被按 `pyserial.available=false` 处理，保证 JSON artifact fail-closed 输出
- `ros_env_hints.humble_setup_bash.exists` 只检查 `/opt/ros/humble/setup.bash`
- `lidar_reference_readiness.status=software_reference_not_hil`
- `lidar_reference_readiness.source_of_truth=docs/vendor/lidar_pkg_ros2-main/`
- `lidar_reference_readiness.historical_protocol_reference=docs/vendor/lidar_ros/`
- `lidar_runtime_readiness.status` 只根据 ROS2 Humble setup、pyserial、repo/workspace 和 LiDAR 串口候选判断是否允许人工进入 no-motion LiDAR smoke
- `lidar_runtime_readiness.blockers[]` 给出机器可读 blocker code，例如 `ros2_humble_setup_missing`、`pyserial_missing`、`workspace_not_found`、`lidar_serial_candidate_missing`
- `lidar_runtime_readiness.commands_if_ready[]` 只包含 ROS2 LiDAR driver 与 `/scan`、`/lidar/raw_packet` 只读观察命令；它们不发送 WAVE ROVER 底盘运动命令，也不写 `/cmd_vel`
- `wave_rover_readiness.status=not_ready_for_control`
- `next_safe_commands[]` 只包含编译、单测和只读 probe 命令

## 历史远端观察

`2026.06.01_15-16_o1-upper-computer-readiness-probe` 使用：

```bash
ssh -p 37878 root@192.168.1.11 'python3 -s -- --once-json' < onboard/scripts/o1_upper_computer_readiness_probe.py
```

按上面原命令执行时，远端 Python 把 `--once-json` 解释为脚本路径并失败：

```text
python3: can't open file '/root/--once-json': [Errno 2] No such file or directory
```

随后使用等价 stdin 语法采集成功：

```bash
ssh -p 37878 root@192.168.1.11 'python3 -s - --once-json' < onboard/scripts/o1_upper_computer_readiness_probe.py
```

脱敏摘要：

- `schema=trashbot.o1.upper_computer_readiness.v1`
- `safe_to_control=false`、`sends_commands=false`、`robot_control_executed=false`、`delivery_success=false`
- host: Linux `aarch64`，Python `3.10.12`
- `pyserial.available=false`
- `/opt/ros/humble/setup.bash` 不存在
- repo root 未发现，stdin 执行时 cwd 为 `/root`
- 串口候选只枚举不打开：`/dev/ttyACM0`、`/dev/serial`、`/dev/serial/by-id/usb-STC_STC_USB_Serial-if00`、`/dev/serial/by-path/platform-5311400.usb-usb-0:1:1.0`

仓库不保存远端原始 artifact。

## 本轮远端观察

`2026.06.02_06-07_o1-lidar-upper-runtime-readiness` 使用用户指定的只读 SSH readiness probe：

```bash
timeout 20 ssh -o BatchMode=yes -o ConnectTimeout=8 -p 37878 root@192.168.1.11 'python3 -s - --once-json' < onboard/scripts/o1_upper_computer_readiness_probe.py
```

结果：

```text
ssh: connect to host 192.168.1.11 port 37878: No route to host
```

结论：

- 本轮没有进入上位机，因此未采集到新的远端 JSON artifact。
- 未确认当前小时的 ROS2 Humble runtime、workspace、pyserial 或 LiDAR 串口状态。
- 未运行 LiDAR driver，也未采到真实 ROS2 `/scan` 或 `/lidar/raw_packet`。
- 因为 SSH 是网络层不可达，本轮新增 `lidar_runtime_readiness` gate，让下一轮一旦 SSH 恢复即可直接看到是否满足 no-motion LiDAR smoke 前置条件。

下一轮 SSH 恢复后的最小路径：

1. 先重跑同一条 readiness probe，检查 `lidar_runtime_readiness.status`。
2. 若状态是 `blocked_by_readiness`，按 `blockers[].code` 逐项补齐 ROS2 Humble、pyserial、workspace 或 LiDAR 串口候选。
3. 只有状态是 `ready_for_no_motion_lidar_smoke` 时，才按 `commands_if_ready[]` 人工尝试 LiDAR driver 和 `/scan` 观察。
4. 全程不得发送 `T=1`、`T=13`、`T=131`、`/cmd_vel` 或任何底盘运动命令。

## Not Proven

- 真实 WAVE ROVER UART 设备路径未由本 probe 确认。
- 本 probe 未打开 pyserial，未读取或写入任何串口。
- 真实 `T=1001` chassis feedback 未采集。
- `T=13` 在当前底盘固件上的真实行为未验证。
- LiDAR 真实 USB path、`150000` 目标硬件稳定性、ROS2 `/scan`、TF/Nav2/SLAM 消费链路仍未验证。
- 因为没有执行任何控制命令，本轮不能写成 HIL pass，也不能写成真实送达、真实底盘控制或真实 LiDAR ready。
