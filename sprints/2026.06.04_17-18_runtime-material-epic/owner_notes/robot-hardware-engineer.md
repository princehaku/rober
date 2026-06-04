# Robot Hardware Engineer Owner Note

## 本轮范围

- sprint: `sprints/2026.06.04_17-18_runtime-material-epic/`
- owner: Hardware Infra Engineer
- 目标: 推进 O1/O7 stop-first HIL 准入前的 vendor-sourced runtime material。
- 安全结论: 本轮只做非运动 device inventory、串口占用、status 和 `T=130 -> T=1001` feedback 检查；2026-06-04 18:12-18:15 CST 复跑时未执行 forward/back/left/right/stop pulse。
- evidence type: `robot_runtime_material` + `software_guard`；不产生 `field_hil_material`。

## 已读 vendor 来源

- `AGENTS.md`
- `OKR.md`
- `docs/vendor/VENDOR_INDEX.md`
- `docs/vendor/waveshare_wave_rover/ugv_rpi/base_ctrl.py`
- `docs/vendor/waveshare_wave_rover/ugv_rpi/config.yaml`
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/json_cmd.h`
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/uart_ctrl.h`
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/ugv_advance.h`
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/WAVE_ROVER_V0.9.ino`
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/IMU_ctrl.h`
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/battery_ctrl.h`
- `docs/hardware/o1_wave_rover_serial_feedback_probe.md`
- `docs/hardware/o1_pc_manual_lidar_hil_boundary.md`

## 已证实的硬件结论

- WAVE ROVER vendor reference 使用 UART 串口、UTF-8 JSON、每行一个 JSON 对象并以 `\n` 结束。
- Vendor Raspberry Pi reference 在 `base_ctrl.py` 中使用 `/dev/ttyAMA0 @115200`，但 Orange Pi 目标设备名必须现场确认，不能回退为 Raspberry Pi 路径。
- 固件 `WAVE_ROVER_V0.9.ino` 执行 `Serial.begin(115200)`。
- `json_cmd.h` 定义:
  - `CMD_SPEED_CTRL=1`，字段 `L/R`，是运动命令。
  - `CMD_ROS_CTRL=13`，字段 `X/Z`，firmware comment 写 m/s 和 rad/s，仍需 HIL 才能确认实车行为。
  - `CMD_BASE_FEEDBACK=130`，是非运动 base feedback request。
  - `CMD_BASE_FEEDBACK_FLOW=131`，会改变 feedback flow 状态，本轮未发送。
  - `FEEDBACK_BASE_INFO=1001`，是 vendor base feedback 类型。
- `uart_ctrl.h` 收到 `T=130` 后调用 `baseInfoFeedback()`；`ugv_advance.h` 中该函数输出 `T=1001`，字段包含 `L/R/r/p/y/v`，其中 `v` 来自 INA219 `loadVoltage_V`。
- `T=1001` 只能作为 vendor feedback material；本轮仍不能写成 robot ACK、HIL pass、ROS `/odom`、`/imu/data`、`/battery` 已验证，或 `safe_to_control=true`。

## 远端非运动检查结果

### SSH device inventory 和占用

命令:

```bash
timeout 30 ssh -o BatchMode=yes -o ConnectTimeout=8 root@192.168.1.11 -p 37878 'hostname; date; ls -l /dev/ttyS5 /dev/ttyACM0 /dev/lidar 2>/dev/null || true; fuser -v /dev/ttyS5 /dev/ttyACM0 /dev/lidar 2>/dev/null || true'
```

关键结果:

```text
op-z3-b6.home
Thu Jun  4 06:12:24 PM CST 2026
crw-rw---- 1 root dialout 166,  0 Jun  4 00:47 /dev/ttyACM0
crw-rw---- 1 root dialout   4, 69 Jun  4 17:24 /dev/ttyS5
```

结论:

- `/dev/ttyS5` 存在，权限 `root:dialout 0660`，符合本轮 base 口候选。
- `/dev/ttyACM0` 存在，权限 `root:dialout 0660`，继续按 STC/LiDAR 风险口处理。
- `/dev/lidar` 本次未列出。
- `fuser` 未输出占用进程；这只能说明本次命令未看到占用，不等于后续服务不会打开设备。

### 8787 status 只读检查

命令:

```bash
timeout 20 ssh -o BatchMode=yes -o ConnectTimeout=8 root@192.168.1.11 -p 37878 'curl -sS --max-time 8 http://127.0.0.1:8787/api/status'
```

关键结果:

- `schema=trashbot.upper_robot_api.v1.status`
- base:
  - `port=/dev/ttyS5`
  - `baudrate=115200`
  - `port_info.exists=true`
  - `pyserial_available=true`
  - `write_control_available=true`
  - `feedback_ack.t1001_observed=false`，原因是 status GET 本身没有执行新一轮 `T=130`，只能读取当前状态。
  - `safe_to_control=false`
  - `robot_control_executed=false`
  - `feedback_samples_latest.latest_t1001_observed_count=3`
  - `feedback_samples_latest.freshness.status=stale`
- radar:
  - `/dev/lidar` 不存在。
  - observed LiDAR candidate 是 `/dev/ttyACM0 @150000`。
  - latest scan proof 仍是 `blocked_or_not_observed`。
  - raw packet proof 为 stale material。

结论:

- status GET 是只读 readback，本轮没有通过它发送 `T=130` 或任何运动命令。
- base 口径已在 runtime status 面显示为 `/dev/ttyS5 @115200`。
- status 面读到的旧 feedback artifact 已过期，本轮随后刷新 `feedback-samples` 材料。

### 8787 `T=130 -> T=1001` 非运动 feedback samples

命令:

```bash
timeout 30 ssh -o BatchMode=yes -o ConnectTimeout=8 root@192.168.1.11 -p 37878 'curl -sS --max-time 12 -X POST http://127.0.0.1:8787/api/base/feedback-samples -H "Content-Type: application/json" -d "{\"sample_count\":3,\"sample_interval_s\":0.2,\"read_timeout_s\":0.2,\"read_window_s\":1.2}"'
```

关键结果:

- `schema=trashbot.upper_robot_api.v1.base_feedback_samples_result`
- `port=/dev/ttyS5`
- `baudrate=115200`
- request command: `{"T":130}`
- `requested_sample_count=3`
- `completed_sample_count=3`
- 每个 sample:
  - `serial_open.ok=true`
  - `serial_write.command={"T":130}`
  - `serial_write.bytes_written=10`
  - `serial_read.ok=true`
  - `read_line_count=2`
  - `parsed_json_count=2`
  - `invalid_json_count=0`
  - `observed_feedback_types=[130,1001]`
  - `t1001_feedback_status=observed`
  - `safe_to_control=false`
  - `sends_motion_commands=false`
  - `robot_control_executed=false`
  - `delivery_success=false`
  - `hil_pass=false`
- aggregate:
  - `t1001_observed_count=3`
  - `all_samples_observed_t1001=true`
  - `blocked_commands_not_sent=["T=1","T=13","T=131","cmd_vel","/api/base/manual"]`
  - `safe_to_control=false`
  - `sends_motion_commands=false`
  - `robot_control_executed=false`
  - `hil_pass=false`
- artifact:
  - `runtime/base_feedback_samples_latest.json`
  - `write.ok=true`
  - `method=atomic_replace`

结论:

- 本轮拿到新的 `robot_runtime_material`: `/dev/ttyS5 @115200` 上显式 `T=130` 三次请求均观察到 vendor `T=1001`。
- 该材料不包含运动命令，不包含 `/api/base/manual`，不包含 `/cmd_vel`，不证明 HIL pass。

### latest artifact 只读回放

命令:

```bash
timeout 20 ssh -o BatchMode=yes -o ConnectTimeout=8 root@192.168.1.11 -p 37878 'curl -sS --max-time 8 http://127.0.0.1:8787/api/base/feedback-samples/latest'
```

关键结果:

- `schema=trashbot.upper_robot_api.v1.base_feedback_samples_latest_result`
- `readback_sends_commands=false`
- `sends_commands=false`
- `sends_motion_commands=false`
- `safe_to_control=false`
- latest result:
  - `all_samples_observed_t1001=true`
  - `t1001_observed_count=3`
  - `observed_feedback_types=[130,1001]`
  - `port=/dev/ttyS5`
  - `baudrate=115200`
  - `feedback_ack.robot_ack_connected=false`
  - `hil_pass=false`

结论:

- latest GET 已确认本轮 artifact 可读取；GET 本身没有再发 `T=130`。

### USB/串口 inventory 只读 probe

命令:

```bash
timeout 30 ssh -o BatchMode=yes -o ConnectTimeout=8 root@192.168.1.11 -p 37878 'python3 -s - --once-json' < onboard/scripts/o1_usb_serial_inventory_probe.py
```

关键结果:

- `schema=trashbot.o1.usb_serial_inventory.v1`
- `generated_at=2026-06-04T10:15:03.625955Z`
- `evidence_boundary=usb_serial_inventory_read_only_not_hil`
- `opens_serial_devices=false`
- `sends_commands=false`
- `safe_to_control=false`
- `/dev/lidar` count `0`
- `/dev/ttyACM0` count `1`
- `/dev/serial/by-id/usb-STC_STC_USB_Serial-if00 -> /dev/ttyACM0`
- `/dev/serial/by-path/platform-5200400.usb-usb-0:1:1.0 -> /dev/ttyACM0`
- sysfs:
  - `idVendor=34bf`
  - `idProduct=ff0a`
  - `manufacturer=STC`
  - `product=STC USB Serial`
  - `DRIVER=cdc_acm`
- `identity_risks[0].risk_id=possible_lidar_or_other_stc`
- recommended check: `unplug_lidar_then_rerun_inventory_and_compare_changed_aliases`

结论:

- `/dev/ttyACM0` 仍不能作为 WAVE ROVER base 口；它是 STC `34bf:ff0a` 风险口，按 LiDAR/其他 STC 候选处理。
- USB inventory probe 不覆盖板载 `/dev/ttyS5` 的 USB sysfs 身份，因此 `/dev/ttyS5` 的当前证据来自 SSH device inventory、8787 status 和 `T=130 -> T=1001` runtime response。

## 未执行运动的原因

本轮没有从现有材料明确证明以下现场安全前提全部成立:

- 现场看护人员在位。
- 机器人周围物理净空满足低速 pulse。
- 人工急停或物理断电路径已就绪。
- CEO/现场负责人对本轮低速 pulse 明确授权。

因此按 fail-closed 执行，只做 `T=130` 非运动 feedback；未调用 `/api/base/manual`，未发送 `T=1`、`T=13`、`T=131` 或 `/cmd_vel`。

## 剩余风险

- `T=1001` 仍是 vendor feedback material，不是项目 robot ACK。
- `safe_to_control` 仍为 `false`；本轮不产生 `field_hil_material`。
- 真实 `/odom`、`/imu/data`、`/battery` ROS topic 尚未在本轮证明。
- 未执行 low-speed pulse，不能证明 forward/back/left/right/stop 现场运动和自动停车。
- `/dev/lidar` symlink 缺失；LiDAR 当前仍通过 `/dev/ttyACM0` STC 候选呈现，需 Software/现场继续处理 udev 或启动链路。
- `fuser` 无输出不等于串口不会被后续服务占用；运动前仍需重新检查占用和 API status。

## 下一步履约动作

1. 现场条件满足后，先写 operator preflight report，确认 `operator_present=true`、`physical_clearance_confirmed=true`、`emergency_stop_ready=true`。
2. 先跑 `onboard/scripts/o1_ttyS5_safe_pulse_acceptance.py --dry-run`，确认 `/api/status` 仍显示 `/dev/ttyS5 @115200` 且 `safe_to_control=false`、`hil_pass=false`。
3. 只有现场授权和安全条件成立时，执行单方向低速短 pulse，初始建议仍遵守 runbook 的 `speed <= 0.08`、`duration_ms <= 350`，并使用同一 `evidence_ref` 绑定 pre-stop、manual response、auto-stop、post-status、`T=1001` 和 operator report。
4. Robot Software Engineer 需要补真实 ROS `/odom`、`/imu/data`、`/battery` topic 材料，避免把 vendor feedback 外推为 ROS feedback。
5. Product/OKR Owner 收口前不得把本轮材料写成 O1 HIL pass 或 `safe_to_control=true`；最多可计入 O1/O7 非运动 `robot_runtime_material`。

## KR / 决策

- 本轮不新增 KR；继续推进既有 KR-O1/O7-Stop-First-HIL 的非运动 runtime material。
- 需要 CEO/现场负责人决策: 是否在下一轮提供现场看护、净空、急停和明确授权，用于执行一次 stop-first 低速 pulse。
