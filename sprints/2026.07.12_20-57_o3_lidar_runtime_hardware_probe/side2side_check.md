# Side2Side Check - O3 LiDAR Runtime Hardware Probe

## Sprint Metadata

- sprint_type: epic
- Sprint: `sprints/2026.07.12_20-57_o3_lidar_runtime_hardware_probe/`
- Product owner: `product-okr-owner`
- Implementation owner: `robot-hardware-engineer`
- Product acceptance: accepted as O3/O1 strict no-motion LiDAR runtime hardware probe / baud status drift narrowing only.
- Proof boundary: `software_proof_o3_o1_strict_no_motion_lidar_runtime_hardware_probe_only`
- OKR handling: O5 remains about `85%`; O1/O6/O7 remain about `93%`; `不调整` percentage; `不归档` KR.

## 用户价值和产品北极星

产品北极星仍是普通手机用户把垃圾交给小车后，一键发车并获得可验证的送达或失败结果。本轮不交付手机发车、路线执行或送达；它交付的是 fixed-route delivery 前的 LiDAR runtime 事实收敛。

用户价值在于把“`/scan` 读不到样本”的黑盒问题拆成更明确的运行态事实：现有 `150000` lifecycle 已可读 `/scan`、`/lidar/raw_packet` 和 TF；`230400` 仍不是干净替换证据；新的窄 blocker 是 radar status / lifecycle config drift。

## Side-by-side Acceptance Check

| Gate | Expected | Actual evidence | Product judgment |
| --- | --- | --- | --- |
| Vendor/read gate | Hardware conclusion must cite local vendor sources. | `tech-done.md` lists `docs/vendor/VENDOR_INDEX.md`, Orange Pi manual/schematic, WAVE ROVER docs, `ugv_rpi/base_ctrl.py`, `config.yaml`, firmware UART headers, and `docs/hardware/board_sensor_stack_smoke.md`. | Accepted for hardware-fact discipline. |
| Strict no-motion | No `/cmd_vel`, no `/api/base/manual`, no NavigateToPose, no WAVE ROVER UART, no `/dev/ttyS5`. | `tech-done.md` records no motion/control paths executed; artifact summaries keep `safe_to_control=false`, `route_execution_success=false`, `delivery_success=false`, `hil_pass=false`. | Accepted. |
| Existing lifecycle readback | Determine whether a current LiDAR lifecycle can publish useful samples. | `existing_lifecycle_readonly_collector_final.json` has `proof.status=scan_once_hz_raw_packet_tf_observed`; `/scan` once and hz observed; `/lidar/raw_packet` observed; TF observed; holder PID `550922` owns `/dev/ttyACM0`. | Accepted as current no-motion LiDAR runtime evidence. |
| Baud comparison | Compare `150000` vs `230400` without guessing. | Existing lifecycle commands use `--serial-baudrate 150000`; `/api/radar/status` top-level still reports `baudrate=230400`; first `230400` smoke produced samples but was contaminated by holder overlap and `serial.serialutil.SerialException`; clean retry fail-closed on holder `550922`. | Accepted as baud/status drift narrowing, not as clean `230400` proof. |
| Mission-grade proof | Only accept route/path/delivery/HIL when evidence exists. | No same-run path generation, route execution, delivery/operator acceptance, current live HIL, safe-to-control, or production external evidence. | Rejected for mission progress. |

## Accepted Facts

- Existing `150000` lifecycle collector is accepted with `scan_once_hz_raw_packet_tf_observed`.
- `/scan` once/hz, `/lidar/raw_packet`, and TF were observed in the read-only collector window.
- Holder PID `550922` owns `/dev/ttyACM0`; clean retry correctly refused to start a second driver.
- `smoke_230400/summary.json` is contaminated by preexisting/new holder overlap plus `serial.serialutil.SerialException`.
- `smoke_230400_clean_final/summary.json` fail-closes on preexisting holder PID `550922`, with `driver_started_by_smoke=false`.
- New narrow blocker: radar status / lifecycle config drift where actual commands use `150000` but `/api/radar/status` top-level still reports `baudrate=230400`.

## Rejected Claims

- Not mission progress.
- Not same-run path generation.
- Not route execution.
- Not delivery/operator acceptance.
- Not current live HIL.
- Not safe-to-control.
- Not production external evidence.
- Not a clean exclusive `230400` LiDAR runtime proof.
- Not a reason to archive any KR.

## OKR Mapping And Direction Judgment

- O5 remains the lowest numeric Objective at about `85%`, but this sprint correctly avoided another O5 support-only wrapper because no real external production evidence was available.
- O1/O3 direction continues, but only as strict no-motion runtime readiness. The evidence is useful because `/scan` is now available through the existing lifecycle, yet `/amcl_pose`, dynamic `map->odom`, planner-only path, route execution, and delivery are still unproven.
- O6/O7 remain about `93%`; no new route execution, delivery record, operator acceptance, production cloud readback, or consumer-grade external proof was produced.
- Direction decision: continue O3/O1; next sprint should be Robot Software first, then Algorithm only after status/readback is corrected; Hardware rejoins only if exclusive-holder USB/power/baud checks are required.

## KR Decision And History Position

- Current KR percentages: O5 about `85%`; O1/O6/O7 about `93%`.
- KR archive decision: `不归档`.
- Historical KR records remain in `OKR.md` archived Objective/KR section and `docs/process/okr_progress_log.md`.
- This sprint adds supporting O3/O1 evidence only; it does not complete or retire a KR.

## Next Owner And Acceptance

Priority 1: `robot-software-engineer` should correct `/api/radar/status` baudrate readback so top-level status reflects current lifecycle/status command or diagnostics instead of stale default `230400`.

Priority 2: `robot-algorithm-engineer` should reuse the existing `150000` lifecycle without starting a second driver and retry `/scan` -> `/amcl_pose` -> dynamic `map->odom` -> planner-only path proof.

Priority 3: `rober-hardware-engineer` rejoins only if the next evidence requires stopping the current holder under Product/Hardware ownership and checking exclusive USB/power/baud stability.

Acceptance for the next sprint requires preserving `safe_to_control=false`, `hil_pass=false`, no `/cmd_vel`, no `/api/base/manual`, no NavigateToPose, and no WAVE ROVER UART unless a separate CEO-approved motion/HIL sprint exists.
