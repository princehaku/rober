# Robot Bringup Checklist

## Hardware Fact Check

- Read `docs/vendor/VENDOR_INDEX.md`.
- Confirm WAVE ROVER UART JSON references before changing driver behavior.
- Confirm Orange Pi serial device on the actual robot.
- Confirm `115200` baud with the loaded ESP32 firmware.
- Confirm evidence source policy: `source=software_proof` for template checks, `source=hil_pass` for real UART verification.
- Run `python3 scripts/hardware_smoke_wave_rover.py --status` first; require no pyserial for this step.
- If `pyserial` is missing or `serial` open fails, record `Blocked` and capture repro steps; do not claim `hil_pass`.

## Evidence Source Boundaries

- `source=software_proof`：只用于离线核验（help/status/参数模板）。
- `source=hil_pass`：必须基于真实 UART 串口交互、反馈采样、运行日志与任务记录。
- 运行脚本时使用 `--evidence-ref run_<YYYYMMDDTHHMMSS>Z_<serial>_hil_pass_speed<...>_dur<...>`，并在 evidence 文档中复用同一 `evidence_ref`。

## Desktop ROS2 Build Check

- Keep the existing WSL `Ubuntu-24.04` untouched for ROS2 Humble.
- Build and verify Humble through Docker:

```bash
# 说明：本仓库的 smoke 脚本在 WSL 下使用 bash + python3
bash scripts/docker_humble_build.sh
```

- Confirm all six ROS2 packages build: interfaces, nav, vision, hardware, behavior, bringup.

## Serial And Base Safety

- Open the configured serial device.
- Record the exact `serial_port`, `serial_baudrate`, `command_mode`, `track_width_m`, `max_wheel_speed_mps`, `feedback_interval_ms`, and `odom_publish_hz` used for the run.
- Capture bridge startup logs showing vendor newline-delimited JSON protocol, selected command mode, and `/odom` source.
- 标注 `source=hil_pass` 在真实硬件采集时，`source=software_proof` 仅用于模板/离线验证。
- Send stop command and verify wheels do not move.
- Confirm startup configuration frames were sent: `T=143` echo off, `T=142` feedback interval, `T=131` feedback flow on.
- Send low-speed `T=1` forward command and verify direction.
- Send low-speed `T=1` reverse command and verify direction.
- Send low-speed turn command and verify left/right mapping.
- Return to stop command after every movement check.
- 如任一步骤缺少反馈、方向不符或出现 timeout，停止推进并在 `wave_rover_hil_evidence.md` 标注 blocked 原因与复现条件。
- If using `scripts/hardware_smoke_wave_rover.py`, run `python3 scripts/hardware_smoke_wave_rover.py --status` first (software proof), then save terminal output and the exact command line for `source=hil_pass` runs.

## Feedback

- Enable feedback stream with `T=131`.
- Confirm `T=1001` feedback is received.
- Confirm battery voltage is plausible.
- Confirm IMU yaw units before relying on orientation.
- Record whether `/odom` is command-integrated or measured.
- Capture one sample `T=1001` JSON line with `L`, `R`, `r`, `p`, `y`, and `v` and mark field completeness as evidence.
- 采样至少两帧并记录平均间隔（`feedback_interval_ms` 验证），标注为 `source=hil_pass`。
- Capture one `ros2 topic echo /battery --once` sample and verify it only claims voltage-level data.
- Capture one `ros2 topic echo /imu/data --once` sample and verify the current contract is yaw-only orientation.
- Capture one `ros2 topic echo /odom --once` sample and label it command-integrated unless encoder validation has been completed.
- 若 `T=1001` 字段缺失或 `feedback_interval_ms` 偏离大幅，记录阻塞原因并在下一轮修复前停止推进。

## Navigation

- Confirm saved map path exists.
- Confirm localization starts.
- Run fixed-route dry-run.
- Verify debug status JSON updates.
- Verify emergency stop path before autonomous movement.

## Mission

- Start `task_orchestrator` with `delivery_dry_run:=true`.
- Send a collection goal with a configured delivery target.
- Confirm task record JSON is written.
- Start `task_orchestrator` or `autonomous.launch.py` with `delivery_mode:=waypoint` only after dry-run passes.
- Confirm `delivery_target` resolves to a waypoint in the configured waypoint YAML.
- Confirm optional `return_target` resolves to a safe waiting/home waypoint before enabling return navigation.
- Run one low-speed physical delivery only after dry-run passes.

## Post-Run Evidence

- Fill `docs/acceptance/wave_rover_hil_evidence.md` for the first real WAVE ROVER run.
- Save task record JSON.
- Save route debug status.
- Save relevant ROS logs.
- Save hardware smoke output, including serial device, feedback frame, and final stop confirmation.
- Save any photos/video used to prove wheel direction, stop behavior, or turn direction.
- Save camera samples when visual debug is enabled.
