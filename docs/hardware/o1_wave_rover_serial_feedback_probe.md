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

## 2026-06-03 `/dev/ttyS5` 控制口证据分层

本轮 Hardware owner 复核了现场新增事实，但复核过程只读取本地资料和 git diff；没有打开任何串口，没有 SSH，没有发送 `T=1`、`T=13`、`cmd_vel` 或其他运动命令，也没有再次发送 `T=130`。

新增现场事实：

- CEO 现场观察到 Orange Pi `/dev/ttyS5 @115200` 上的 `T=1,L=0.08,R=0.08` 可让 WAVE ROVER 底盘响应。
- 现场随后发送 `T=1,L=0,R=0` 停车命令。
- `/dev/ttyACM0` 仍按前序证据归类为 STC/LiDAR 风险口，不作为本轮底盘控制口。
- `/dev/ttyS5 @115200` 后续已通过 8787 非运动 feedback endpoint 读到一次 `T=1001`；本节原始现场点动当时仍未完成反馈/ACK 闭环，最新部署验证见下方 `2026-06-03 13-14` 段落。

采用的 vendor 证据：

- `docs/vendor/waveshare_wave_rover/ugv_rpi/base_ctrl.py`：`base_speed_ctrl()` 写 `{"T":1,"L":...,"R":...}`；写入时使用 `json.dumps(data) + '\n'` 并以 UTF-8 编码；vendor Raspberry Pi reference 端口为 `/dev/ttyAMA0`、波特率 `115200`，但 Orange Pi 路径必须现场确认。
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/json_cmd.h`：`CMD_SPEED_CTRL=1`、`CMD_BASE_FEEDBACK=130`、`FEEDBACK_BASE_INFO=1001`。
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/uart_ctrl.h`：串口接收以 `\n` 作为命令结束符，再对累积字符串执行 `deserializeJson()`。
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/WAVE_ROVER_V0.9.ino`：固件 `Serial.begin(115200)`。

证据边界：

| 事项 | 当前状态 | 不能外推为 |
| --- | --- | --- |
| `/dev/ttyS5 @115200` | 现场可写控制口，`T=1` 低速点动有响应 | HIL pass、闭环安全控制、ROS2 `/cmd_vel` 已接入 |
| `T=1,L=0.08,R=0.08` | CEO 现场观察到底盘响应 | 轮向/速度标定已完成、可量产默认速度 |
| `T=1,L=0,R=0` | 现场已执行停车命令 | 急停链路已产品化、自动停车逻辑已验证 |
| `T=130 -> T=1001` | 2026-06-03 13-14 已通过远端 8787 非运动 endpoint 观察到一次 `T=1001` | HIL pass、闭环安全控制、ROS `/odom`、`/imu/data`、`/battery` 实测反馈已可用 |

下一步短时点动和 ACK/急停门槛：

1. 点动前先确认操作员、车辆周边空间、电源切断路径和日志记录方式。
2. 只允许短时、低速、明确时长的点动；命令后必须自动补发 `T=1,L=0,R=0`。
3. 先把 `/dev/ttyS5`、`115200`、点动速度、点动时长、自动停车超时做成显式参数，不写死到 launch 默认值。
4. 在没有 `T=1001` 或等价 ACK 前，PC/ROS 控制入口必须 fail-closed，不得把 UI 按钮或 `/cmd_vel` 直接接到底盘。
5. 后续 HIL packet 必须同源包含命令日志、停车日志、至少两帧 `T=1001`、ROS `/imu/data`、`/battery` 和 `/odom` 边界说明。

## 2026-06-03 8787 显式 T=130 feedback request endpoint

`onboard/scripts/upper_robot_api.py` 已在 8787 统一上位机 API 中新增显式 `POST /api/base/feedback-request`。该入口只发送一次 vendor `CMD_BASE_FEEDBACK` / `{"T":130}`，随后在短窗口内读取 newline-delimited JSON，并统计是否观察到 `T=1001`。

`POST /api/base/feedback-samples` 是本轮新增的保守多样本 collector。它复用同一条 `request_base_feedback_once()` 路径，重复发送 vendor `{"T":130}`，每个 sample 独立短窗口读取 newline-delimited JSON，再聚合 `T=1001` observed 数量和反馈类型。它不是 motion/manual 入口，不发送 `T=1`、`T=13`、`T=131`、`cmd_vel`，也不调用 `/api/base/manual`。

`GET /api/base/feedback-samples/latest` 是 artifact 只读回放入口。`POST /api/base/feedback-samples` 成功或失败后都会尝试把 latest 结果通过同目录临时文件 + `os.replace()` 原子保存到 `ROBER_BASE_FEEDBACK_SAMPLES_ARTIFACT_PATH` / `--feedback-samples-artifact-path` 指向的 JSON 文件，默认 `runtime/base_feedback_samples_latest.json`。latest GET 只读取该文件；文件不存在、读取失败、JSON 损坏或 JSON root 不是对象时 fail-closed，并固定 `safe_to_control=false`、`sends_commands=false`、`sends_motion_commands=false`、`robot_control_executed=false`、`hil_pass=false`。该 readback 不打开串口、不 import/use pyserial、不发送 `T=130`、`T=1`、`T=13`、`T=131`、`cmd_vel` 或 `/api/base/manual`。

采用的 vendor 证据：

- `docs/vendor/waveshare_wave_rover/ugv_rpi/base_ctrl.py`：vendor Python reference 使用 `json.dumps(data) + '\n'` 写 UART JSON 行。
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/json_cmd.h`：`CMD_BASE_FEEDBACK=130`，`FEEDBACK_BASE_INFO=1001`，同时 `CMD_SPEED_CTRL=1`、`CMD_ROS_CTRL=13`、`CMD_BASE_FEEDBACK_FLOW=131` 分属运动或 feedback-flow 命令。
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/uart_ctrl.h`：ESP32 端按 `\n` 结束符累积 JSON，再进入 `CMD_BASE_FEEDBACK -> baseInfoFeedback()` 分支。
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/ugv_advance.h`：`baseInfoFeedback()` 输出 `T=1001` 反馈字段。

接口边界：

- 只有显式 `POST /api/base/feedback-request` 会触发该请求；`GET /api/status` 和 `GET /api/base/status` 不会自动打开串口、不会写 `T=130`。
- 只有显式 `POST /api/base/feedback-samples` 会触发多样本请求；`GET /api/status` 和 `GET /api/base/status` 不会自动采样。
- 该 endpoint 不发送 `T=1`、`T=13`、`T=131`、`cmd_vel` 或 `/api/base/manual`，并在响应 `blocked_commands_not_sent` 中固定列出这些未发送命令。
- 响应固定 `safe_to_control=false`、`sends_motion_commands=false`、`robot_control_executed=false`、`delivery_success=false`、`hil_pass=false`。
- `feedback_ack.t1001_observed=true` 只表示本次短窗口中解析到 `T=1001` JSON 行；仍不能直接写成 HIL pass、闭环安全控制或真实 `/odom`、`/imu/data`、`/battery` 已接入。
- latest readback 顶层 `sends_commands=false` 表示本次 GET 没有发命令；`latest_result` 内的历史 payload 可能保留上一次 POST 的 `sends_commands=true`，不能混淆为 readback 行为。

## 2026-06-03 13-14 远端 8787 feedback endpoint 部署验证

本轮只做远端脚本部署和非运动 feedback request 验证。已将本地
`onboard/scripts/upper_robot_api.py` 通过 `scp` 复制到远端
`/root/rober/onboard/scripts/upper_robot_api.py`，随后重启
`trashbot-upper-robot-api.service`，`systemctl is-active` 返回 `active`。

非运动验证命令为 `POST /api/base/feedback-request`，请求体只包含
`read_window_s=3` 和 `read_timeout_s=0.2`。真实返回关键字段：

- HTTP `200`
- `port=/dev/ttyS5`
- `baudrate=115200`
- `serial_open.ok=true`
- `serial_write.command={"T":130}`
- `serial_write.bytes_written=10`
- `serial_read.ok=true`
- `read_line_count=2`
- `parsed_json_count=2`
- `invalid_json_count=0`
- `observed_feedback_types=[130,1001]`
- `t1001_feedback_status=observed`

## 2026-06-03 14-15 远端 8787 feedback samples 多样本验证

本轮将新增多样本 collector 的 `onboard/scripts/upper_robot_api.py` 通过 `scp`
部署到远端 `/root/rober/onboard/scripts/upper_robot_api.py`，随后重启
`trashbot-upper-robot-api.service`，`systemctl is-active` 返回 `active`。

非运动验证命令为 `POST /api/base/feedback-samples`，请求体只包含
`sample_count=3`、`sample_interval_s=0.2`、`read_timeout_s=0.2` 和
`read_window_s=1.2`。真实返回关键字段：

- HTTP `200`
- `schema=trashbot.upper_robot_api.v1.base_feedback_samples_result`
- `requested_sample_count=3`
- `completed_sample_count=3`
- `t1001_observed_count=3`
- `observed_feedback_types=[130,1001]`
- `all_samples_observed_t1001=true`
- `partial_samples_observed_t1001=false`
- `samples[].t1001_feedback_status=["observed","observed","observed"]`
- `samples[].observed_feedback_types=[[130,1001],[130,1001],[130,1001]]`
- `blocked_commands_not_sent=["T=1","T=13","T=131","cmd_vel","/api/base/manual"]`
- `safe_to_control=false`
- `sends_motion_commands=false`
- `robot_control_executed=false`
- `delivery_success=false`
- `hil_pass=false`

本轮没有调用 `/api/base/manual`，没有发送 `T=1`、`T=13`、`T=131`
或 ROS `/cmd_vel`。该材料证明同一个 8787 非运动入口可以重复采到
3/3 个 `T=130 -> T=1001` 样本；仍不是 HIL pass，不证明运动控制安全、
robot ACK connected、真实 ROS `/odom`、`/imu/data`、`/battery` 或完整 delivery success。
- `feedback_ack.t1001_observed=true`
- `feedback_ack.robot_ack_connected=false`
- `safe_to_control=false`
- `sends_motion_commands=false`
- `robot_control_executed=false`
- `delivery_success=false`
- `hil_pass=false`

本轮没有调用 `/api/base/manual`，没有发送 `T=1`、`T=13`、`T=131`
或 ROS `/cmd_vel`。因此该证据只把 O1 从“远端 endpoint 405 / 未部署”
推进到“远端 endpoint 已部署且一次 `T=130 -> T=1001` feedback observed”。
它仍不能证明 HIL pass、运动控制安全、真实 `/odom`、`/imu/data`、
`/battery`、自动停车/急停演练或完整上车任务闭环。

## 2026-06-03 O1 safe pulse post-status acceptance

`onboard/scripts/o1_ttyS5_safe_pulse_acceptance.py` 当前只通过 8787 上位 API 采集短 pulse 验收材料，不新增真实串口直连，不 import/use pyserial，不发送 `T=130`、`T=131` 或 ROS `/cmd_vel`。

2026-06-03 09-10 将 operator report 修正为两阶段合同，状态名为 `execution_preflight_report_ready_not_hil`。runner 支持 `--operator-report-json PATH_OR_-`，把现场人工 JSON 合并进同一 artifact 的 `operator_report` 字段，并输出机器可读 `operator_report_status`：

- `missing`：未提供报告。
- `ready_for_execution`：执行前 preflight 三项 `operator_present`、`physical_clearance_confirmed`、`emergency_stop_ready` 均可解析并为 true。该状态允许执行模式通过 operator report gate，但仍不是 HIL pass。
- `ready_for_review`：preflight 三项均为 true，且执行后观察字段 `observed_motion`、`observed_stop` 均可解析并为 true，同时 `operator_notes`、`reported_at` 存在。该状态只表示报告可进入人工/机器复核。
- `unsafe_or_incomplete`：报告缺字段、布尔值不可解析，或 operator/净空/急停路径任一关键字段为 false。

operator report 只代表人工 preflight 和执行后观察材料，不能让 dry-run 变成 motion，不能把 `safe_to_control` 改成 true，也不能替代 `T=1001`、ACK、ROS `/odom`、`/imu/data`、`/battery` 或真实 HIL packet。执行模式如果缺少安全 preflight 三项，或三项里任一项为 false/不可解析，会在 `operator_report_missing_or_incomplete` 阶段 fail-closed，不会 POST `/api/base/manual`。`observed_motion`、`observed_stop`、`operator_notes`、`reported_at` 是执行后观察字段，preflight-only 报告缺少这些字段时不得阻断执行前 manual POST。

执行模式的证据顺序固定为：

1. `GET /api/status`：读取 camera/radar/base 摘要，若失败则 `blocked_before_motion`，不 POST manual。
2. `POST /api/base/manual`：只在 `--execute-motion --confirm-physical-clearance` 且非 `--dry-run` 时触发。
3. `POST /api/base/stop`：manual 后追加一次 stop evidence；失败也要保留。
4. `GET /api/status`：manual + extra stop 后再采一次，形成 `post_status_request`、`post_status_summary`、`post_t1001_feedback_status`。

新增机器字段：

- `acceptance_verdict.status=dry_run_only`：未授权运动，仅采集 status。
- `acceptance_verdict.status=blocked_before_motion`：初始 status 或参数校验失败，运动 POST 被阻断。
- `acceptance_verdict.failed_step=operator_report_missing_or_incomplete`：执行模式缺少安全 preflight 报告，运动 POST 被阻断。
- `acceptance_verdict.status=motion_posted_without_ack`：manual 已尝试，但缺 `T=1001`/ACK，或 manual/stop/post-status 任一步失败。
- `acceptance_verdict.status=motion_posted_with_t1001`：manual/stop 后的 post-status 或 manual response 出现 `T=1001`/ACK 线索；仍不是 HIL pass。

所有 verdict 都固定 `safe_to_control=false`、`hil_pass=false`。缺 `T=1001`/ACK 时不得写成 `safe_to_control=true`；出现 `T=1001`/ACK 或完整 operator report 时也只能作为 HIL packet 前置材料，仍需同源 `feedback_T1001.log`、ROS `/odom`、`/imu/data`、`/battery` 和 operator HIL report。

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

## 2026-06-03 8787 Upper Robot API 安全收口边界

本轮 Hardware owner 只在本地收口 8787 统一上位机 API 的底盘手控安全语义，没有打开真实串口、没有 SSH、没有发送 `T=1/T=13/T=130/T=131`、没有发送 `/cmd_vel`，也没有触发真实运动。

采用的 vendor 来源：

- `docs/vendor/VENDOR_INDEX.md`：WAVE ROVER 上下位机链路为 UART、UTF-8、newline-delimited JSON；Orange Pi 串口设备名必须现场确认。
- `docs/vendor/waveshare_wave_rover/ugv_rpi/base_ctrl.py`：`serial.Serial(uart_dev_set, buad_set, timeout=1)`；`send_command()` 最终写 `(json.dumps(data) + '\n').encode("utf-8")`；示例 `BaseController('/dev/ttyAMA0', 115200)`。
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/json_cmd.h`：`CMD_SPEED_CTRL=1`，`CMD_BASE_FEEDBACK=130`，`FEEDBACK_BASE_INFO=1001`。
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/uart_ctrl.h`：`CMD_SPEED_CTRL` 分支要求 `T/L/R` 且 `L/R` 为 float 后调用 `setGoalSpeed()`；`CMD_BASE_FEEDBACK` 分支调用 `baseInfoFeedback()`。
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/ugv_advance.h`：`baseInfoFeedback()` 输出 `T=1001`，包含 `L/R/r/p/y/v` 等字段并 `Serial.println(...)`。

本轮安全规则：

- 8787 API 手控只允许 `forward/back/left/right/stop`，非法方向必须结构化拒绝，不得 500，不得写串口。
- accepted manual pulse 必须低速、限时、自动停车；返回中必须保留方向写入结果、stop 写入结果和串口失败原因。
- `/api/base/stop` 的 `robot_control_executed` 只反映 stop JSON 写入是否成功；HTTP handler 成功不等于底盘已执行。
- 所有响应继续保留 `feedback_ack.t1001_observed=false`，因为本轮没有读取 `T=1001`，不能声明 ACK、HIL、真实 `/odom`、真实 `/imu/data`、真实 `/battery` 或 delivery success。

## 2026-06-03 `/dev/ttyS5` Safe Pulse Acceptance Runner

`onboard/scripts/o1_ttyS5_safe_pulse_acceptance.py` 是 O1 的短时点动验收 runner，用于以后现场有人看护时，围绕已经确认的 Orange Pi `/dev/ttyS5 @115200` 控制路径采集短 pulse、auto-stop、ACK/`T=1001` 边界材料。

默认模式是 dry-run / read-only：

```bash
python3 onboard/scripts/o1_ttyS5_safe_pulse_acceptance.py --dry-run --once-json
```

默认行为只会读取 8787 上位 API 的 `GET /api/status`，或通过 `--status-json <path>` 消费本地已有 status JSON。默认不会调用 `/api/base/manual`，不会调用 `/api/base/stop`，不会打开 `/dev/ttyS5`，不会发送 `T=1/T=13/T=130/T=131`，不会发送 `/cmd_vel`。

输出 contract：

- `schema=trashbot.o1.ttyS5_safe_pulse_acceptance.v1`
- `evidence_boundary=api_status_dry_run_not_hil`
- `safe_to_control=false`
- `sends_commands=false`
- `sends_motion_commands=false`
- `robot_control_executed=false`
- `delivery_success=false`
- `status_summary.camera/radar/base`
- `status_summary.base.port=/dev/ttyS5`（若 8787 status 返回该字段）
- `status_summary.base.baudrate=115200`（若 8787 status 返回该字段）
- `t1001_feedback_status=observed/not_observed/unknown`
- `blocked_commands_not_sent[]`

执行模式必须同时传入两个显式参数：

```bash
python3 onboard/scripts/o1_ttyS5_safe_pulse_acceptance.py \
  --base-url http://192.168.1.11:8787 \
  --execute-motion \
  --confirm-physical-clearance \
  --direction forward \
  --speed 0.05 \
  --duration-ms 250 \
  --once-json \
  --output /safe/runtime/o1-ttyS5-safe-pulse-acceptance.json
```

执行边界：

- runner 不直连串口，只通过 8787 `/api/base/manual` 调用现有 guardrail。
- runner 本地再次限制 `speed <= 0.08`、`duration_ms <= 350`，然后由 8787 API 进行第二层限幅。
- `/api/base/manual` 返回后，runner 会再调用一次 `/api/base/stop`，作为独立 stop evidence。
- `--output` 使用临时文件 + `os.replace()` 原子写入，避免现场采集中断留下半写 artifact。
- 即使执行模式返回 `manual_command_executed=true`，在没有 `T=1001` 或等价 ACK 前仍只能写 `api_manual_short_pulse_with_extra_stop_not_hil`，不能声明 `safe_to_control=true`、HIL pass、真实 `/odom`、真实 `/imu/data`、真实 `/battery` 或 delivery success。

本轮没有执行远端 `/api/base/manual` 或 `/api/base/stop`；本 prompt 未授权无人看护真实运动。
