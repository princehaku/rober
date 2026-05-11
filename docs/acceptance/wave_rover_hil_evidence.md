# WAVE ROVER Hardware-In-Loop Evidence

Use this file as the evidence checklist for the first real robot run.
Baseline template fields are `source=software_proof`. They can only be upgraded
to `source=hil_pass` after a real hardware run for the same `evidence_ref`.
软件验证结果不能冒充实机证据。

## Run Metadata

- Run ID (run_id): `run_20260511T093000Z_ttyUSB0_hil_pass_speed0p050_dur0p30`
- Date/time (UTC): `2026-05-11T09:30:00Z`（阻塞录制）
- Operator: `Hardware Infra Engineer (local execution context)`
- Robot: `WAVE ROVER`
- Orange Pi OS: `Not available in this host`
- Serial device (现场确认): `/dev/ttyUSB0`（命令行指定）
- Baudrate: `115200`
- Evidence ref (required):
  - `run_20260511T093000Z_ttyUSB0_hil_pass_speed0p050_dur0p30`
- Git branch/commit: `master` / `38cdfb6`
- Launch command: `python3 scripts/hardware_smoke_wave_rover.py --move-test --test-speed 0.05 --test-duration-s 0.3 --serial-port /dev/ttyUSB0 --baudrate 115200 --evidence-ref run_20260511T093000Z_ttyUSB0_hil_pass_speed0p050_dur0p30`
- Smoke command: 同 launch command
- Parameter lock JSON: `{"source":"hil_pass","evidence_ref":"run_20260511T093000Z_ttyUSB0_hil_pass_speed0p050_dur0p30","serial_port":"/dev/ttyUSB0","baudrate":115200,"feedback_interval_ms":100,"feedback_timeout_s":5.0,"test_speed":0.05,"test_duration_s":0.3,"ros_angular_z":0.0,"turn_angular_z":0.3,"run_flags":["move-test"]}`

## Run Blocking Record

- Run status: `Blocked`
- Blocked reason: 串口路径不存在（`FileNotFoundError: /dev/ttyUSB0`）
- Notes:
  - `pyserial` 先通过依赖检查恢复后再重试，阻塞仍在于设备路径/硬件环境
  - 严格 evidence_ref 统一写入 `command.txt`、`serial.log`、`feedback_T1001.log`、`odom_once.jsonl`、`imu_once.jsonl`、`battery_once.jsonl`

## Latest Execution Record (2026-05-11T06:35:59Z)

- Run ID (run_id): `run_20260511T063559Z_-dev-ttyUSB0_hil_pass_speed0p050_dur0p30`
- Required command set:
  - `python3 scripts/hardware_smoke_wave_rover.py --help` -> exit `0`
  - `python3 scripts/hardware_smoke_wave_rover.py --status` -> exit `0`
  - `PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile scripts/hardware_smoke_wave_rover.py` -> exit `0`
  - `python3 scripts/hardware_smoke_wave_rover.py --move-test --test-speed 0.05 --test-duration-s 0.3 --serial-port /dev/ttyUSB0 --baudrate 115200` -> exit `1`
- Blocked reason: `ERROR: serial failure: [Errno 2] could not open port /dev/ttyUSB0`
- Evidence packet check (`evidence/<evidence_ref>/...`):
  - `command.txt`: missing
  - `serial.log`: missing
  - `feedback_T1001.log`: missing
  - `odom_once.jsonl`: missing
  - `imu_once.jsonl`: missing
  - `battery_once.jsonl`: missing
- Source boundary:
  - `source=software_proof`: confirmed for `--help/--status/py_compile`
  - `source=hil_pass`: blocked, cannot claim pass

## Vendor Sources Used

- `docs/vendor/VENDOR_INDEX.md`
- `docs/vendor/waveshare_wave_rover/ugv_rpi/base_ctrl.py`
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/json_cmd.h`
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/uart_ctrl.h`
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/movtion_module.h`
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/ugv_advance.h`

## Evidence Source

- `source=software_proof`：脚本模板、离线检查、参数约定、风险声明。
- `source=hil_pass`：真实硬件串口、反馈、里程、IMU、电源、急停/方向验收结果。

## Run-level Evidence Rule

- `software_proof`：仅表示模板和闭环前置条件，不得作为 HIL 合格判据。
- `hil_pass`：必须使用同一 `evidence_ref` 绑定一组 run 产物：
  - `evidence/<evidence_ref>/command.txt`
  - `evidence/<evidence_ref>/serial.log`
  - `evidence/<evidence_ref>/feedback_T1001.log`
- 若 HIL 遭遇环境阻塞，`Blocked` 条目需完整记录：
  - 缺依赖（如 pyserial）
  - 缺串口权限/设备
  - 采样不足（如单帧、字段缺失）

## Required Evidence

| Check | Evidence Source | Evidence |
| --- | --- | --- |
| `source=software_proof` baseline captured | `software_proof` | `python3 scripts/hardware_smoke_wave_rover.py --status` 输出及脚本版本 |
| Smoke command template可复用 | `software_proof` | 运行命令行记录：`python3 scripts/hardware_smoke_wave_rover.py --help` |
| 脚本访问前后参数与串口约定确认 | `software_proof` | `docs/acceptance/robot_bringup_checklist.md` 与 `docs/acceptance/hil_runbook.md` |
| 首轮 evidence packet 产物归档 | `hil_pass` | `evidence/<evidence_ref>/command.txt`、`serial.log`、`feedback_T1001.log` |
| 真实设备串口打开（115200 或记录覆盖值） | `hil_pass` | `HIL Smoke` 终端日志中的 `Opened <serial> @ <baud>` |
| 停止命令覆盖运动并前后成立 | `hil_pass` | 运动段前后 `T=1,L=0,R=0` 命令与最终轮停确认 |
| 下发启动命令（`T=143`,`T=142`,`T=131`） | `hil_pass` | 启动日志含三条 startup frame |
| `T=1001` 反馈收到且完整字段存在 | `hil_pass` | 至少一条 `T=1001` 样本含 `L,R,r,p,y,v` |
| `T=1001` 反馈采样频率 | `hil_pass` | 连续>=2帧间隔估算（目标接近 `feedback_interval_ms`） |
| 运行源与参数留存 | `hil_pass` | 同一次 `evidence_ref` 下保存参数快照（`serial_port`、`baudrate`、`feedback_interval_ms`、`test_speed`、`test_duration_s`） |
| 正向低速 `T=1` 方向正确 | `hil_pass` | 行驶轨迹/照片/视频 |
| 反向低速 `T=1` 方向正确 | `hil_pass` | 行驶轨迹/照片/视频 |
| 低速原地转向 `T=1`/`T=13` 方向正确 | `hil_pass` | 行驶轨迹/照片/视频 |
| `T=13` 测试（如启用） | `hil_pass` | `--ros-mode-test`/`--turn-test` 终端与安全评估 |
| `/battery` 电压语义记录 | `hil_pass` | `ros2 topic echo /battery --once` 与 `T=1001.v` 对照 |
| `/imu/data` yaw 语义记录 | `hil_pass` | `/imu/data` 与 `T=1001.y` 采样记录 |
| `/odom` 来源声明（命令积分 vs 实测里程） | `hil_pass` | `/odom` 样本并标注 `source=command_integration` |
| 紧急停机路径演示 | `hil_pass` | 停止按钮/服务触发日志与最终停止确认 |

## Attached Artifacts

- `source=software_proof`：
  - 采样模板：`docs/acceptance/hil_runbook.md`
  - 脚本说明：`docs/hardware/wave_rover_json_bridge.md`
- Hardware smoke terminal output:
- ROS log path:
- Task record JSON:
- Route debug status JSON:
- Photos/video:
