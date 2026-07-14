# Tech Done - O3 LiDAR Runtime Hardware Probe

## Sprint Metadata

- sprint_type: epic
- Sprint: `sprints/2026.07.12_20-57_o3_lidar_runtime_hardware_probe/`
- Owner: `robot-hardware-engineer`
- Scope: O3/O1 strict no-motion LiDAR serial/runtime/wiring probe only.
- Proof boundary: `software_proof_o3_o1_strict_no_motion_lidar_runtime_hardware_probe_only`
- OKR handling: 本轮是 blocker narrowing / LiDAR runtime evidence，不声明 mission progress，不调整 O5/O1/O6/O7 百分比，不归档 KR。

## 已读 Vendor 来源

- `AGENTS.md`
- `OKR.md`
- `docs/vendor/VENDOR_INDEX.md`
- `docs/vendor/orangepizero3/OrangePi_Zero3_H618_用户手册_v1.6.pdf`
- `docs/vendor/orangepizero3/OrangePi-ZERO3_电路图.pdf`
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER.wiki.html`
- `docs/vendor/waveshare_wave_rover/ugv_rpi/base_ctrl.py`
- `docs/vendor/waveshare_wave_rover/ugv_rpi/config.yaml`
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/json_cmd.h`
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/uart_ctrl.h`
- `docs/hardware/board_sensor_stack_smoke.md`

Vendor gate 结论：

- 本地 WAVE ROVER 上位机参考 `ugv_rpi/base_ctrl.py` 使用 `/dev/ttyACM* @ 230400`，并按 STC `0x54`、47 字节 packet、12 个采样点解析 LiDAR。
- 历史项目现场 runbook 仍保留 `/dev/ttyACM0 @ 150000` 候选；该值来自实板 artifact，不是 WAVE ROVER vendor baudrate 结论。
- `docs/vendor/` 当前没有 `docs/vendor/lidar_pkg_ros2-main/` 专用 LiDAR vendor 包；因此本轮不能把 230400 或 150000 写成专用 LiDAR 厂商已确认，只能按 vendor reference + live readback 收口。
- Orange Pi 手册要求 Type-C 高质量 `5V/2A` 或 `5V/3A` 供电，且不要输入大于 `5V`；供电/线缆仍是 USB LiDAR 稳定性的现场风险。

## 实际改动

- `onboard/src/ros2_trashbot_hardware/ros2_trashbot_hardware/lidar_driver.py`
  - 新增 `read_exception_count`、`last_exception_type`、`last_exception_message_hint`、`raw_bytes_observed`、`last_chunk_preview_hex`、`unparsed_buffer_*` 等诊断字段。
  - timer 内捕获串口 read exception，写 `serial_read_exception` diagnostics，不再只让异常停留在 stderr。
  - diagnostics 增加 vendor/reference 边界和 strict no-motion false 字段。
- `onboard/scripts/o1_lidar_ros2_scan_smoke.sh`
  - 增加 before/during/after LiDAR device snapshot，记录 `/dev/ttyACM0`、STC by-id/by-path 和 holder。
  - 增加 preexisting-holder fail-closed；发现已有 holder 时不再启动第二个 driver。
  - driver/static TF 改为独立进程组并按进程组 cleanup，避免只杀 timeout wrapper 后遗留 `lidar_driver`。
  - summary 合并 driver diagnostics、serial exception、raw byte、packet count、baudrate probe 和 no-motion false 字段。
- `onboard/scripts/o1_lidar_lifecycle.sh`
  - status JSON 增加 vendor/reference 边界与 `safe_to_control=false`、`uses_base_uart=false`、`route_execution_success=false` 等字段。
- `onboard/scripts/o1_lidar_scan_proof_collector.py`
  - artifact 增加 vendor source status、专用 LiDAR vendor 包缺失状态、baudrate candidates 和 LiDAR holder probe。
  - collector 只读 `/scan`、`/lidar/raw_packet`、TF 和 LiDAR device holder；不启动 driver、不打开 `/dev/ttyS5`。
- Tests:
  - `onboard/src/ros2_trashbot_hardware/test/test_lidar_driver_stubs.py`
  - `onboard/tests/test_lidar_scan_proof_collector.py`
- Docs:
  - `docs/hardware/board_sensor_stack_smoke.md`
  - `docs/navigation/field_route_evidence_preflight.md`
  - `docs/navigation/fixed_route_workflow.md`
- Artifacts:
  - `sprints/2026.07.12_20-57_o3_lidar_runtime_hardware_probe/artifacts/live_o1_lidar_artifacts/`

## True-board Readback

Artifact anchors:

- `artifacts/live_o1_lidar_artifacts/smoke_230400/summary.json`
- `artifacts/live_o1_lidar_artifacts/smoke_230400_clean_final/summary.json`
- `artifacts/live_o1_lidar_artifacts/existing_lifecycle_readonly_collector_final.json`

### 230400 Probe

`smoke_230400/summary.json`:

- `serial_baudrate=230400`
- `/scan` sample observed: `scan_once_observed=true`
- `/scan` hz observed: `scan_hz_observed=true`
- `/lidar/raw_packet` observed: `raw_packet_once_observed=true`
- TF observed: `tf_observed=true`
- raw bytes observed: `raw_bytes_observed=true`
- `bytes_read_total=86530`
- `packet_count_total=2611`
- `published_raw_packet_count=2611`
- `published_scan_count=166`
- `serial_exception_observed=true`
- `serial_exception_type=serial.serialutil.SerialException`
- `serial_exception_message_hint=device reports readiness to read but returned no data (device disconnected or multiple access on port?)`
- `empty_read_count=837`

Important boundary: this first 230400 smoke was not a clean config-switch proof because the old script allowed a preexisting holder. Device snapshots show:

- before holder: PID `544420`
- during holder: PID `549589`
- after holder: PID `549725`

This explains why `serial.serialutil.SerialException` persisted despite `/scan` and `/lidar/raw_packet` samples: the window was contaminated by existing/new LiDAR holders and cleanup leakage. The script was then fixed to fail closed on preexisting holder and clean process groups.

### Clean-window Guard

`smoke_230400_clean_final/summary.json` after the guard fix:

- `preexisting_lidar_holder_detected=true`
- `preexisting_lidar_holder_pids=["550922"]`
- `scan_once_observed=false`
- `raw_packet_once_observed=false`
- `driver_started_by_smoke=false` in the final script version
- Safety fields remain false.

The clean retry correctly refused to start a second `lidar_driver` because current live runtime already held `/dev/ttyACM0`.

### Existing 150000 Lifecycle Read-only Collector

`existing_lifecycle_readonly_collector_final.json`:

- `proof.status=scan_once_hz_raw_packet_tf_observed`
- `/scan` once observed: `true`
- `/scan` hz observed: `true`
- `scan_hz_average_rate_hz=14.761`
- `/lidar/raw_packet` observed: `true`
- TF observed: `true`
- holder paths: `/dev/ttyACM0`, `/dev/serial/by-id/usb-STC_STC_USB_Serial-if00`
- holder PID: `550922`
- `driver_diagnostics_latest.diagnosis_status=scan_published`
- `driver_diagnostics_latest.runtime.parsed_packet_count=58748`
- `driver_diagnostics_latest.runtime.published_raw_packet_count=58748`
- `driver_diagnostics_latest.runtime.published_scan_count=3053`
- `driver_diagnostics_latest.artifact.bytes_read=35640`
- required vendor sources exist on target readback; dedicated LiDAR vendor docs are still absent.

Config drift narrowed:

- `upper_api.radar_status.payload.controls.start.command.argv` uses `--serial-baudrate 150000`.
- `upper_api.radar_status.payload.controls.scan_proof_refresh.runtime_command.argv` uses `--serial-baudrate 150000`.
- `upper_api.radar_status.payload.baudrate` still reports `230400`.

Therefore the next narrow fix is not generic `/scan_reliable_and_best_effort_timeout`; it is radar status / lifecycle config drift: current clean runtime is `/dev/ttyACM0 @ 150000` and publishes `/scan`, but status still exposes a `230400` top-level baudrate while command config uses `150000`.

## 验证结果

Python compile:

```text
python3 -m py_compile .../lidar_driver.py .../lidar_packets.py onboard/scripts/o1_lidar_scan_proof_collector.py
exit 0
```

Unit tests:

```text
python3 -m unittest \
  onboard.src.ros2_trashbot_hardware.test.test_lidar_driver_stubs \
  onboard.src.ros2_trashbot_hardware.test.test_lidar_packets \
  onboard.tests.test_lidar_scan_proof_collector

Ran 28 tests in 0.001s
OK
```

Extra lifecycle script regression:

```text
python3 -m unittest onboard.tests.test_lidar_lifecycle_script

Ran 3 tests in 0.063s
OK
```

Shell syntax:

```text
bash -n onboard/scripts/o1_lidar_lifecycle.sh
exit 0

bash -n onboard/scripts/o1_lidar_ros2_scan_smoke.sh
exit 0
```

True-board commands:

```text
ssh root@192.168.1.11 -p 37878 mkdir ...
exit 0

scp scripts and LiDAR driver/parser to root@192.168.1.11
exit 0

230400 first smoke
exit 0, but contaminated by preexisting/new holders and SerialException.

230400 clean retry after guard fix
exit 45, fail-closed on preexisting holder PID 550922.

read-only collector on existing lifecycle
exit 0, proof.status=scan_once_hz_raw_packet_tf_observed.

artifact pull
exit 0
```

## 已证实硬件结论

- `/dev/ttyACM0` exists on the true board; STC by-id symlink resolves to `/dev/ttyACM0`.
- Current live LiDAR runtime holder is `lidar_driver` PID `550922`, owned by `o1_lidar_lifecycle.sh __run`.
- Current live lifecycle commands use `/dev/ttyACM0 @ 150000`, and read-only collector proves `/scan`、`/lidar/raw_packet` and TF are observed in the same no-motion window.
- 230400 is vendor reference from WAVE ROVER upper-computer code, and it can produce packets/samples in the contaminated first smoke, but because there was preexisting holder contamination plus repeated `serial.serialutil.SerialException`, this sprint does not accept 230400 as clean replacement config.
- The remaining narrow candidate is config/readback drift: API/radar top-level `baudrate=230400` conflicts with actual configured start/scan-proof commands using `150000`.

## 未验证项、风险和下一步

- 未验证 mission progress：`safe_to_control=false`、`publishes_cmd_vel=false`、`calls_base_manual=false`、`uses_base_uart=false`、`robot_control_executed=false`、`route_execution_success=false`、`delivery_success=false`、`hil_pass=false`。
- 未执行 `/cmd_vel`、`/api/base/manual`、NavigateToPose、WAVE ROVER UART、`/dev/ttyS5`、route execution 或 base manual relay。
- 未验证 230400 clean exclusive runtime；当前 live holder 会 fail-closed 阻止二次打开。若要继续比较 230400，必须先通过 Product/Hardware 明确暂停现有 150000 lifecycle，并记录 stop/start ownership。
- 下一步建议：
  1. 修正 `/api/radar/status` 顶层 baudrate readback，让它来自 current lifecycle/status command 或 diagnostics，而不是陈旧默认 `230400`。
  2. 在不启动第二个 driver 的前提下，让 O3 direct helper 复用现有 150000 lifecycle，重跑 `/scan` -> `/amcl_pose` -> dynamic `map->odom` -> planner-only path proof。
  3. 若仍有 `serial.serialutil.SerialException`，只在 exclusive holder 窗口复验 USB 供电/线缆/holder，而不要并发打开 `/dev/ttyACM0`。
