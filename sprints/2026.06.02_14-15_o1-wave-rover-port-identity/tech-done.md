# 2026.06.02 14-15 O1 WAVE ROVER Port Identity

sprint_type: micro

## 目标

本轮聚焦当前最低完成度 O1。上一轮已确认 `ssh root@192.168.1.11 -p 37878` 曾恢复，`/dev/serial/by-id/usb-STC_STC_USB_Serial-if00 -> /dev/ttyACM0` 可打开，显式 `{"T":130}\n` 可写入，但 12 秒窗口无任何串口行，`T=1001` 仍为 `not_proven`。

本轮新增 no-motion 端口身份 readiness probe，让 automation/现场同学在不打开串口、不发送任何命令的情况下，机器可读地判断目标端口 realpath、by-id/by-path 线索、sysfs USB/tty 描述、候选端口风险和下一步检查项。

## 已读 vendor 来源

- `AGENTS.md`
- `OKR.md`
- `docs/vendor/VENDOR_INDEX.md`
- `docs/vendor/waveshare_wave_rover/ugv_rpi/base_ctrl.py`
- `docs/vendor/waveshare_wave_rover/ugv_rpi/config.yaml`
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/json_cmd.h`
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/uart_ctrl.h`
- `docs/vendor/lidar_pkg_ros2-main/README.md`
- `docs/vendor/lidar_pkg_ros2-main/scripts/99-lidar.rules`

## 已证实的硬件结论

- WAVE ROVER vendor 上下位机 reference 是 UART 上的 UTF-8 newline-delimited JSON；`base_ctrl.py` 使用 `json.dumps(data) + '\n'` 写入和 `readline()` 读取。
- `config.yaml` 中 vendor Raspberry Pi reference 仍是上位应用配置，不可直接当 Orange Pi 真实串口路径。
- `json_cmd.h` 定义 `CMD_BASE_FEEDBACK=130`、`CMD_BASE_FEEDBACK_FLOW=131`、`CMD_SPEED_CTRL=1`、`CMD_ROS_CTRL=13`、`FEEDBACK_BASE_INFO=1001`；本轮 probe 不发送这些命令。
- `uart_ctrl.h` 会按 `T` 字段分发 `CMD_BASE_FEEDBACK`、`CMD_BASE_FEEDBACK_FLOW`、`CMD_SPEED_CTRL` 和 `CMD_ROS_CTRL`；因此端口身份 readiness 不能通过发送命令确认身份。
- LiDAR vendor README 明确雷达可能通过 `/dev/ttyUSB*` 或 `/dev/ttyACM*` 插拔对比确认；`99-lidar.rules` 把 `idVendor=34bf`、`idProduct=ff0a` 映射为 `/dev/lidar`。所以 STC/ttyACM/by-id 线索不能单独证明 WAVE ROVER ESP32。

## 实际改动

- `onboard/scripts/o1_wave_rover_port_identity_probe.py`
  - 新增 schema `trashbot.o1.wave_rover_port_identity_probe.v1` 的只读端口身份 probe。
  - 只执行 `glob/readlink/stat/sysfs_text_read`，不 import pyserial、不打开 `/dev/*`、不写串口、不发送 `T=130/T=131/T=1/T=13/cmd_vel`。
  - 固定输出 `safe_to_control=false`、`sends_commands=false`、`opens_serial_devices=false`、`robot_control_executed=false`、`delivery_success=false`。
  - 输出 `target.realpath`、`serial_candidates.related_to_target_realpath[]`、`sysfs_usb_tty_description`、`identity_assessment.status/risk_flags/next_required_checks[]`。
  - 保守分类：`port_missing`、`possible_lidar_or_other_stc`、`identity_insufficient`、`possible_wave_rover_esp32`，不输出硬件定论。
- `onboard/src/ros2_trashbot_hardware/test/test_o1_wave_rover_port_identity_probe.py`
  - 新增 fake inspector 单元测试，覆盖 by-id realpath、端口缺失、STC/ttyACM 身份不足、LiDAR 线索、fail-closed 字段、CLI once-json 输出。
- `docs/hardware/o1_wave_rover_serial_feedback_probe.md`
  - 增加端口身份 readiness probe 的运行命令、输出 contract、分类口径和证据边界。
- `docs/interfaces/o1_o5_90_evidence_boundary.md`
  - 明确端口身份 readiness 不能替代真实 `T=1001`、HIL packet 或现场物理追线。
- `docs/process/okr_progress_log.md`
  - 增加本轮 O1 micro closeout 记录。
- `OKR.md`
  - O1 口径更新为 `port identity readiness ready; T=1001 not_proven`，百分比保持约 93%，不把 readiness 写成 HIL pass。

## 验证结果

```text
$ python3 -m py_compile onboard/scripts/o1_wave_rover_port_identity_probe.py
# passed
```

```text
$ PYTHONDONTWRITEBYTECODE=1 python3 -m unittest onboard/src/ros2_trashbot_hardware/test/test_o1_wave_rover_port_identity_probe.py
......
----------------------------------------------------------------------
Ran 6 tests in 0.044s

OK
```

```text
$ git diff --check -- OKR.md docs/hardware/o1_wave_rover_serial_feedback_probe.md docs/interfaces/o1_o5_90_evidence_boundary.md docs/process/okr_progress_log.md sprints/2026.06.02_14-15_o1-wave-rover-port-identity/tech-done.md onboard/scripts/o1_wave_rover_port_identity_probe.py onboard/src/ros2_trashbot_hardware/test/test_o1_wave_rover_port_identity_probe.py
# passed
```

## 远端采集状态

远端 SSH 采集是可选材料。本轮按用户状态更新要求，不等待远端、不把远端作为阻塞项。可选命令保留为：

```bash
timeout 20 ssh -o BatchMode=yes -o ConnectTimeout=8 -p 37878 root@192.168.1.11 'python3 -s - --once-json --port /dev/serial/by-id/usb-STC_STC_USB_Serial-if00' < onboard/scripts/o1_wave_rover_port_identity_probe.py
```

## 剩余风险和下一步

- `identity_assessment.status=possible_wave_rover_esp32` 也只能代表只读文本线索，不代表端口身份已验证。
- `identity_assessment.status=identity_insufficient` 时，必须现场分别拔插 LiDAR 和 WAVE ROVER base controller，对比 by-id/by-path/realpath。
- 若出现 `/dev/lidar`、LiDAR vendor/product 或 lidar/laser 文本，应优先排查错口风险。
- O1 仍缺真实 `T=1001`、真实 UART/HIL、真实底盘控制、真实 `/imu/data`、真实 `/battery`、真实 `/odom`、真实 LiDAR `/scan`、TF、Nav2/SLAM 和 150000 长稳材料。
- 下一步履约动作：先运行 no-motion port identity probe，确认目标端口风险；再做物理追线和设备插拔对比；身份确认后才允许继续显式 `T=130` feedback probe 或 vendor terminal 交叉验证。
