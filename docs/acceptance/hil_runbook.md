# WAVE ROVER HIL Runbook (04-05)

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

可选添加方向与 `T=13` 验证：

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
