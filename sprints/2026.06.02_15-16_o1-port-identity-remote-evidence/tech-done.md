# 2026.06.02 15-16 O1 Port Identity Remote Evidence

sprint_type: micro

## 目标

本轮继续推进当前最低 Objective 1，但不重复盲目发送 `T=130`。目标是在上位机 `root@192.168.1.11:37878` 上运行 no-motion port identity probe，确认 `/dev/serial/by-id/usb-STC_STC_USB_Serial-if00` 的端口身份风险，并把材料写回 OKR。

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

- WAVE ROVER vendor 资料仍只证明上/下位机协议是 UART newline-delimited JSON；`json_cmd.h` 定义 `CMD_BASE_FEEDBACK=130`、`FEEDBACK_BASE_INFO=1001`，`uart_ctrl.h` 在收到 `CMD_BASE_FEEDBACK` 时调用 `baseInfoFeedback()`。
- 当前 LiDAR ROS2 vendor 资料明确要求通过 `/dev/ttyUSB*` 或 `/dev/ttyACM*` 插拔对比确认雷达设备；`99-lidar.rules` 把 `idVendor=34bf`、`idProduct=ff0a` 的 STC USB Serial 映射为 `/dev/lidar`。
- 远端 no-motion identity probe 证实目标端口存在，`/dev/serial/by-id/usb-STC_STC_USB_Serial-if00 -> /dev/ttyACM0`，同一 realpath 还有 `/dev/serial/by-path/platform-5200400.usb-usb-0:1:1.0` 和 `/dev/ttyACM0`。
- 远端 sysfs 证实该 `ttyACM0` 的 USB device 为 `idVendor=34bf`、`idProduct=ff0a`、`manufacturer=STC`、`product=STC USB Serial`，`uevent` 中也出现 `PRODUCT=34bf/ff0a/100`、`DRIVER=cdc_acm`。
- 以上结果与 LiDAR vendor udev 规则完全一致，因此目标端口当前只能判定为 `possible_lidar_or_other_stc`。它不能证明该端口是 WAVE ROVER ESP32，不能证明 `T=1001`，不能证明 HIL、底盘可控或 delivery success。

## 实际改动

- 新增本文件，记录远端 port identity 材料、验证命令和剩余风险。
- 更新 `OKR.md`，保持 O1 约 93%，把 15-16 远端身份材料纳入 O1 当前进展和最高优先级说明。
- 更新 `docs/process/okr_progress_log.md`，追加本轮 micro sprint closeout。
- 未修改 `onboard/scripts/o1_wave_rover_port_identity_probe.py` 和对应测试，因为远端 JSON 已包含 `status`、`realpath`、候选端口、sysfs vendor/product/manufacturer/product/interface、`risk_flags` 和 `next_required_checks`。

## 验证结果

### 远端 no-motion 身份采集

命令：

```bash
timeout 30 ssh -o BatchMode=yes -o ConnectTimeout=8 -p 37878 root@192.168.1.11 'python3 -s - --once-json --port /dev/serial/by-id/usb-STC_STC_USB_Serial-if00' < onboard/scripts/o1_wave_rover_port_identity_probe.py
```

结果：exit 0，返回 `trashbot.o1.wave_rover_port_identity_probe.v1` JSON。

关键字段：

- `identity_assessment.status=possible_lidar_or_other_stc`
- `identity_assessment.possible_role=possible_lidar_or_other_stc_not_wave_rover_proven`
- `identity_assessment.risk_flags=["stc_or_ttyacm_is_not_unique","lidar_clue_present"]`
- `target.realpath=/dev/ttyACM0`
- `serial_candidates.related_to_target_realpath` 包含 `/dev/serial/by-id/usb-STC_STC_USB_Serial-if00`、`/dev/serial/by-path/platform-5200400.usb-usb-0:1:1.0`、`/dev/ttyACM0`
- `sysfs_usb_tty_description.nodes[1].attributes.idVendor=34bf`
- `sysfs_usb_tty_description.nodes[1].attributes.idProduct=ff0a`
- `sysfs_usb_tty_description.nodes[1].attributes.manufacturer=STC`
- `sysfs_usb_tty_description.nodes[1].attributes.product=STC USB Serial`
- `sysfs_usb_tty_description.nodes[0].uevent` 包含 `DRIVER=cdc_acm`、`PRODUCT=34bf/ff0a/100`、`INTERFACE=2/2/1`
- `safe_to_control=false`
- `sends_commands=false`
- `opens_serial_devices=false`
- `robot_control_executed=false`
- `delivery_success=false`

`next_required_checks`：

- `physically trace USB/UART cable from target port to WAVE ROVER ESP32`
- `compare by-id/by-path before and after unplugging LiDAR and base controller separately`
- `check whether /dev/lidar or LiDAR udev vendor/product points to the same realpath`
- `only after identity is confirmed, run explicit serial feedback probe or vendor terminal T=130`

## 剩余风险

- O1 不提升百分比：本轮只证明目标端口存在且强命中 STC/LiDAR 风险线索，不证明 WAVE ROVER ESP32 身份。
- 下一步必须现场物理追线，并分别插拔 LiDAR 与底盘控制器，对比 by-id/by-path/`/dev/lidar` 是否变化。
- 只有确认目标端口确实连接 WAVE ROVER ESP32 后，才能重新运行显式 serial feedback probe 或 vendor terminal `T=130`；在身份确认前继续发送 `T=130` 会污染判断。
- 真实 `T=1001` feedback、UART/HIL、真实底盘控制、真实 LiDAR `/scan`、ROS Humble runtime、TF、Nav2/SLAM 和完整送达闭环仍为 `not_proven`。
