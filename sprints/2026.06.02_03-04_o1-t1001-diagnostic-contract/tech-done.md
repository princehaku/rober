# O1 T1001 Diagnostic Contract

sprint_type: micro

## 实际改动

- `onboard/scripts/o1_wave_rover_serial_feedback_probe.py`
  - 新增稳定字段 `t1001_feedback_status`，覆盖 `observed`、`not_observed_after_t130`、`not_requested`、`serial_not_opened`、`pyserial_unavailable`。
  - 新增稳定字段 `next_required_checks[]`，把无 `T=1001` 的下一步现场检查从 prose/root-cause hint 升级为可机器读取合同。
  - 保持 fail-closed 字段不变：`safe_to_control=false`、`sends_motion_commands=false`、`robot_control_executed=false`、`delivery_success=false`。
- `onboard/src/ros2_trashbot_hardware/test/test_o1_wave_rover_serial_feedback_probe.py`
  - 补充回归覆盖：默认未请求、显式 `T=130` 后无行、`T=1001` observed、pyserial 缺失、串口打开失败。
- `docs/hardware/o1_wave_rover_serial_feedback_probe.md`
  - 同步新增诊断合同字段、远端 SSH 失败边界和非 HIL 结论。
- `sprints/2026.06.02_03-04_o1-t1001-diagnostic-contract/tech-done.md`
  - 记录本 micro sprint 的实际改动、验证结果和剩余风险。

## 已读 vendor 来源

- `AGENTS.md`
- `OKR.md`
- `docs/vendor/VENDOR_INDEX.md`
- `docs/vendor/waveshare_wave_rover/ugv_rpi/base_ctrl.py`
- `docs/vendor/waveshare_wave_rover/ugv_rpi/config.yaml`
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/json_cmd.h`
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/uart_ctrl.h`
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/ugv_advance.h`

## 已证实硬件结论

- vendor 上位机 reference 使用 UART、UTF-8 JSON、newline-delimited framing。
- vendor Raspberry Pi reference baudrate 为 `115200`；Orange Pi 目标串口必须由现场确认，不能继承 Raspberry Pi 默认路径。
- `json_cmd.h` 定义 `CMD_BASE_FEEDBACK=130`、`FEEDBACK_BASE_INFO=1001`。
- `uart_ctrl.h` 中 `CMD_BASE_FEEDBACK` 分支调用 `baseInfoFeedback()`。
- `ugv_advance.h` 中 `baseInfoFeedback()` 通过 `Serial.println()` 输出 `T=1001`，包含 `L/R/r/p/y/v` 等字段。

## 验证结果

### 远端默认只读 probe

命令：

```bash
ssh -o BatchMode=yes -o ConnectTimeout=8 -p 37878 root@192.168.1.11 'python3 -s - --once-json --port /dev/serial/by-id/usb-STC_STC_USB_Serial-if00 --baudrate 115200 --read-timeout-s 2' < onboard/scripts/o1_wave_rover_serial_feedback_probe.py
```

结果：

```text
ssh: connect to host 192.168.1.11 port 37878: No route to host
```

边界：SSH 网络层失败，未触达远端 Python，未打开串口，未读取任何 `T=1001`。

### 远端显式 T=130 非运动请求 probe

命令：

```bash
ssh -o BatchMode=yes -o ConnectTimeout=8 -p 37878 root@192.168.1.11 'python3 -s - --once-json --request-base-feedback --port /dev/serial/by-id/usb-STC_STC_USB_Serial-if00 --baudrate 115200 --read-timeout-s 8' < onboard/scripts/o1_wave_rover_serial_feedback_probe.py
```

结果：

```text
ssh: connect to host 192.168.1.11 port 37878: No route to host
```

边界：SSH 网络层失败，未触达远端 Python，未发送 `T=130`，未读取任何 `T=1001`。

### Targeted unittest

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s onboard/src/ros2_trashbot_hardware/test -p 'test_o1_wave_rover_serial_feedback_probe.py'
```

结果：

```text
Ran 9 tests in 0.275s
OK
```

## 剩余风险

- 本轮远端 SSH 不可达，无法复验上一轮 `serial_opened=true` 或 `T=130` 写入现象。
- 仍未采集真实 `T=1001`，不能写成 HIL pass、真实 WAVE ROVER feedback pass 或底盘可控。
- 下一步现场检查应按 `next_required_checks[]` 执行：核对 ESP32 供电和固件、UART TX/RX 是否交叉、目标串口是否确为 WAVE ROVER ESP32、是否有串口占用，并用 vendor 串口终端交叉验证 `T=130`。
