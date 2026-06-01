# Tech Done

## Sprint Type

sprint_type: micro

## 本轮目标

推进 O1 WAVE ROVER `T=130 -> T=1001` feedback 真实证据链。用户本轮给出上位机入口 `ssh root@192.168.1.11 -p 37878`，因此本轮优先在严格 fail-closed 边界下复用现有 stdin probe：默认不发命令，只有显式 `--request-base-feedback` 才允许发送一次 vendor `{"T":130}\n`，禁止任何运动命令。

## 已读资料

- `AGENTS.md`
- `OKR.md`
- `docs/vendor/VENDOR_INDEX.md`
- `docs/vendor/waveshare_wave_rover/ugv_rpi/base_ctrl.py`
- `docs/vendor/waveshare_wave_rover/ugv_rpi/config.yaml`
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/json_cmd.h`
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/uart_ctrl.h`

## 已证实硬件结论

- WAVE ROVER vendor 上位机 reference 通过 UART 发送 UTF-8 JSON，并以 `\n` 结束。
- vendor Raspberry Pi reference baudrate 为 `115200`；本轮 Orange Pi/上位机串口路径使用现场已观察到的 `/dev/serial/by-id/usb-STC_STC_USB_Serial-if00`，不把 Raspberry Pi `/dev/ttyAMA0` 当默认。
- `json_cmd.h` 定义 `CMD_BASE_FEEDBACK=130`，`uart_ctrl.h` 将 `CMD_BASE_FEEDBACK` 分发到 `baseInfoFeedback()`。
- `json_cmd.h` 定义 `FEEDBACK_BASE_INFO=1001`；本轮未读到任何 `T=1001` 行。
- `T=1`、`T=13`、`T=131` 和 `cmd_vel` 均不属于本轮允许动作；本轮没有发送任何运动命令或 feedback-flow 状态切换命令。

## 实际改动

- `docs/hardware/o1_wave_rover_serial_feedback_probe.md`：补充 2026.06.01_23-24 远端可达、T=130 显式请求、5 秒和 15 秒窗口无反馈的证据边界。
- `docs/interfaces/o1_o5_90_evidence_boundary.md`：在 O1 边界中补充最新状态 `serial_open_t130_feedback_request_observed_without_t1001`，明确仍不满足真实 `T=1001` HIL packet。
- `sprints/2026.06.01_23-24_o1-t130-feedback-real-probe/tech-done.md`：记录本 micro sprint 的资料来源、远端 probe 结果、验证命令和剩余风险。

本轮未修改 `onboard/scripts/o1_wave_rover_serial_feedback_probe.py` 和 `onboard/src/ros2_trashbot_hardware/test/test_o1_wave_rover_serial_feedback_probe.py`。现有脚本已经具备显式 `--request-base-feedback` 和可配置 `--read-timeout-s`，因此没有新增更大能力面。

## 验证结果

### 1. py_compile

```text
$ python3 -m py_compile onboard/scripts/o1_wave_rover_serial_feedback_probe.py
exit 0
```

### 2. unit test

```text
$ PYTHONDONTWRITEBYTECODE=1 python3 -m unittest onboard/src/ros2_trashbot_hardware/test/test_o1_wave_rover_serial_feedback_probe.py
.......
----------------------------------------------------------------------
Ran 7 tests in 0.186s

OK
```

### 3. 远端 5 秒 no-motion probe

```text
$ ssh -o BatchMode=yes -o ConnectTimeout=8 -p 37878 root@192.168.1.11 'python3 -s - --once-json --request-base-feedback --port /dev/serial/by-id/usb-STC_STC_USB_Serial-if00 --baudrate 115200 --read-timeout-s 5' < onboard/scripts/o1_wave_rover_serial_feedback_probe.py
```

关键输出：

```json
{
  "pyserial": {"available": true, "error": null, "module_name": "serial"},
  "serial_opened": true,
  "feedback_request": {"enabled": true, "sent": true, "write_error": null},
  "read_timeout_s": 5.0,
  "read_line_count": 0,
  "parsed_json_count": 0,
  "invalid_json_count": 0,
  "observed_feedback_types": [],
  "safe_to_control": false,
  "sends_commands": true,
  "sends_motion_commands": false,
  "robot_control_executed": false,
  "delivery_success": false,
  "error": null
}
```

### 4. 远端 15 秒扩展窗口 no-motion probe

5 秒窗口无反馈后，按现有参数延长读取窗口，没有新增脚本能力：

```text
$ ssh -o BatchMode=yes -o ConnectTimeout=8 -p 37878 root@192.168.1.11 'python3 -s - --once-json --request-base-feedback --port /dev/serial/by-id/usb-STC_STC_USB_Serial-if00 --baudrate 115200 --read-timeout-s 15' < onboard/scripts/o1_wave_rover_serial_feedback_probe.py
```

关键输出：

```json
{
  "pyserial": {"available": true, "error": null, "module_name": "serial"},
  "serial_opened": true,
  "feedback_request": {"enabled": true, "sent": true, "write_error": null},
  "read_timeout_s": 15.0,
  "read_line_count": 0,
  "parsed_json_count": 0,
  "invalid_json_count": 0,
  "observed_feedback_types": [],
  "safe_to_control": false,
  "sends_commands": true,
  "sends_motion_commands": false,
  "robot_control_executed": false,
  "delivery_success": false,
  "error": null
}
```

### 5. diff check

```text
$ git diff --check -- onboard/scripts/o1_wave_rover_serial_feedback_probe.py onboard/src/ros2_trashbot_hardware/test/test_o1_wave_rover_serial_feedback_probe.py docs/hardware/o1_wave_rover_serial_feedback_probe.md docs/interfaces/o1_o5_90_evidence_boundary.md sprints/2026.06.01_23-24_o1-t130-feedback-real-probe/tech-done.md
exit 0
```

## 失败定位

本轮不再 blocked 于 SSH 网络层：远端可达，远端 Python 已运行，`pyserial` 可用，目标 by-id 串口可打开，显式 `T=130` 写入成功且 `write_error=null`。

当前 blocker 收敛为：`T=130` 后 5 秒和 15 秒读取窗口均没有任何串口行返回。该现象不能直接判定为 WAVE ROVER 无反馈；可能原因包括下位机供电/连接、TX/RX 方向、USB 串口是否接到 ESP32 控制口、目标串口是否被其他进程占用、当前固件是否为 WAVE ROVER `CMD_BASE_FEEDBACK` 分支、或需要现场 vendor 工具链交叉验证。

## 剩余风险与下一步

- 真实 `T=1001` 仍为 `not_proven`；本轮没有生成 `feedback_T1001.log`，不满足 O1 HIL packet。
- 本轮共执行两次显式 `--request-base-feedback` probe，每次只发送一次 vendor `{"T":130}\n`；没有发送任何 `T=1`、`T=13`、`T=131`、`cmd_vel` 或其他运动命令。
- `serial_opened=true` 只证明 Linux 设备节点可打开，不证明它必然连接到 WAVE ROVER ESP32 的正确 UART。
- 下一步应现场核对接线/供电/串口占用和固件状态，再用同一脚本或 vendor 串口工具采集至少一帧真实 `T=1001`，随后再进入同源 `/imu/data`、`/battery`、`/odom` 材料采集。

## OKR 最低优先级说明

本 micro sprint 针对 O1。O1 与 O5/O6 同为约 93% 的最低 Objective 之一，本轮推进的是 O1 中最新缺口：真实 WAVE ROVER `T=130 -> T=1001` feedback 证据链。
