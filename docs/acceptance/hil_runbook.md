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

### 0.0.1) Docker-only Host Boundary

- Docker/Humble preflight 的目标是证明 ROS2 Humble 容器入口可用：
  `SKIP_COLCON=1 bash scripts/docker_humble_build.sh`。
- 本机只有 Docker、没有真实 WAVE ROVER、Orange Pi 串口或 `/dev/ttyUSB*`
  时，只能产出 readiness/blocked evidence。
- Docker 镜像构建成功不等于 `hil_pass`；`hil_pass` 必须来自真实 UART
  设备打开、WAVE ROVER `T=1001` 反馈和同一 `evidence_ref` 的证据包归档。
- 如果 Docker 构建失败，先看 `scripts/docker_humble_build.sh` 输出的
  `Docker build failure classification`，按类别处理：
  - `Docker daemon`：启动 Docker Desktop/Engine，确认当前 context。
  - `Docker builder`：检查 `docker buildx ls`，切换或重建 builder。
  - `base image`：单独验证 `docker pull osrf/ros:humble-desktop`。
  - `registry mirror/proxy`：关闭或更换 registry mirror/proxy，避免 HTML
    响应被当作镜像 metadata/layer。
  - `proxy`：修复主机 DNS、代理认证或证书链。
  - `cache`：确认无其他构建依赖后清理 Docker builder cache。

### 0.1) 环境阻塞前置

- 如 `pyserial` 缺失：先执行 `python3 -c "import importlib.util; print(bool(importlib.util.find_spec('serial')))"` 验证，若失败执行：
  - `python3 -m pip install pyserial`
  - 或进入项目镜像：`bash scripts/docker_humble_build.sh` / `bash scripts/docker_humble_dev.sh`
- 依赖缺失只允许跑 `--help` 与 `--status`，禁止误报 `hil_pass` 成功。
- `--status` 现在会只读扫描 `/dev/ttyUSB*`、`/dev/ttyAMA*`、`/dev/serial*`，
  输出 `serial_candidates`、`pyserial_available`、`hil_ready` 与 `blocked_reason`。
  该输出仍是 `source=software_proof`，只能说明当前主机是否具备发起 HIL 的前置条件；
  不能替代真实 WAVE ROVER 串口打开、`T=1001` 反馈和证据包归档。
- 在 Docker-only host 上，`blocked_reason=no_serial_candidates_found` 是预期阻塞；
  记录为 preflight readiness 结果，不创建 `source=hil_pass` 条目。
- 真实上车前，通过 Docker 传入串口设备：
  `EXTRA_DOCKER_ARGS="--device=<real_serial_device>" bash scripts/docker_humble_dev.sh`。

## 0.5) Evidence Packet（单次 run）

- 命名建议：`run_<YYYYMMDDTHHMMSS>Z_<serial>_hil_pass_speed<...>_dur<...>`
- 每次 `hil_pass` 运行应产出证据目录并包含：
  - `command.txt`（完整命令与参数）
  - `serial.log`（脚本原始输出）
  - `feedback_T1001.log`（至少两条）
  - `odom_once.jsonl`、`imu_once.jsonl`、`battery_once.jsonl`
  - 回填 `evidence_ref`（回链到 task record / diagnostics）
- `--status` 输出中的 `required_evidence_files` 是证据包清单模板，`source=software_proof`；
  只有同一个 `evidence_ref` 下实际写入文件并采到硬件反馈后，才可登记为 `source=hil_pass`。

### 0.5.1) Evidence Packet Gate

在归档或升级 O1 证据前，必须运行文件层 gate：

```bash
python3 scripts/hil_evidence_packet_gate.py --packet-dir evidence/<evidence_ref>
```

Gate 不打开串口、不依赖 ROS2、不导入 pyserial，可在 Docker-only 环境运行。它只检查归档文件是否满足真实 HIL 证据最低门槛：

- 必需文件非空：`command.txt`、`serial.log`、`feedback_T1001.log`、`odom_once.jsonl`、`imu_once.jsonl`、`battery_once.jsonl`。
- `feedback_T1001.log` 至少有一条可解析 JSON 且 `T=1001`。
- 三个 topic JSONL 文件各至少有一条可解析 JSON object。
- `serial.log` 不能只是串口打开失败、无串口候选、`No such file`、`pyserial` 缺失或 blocked 记录。
- `command.txt` 必须能追踪到 `hardware_smoke_wave_rover.py` smoke 或 move-test 命令。
- 同一 packet 内 `evidence_ref` 不得互相矛盾；`source=software_proof`、`simulated`、`legacy`、`run_template` 或 dry-run 来源不得通过 `hil_pass`。

Gate 输出 JSON 字段包含 `status`、`source`、`evidence_ref`、`blocked_reason`、`failures`、`checks`、`vendor_sources`。默认只有 `status=hil_pass` 返回 exit 0。模板或 status-only packet 如需记录为软件证据，必须显式加 `--allow-software-proof`；该模式仍返回非 0，不能作为真实 HIL 通过。

本 gate 的 vendor 来源为 `docs/vendor/VENDOR_INDEX.md`、`docs/vendor/waveshare_wave_rover/ugv_rpi/base_ctrl.py`、`docs/vendor/waveshare_wave_rover/ugv_rpi/config.yaml`、`docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/json_cmd.h`、`docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/uart_ctrl.h`。

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
