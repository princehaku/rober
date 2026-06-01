# O1 WAVE ROVER Serial Feedback Probe

## 目标

`onboard/scripts/o1_wave_rover_serial_feedback_probe.py` 是 O1 的串口打开和反馈探测入口。默认模式只按调用方指定的 `--port` 和 `--baudrate` 打开串口，在短窗口内读取已经存在的行，尝试解析 JSON，并输出结构化结果。

本 probe 默认不发送任何串口写入。只有调用方显式传入 `--request-base-feedback` 时，才允许发送一次 vendor `CMD_BASE_FEEDBACK` / `{"T":130}`，随后短时间读取反馈。该请求不带速度、转向、PWM、ROS velocity 或 feedback-flow 状态字段。

本 probe 永远不发送 `T=1`、`T=13`、`T=131`、`cmd_vel` 或任何会驱动底盘运动的命令。`T=130` 虽然会产生一次串口写入，但证据边界仍是 `serial_open_t130_feedback_request_not_hil`，不能写成底盘可控或 HIL pass。

固定 fail-closed 字段：

- `safe_to_control=false`
- `sends_motion_commands=false`
- `robot_control_executed=false`
- `delivery_success=false`

## Vendor 来源

本轮已读并采用的本地资料：

- `docs/vendor/VENDOR_INDEX.md`
- `docs/vendor/waveshare_wave_rover/ugv_rpi/base_ctrl.py`
- `docs/vendor/waveshare_wave_rover/ugv_rpi/config.yaml`
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/json_cmd.h`
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/uart_ctrl.h`

已证实的资料结论：

- WAVE ROVER 上位机 reference 使用 UART、UTF-8 JSON、每行一个 JSON 对象并以 `\n` 结束。
- vendor Raspberry Pi reference 使用 `/dev/ttyAMA0`、`115200`；Orange Pi Zero 3 的真实串口路径必须在目标机确认，不能硬编码 Raspberry Pi 路径。
- `T=1` 是左右轮速度命令，`T=13` 是 ROS velocity 命令，`T=131` 会改变 feedback flow 状态；本 probe 全部列为 `blocked_commands_not_sent`。
- `T=130` 是 base feedback request，在本轮只允许通过 `--request-base-feedback` 显式发送一次；默认模式仍不发送。

## 运行命令

本地 dry-run 缺失串口验证：

```bash
python3 onboard/scripts/o1_wave_rover_serial_feedback_probe.py --once-json --port /dev/definitely-missing-rober-probe
```

远端只读运行，优先使用 by-id 设备；若不存在则使用 `/dev/ttyACM0`：

```bash
ssh -p 37878 root@192.168.1.11 'python3 -s - --once-json --port /dev/serial/by-id/usb-STC_STC_USB_Serial-if00 --baudrate 115200 --read-timeout-s 2' < onboard/scripts/o1_wave_rover_serial_feedback_probe.py
```

远端非运动反馈请求运行，只发送一次 `T=130`：

```bash
ssh -p 37878 root@192.168.1.11 'python3 -s - --once-json --request-base-feedback --port /dev/serial/by-id/usb-STC_STC_USB_Serial-if00 --baudrate 115200 --read-timeout-s 2' < onboard/scripts/o1_wave_rover_serial_feedback_probe.py
```

若 by-id 不存在：

```bash
ssh -p 37878 root@192.168.1.11 'python3 -s - --once-json --port /dev/ttyACM0 --baudrate 115200 --read-timeout-s 2' < onboard/scripts/o1_wave_rover_serial_feedback_probe.py
```

## 输出 contract

关键字段：

- `schema=trashbot.o1.wave_rover_serial_feedback_probe.v1`
- `vendor_sources[]` 固定列出本轮 vendor 来源
- `evidence_boundary=serial_open_read_only_not_hil` 或 `serial_open_t130_feedback_request_not_hil`
- `safe_to_control=false`
- `sends_commands`：只表示是否显式发送过 `T=130`
- `sends_motion_commands=false`
- `robot_control_executed=false`
- `delivery_success=false`
- `port`、`baudrate`、`baudrate_source`
- `pyserial.available`、`pyserial.error`
- `serial_opened`
- `read_line_count`
- `parsed_json_count`
- `invalid_json_count`
- `observed_feedback_types`
- `t1001_feedback_status`：稳定机器字段，取值包括 `observed`、`not_observed_after_t130`、`not_requested`、`serial_not_opened`、`pyserial_unavailable`
- `next_required_checks[]`：稳定下一步检查项，例如 `verify_esp32_power_and_firmware`、`verify_uart_tx_rx_crossed`、`verify_target_port_is_wave_rover_esp32`、`check_serial_owner_process`、`use_vendor_terminal_cross_check_t130`
- `error`
- `feedback_request.enabled/sent/command/write_error`
- `blocked_commands_not_sent`

## 证据边界

这不是 HIL pass，也不是底盘控制通过。通过本 probe 最多只能说明：

- 远端 Python 能运行脚本。
- pyserial 是否可用。
- 指定串口是否能被打开。
- 在默认只读模式下，短时间内是否读到已有行。
- 在显式 `--request-base-feedback` 模式下，一次 `T=130` 后短时间内是否读到反馈。
- 已有行是否能被解析为 JSON，以及 JSON 中出现了哪些 `T` 类型。

即使读到 `T=1001` 或其他反馈类型，也只能记为 `serial_open_t130_feedback_material_observed` 或 `serial_open_read_only_material_observed`。还不能证明：

- 当前串口必然就是 WAVE ROVER ESP32。
- 底盘可安全控制。
- `T=13` 在当前固件和底盘上可用。
- IMU、battery、odom 单位和标定已经正确。
- Nav2、SLAM 或完整送达闭环已经准备好。

## 本轮远端观察

`2026.06.01_16-17_o1-wave-rover-serial-feedback-probe` 按 stdin 方式在 `root@192.168.1.11:37878` 运行。结果记录在对应 sprint 的 `tech-done.md` 中；仓库不保存远端原始 artifact。

`2026.06.01_20-21_o1-t130-feedback-observation` 继续使用同一 SSH 入口尝试一次显式 `--request-base-feedback` 采集：

```bash
ssh -o BatchMode=yes -o ConnectTimeout=8 -p 37878 root@192.168.1.11 'python3 -s - --once-json --request-base-feedback --port /dev/serial/by-id/usb-STC_STC_USB_Serial-if00 --baudrate 115200 --read-timeout-s 2' < onboard/scripts/o1_wave_rover_serial_feedback_probe.py
```

本轮结果为 SSH 层失败：`ssh: connect to host 192.168.1.11 port 37878: No route to host`。因此本轮未触达远端 Python、未打开 `/dev/serial/by-id/usb-STC_STC_USB_Serial-if00`、未发送 `{"T":130}\n`、未读取到 `T=1001` 或其他 feedback 类型。该结果只能作为 `remote_network_unreachable` blocker 证据，不得写成串口反馈失败、WAVE ROVER 无反馈或 HIL pass。

`2026.06.01_23-24_o1-t130-feedback-real-probe` 使用用户提供的同一入口重新采集：

```bash
ssh -o BatchMode=yes -o ConnectTimeout=8 -p 37878 root@192.168.1.11 'python3 -s - --once-json --request-base-feedback --port /dev/serial/by-id/usb-STC_STC_USB_Serial-if00 --baudrate 115200 --read-timeout-s 5' < onboard/scripts/o1_wave_rover_serial_feedback_probe.py
```

本轮远端可达，远端 Python 成功运行，`pyserial.available=true`，`serial_opened=true`，`feedback_request.sent=true`，`write_error=null`。该命令只发送一次 vendor `{"T":130}\n`，仍保持 `safe_to_control=false`、`sends_motion_commands=false`、`robot_control_executed=false`、`delivery_success=false`，且 `blocked_commands_not_sent` 继续包含 `T=1`、`T=13`、`T=131` 和 `cmd_vel`。

5 秒窗口结果为：`read_line_count=0`、`parsed_json_count=0`、`invalid_json_count=0`、`observed_feedback_types=[]`、`raw_line_preview=[]`、`error=null`。因此本轮已证明 SSH 网络 blocker 解除、上位机能打开目标串口并完成一次显式非运动 T=130 写入，但仍未读到真实 `T=1001` feedback。

随后按现有参数把读取窗口延长到 15 秒复测：

```bash
ssh -o BatchMode=yes -o ConnectTimeout=8 -p 37878 root@192.168.1.11 'python3 -s - --once-json --request-base-feedback --port /dev/serial/by-id/usb-STC_STC_USB_Serial-if00 --baudrate 115200 --read-timeout-s 15' < onboard/scripts/o1_wave_rover_serial_feedback_probe.py
```

15 秒窗口结果仍为：`serial_opened=true`、`feedback_request.sent=true`、`write_error=null`、`read_line_count=0`、`parsed_json_count=0`、`observed_feedback_types=[]`、`error=null`。本轮共执行两次显式 `--request-base-feedback` probe，每次只发送一次 vendor `T=130`；未发送任何 `T=1`、`T=13`、`T=131`、`cmd_vel` 或其他运动命令。

当前结论只能写成 `serial_open_t130_feedback_request_observed_without_t1001`。它不是 HIL pass，不证明 WAVE ROVER 无反馈，也不证明底盘可控；下一步应在现场核对下位机供电/连接、串口方向、是否被其他进程占用、ESP32 firmware 是否加载 WAVE ROVER `CMD_BASE_FEEDBACK` 分支，并在必要时用 vendor 工具链或串口终端做人工交叉验证。

`2026.06.02_03-04_o1-t1001-diagnostic-contract` 将 probe 输出升级为机器可读诊断合同。新增字段不改变安全边界：

- `t1001_feedback_status=observed`：窗口内已读到 `T=1001`。
- `t1001_feedback_status=not_requested`：默认只读模式没有发送 `T=130`，不能把无反馈写成 after-T130 失败。
- `t1001_feedback_status=not_observed_after_t130`：显式发送一次 `T=130` 后仍未读到 `T=1001`；下一步检查项必须回到 vendor/现场边界。
- `t1001_feedback_status=serial_not_opened`：目标串口未打开，优先核对目标端口和占用。
- `t1001_feedback_status=pyserial_unavailable`：远端 Python 缺 pyserial，优先补运行依赖。

同轮远端 SSH 采集再次使用指定入口：

```bash
ssh -o BatchMode=yes -o ConnectTimeout=8 -p 37878 root@192.168.1.11 'python3 -s - --once-json --port /dev/serial/by-id/usb-STC_STC_USB_Serial-if00 --baudrate 115200 --read-timeout-s 2' < onboard/scripts/o1_wave_rover_serial_feedback_probe.py
ssh -o BatchMode=yes -o ConnectTimeout=8 -p 37878 root@192.168.1.11 'python3 -s - --once-json --request-base-feedback --port /dev/serial/by-id/usb-STC_STC_USB_Serial-if00 --baudrate 115200 --read-timeout-s 8' < onboard/scripts/o1_wave_rover_serial_feedback_probe.py
```

两条命令均在 SSH 网络层失败：`ssh: connect to host 192.168.1.11 port 37878: No route to host`。因此本轮没有触达远端 Python、没有打开串口、没有发送 `T=130`、没有读取到 `T=1001`。本轮可交付只限于本地 probe 诊断合同和回归测试；O1 仍只能推进为“诊断合同更清楚 + 远端现象更可复验”，不是 HIL pass。
