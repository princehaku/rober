# Robot Hardware Engineer Owner Note

## 任务口径

- sprint_type: epic owner note
- Objective: O1/O7 stop-first HIL 准入
- 本轮只做 SSH 非运动 serial/device/status 检查和 HIL safety preflight。
- 禁止事项：未调用 `/api/base/manual`，未发布 `/cmd_vel`，未发送 `T=1/T=13/T=131`，未执行 forward/back/left/right pulse。
- 证据边界：本轮是 `vendor_feedback_material + safety_preflight_material`，不是 HIL pass，不证明 `safe_to_control=true`。

## 已读 vendor 来源

- `AGENTS.md`
  - 硬件相关任务必须先读 `docs/vendor/VENDOR_INDEX.md`，不能凭记忆猜 UART、波特率、JSON 指令或反馈字段。
- `OKR.md`
  - O1 只有低速短 pulse、同场 stop/status、`T=130 -> T=1001`、真实 `/odom`/`/imu/data`/`/battery`、HIL 复核等材料才涨分；非运动 feedback 只能增强材料，不等于 HIL。
- `docs/vendor/VENDOR_INDEX.md`
  - WAVE ROVER 上下位机链路是 UART、UTF-8、newline-delimited JSON。
  - vendor Raspberry Pi reference 是 `/dev/ttyAMA0 @115200`；Orange Pi 目标设备名必须上车确认，不能照搬。
- `docs/vendor/waveshare_wave_rover/ugv_rpi/base_ctrl.py`
  - `BaseController` 使用 `serial.Serial(uart_dev_set, buad_set, timeout=1)`。
  - `process_commands()` 写入 `(json.dumps(data) + '\n').encode("utf-8")`。
  - `base_speed_ctrl()` 发送 `{"T":1,"L":...,"R":...}`，本轮未触发该路径。
- `docs/vendor/waveshare_wave_rover/ugv_rpi/config.yaml`
  - vendor app 中有 `slow_speed: 0.2`、`max_speed: 1.3`，只能作为 vendor reference；本轮未执行任何速度命令。
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/json_cmd.h`
  - `CMD_SPEED_CTRL=1`、`CMD_ROS_CTRL=13`、`CMD_BASE_FEEDBACK=130`、`CMD_BASE_FEEDBACK_FLOW=131`、`FEEDBACK_BASE_INFO=1001`。
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/uart_ctrl.h`
  - ESP32 串口按 `\n` 判断一条完整 JSON，再 `deserializeJson()`。
  - `CMD_BASE_FEEDBACK` 分支调用 `baseInfoFeedback()`。
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/ugv_advance.h`
  - `baseInfoFeedback()` 输出 `T=FEEDBACK_BASE_INFO`，包含 `L/R/r/p/y/v` 等字段，并 `Serial.println(...)`。
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/WAVE_ROVER_V0.9.ino`
  - 固件 `Serial.begin(115200)`。
- `docs/hardware/o1_pc_manual_lidar_hil_boundary.md`
  - PC manual HIL 必须 stop-first、同一 evidence ref、operator report、post-status 和 `T=1001` 边界齐全；`T=1001` 不能单独写成 robot ACK/HIL pass。
- `docs/hardware/o1_wave_rover_serial_feedback_probe.md`
  - `T=130` 是显式非运动 feedback request；即使观察到 `T=1001`，证据边界仍不是 HIL pass。

## 已证实的硬件结论

- 远端 SSH 可达，目标机为 `op-z3-b6.home`，`Linux aarch64`。
- 远端 `/dev/ttyS5` 存在且是字符设备，权限摘要为 `mode_octal=0o660`、`uid=0`、`gid=20`。
- `/dev/ttyS5` 身份 probe 仍给出 `identity_insufficient`：路径存在不等于物理追线已完成；后续 HIL 前仍要确认该线实际接到 WAVE ROVER ESP32。
- 远端 inventory 只读枚举到 `/dev/ttyACM0`、`/dev/serial/by-id/usb-STC_STC_USB_Serial-if00`、`/dev/serial/by-path/platform-5200400.usb-usb-0:1:1.0`，全部指向 `/dev/ttyACM0`，且带 STC `34bf:ff0a` 线索；该口继续按 LiDAR/错口高风险处理，不能当底盘口盲发 `T=130`。
- 上位机 readiness 显示 ROS Humble setup、`/root/rober/onboard/install/setup.bash` 和 pyserial 均存在；但 `wave_rover_readiness.status=not_ready_for_control`，安全字段保持 `safe_to_control=false`。
- 8787 dry-run HIL preflight 只读取 `/api/status`，`acceptance_verdict.status=dry_run_only`，`manual_request=null`，`robot_control_executed=false`。
- fresh 8787 非运动 `POST /api/base/feedback-request` 在 `/dev/ttyS5 @115200` 上发送一次 vendor `{"T":130}`，读到 `observed_feedback_types=[130,1001]`，`t1001_feedback_status=observed`。
- 该 `T=1001` 只证明 vendor feedback material observed；`feedback_ack.robot_ack_connected=false`、`hil_pass=false`、`safe_to_control=false`，不能写成 robot ACK、运动安全或 HIL pass。

## SSH 验证摘要

### 1. USB/serial inventory 只读检查

命令：

```bash
timeout 30 bash -lc "ssh -o BatchMode=yes -o ConnectTimeout=8 -p 37878 root@192.168.1.11 'python3 -s - --once-json' < onboard/scripts/o1_usb_serial_inventory_probe.py"
```

关键输出：

```json
{
  "schema": "trashbot.o1.usb_serial_inventory.v1",
  "host": {"hostname": "op-z3-b6.home", "machine": "aarch64"},
  "safe_to_control": false,
  "sends_commands": false,
  "opens_serial_devices": false,
  "robot_control_executed": false,
  "inventory_summary": {
    "realpath_to_aliases": {
      "/dev/ttyACM0": [
        "/dev/serial/by-id/usb-STC_STC_USB_Serial-if00",
        "/dev/serial/by-path/platform-5200400.usb-usb-0:1:1.0",
        "/dev/ttyACM0"
      ]
    },
    "stc_or_ttyacm_realpaths": ["/dev/ttyACM0"]
  },
  "identity_risks": [
    {"risk_id": "possible_lidar_or_other_stc", "severity": "high"}
  ]
}
```

### 2. `/dev/ttyS5` 身份只读检查

命令：

```bash
timeout 30 bash -lc "ssh -o BatchMode=yes -o ConnectTimeout=8 -p 37878 root@192.168.1.11 'python3 -s - --once-json --port /dev/ttyS5' < onboard/scripts/o1_wave_rover_port_identity_probe.py"
```

关键输出：

```json
{
  "schema": "trashbot.o1.wave_rover_port_identity_probe.v1",
  "target_port": "/dev/ttyS5",
  "safe_to_control": false,
  "sends_commands": false,
  "opens_serial_devices": false,
  "target": {
    "exists": true,
    "is_character_device": true,
    "realpath": "/dev/ttyS5",
    "mode_octal": "0o660"
  },
  "identity_assessment": {
    "status": "identity_insufficient",
    "possible_role": "unknown_serial_device",
    "risk_flags": ["no_distinctive_usb_identity_clue"]
  }
}
```

### 3. 上位机 readiness 只读检查

命令：

```bash
timeout 35 bash -lc "ssh -o BatchMode=yes -o ConnectTimeout=8 -p 37878 root@192.168.1.11 'python3 -s - --once-json' < onboard/scripts/o1_upper_computer_readiness_probe.py"
```

关键输出：

```json
{
  "schema": "trashbot.o1.upper_computer_readiness.v1",
  "boundary": {
    "safe_to_control": false,
    "sends_commands": false,
    "opens_serial_devices": false,
    "sends_cmd_vel": false,
    "robot_control_executed": false
  },
  "pyserial": {"available": true, "opened": false},
  "ros_env_hints": {
    "humble_setup_bash": {"exists": true},
    "rober_install_setup_bash": {"exists": true}
  },
  "repo_hints": {"repo_root": "/root/rober"},
  "wave_rover_readiness": {
    "status": "not_ready_for_control",
    "orange_pi_serial_status": "candidate_paths_listed_only_not_confirmed"
  }
}
```

### 4. HIL safety preflight dry-run

命令：

```bash
timeout 35 bash -lc "ssh -o BatchMode=yes -o ConnectTimeout=8 -p 37878 root@192.168.1.11 'python3 -s - --base-url http://127.0.0.1:8787 --dry-run --once-json --evidence-ref o1-o7-stop-first-preflight-20260604T2051Z' < onboard/scripts/o1_ttyS5_safe_pulse_acceptance.py"
```

关键输出：

```json
{
  "schema": "trashbot.o1.ttyS5_safe_pulse_acceptance.v1",
  "evidence_boundary": "api_status_dry_run_not_hil",
  "execution_gate": {
    "dry_run": true,
    "execute_motion": false,
    "confirm_physical_clearance": false,
    "authorized": false
  },
  "acceptance_verdict": {
    "status": "dry_run_only",
    "hil_pass": false,
    "safe_to_control": false,
    "reason": "execution was not authorized; only status evidence was collected"
  },
  "manual_request": null,
  "safe_to_control": false,
  "sends_commands": false,
  "sends_motion_commands": false,
  "robot_control_executed": false,
  "status_summary": {
    "base": {
      "port": "/dev/ttyS5",
      "baudrate": 115200,
      "safe_to_control": false,
      "write_control_available": true,
      "t1001_observed": false,
      "robot_ack_connected": false
    }
  }
}
```

### 5. Fresh 非运动 `T=130 -> T=1001` feedback request

命令：

```bash
timeout 45 ssh -o BatchMode=yes -o ConnectTimeout=8 -p 37878 root@192.168.1.11 'python3 -s -'
```

远端脚本只访问：

- `GET http://127.0.0.1:8787/health`
- `GET http://127.0.0.1:8787/api/base/status`
- `POST http://127.0.0.1:8787/api/base/feedback-request`
- `GET http://127.0.0.1:8787/api/base/status`

关键输出：

```json
{
  "schema": "trashbot.o1_o7.stop_first_non_motion_ssh_status.v1",
  "forbidden_paths_not_called": ["/api/base/manual", "/cmd_vel", "T=1", "T=13", "T=131"],
  "health": {"ok": true, "http_status": 200, "status": "ready"},
  "feedback_request": {
    "schema": "trashbot.upper_robot_api.v1.base_feedback_request_result",
    "port": "/dev/ttyS5",
    "baudrate": 115200,
    "request": {"method": "POST", "endpoint": "/api/base/feedback-request", "command": {"T": 130}},
    "serial_open": {"ok": true, "port": "/dev/ttyS5", "baudrate": 115200},
    "serial_write": {"ok": true, "bytes_written": 10, "command": {"T": 130}},
    "serial_read": {"ok": true, "error": null},
    "read_line_count": 2,
    "parsed_json_count": 2,
    "invalid_json_count": 0,
    "observed_feedback_types": [130, 1001],
    "t1001_feedback_status": "observed",
    "feedback_ack": {
      "t1001_observed": true,
      "robot_ack_connected": false,
      "reason": "T=1001 observed after explicit T=130 request; this is vendor feedback material, not project robot ACK or HIL proof"
    },
    "safe_to_control": false,
    "sends_commands": true,
    "sends_motion_commands": false,
    "robot_control_executed": false,
    "delivery_success": false,
    "hil_pass": false
  }
}
```

## 主动发现的风险

- Fresh `POST /api/base/feedback-request` 已观察到 `T=1001`，但紧随其后的 `GET /api/base/status` 仍显示 `feedback_ack.t1001_observed=false`，且 status 中的 `feedback_samples_latest.freshness.status=stale`。
- 当前原因判断：一次性 feedback request 返回的是 fresh endpoint response，但 `/api/base/status` 的摘要仍消费 latest samples artifact；如果不在 PC/operator 层标清来源，用户可能看到“刚采到 T=1001，但状态仍 not_observed”的口径冲突。
- 风险边界：这不推翻本轮 fresh feedback material；它只说明 status readback 不能替代本次 endpoint response，也不能作为 HIL pass。
- 下一步动作：由 Robot Software Engineer / User Touchpoint Full-Stack Engineer 决定是否让 `/api/base/status` 明确展示 latest one-shot feedback request，或在 PC UI 中区分 `fresh_feedback_request` 与 `stale_feedback_samples_latest`。

## 未验证项和下一步履约动作

- 未验证现场看护、物理净空、人工急停和 CEO/现场授权；因此没有执行任何 forward/back/left/right/stop pulse。
- 未验证 `/dev/ttyS5` 物理追线；身份 probe 只证明路径存在，不能证明一定接到 WAVE ROVER ESP32。
- 未验证 `T=1`、`T=13`、`T=131` 或 `/cmd_vel`；这些均保持禁止。
- 未验证 robot ACK、HIL pass、急停演练、真实 `/odom`、`/imu/data`、`/battery`、SLAM/Nav2 消费或 delivery success。
- 下一步如要进入短 pulse，必须先补 operator preflight：现场看护、物理净空、人工急停、统一 evidence ref、先 stop、低速短时、post-status、operator report、视频/现场记录。
- 本轮未提出新 KR；只记录 O1/O7 风险和下一步 owner handoff。

## 验证命令状态

- SSH 非运动 serial/device/status 检查：已完成。
- HIL safety preflight dry-run：已完成。
- 非运动 `T=130 -> T=1001`：已通过 8787 feedback endpoint fresh 观察到。
- 脚本改动：无，因此未运行脚本级 unittest/compileall。
- `git diff --check -- docs/hardware onboard/scripts sprints/2026.06.04_20-21_runtime-material-followup`：通过，无输出。
- 当前 `git status --short -- docs/hardware onboard/scripts sprints/2026.06.04_20-21_runtime-material-followup OKR.md` 仍显示并行 worker 的 `onboard/scripts/o1_lidar_scan_proof_collector.py` 与 `onboard/scripts/test_o1_lidar_scan_proof_collector.py` 修改；本轮未触碰、未回滚。
