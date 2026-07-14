# Tech Plan - O3 LiDAR Runtime Hardware Probe

## Objective

`robot-hardware-engineer` owns this O3/O1 strict no-motion sprint. Starting blocker:

`/scan_lidar_runtime_exception_after_endpoint_visible_qos_compatible_timeout`

The goal is to turn the LiDAR runtime exception candidate into a vendor-doc-backed executable fix/config/wiring conclusion, or produce a narrower no-motion live artifact. This sprint must not publish `/cmd_vel`, call `/api/base/manual`, send NavigateToPose, or open WAVE ROVER UART.

## OKR 最低优先级核对

- 当前 `OKR.md` 4.1 / 当前推进区完成度最低的 Objective：O5，约 `85%`。
- 本 sprint 是否针对最低 Objective：否。
- 不针对 O5 的理由：O5 当前缺真实 external production evidence。继续做 support-only、readiness packet、handoff、review、status surface、production checklist 或 cutover wrapper 不会产生真实 HTTPS/TLS、4G/SIM、production DB/queue、worker cutover、OSS/CDN live traffic、真实手机/browser 或 `external_artifact_delta`，只会重复 `okr_credit_allowed=false`。
- 本 sprint 选择 O3/O1 strict no-motion LiDAR blocker 的理由：18:56 `/scan_reliable_and_best_effort_timeout` 已在 19:56 被拆到 `/scan_lidar_runtime_exception_after_endpoint_visible_qos_compatible_timeout`，且 next_owner=`hardware_after_vendor_doc_review`。这是恢复 `/scan`、`/amcl_pose`、dynamic `map->odom`、same-run path generation、route execution、delivery/operator evidence 的最近可执行 blocker。
- 收口复核口径：若本轮只产生 hardware diagnosis、readback/helper/docs 或 blocker narrowing，O5/O1/O6/O7 百分比保持 flat；若产生 same-run path generation、route execution、delivery/operator acceptance、current live HIL 或 real production external evidence，Product 再另行评估 OKR percentage update 和 KR 归档。

## 最近两轮 Blocker 扫描

- 18:56 sprint `sprints/2026.07.12_18-56_o3_lifecycle_active_graph_readback_repair/`: primary blocker `/scan_reliable_and_best_effort_timeout` after lifecycle-active and map sample readback became clean.
- 19:56 sprint `sprints/2026.07.12_19-56_o3_scan_qos_endpoint_readback_split/`: primary blocker `/scan_lidar_runtime_exception_after_endpoint_visible_qos_compatible_timeout`; endpoint visible/stable, QoS compatible, BEST_EFFORT and RELIABLE both zero-sample timeout, `serial.serialutil.SerialException` observed, next_owner=`hardware_after_vendor_doc_review`.
- Decision: this is not same-blocker repeat. The sprint changes owner to `robot-hardware-engineer` and narrows from ROS2 readback split to LiDAR serial/runtime/wiring proof.

## Owner, Priority, And Role Split

- P0 owner: `robot-hardware-engineer`.
- Product owner: `product-okr-owner` only for sprint planning, acceptance wording, OKR flat/adjust decision, and KR archive decision.
- Robot Software: support only if Hardware needs a helper contract or artifact schema tweak; no independent implementation lane.
- Algorithm: wait until `/scan`, `/amcl_pose`, and dynamic `map->odom` are clean enough for planner-only path proof.
- Full-stack: not involved.

Priority order:

1. Read `docs/vendor/VENDOR_INDEX.md` and the exact linked local vendor docs needed for the diagnosis.
2. Keep strict no-motion and avoid WAVE ROVER UART entirely.
3. Reproduce or inspect LiDAR runtime around `/dev/ttyACM0`, baudrate `150000` vs `230400`, raw bytes, empty-read counters, and `serial.serialutil.SerialException`.
4. Produce either clean `/scan` sample evidence, a vendor-doc-backed executable fix/config/wiring candidate, or a narrower fail-closed artifact.
5. Update `tech-done.md` with actual changes, command output, failure location, and remaining risk.

## Required Vendor Read Gate

Hardware must read and cite local sources before any serial/runtime/wiring conclusion:

- Always first: `docs/vendor/VENDOR_INDEX.md`.
- Orange Pi serial, USB, power, GPIO, voltage, or electrical checks:
  - `docs/vendor/orangepizero3/OrangePi_Zero3_H618_用户手册_v1.6.pdf`
  - `docs/vendor/orangepizero3/OrangePi-ZERO3_电路图.pdf`
- WAVE ROVER/base UART/ESP32/firmware facts, if mentioned:
  - `docs/vendor/waveshare_wave_rover/WAVE_ROVER.wiki.html`
  - `docs/vendor/waveshare_wave_rover/ugv_rpi/README.md`
  - `docs/vendor/waveshare_wave_rover/ugv_rpi/base_ctrl.py`
  - `docs/vendor/waveshare_wave_rover/ugv_rpi/config.yaml`
  - `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/json_cmd.h`
  - `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/uart_ctrl.h`
- This sprint may read WAVE ROVER docs but must not use WAVE ROVER UART, `/dev/ttyS5`, `/cmd_vel`, `/api/base/manual`, or NavigateToPose.

## Planned File Scope For Hardware Implementation

Allowed implementation and evidence files for the next owner:

- `onboard/src/ros2_trashbot_hardware/ros2_trashbot_hardware/lidar_driver.py`
- `onboard/src/ros2_trashbot_hardware/ros2_trashbot_hardware/lidar_packets.py`
- `onboard/src/ros2_trashbot_hardware/test/test_lidar_driver_stubs.py`
- `onboard/src/ros2_trashbot_hardware/test/test_lidar_packets.py`
- `onboard/scripts/o1_lidar_lifecycle.sh`
- `onboard/scripts/o1_lidar_ros2_scan_smoke.sh`
- `onboard/scripts/o1_lidar_scan_proof_collector.py`
- `onboard/tests/test_lidar_lifecycle_script.py`
- `onboard/tests/test_lidar_scan_proof_collector.py`
- `docs/navigation/field_route_evidence_preflight.md`
- `docs/navigation/fixed_route_workflow.md`
- `sprints/2026.07.12_20-57_o3_lidar_runtime_hardware_probe/artifacts/`
- `sprints/2026.07.12_20-57_o3_lidar_runtime_hardware_probe/tech-done.md`

Product acceptance files after implementation:

- `sprints/2026.07.12_20-57_o3_lidar_runtime_hardware_probe/side2side_check.md`
- `sprints/2026.07.12_20-57_o3_lidar_runtime_hardware_probe/final.md`

Forbidden without new Product routing:

- O5/O6/O7 implementation files.
- UI/API/mobile/cloud code.
- WAVE ROVER UART, ESP32 command paths, `/dev/ttyS5`, firmware flashing, base driver launch defaults, or motion-control configuration.
- `OKR.md` and `docs/process/okr_progress_log.md` during Hardware implementation; Product may update only during acceptance if evidence justifies it.
- Historical sprint files.

## Interface Boundary

Hardware may work only on LiDAR runtime proof and no-motion evidence:

- Input boundary: local vendor docs, LiDAR serial device observation, ROS2 LiDAR driver logs, no-motion `/scan` readback.
- Output boundary: structured artifact/logs that distinguish device path, baudrate, raw bytes, empty reads, runtime exception, driver diagnostics, `/scan` sample state, and next owner.
- Safety boundary: no movement, no base manual control, no WAVE ROVER UART, no route execution.
- Handoff boundary: Algorithm receives work only after `/scan`, `/amcl_pose`, and dynamic `map->odom` are clean enough; Robot Software assists only if a helper contract blocks Hardware evidence capture.

Expected artifact anchors or equivalent summaries:

- `docs/vendor/VENDOR_INDEX.md` read confirmation and linked sources read.
- `/dev/ttyACM0` presence and ownership check.
- `150000` vs `230400` tested or justified as not testable.
- `lidar_driver` diagnostics path and tail.
- raw bytes observed or `raw_bytes_observed=false`.
- empty-read counter or explicit evidence that it is unavailable.
- `serial.serialutil.SerialException` reproduced, resolved, or ruled out.
- `/scan` sample status and sample count.
- `/lidar/raw_packet` status if smoke collects it.
- strict no-motion fields false.

## Strict No-Motion 禁止项

Required prohibitions:

- no `/cmd_vel`
- no `/api/base/manual`
- no NavigateToPose
- no WAVE ROVER UART
- no `/dev/ttyS5`
- no route execution
- no base manual relay
- no safe-to-control claim

Required false fields or equivalent summary:

- `safe_to_control=false`
- `publishes_cmd_vel=false`
- `calls_base_manual=false`
- `uses_base_uart=false`
- `robot_control_executed=false`
- `route_execution_success=false`
- `delivery_success=false`
- `hil_pass=false`

## Implementation Plan

1. Vendor gate: read `docs/vendor/VENDOR_INDEX.md`; open Orange Pi manual/schematic if serial/electrical/USB facts are needed; read WAVE ROVER/ugv_rpi/firmware files only for exclusion and base-UART safety facts.
2. Evidence baseline: inspect 19:56 artifact anchors and confirm the starting blocker is `/scan_lidar_runtime_exception_after_endpoint_visible_qos_compatible_timeout`, not the older `/scan_reliable_and_best_effort_timeout`.
3. Device and process check: capture `/dev/ttyACM0` existence, permissions, symlink/by-id if available, `lsof`/`fuser`, and whether another runtime owns the LiDAR.
4. Baud/runtime probe: compare `150000` vs `230400` through no-motion LiDAR-only smoke or driver stub where real board allows; record exact command, timeout, and result without changing global defaults until evidence supports it.
5. Driver diagnostics: collect `lidar_driver` diagnostics, raw packet sample, empty-read counters or lack thereof, and any `serial.serialutil.SerialException` trace.
6. Artifact normalization: write artifact/logs under this sprint and classify the next step as clean `/scan` handoff, config/baud/device/wiring candidate, or narrower blocked root cause.
7. Closeout: update `tech-done.md` with actual changes, verification output, failure location, remaining risks, and exact next owner.

## Acceptance Commands For Hardware

Hardware must run and report these commands after implementation, adjusting only paths/options needed for the actual evidence while preserving strict no-motion.

Python compile:

```bash
python3 -m py_compile \
  onboard/src/ros2_trashbot_hardware/ros2_trashbot_hardware/lidar_driver.py \
  onboard/src/ros2_trashbot_hardware/ros2_trashbot_hardware/lidar_packets.py \
  onboard/scripts/o1_lidar_scan_proof_collector.py
```

Unit tests for LiDAR driver stubs and proof collector:

```bash
python3 -m unittest \
  onboard.src.ros2_trashbot_hardware.test.test_lidar_driver_stubs \
  onboard.src.ros2_trashbot_hardware.test.test_lidar_packets \
  onboard.tests.test_lidar_scan_proof_collector
```

Shell syntax for no-motion LiDAR lifecycle/smoke:

```bash
bash -n onboard/scripts/o1_lidar_lifecycle.sh
bash -n onboard/scripts/o1_lidar_ros2_scan_smoke.sh
```

Local artifact directory setup:

```bash
mkdir -p sprints/2026.07.12_20-57_o3_lidar_runtime_hardware_probe/artifacts
```

True-board strict no-motion smoke if reachable. If SSH is unreachable, record the exact failure and do not replace it with local-only success.

```bash
ssh -p 37878 root@192.168.1.11 \
  'mkdir -p /root/rober/onboard/scripts /tmp/rober_o1_lidar_artifacts'
```

```bash
scp -P 37878 onboard/scripts/o1_lidar_lifecycle.sh \
  root@192.168.1.11:/root/rober/onboard/scripts/o1_lidar_lifecycle.sh
scp -P 37878 onboard/scripts/o1_lidar_ros2_scan_smoke.sh \
  root@192.168.1.11:/root/rober/onboard/scripts/o1_lidar_ros2_scan_smoke.sh
scp -P 37878 onboard/scripts/o1_lidar_scan_proof_collector.py \
  root@192.168.1.11:/root/rober/onboard/scripts/o1_lidar_scan_proof_collector.py
```

Probe default/current helper path first:

```bash
ssh -p 37878 root@192.168.1.11 \
  'cd /root/rober/onboard && /usr/bin/timeout 180s bash scripts/o1_lidar_ros2_scan_smoke.sh --serial-port /dev/ttyACM0 --serial-baudrate 230400 --output-dir /tmp/rober_o1_lidar_artifacts/smoke_230400'
```

Probe historical field baud only if Hardware confirms it is safe for LiDAR-only runtime:

```bash
ssh -p 37878 root@192.168.1.11 \
  'cd /root/rober/onboard && /usr/bin/timeout 180s bash scripts/o1_lidar_ros2_scan_smoke.sh --serial-port /dev/ttyACM0 --serial-baudrate 150000 --output-dir /tmp/rober_o1_lidar_artifacts/smoke_150000'
```

Pull artifacts:

```bash
scp -P 37878 -r root@192.168.1.11:/tmp/rober_o1_lidar_artifacts \
  sprints/2026.07.12_20-57_o3_lidar_runtime_hardware_probe/artifacts/live_o1_lidar_artifacts
```

Artifact inspection anchors must be recorded in `tech-done.md`:

- `/scan_lidar_runtime_exception_after_endpoint_visible_qos_compatible_timeout`
- `/scan_reliable_and_best_effort_timeout`
- `/dev/ttyACM0`
- `150000`
- `230400`
- `serial.serialutil.SerialException`
- `lidar_driver`
- raw bytes / empty-read counters
- `/scan` sample count or reason missing
- `/lidar/raw_packet` sample status if available
- `safe_to_control=false`
- `publishes_cmd_vel=false`
- `calls_base_manual=false`
- `uses_base_uart=false`
- `robot_control_executed=false`
- `route_execution_success=false`
- `delivery_success=false`
- `hil_pass=false`

Scoped diff check:

```bash
git diff --check -- \
  onboard/src/ros2_trashbot_hardware/ros2_trashbot_hardware/lidar_driver.py \
  onboard/src/ros2_trashbot_hardware/ros2_trashbot_hardware/lidar_packets.py \
  onboard/src/ros2_trashbot_hardware/test/test_lidar_driver_stubs.py \
  onboard/src/ros2_trashbot_hardware/test/test_lidar_packets.py \
  onboard/scripts/o1_lidar_lifecycle.sh \
  onboard/scripts/o1_lidar_ros2_scan_smoke.sh \
  onboard/scripts/o1_lidar_scan_proof_collector.py \
  onboard/tests/test_lidar_lifecycle_script.py \
  onboard/tests/test_lidar_scan_proof_collector.py \
  docs/navigation/field_route_evidence_preflight.md \
  docs/navigation/fixed_route_workflow.md \
  sprints/2026.07.12_20-57_o3_lidar_runtime_hardware_probe
```

## Product Acceptance Gate

Accept as useful sprint progress only if one of these is true:

- Preferred: `/scan` sample readback becomes clean enough that Algorithm can retry `/amcl_pose`, dynamic `map->odom`, and planner-only path proof.
- Acceptable blocked: Hardware narrows `/scan_lidar_runtime_exception_after_endpoint_visible_qos_compatible_timeout` into an exact config/baud/device/wiring/runtime candidate with vendor-doc and no-motion artifact support.
- Acceptable blocked: Hardware proves the next required physical check or vendor/source gap and records why it cannot be completed in the current environment.

Do not accept:

- O5 support-only/wrapper/readiness material.
- Repeating `/scan_lidar_runtime_exception_after_endpoint_visible_qos_compatible_timeout` without a narrower Hardware conclusion.
- Claiming mission progress without same-run path generation, route execution, delivery/operator acceptance, current live HIL, or real production external evidence.
- Any no-motion violation.

## OKR Success / Non-Success 口径

Normal success:

- Keep O5 about `85%`.
- Keep O1/O6/O7 about `93%`.
- Do not archive KR.
- Record as O3/O1 supporting hardware diagnosis only.

Potential stronger success:

- If clean `/scan` allows same-run `/amcl_pose`, dynamic `map->odom`, and planner-only path proof in a follow-up artifact, Product may reopen percentage review after that evidence exists.

Non-success:

- If the sprint repeats the 19:56 blocker without new vendor-doc, serial, baud, raw-byte, empty-read, diagnostics, or sample evidence, send it back to Hardware for repair.
- If true-board is unreachable, close only as local/stub evidence and state live progress is not proven.
- If the diagnosis requires motion, WAVE ROVER UART, or base control, stop and request a separate CEO-approved motion/HIL sprint.

## Risks

- The LiDAR may need physical wiring, power, USB, or module replacement that cannot be proven by software alone.
- `150000` and `230400` may each fail for different reasons if runtime startup sequence, permissions, or serial ownership are wrong.
- `serial.serialutil.SerialException` may be caused by driver lifecycle timing, OS serial behavior, device disconnect, wrong baud, empty packets, or hardware fault; this sprint must distinguish as far as no-motion evidence allows.
- `/amcl_pose` and dynamic `map->odom` remain blocked until `/scan` samples are usable.
- Still no same-run path success, route execution, `route.csv`, keyframe, rosbag, replay JSONL, delivery/operator acceptance, current live HIL, safe-to-control proof, or production external evidence.
