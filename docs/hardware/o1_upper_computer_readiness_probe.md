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
- `docs/vendor/lidar_ros/SOURCE.md`
- `docs/vendor/lidar_ros/README.md`
- `docs/vendor/lidar_ros/plot.py`
- `docs/vendor/lidar_ros/src/lidar_pkg/scripts/lidar_driver.py`
- `docs/vendor/lidar_ros/src/lidar_pkg/src/lidar_driver.cpp`

已证实的软件 reference 边界：

- WAVE ROVER 上位机参考使用 UART、UTF-8 JSON、每行一个 JSON 对象并以 `\n` 结束。
- vendor Raspberry Pi reference 提到 `/dev/ttyAMA0`、`115200`；Orange Pi 实际设备名必须上机确认，不能直接继承 Raspberry Pi 路径。
- WAVE ROVER `T=1`、`T=13`、`T=131` 都属于会改变底盘或反馈流状态的命令，本 probe 只把它们列为 `blocked_commands_not_sent`，不发送。
- LiDAR reference 来自 ROS1/catkin snapshot，`150000` baud、`0xAA 0x55`、`/lidar/raw_packet`、`laser_frame` 只代表 `software_reference_not_hil`，不等于真实 LiDAR 已跑通。

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
ssh -p 37878 root@192.168.1.11 'python3 -s -- --once-json' < onboard/scripts/o1_upper_computer_readiness_probe.py
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
- `ros_env_hints.humble_setup_bash.exists` 只检查 `/opt/ros/humble/setup.bash`
- `lidar_reference_readiness.status=software_reference_not_hil`
- `wave_rover_readiness.status=not_ready_for_control`
- `next_safe_commands[]` 只包含编译、单测和只读 probe 命令

## 本轮远端观察

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

## Not Proven

- 真实 WAVE ROVER UART 设备路径未由本 probe 确认。
- 本 probe 未打开 pyserial，未读取或写入任何串口。
- 真实 `T=1001` chassis feedback 未采集。
- `T=13` 在当前底盘固件上的真实行为未验证。
- LiDAR 真实 USB path、`150000` 目标硬件稳定性、ROS2 `/scan`、TF/Nav2/SLAM 消费链路仍未验证。
- 因为没有执行任何控制命令，本轮不能写成 HIL pass，也不能写成真实送达、真实底盘控制或真实 LiDAR ready。
