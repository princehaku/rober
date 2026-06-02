# O1 USB/串口 Inventory Probe Micro Sprint

## sprint_type

micro

## 本轮目标

继续推进当前最低 Objective 1。上一轮已经确认 `/dev/serial/by-id/usb-STC_STC_USB_Serial-if00 -> /dev/ttyACM0` 的 sysfs 为 STC `34bf:ff0a`，与当前 LiDAR vendor `99-lidar.rules` 一致，因此本轮不继续盲发 `T=130`，只做无运动、只读 USB/串口 inventory，帮助现场分别插拔 LiDAR 与 WAVE ROVER ESP32/底盘控制器后对比 alias/realpath 变化。

## 已读 vendor 来源

- `AGENTS.md`
- `OKR.md`
- `docs/vendor/VENDOR_INDEX.md`
- `docs/vendor/waveshare_wave_rover/ugv_rpi/base_ctrl.py`
- `docs/vendor/waveshare_wave_rover/ugv_rpi/config.yaml`
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/json_cmd.h`
- `docs/vendor/lidar_pkg_ros2-main/scripts/99-lidar.rules`
- `docs/vendor/lidar_pkg_ros2-main/config/lidar_params.yaml`
- `docs/vendor/lidar_pkg_ros2-main/src/lidar_node.cpp`

## 已证实的硬件结论

- WAVE ROVER vendor reference 使用 UART、UTF-8 JSON、每行一个 JSON object 并以 `\n` 结束。
- `json_cmd.h` 定义 `CMD_BASE_FEEDBACK=130`、`CMD_BASE_FEEDBACK_FLOW=131`、`CMD_SPEED_CTRL=1`、`CMD_ROS_CTRL=13`，本轮全部列入 `blocked_commands_not_sent`，不发送。
- 当前 LiDAR ROS2 vendor 资料使用 `/dev/lidar` 参数，`99-lidar.rules` 把 STC `idVendor=34bf`、`idProduct=ff0a` 映射为 `lidar`，`lidar_node.cpp` 打开串口并发送 `A5 60`。因此 STC `34bf:ff0a`/ttyACM 线索不能当成 WAVE ROVER ESP32 身份。
- 本轮 inventory probe 只证明 USB/tty/sysfs 可见性和 alias/realpath 关系；不证明真实 WAVE ROVER 身份、不证明 `T=1001`、不证明 HIL、不证明底盘可控。

## 实际改动

- 新增 `onboard/scripts/o1_usb_serial_inventory_probe.py`
  - 输出 schema：`trashbot.o1.usb_serial_inventory.v1`。
  - 枚举 `/dev/ttyUSB*`、`/dev/ttyACM*`、`/dev/serial/by-id/*`、`/dev/serial/by-path/*`、`/dev/lidar`。
  - 读取 `/sys/class/tty/<name>/device` 上游 sysfs USB 小文本。
  - 固定 fail-closed 字段：`safe_to_control=false`、`sends_commands=false`、`opens_serial_devices=false`、`robot_control_executed=false`、`delivery_success=false`。
  - 输出 `inventory_summary`、`identity_risks`、`recommended_physical_checks`。
- 新增 `onboard/src/ros2_trashbot_hardware/test/test_o1_usb_serial_inventory_probe.py`
  - fake inspector 覆盖 STC/LiDAR 风险、alias 聚合、无候选设备、CLI JSON 和静态 pyserial 禁用。
- 更新 `docs/hardware/o1_wave_rover_serial_feedback_probe.md`
  - 增加 USB/串口 inventory probe contract、运行命令、远端观察和证据边界。
- 更新 `docs/interfaces/o1_o5_90_evidence_boundary.md`
  - 增加 inventory probe 的 O1 90% 边界说明。
- 更新 `docs/process/okr_progress_log.md`
  - 追加 2026-06-02 17-18 O1 inventory 进度记录。
- 更新 `OKR.md`
  - O1 口径更新为 read-only USB inventory remote STC/LiDAR risk observed；百分比仍保持约 93%，不提升为 HIL。

## 验证结果

```text
$ python3 -m py_compile onboard/scripts/o1_usb_serial_inventory_probe.py
# exit 0, no output
```

```text
$ PYTHONDONTWRITEBYTECODE=1 python3 -m unittest onboard/src/ros2_trashbot_hardware/test/test_o1_usb_serial_inventory_probe.py
.......
----------------------------------------------------------------------
Ran 7 tests in 0.052s

OK
```

远端只读采集：

```bash
timeout 30 ssh -o BatchMode=yes -o ConnectTimeout=8 -p 37878 root@192.168.1.11 'python3 -s - --once-json' < onboard/scripts/o1_usb_serial_inventory_probe.py
```

远端命令 exit 0。结果摘要：

- `schema=trashbot.o1.usb_serial_inventory.v1`
- `host.hostname=op-z3-b6.home`
- `safe_to_control=false`
- `sends_commands=false`
- `opens_serial_devices=false`
- `robot_control_executed=false`
- `delivery_success=false`
- `inventory_summary.total_candidate_paths=3`
- `inventory_summary.realpath_to_aliases["/dev/ttyACM0"]=["/dev/serial/by-id/usb-STC_STC_USB_Serial-if00","/dev/serial/by-path/platform-5200400.usb-usb-0:1:1.0","/dev/ttyACM0"]`
- `/dev/lidar` count 为 `0`，`/dev/ttyUSB*` count 为 `0`
- sysfs 包含 `idVendor=34bf`、`idProduct=ff0a`、`manufacturer=STC`、`product=STC USB Serial`、`DRIVER=cdc_acm`、`PRODUCT=34bf/ff0a/100`
- `identity_risks[0].risk_id=possible_lidar_or_other_stc`
- `identity_risks[0].severity=high`
- 推荐下一步：`unplug_lidar_then_rerun_inventory_and_compare_changed_aliases`

最终 scoped diff check：

```text
$ git diff --check -- OKR.md docs/hardware/o1_wave_rover_serial_feedback_probe.md docs/interfaces/o1_o5_90_evidence_boundary.md docs/process/okr_progress_log.md sprints/2026.06.02_17-18_o1-usb-serial-inventory/tech-done.md onboard/scripts/o1_usb_serial_inventory_probe.py onboard/src/ros2_trashbot_hardware/test/test_o1_usb_serial_inventory_probe.py
# exit 0, no output
```

## 剩余风险与下一步

- 真实 WAVE ROVER ESP32/底盘控制器身份仍未确认；STC `34bf:ff0a` 与 LiDAR udev 一致，必须现场物理追线和分别插拔确认。
- 真实 `T=1001` feedback 仍未观察到；本轮没有发送 `T=130`，也没有打开任何串口。
- 真实 WAVE ROVER UART/HIL、真实底盘控制、真实 `/odom`/`/imu/data`/`/battery`、真实 LiDAR `/scan`、TF/Nav2/SLAM 仍为 `not_proven`。
- 下一步履约动作：现场保存 baseline inventory，拔 LiDAR 后重跑 inventory，恢复 LiDAR 后拔底盘控制器重跑 inventory，比对 by-id/by-path/`/dev/lidar`/realpath 变化；只有物理确认目标端口连接 WAVE ROVER ESP32 后，才运行显式 serial feedback probe 或 vendor terminal `T=130` 交叉验证。
