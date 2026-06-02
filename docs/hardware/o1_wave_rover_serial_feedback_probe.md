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

## 端口身份 readiness probe

`onboard/scripts/o1_wave_rover_port_identity_probe.py` 是本轮新增的 no-motion 端口身份 readiness probe。它解决的是上一轮留下的端口身份风险：`/dev/serial/by-id/usb-STC_STC_USB_Serial-if00 -> /dev/ttyACM0` 可打开并不等于该端口一定是 WAVE ROVER ESP32；vendor LiDAR README 也要求通过 `/dev/ttyUSB*` 或 `/dev/ttyACM*` 插拔对比确认雷达设备，vendor LiDAR udev 规则还会把 `idVendor=34bf`、`idProduct=ff0a` 映射为 `/dev/lidar`。

该 probe 默认只执行 `glob`、`readlink`、`stat` 和 `/sys/class/tty/<name>/device` 上游 sysfs 小文本读取。它不 import pyserial、不打开 `/dev/*` 串口、不写串口、不发送 `T=130`、`T=131`、`T=1`、`T=13` 或 `cmd_vel`。输出固定 fail-closed 字段：

- `safe_to_control=false`
- `sends_commands=false`
- `opens_serial_devices=false`
- `robot_control_executed=false`
- `delivery_success=false`

运行示例：

```bash
python3 onboard/scripts/o1_wave_rover_port_identity_probe.py --once-json --port /dev/serial/by-id/usb-STC_STC_USB_Serial-if00
```

远端只读运行示例：

```bash
timeout 20 ssh -o BatchMode=yes -o ConnectTimeout=8 -p 37878 root@192.168.1.11 'python3 -s - --once-json --port /dev/serial/by-id/usb-STC_STC_USB_Serial-if00' < onboard/scripts/o1_wave_rover_port_identity_probe.py
```

关键输出字段：

- `target.realpath`：目标端口 realpath，例如 by-id 指向 `/dev/ttyACM0`。这只是路径证据，不是设备身份定论。
- `serial_candidates.related_to_target_realpath[]`：同一 realpath 的 by-id、by-path、ttyACM/ttyUSB 和 `/dev/lidar` 线索。
- `sysfs_usb_tty_description`：从 sysfs 读取的 USB/tty 文本，如 `idVendor`、`idProduct`、`manufacturer`、`product`、`serial`、`interface`、`uevent`。
- `identity_assessment.status`：稳定机器分类，取值包括 `port_missing`、`possible_wave_rover_esp32`、`possible_lidar_or_other_stc`、`identity_insufficient`。
- `identity_assessment.risk_flags[]`：例如 `stc_or_ttyacm_is_not_unique`、`lidar_clue_present`、`no_distinctive_usb_identity_clue`。
- `identity_assessment.next_required_checks[]`：现场下一步检查项，重点是分别拔插 LiDAR 和 base controller 对比 by-id/by-path、物理追线、确认 `/dev/lidar` 或 LiDAR udev 是否指向同一 realpath。

分类口径必须保守：

- 端口缺失只能写 `port_missing`，下一步先恢复 USB/UART 可见性。
- 只看到 STC、ttyACM 或 by-id 指向时，默认仍是 `identity_insufficient`，因为 LiDAR 参考也可能使用 ttyACM/ttyUSB。
- 出现 `/dev/lidar`、`lidar/laser` 文本或 LiDAR udev vendor/product 时，写 `possible_lidar_or_other_stc`，优先暴露错口风险。
- 只有出现 ESP32/Waveshare/WAVE ROVER 这类文本线索且没有 LiDAR/STC 风险时，才允许写 `possible_wave_rover_esp32`，仍不能写成 proven。

## USB/串口 inventory probe

`onboard/scripts/o1_usb_serial_inventory_probe.py` 是 2026-06-02 17-18 新增的 O1 只读 inventory probe。它用于现场在同一上位机上枚举 `/dev/ttyUSB*`、`/dev/ttyACM*`、`/dev/serial/by-id/*`、`/dev/serial/by-path/*` 和 `/dev/lidar`，并读取对应 tty 上游 sysfs USB 小文本，帮助分别插拔 LiDAR 与 WAVE ROVER ESP32/底盘控制器后对比 alias/realpath 变化。

本 probe 不 import/use pyserial，不打开任何 `/dev/*` 串口，不发送 `T=130`、`T=131`、`T=1`、`T=13` 或 `cmd_vel`。输出 schema 固定为 `trashbot.o1.usb_serial_inventory.v1`，安全字段固定：

- `safe_to_control=false`
- `sends_commands=false`
- `opens_serial_devices=false`
- `robot_control_executed=false`
- `delivery_success=false`

运行示例：

```bash
python3 onboard/scripts/o1_usb_serial_inventory_probe.py --once-json --pretty
```

远端只读运行示例：

```bash
timeout 30 ssh -o BatchMode=yes -o ConnectTimeout=8 -p 37878 root@192.168.1.11 'python3 -s - --once-json' < onboard/scripts/o1_usb_serial_inventory_probe.py
```

关键输出字段：

- `inventory_summary.realpath_to_aliases`：按 realpath 聚合同一设备的 `/dev/tty*`、by-id、by-path 和 `/dev/lidar` alias。
- `inventory_summary.stc_or_ttyacm_realpaths`：出现 STC、`34bf:ff0a` 或 ttyACM 线索的 realpath；这只是错口风险，不是底盘身份结论。
- `identity_risks[]`：机器可读风险，如 `possible_lidar_or_other_stc`、`stc_or_ttyacm_is_not_unique`、`possible_base_controller_not_proven`、`no_serial_candidates_visible`。
- `recommended_physical_checks[]`：现场 SOP，要求先保存 baseline inventory，再分别拔 LiDAR 与底盘控制器，对比哪些 alias/realpath 改变，最后物理追线确认后才允许运行显式 feedback probe。

分类口径必须保守：STC `34bf:ff0a` 已与当前 LiDAR vendor `99-lidar.rules` 一致，因此出现该线索时只允许提示 `possible_lidar_or_other_stc` 或 `stc_or_ttyacm_is_not_unique` 风险，不得继续把 `/dev/ttyACM0` 当成 WAVE ROVER ESP32 默认控制端口，也不得继续盲发 `T=130`。

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

`2026.06.02_17-18_o1-usb-serial-inventory` 使用同一 SSH 入口只读运行 inventory probe：

```bash
timeout 30 ssh -o BatchMode=yes -o ConnectTimeout=8 -p 37878 root@192.168.1.11 'python3 -s - --once-json' < onboard/scripts/o1_usb_serial_inventory_probe.py
```

远端命令 exit 0，输出 `schema=trashbot.o1.usb_serial_inventory.v1`，安全字段保持 `safe_to_control=false`、`sends_commands=false`、`opens_serial_devices=false`、`robot_control_executed=false`、`delivery_success=false`。远端 inventory 只看到 3 个候选路径：`/dev/serial/by-id/usb-STC_STC_USB_Serial-if00`、`/dev/serial/by-path/platform-5200400.usb-usb-0:1:1.0`、`/dev/ttyACM0`，全部指向 `/dev/ttyACM0`；`/dev/lidar` 和 `/dev/ttyUSB*` 未命中。sysfs 继续显示 `idVendor=34bf`、`idProduct=ff0a`、`manufacturer=STC`、`product=STC USB Serial`、`DRIVER=cdc_acm`、`PRODUCT=34bf/ff0a/100`。机器风险为 `identity_risks[0].risk_id=possible_lidar_or_other_stc`、`severity=high`，推荐检查为先拔 LiDAR 后重跑 inventory 并比较 alias/realpath 变化。该材料仍不能证明目标端口是 WAVE ROVER ESP32，不能继续盲发 `T=130`。

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

`2026.06.02_06-07_o1-wave-rover-t1001-live-retry` 使用用户提供的同一 SSH 入口复采，目标是确认显式 `T=130` 后是否至少能读到一帧真实 `T=1001`。本轮先执行只读 probe：

```bash
timeout 20 ssh -o BatchMode=yes -o ConnectTimeout=8 -p 37878 root@192.168.1.11 'python3 -s - --once-json --port /dev/serial/by-id/usb-STC_STC_USB_Serial-if00 --baudrate 115200 --read-timeout-s 2' < onboard/scripts/o1_wave_rover_serial_feedback_probe.py
```

只读命令失败在 SSH 网络层：`ssh: connect to host 192.168.1.11 port 37878: No route to host`。因此本命令没有触达远端 Python、没有打开串口、没有读取串口行。

随后按验收要求执行显式非运动 feedback request：

```bash
timeout 35 ssh -o BatchMode=yes -o ConnectTimeout=8 -p 37878 root@192.168.1.11 'python3 -s - --once-json --request-base-feedback --port /dev/serial/by-id/usb-STC_STC_USB_Serial-if00 --baudrate 115200 --read-timeout-s 12' < onboard/scripts/o1_wave_rover_serial_feedback_probe.py
```

该命令同样失败在 SSH 网络层：`ssh: connect to host 192.168.1.11 port 37878: No route to host`。因此本轮没有发送 `{"T":130}\n`，没有发送 `T=1`、`T=13`、`T=131`、`cmd_vel` 或任何运动命令，也没有采到真实 `T=1001`。

本轮机器可读结论：

- `remote_probe_status=ssh_no_route_to_host`
- `safe_to_control=false`
- `sends_motion_commands=false`
- `robot_control_executed=false`
- `t130_request_reached_serial=false`
- `t1001_observed=false`
- `evidence_boundary=remote_network_unreachable_not_serial_feedback_result`

下一步现场检查材料：

1. 先在与上位机同网段的机器上确认 `192.168.1.11:37878` 可路由、上位机已开机、SSH 端口映射仍然存在。
2. SSH 恢复后先运行只读 probe，确认 `/dev/serial/by-id/usb-STC_STC_USB_Serial-if00` 是否仍存在并指向预期 `ttyACM*`。
3. 只读 probe 能触达后，再运行一次显式 `--request-base-feedback`；若仍为 `read_line_count=0`，按 `next_required_checks[]` 现场核对下位机供电/固件、TX/RX 交叉、目标端口是否为 WAVE ROVER ESP32、串口占用和 vendor terminal 交叉验证。

`2026.06.02_07-08_o1-wave-rover-t1001-live-retry` 再次按 O1 最低完成度执行复采。vendor 复核结论保持不变：`json_cmd.h` 定义 `CMD_BASE_FEEDBACK=130` 与 `FEEDBACK_BASE_INFO=1001`，`uart_ctrl.h` 中 `CMD_BASE_FEEDBACK` 分支调用 `baseInfoFeedback()`，`ugv_advance.h` 中 `baseInfoFeedback()` 输出 `T=FEEDBACK_BASE_INFO`、左右轮反馈、IMU roll/pitch/yaw、电压和可选模块字段。因此本轮仍只允许显式发送一次 vendor `{"T":130}\n`，严禁发送 `T=1`、`T=13`、`T=131`、`cmd_vel` 或任何运动命令。

本轮只读 probe：

```bash
timeout 20 ssh -o BatchMode=yes -o ConnectTimeout=8 -p 37878 root@192.168.1.11 'python3 -s - --once-json --port /dev/serial/by-id/usb-STC_STC_USB_Serial-if00 --baudrate 115200 --read-timeout-s 2' < onboard/scripts/o1_wave_rover_serial_feedback_probe.py
```

结果仍失败在 SSH 网络层：

```text
ssh: connect to host 192.168.1.11 port 37878: No route to host
```

本轮显式非运动 feedback request：

```bash
timeout 35 ssh -o BatchMode=yes -o ConnectTimeout=8 -p 37878 root@192.168.1.11 'python3 -s - --once-json --request-base-feedback --port /dev/serial/by-id/usb-STC_STC_USB_Serial-if00 --baudrate 115200 --read-timeout-s 12' < onboard/scripts/o1_wave_rover_serial_feedback_probe.py
```

结果同样失败在 SSH 网络层：

```text
ssh: connect to host 192.168.1.11 port 37878: No route to host
```

因此本轮没有触达远端 Python、没有打开 `/dev/serial/by-id/usb-STC_STC_USB_Serial-if00`、没有发送 `{"T":130}\n`、没有读取到任何串口行，也没有观察到真实 `T=1001`。安全边界保持：

- `safe_to_control=false`
- `sends_motion_commands=false`
- `robot_control_executed=false`
- `delivery_success=false`
- `t130_request_reached_serial=false`
- `t1001_observed=false`
- `evidence_boundary=remote_network_unreachable_not_serial_feedback_result`

这是第三次同类 `remote_network_unreachable` / `ssh_no_route_to_host` blocker 消费：`2026.06.01_20-21`、`2026.06.02_06-07`、`2026.06.02_07-08` 均未触达远端 Python。按项目 blocker 红线，不能继续把同一 SSH/路由不可达问题当成 O1 完成材料；下一轮必须切换到不依赖该 blocker 的 Objective，或由 CEO 现场处理/决策，先恢复 `192.168.1.11:37878` 可路由与 SSH 映射后再继续采集 `T=1001`。

`2026.06.02_13-14_o1-t1001-live-recovery` 按用户恢复后的同一 SSH 入口执行 fail-closed 复采。本轮没有发送 `T=1`、`T=13`、`T=131`、`cmd_vel` 或任何运动命令，只按显式参数发送一次 vendor `{"T":130}\n`。

远端只读 upper readiness：

```bash
timeout 20 ssh -o BatchMode=yes -o ConnectTimeout=8 -p 37878 root@192.168.1.11 'python3 -s - --once-json' < onboard/scripts/o1_upper_computer_readiness_probe.py
```

结果证明 SSH 已恢复，远端主机为 `op-z3-b6.home`，Linux `aarch64`，Python `3.10.12`，`pyserial.available=true`。只读枚举发现 `/dev/serial/by-id/usb-STC_STC_USB_Serial-if00`、`/dev/serial/by-path/platform-5200400.usb-usb-0:1:1.0` 和 `/dev/ttyACM0`，readiness probe 仍固定 `safe_to_control=false`、`sends_commands=false`、`robot_control_executed=false`、`delivery_success=false`，且不打开串口、不写 `/dev/*`。

远端只读 serial probe：

```bash
timeout 20 ssh -o BatchMode=yes -o ConnectTimeout=8 -p 37878 root@192.168.1.11 'python3 -s - --once-json --port /dev/serial/by-id/usb-STC_STC_USB_Serial-if00 --baudrate 115200 --read-timeout-s 2' < onboard/scripts/o1_wave_rover_serial_feedback_probe.py
```

结果为 `serial_opened=true`，目标 by-id 端口存在并指向 `/dev/ttyACM0`，但只读 2 秒窗口 `read_line_count=0`、`parsed_json_count=0`、`observed_feedback_types=[]`，`feedback_request.enabled=false`、`feedback_request.sent=false`，因此 `t1001_feedback_status=not_requested`。该结果只能说明目标端口可打开且默认无被动串口行，不能写成 WAVE ROVER 无反馈或 HIL pass。

远端显式非运动 `T=130` request：

```bash
timeout 35 ssh -o BatchMode=yes -o ConnectTimeout=8 -p 37878 root@192.168.1.11 'python3 -s - --once-json --request-base-feedback --port /dev/serial/by-id/usb-STC_STC_USB_Serial-if00 --baudrate 115200 --read-timeout-s 12' < onboard/scripts/o1_wave_rover_serial_feedback_probe.py
```

结果为 `serial_opened=true`、`feedback_request.enabled=true`、`feedback_request.sent=true`、`feedback_request.write_error=null`、`safe_to_control=false`、`sends_commands=true`、`sends_motion_commands=false`、`robot_control_executed=false`、`delivery_success=false`。12 秒读取窗口仍为 `read_line_count=0`、`parsed_json_count=0`、`invalid_json_count=0`、`observed_feedback_types=[]`、`raw_line_preview=[]`、`error=null`，机器状态为 `t1001_feedback_status=not_observed_after_t130`。

本轮结论：

- `remote_probe_status=ssh_recovered`
- `serial_opened=true`
- `t130_request_reached_serial=true`
- `t130_write_error=null`
- `t1001_observed=false`
- `t1001_feedback_status=not_observed_after_t130`
- `evidence_boundary=serial_open_t130_feedback_request_not_hil`

下一步现场检查必须按 probe 输出的 `next_required_checks[]` 执行：

1. `verify_esp32_power_and_firmware`：确认 WAVE ROVER ESP32 下位机供电、运行固件和 vendor `CMD_BASE_FEEDBACK` 分支。
2. `verify_uart_tx_rx_crossed`：确认上位机到下位机 UART TX/RX 交叉和线缆可靠。
3. `verify_target_port_is_wave_rover_esp32`：确认 `/dev/serial/by-id/usb-STC_STC_USB_Serial-if00` 不是 LiDAR、其他 STC 设备或错误 USB 串口。
4. `check_serial_owner_process`：确认没有 vendor app、systemd service 或其他进程占用同一串口。
5. `use_vendor_terminal_cross_check_t130`：用 vendor terminal 或最小串口终端人工交叉发送 `{"T":130}` 并观察原始行。
6. `verify_wave_rover_cmd_base_feedback_firmware_branch`：确认当前烧录固件包含 `uart_ctrl.h` 的 `CMD_BASE_FEEDBACK` 到 `baseInfoFeedback()` 路径。
