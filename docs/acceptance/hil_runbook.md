# WAVE ROVER HIL Runbook (06-07)

## Scope

- 使用 `source=software_proof` 先完成脚本与参数模板核验。
- 使用 `source=hil_pass` 完成第一轮真实硬件准入。

## 0) Preflight (software proof)

1. 固定脚本文档版本：  
   `python3 scripts/hardware_smoke_wave_rover.py --help`
2. 固定模板状态：  
   `python3 scripts/hardware_smoke_wave_rover.py --status`
3. 记录下列文件路径（本轮更新）：
  - `docs/hardware/wave_rover_json_bridge.md`
  - `docs/acceptance/wave_rover_hil_evidence.md`
  - `docs/acceptance/robot_bringup_checklist.md`

### 0.1) 环境阻塞前置

- 如 `pyserial` 缺失：先执行 `python3 -c "import importlib.util; print(bool(importlib.util.find_spec('serial')))"` 验证，若失败执行：
  - `python3 -m pip install pyserial`
  - 或进入项目镜像：`bash scripts/docker_humble_build.sh` / `bash scripts/docker_humble_dev.sh`
- 依赖缺失只允许跑 `--help` 与 `--status`，禁止误报 `hil_pass` 成功。

## 0.5) Evidence Packet（单次 run）

- 命名建议：`run_<YYYYMMDDTHHMMSS>Z_<serial>_hil_pass_speed<...>_dur<...>`
- 每次 `hil_pass` 运行应产出证据目录并包含：
  - `command.txt`（完整命令与参数）
  - `serial.log`（脚本原始输出）
  - `feedback_T1001.log`（至少两条）
  - `odom_once.jsonl`、`imu_once.jsonl`、`battery_once.jsonl`
  - 回填 `evidence_ref`（回链到 task record / diagnostics）

## 0.6) Blocked Run Record

- evidence ref: `run_20260511T093000Z_ttyUSB0_hil_pass_speed0p050_dur0p30`
- command: `python3 scripts/hardware_smoke_wave_rover.py --move-test --test-speed 0.05 --test-duration-s 0.3 --serial-port /dev/ttyUSB0 --baudrate 115200 --evidence-ref run_20260511T093000Z_ttyUSB0_hil_pass_speed0p050_dur0p30`
- source: `software_proof` 已完成；`hil_pass` 因串口路径缺失阻塞
- 阻塞归因: `/dev/ttyUSB0` 不存在（host 无可见串口）
- 产物:
  - `evidence/run_20260511T093000Z_ttyUSB0_hil_pass_speed0p050_dur0p30/command.txt`
  - `evidence/run_20260511T093000Z_ttyUSB0_hil_pass_speed0p050_dur0p30/serial.log`
  - `evidence/run_20260511T093000Z_ttyUSB0_hil_pass_speed0p050_dur0p30/feedback_T1001.log`
  - `evidence/run_20260511T093000Z_ttyUSB0_hil_pass_speed0p050_dur0p30/odom_once.jsonl`
  - `evidence/run_20260511T093000Z_ttyUSB0_hil_pass_speed0p050_dur0p30/imu_once.jsonl`
  - `evidence/run_20260511T093000Z_ttyUSB0_hil_pass_speed0p050_dur0p30/battery_once.jsonl`

## 0.6.1) Latest Blocked Run Record

- evidence ref: `run_20260511T063559Z_-dev-ttyUSB0_hil_pass_speed0p050_dur0p30`
- command: `python3 scripts/hardware_smoke_wave_rover.py --move-test --test-speed 0.05 --test-duration-s 0.3 --serial-port /dev/ttyUSB0 --baudrate 115200`
- source: `software_proof` 已完成（`--help`、`--status`、`py_compile`）；`hil_pass` 阶段阻塞
- return code:
  - `--help`: `0`
  - `--status`: `0`
  - `py_compile`: `0`
  - `--move-test`: `1`
- 阻塞归因: `ERROR: serial failure: [Errno 2] could not open port /dev/ttyUSB0`
- 产物状态:
  - `evidence/run_20260511T063559Z_-dev-ttyUSB0_hil_pass_speed0p050_dur0p30/command.txt` (missing)
  - `evidence/run_20260511T063559Z_-dev-ttyUSB0_hil_pass_speed0p050_dur0p30/serial.log` (missing)
  - `evidence/run_20260511T063559Z_-dev-ttyUSB0_hil_pass_speed0p050_dur0p30/feedback_T1001.log` (missing)
  - `evidence/run_20260511T063559Z_-dev-ttyUSB0_hil_pass_speed0p050_dur0p30/odom_once.jsonl` (missing)
  - `evidence/run_20260511T063559Z_-dev-ttyUSB0_hil_pass_speed0p050_dur0p30/imu_once.jsonl` (missing)
  - `evidence/run_20260511T063559Z_-dev-ttyUSB0_hil_pass_speed0p050_dur0p30/battery_once.jsonl` (missing)

- evidence ref: `run_20260511T094018Z_hil_pass_speed0p050_dur0p30`（当前轮次）
- command: `python3 scripts/hardware_smoke_wave_rover.py --move-test --test-speed 0.05 --test-duration-s 0.3 --serial-port /dev/ttyUSB0 --baudrate 115200 --evidence-ref run_20260511T094018Z_hil_pass_speed0p050_dur0p30`
- source: `software_proof` 已完成；`hil_pass` 因串口路径缺失阻塞
- 阻塞归因: `/dev/ttyUSB0` 不存在（host 无真实 `/dev/ttyUSB*`）
- return:
  - `--help`: `0`
  - `--status`: `0`
  - `py_compile`: `0`
  - `--move-test`: `1`
- 产物状态:
  - `evidence/run_20260511T094018Z_hil_pass_speed0p050_dur0p30/command.txt`（已生成）
  - `evidence/run_20260511T094018Z_hil_pass_speed0p050_dur0p30/serial.log`（已生成）
  - `evidence/run_20260511T094018Z_hil_pass_speed0p050_dur0p30/feedback_T1001.log`（已生成）
  - `evidence/run_20260511T094018Z_hil_pass_speed0p050_dur0p30/odom_once.jsonl`（已生成）
  - `evidence/run_20260511T094018Z_hil_pass_speed0p050_dur0p30/imu_once.jsonl`（已生成）
  - `evidence/run_20260511T094018Z_hil_pass_speed0p050_dur0p30/battery_once.jsonl`（已生成）

## 1) Parameter Lock

确认以下参数并记录到 evidence `Run Metadata`（默认值仅作起点）：

- `serial_port`（务必现场确认）
- `baudrate`（默认 115200）
- `feedback_interval_ms`（默认 100）
- `test_speed`（默认 0.05）
- `test_duration_s`（默认 0.3）
- `track_width_m`、`max_wheel_speed_mps`、`command_mode`

## 2) HIL Smoke (must be `source=hil_pass`)

### 2.1 Hardware smoke command

```bash
python3 scripts/hardware_smoke_wave_rover.py \
  --serial-port /dev/ttyUSB0 \
  --baudrate 115200 \
  --feedback-interval-ms 100 \
  --move-test --test-speed 0.05 --test-duration-s 0.3
```

可选方向复验（同一 run）：`--reverse-test --ros-mode-test --turn-test`。

```bash
python3 scripts/hardware_smoke_wave_rover.py \
  --serial-port /dev/ttyUSB0 \
  --baudrate 115200 \
  --feedback-interval-ms 100 \
  --move-test --reverse-test --ros-mode-test --turn-test \
  --test-speed 0.05 --test-duration-s 0.3
```

### 2.2 通过条件

- 终端能打开串口并打印 `Opened ... @ ...`
- 先后观察到 `T=143`、`T=142`、`T=131` 下发
- `T=1001` 至少一条且包含 `L,R,r,p,y,v`（建议两条以上，用于计算间隔）
- 能看到平均反馈间隔接近 `feedback_interval_ms`
- 每次运动前后都发送 `T=1,L=0,R=0`
- 方向验证：前进/后退/转向的运动轨迹与期望一致

## 3) Topic Evidence Snapshot

- `ros2 topic echo /odom --once`（标注来源：`command_integration` 或 `encoder_validated`）
- `ros2 topic echo /imu/data --once`
- `ros2 topic echo /battery --once`

在 evidence 文件中把对应条目标注为 `source=hil_pass`。

## 4) HIL Record

在 `docs/acceptance/wave_rover_hil_evidence.md` 填写：

- `source=software_proof` 条目：脚本 help/status 与 checklist 版本
- `source=hil_pass` 条目：真实硬件终端日志、视频/照片、主题快照
