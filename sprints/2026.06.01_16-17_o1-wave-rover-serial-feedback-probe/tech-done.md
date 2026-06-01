# O1 WAVE ROVER Serial Feedback Probe Tech Done

## sprint_type

micro

## 实际改动

- 新增 `onboard/scripts/o1_wave_rover_serial_feedback_probe.py`：输出 `trashbot.o1.wave_rover_serial_feedback_probe.v1` JSON；支持 `--port`、`--baudrate`、`--read-timeout-s`、`--once-json`；默认只打开串口、短时间读取已有行、解析 JSON；固定 `safe_to_control=false`、`sends_commands=false`、`robot_control_executed=false`、`delivery_success=false`。
- 新增 `onboard/src/ros2_trashbot_hardware/test/test_o1_wave_rover_serial_feedback_probe.py`：用 fake serial 证明默认只读、不会调用 `write()`，覆盖 pyserial 缺失、串口打开失败、JSON/坏行解析、blocked command contract。
- 新增 `docs/hardware/o1_wave_rover_serial_feedback_probe.md`：记录 vendor 来源、远端运行命令、serial-open/read-only 边界，以及为什么不能写成 HIL pass。

## 已读 vendor 来源

- `docs/vendor/VENDOR_INDEX.md`
- `docs/vendor/waveshare_wave_rover/ugv_rpi/base_ctrl.py`
- `docs/vendor/waveshare_wave_rover/ugv_rpi/config.yaml`
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/json_cmd.h`
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/uart_ctrl.h`

## 验证结果

- `python3 -m py_compile onboard/scripts/o1_wave_rover_serial_feedback_probe.py`：passed。
- `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest onboard/src/ros2_trashbot_hardware/test/test_o1_wave_rover_serial_feedback_probe.py`：`Ran 6 tests ... OK`。
- 本地 missing-port probe：返回 fail-closed JSON，`error` 为 `SerialException`；保持 `safe_to_control=false`、`sends_commands=false`、`robot_control_executed=false`、`delivery_success=false`。
- 远端只读串口枚举：`/dev/serial/by-id/usb-STC_STC_USB_Serial-if00` 存在，并指向 `/dev/ttyACM0`。
- 远端 read-only probe：返回 `pyserial.available=true`、`serial_opened=true`、`read_line_count=0`、`parsed_json_count=0`、`observed_feedback_types=[]`、`error=null`。
- `git diff --check`：passed。
- 中文技术注释比例检查：script `21.0%`，test `20.8%`。

## 远端脱敏摘要

- 目标路径：`/dev/serial/by-id/usb-STC_STC_USB_Serial-if00 -> /dev/ttyACM0`。
- 运行方式：read-only probe，仅打开串口并短时读取已有行；不写串口、不发送 `T=1`、`T=13`、`T=131`、`/cmd_vel` 或任何控制命令。
- 观察结果：`pyserial.available=true` 且 `serial_opened=true`，但没有读到任何行，`T=1001` feedback not_proven。
- 证据边界：本轮只能写成 `serial-open observed`，不能写成 HIL pass、底盘控制通过、反馈协议通过或送达闭环完成。

## Product Closeout

Objective 1 从约 92% 保守调整为约 93%：`software_reference + upper-computer serial-open observed; feedback not_proven`。

本轮真实关闭的是“O1 上位机目标/疑似 WAVE ROVER 串口路径可枚举、pyserial 可 import、串口可 read-only open、probe fail-closed 行为可复验”缺口。方向判断为**继续**，不替换、不暂停；下一步应围绕同一路径补真实 WAVE ROVER `T=1001` feedback、HIL packet、ROS runtime 消费和控制链路验证。

## 剩余风险

- 本轮未读到任何串口行，`read_line_count=0`、`parsed_json_count=0`、`observed_feedback_types=[]`，因此真实 WAVE ROVER feedback/T=1001 仍为 `not_proven`。
- 本轮没有发送控制命令，没有证明真实底盘控制、HIL pass、IMU/battery/odom 标定、ROS Humble runtime、Nav2/SLAM、LiDAR `/scan` 或完整送达闭环。
- `/dev/serial/by-id/usb-STC_STC_USB_Serial-if00` 已成功打开，但仍需要用真实 `T=1001` 反馈、受控 HIL 日志和 vendor 对照证明它是可用的 WAVE ROVER UART 数据链路。
