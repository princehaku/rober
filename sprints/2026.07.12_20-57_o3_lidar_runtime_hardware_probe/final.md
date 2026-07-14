# Final - O3 LiDAR Runtime Hardware Probe

## Product Acceptance

Product accepts this sprint as O3/O1 strict no-motion LiDAR runtime hardware probe / baud status drift narrowing only.

Accepted evidence:

- `existing_lifecycle_readonly_collector_final.json` proves `proof.status=scan_once_hz_raw_packet_tf_observed`.
- Existing lifecycle has `/scan` once/hz, `/lidar/raw_packet`, and TF observed.
- Holder PID `550922` owns `/dev/ttyACM0`.
- Actual lifecycle and scan-proof commands use `--serial-baudrate 150000`.
- `/api/radar/status` top-level still reports `baudrate=230400`, creating radar status / lifecycle config drift.
- First `230400` smoke is contaminated by holder overlap and `serial.serialutil.SerialException`; the clean retry fail-closes on holder PID `550922`.

Rejected scope:

- No mission progress.
- No same-run path generation.
- No route execution.
- No delivery/operator acceptance.
- No current live HIL.
- No safe-to-control claim.
- No production external evidence.
- No clean exclusive `230400` runtime proof.

Proof boundary: `software_proof_o3_o1_strict_no_motion_lidar_runtime_hardware_probe_only`.

## 用户价值和产品北极星

北极星仍是普通手机用户一键发车后获得可验证送达或失败结果。本轮价值不是把车开起来，而是把路线执行前的 LiDAR 输入条件拉清楚：当前已有一个可读 `/scan` 的 `150000` lifecycle；下一轮应停止猜 baudrate，先修 radar status readback，再让 O3 helper复用现有 lifecycle 继续定位 `/amcl_pose` 和 dynamic `map->odom`。

## OKR Mapping And Direction

- Direction: continue O3/O1 strict no-motion; pause O5 support-only; freeze independent O6/O7 surface work.
- O5: remains about `85%` because no HTTPS/TLS, 4G/SIM, production DB/queue, worker cutover, OSS/CDN live traffic, phone/browser, or external production evidence was added.
- O1/O6/O7: remain about `93%`.
- Percentage decision: `不调整`.
- KR archive decision: `不归档`.
- 已完成 KR historical records remain in `OKR.md` archived Objective/KR section and `docs/process/okr_progress_log.md`; this sprint archives none.

## Actual Closeout Updates

- Created `sprints/2026.07.12_20-57_o3_lidar_runtime_hardware_probe/side2side_check.md`.
- Created `sprints/2026.07.12_20-57_o3_lidar_runtime_hardware_probe/final.md`.
- Updated `OKR.md` with the 20-57 current snapshot, O3 lane state, and next-owner routing.
- Updated `docs/process/okr_progress_log.md` with this sprint's Product acceptance entry.

Implementation evidence accepted from `tech-done.md` includes LiDAR driver diagnostics, smoke-script holder fail-close, read-only collector artifact, Hardware vendor read gate, unit tests, shell syntax checks, true-board smoke/retry/collector commands, and artifact pull.

## Verification Evidence

Implementation verification from `tech-done.md`:

- `python3 -m py_compile ...` exit `0`.
- LiDAR driver/parser/proof collector unit tests: `Ran 28 tests in 0.001s OK`.
- Lifecycle script regression: `Ran 3 tests in 0.063s OK`.
- `bash -n onboard/scripts/o1_lidar_lifecycle.sh` exit `0`.
- `bash -n onboard/scripts/o1_lidar_ros2_scan_smoke.sh` exit `0`.
- True-board SSH/scp exit `0`.
- `230400` first smoke exit `0`, but contaminated by holders and SerialException.
- `230400` clean retry exit `45`, fail-closed on holder PID `550922`.
- Read-only collector exit `0`, `proof.status=scan_once_hz_raw_packet_tf_observed`.
- Artifact pull exit `0`.

Product closeout validation:

- Targeted `rg` over `side2side_check.md`, `final.md`, `OKR.md`, and `docs/process/okr_progress_log.md` passed and hit `LiDAR runtime hardware probe`, `scan_once_hz_raw_packet_tf_observed`, `baudrate=230400`, `150000`, `radar status`, `safe_to_control=false`, `hil_pass=false`, `不调整`, and `不归档`.
- Scoped `git diff --check` over the four Product closeout files passed.

## Risks And Remaining Evidence Gap

- `/api/radar/status` currently exposes stale/conflicting `baudrate=230400` while commands use `150000`.
- `230400` was not proven in a clean exclusive window.
- Current `/scan` readiness does not prove `/amcl_pose`, dynamic `map->odom`, planner-only path, route execution, delivery, operator acceptance, current live HIL, or production external evidence.
- The existing holder must not be interrupted casually; any exclusive baud/USB/power check needs explicit Product/Hardware ownership.

## Next Sprint Recommendation

1. `robot-software-engineer`: fix `/api/radar/status` baudrate readback so it derives from current lifecycle/status command or diagnostics instead of stale default `230400`.
2. `robot-algorithm-engineer`: reuse the existing `150000` lifecycle and retry `/scan` -> `/amcl_pose` -> dynamic `map->odom` -> planner-only path proof without starting a second driver.
3. `rober-hardware-engineer`: rejoin only if exclusive-holder USB/power/baud investigation is required.

Next acceptance remains strict no-motion: `safe_to_control=false`, `hil_pass=false`, no `/cmd_vel`, no `/api/base/manual`, no NavigateToPose, no WAVE ROVER UART.
