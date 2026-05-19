# Hardware Real Material Escalation Request

`hardware_real_material_escalation_request` is a fail-closed PC evidence gate
for the Objective 1 / PR #5 real-material gap. It turns missing real hardware
materials into a summary-only escalation request that Robot diagnostics and
phone/mobile surfaces can consume without implying field proof.

## Vendor Source Boundary

The gate must start from `docs/vendor/VENDOR_INDEX.md`. The local source
boundary cited by the gate is:

- `docs/vendor/VENDOR_INDEX.md`
- `docs/vendor/waveshare_wave_rover/ugv_rpi/base_ctrl.py`
- `docs/vendor/waveshare_wave_rover/ugv_rpi/config.yaml`
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/json_cmd.h`
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/uart_ctrl.h`
- `docs/vendor/orangepizero3/OrangePi_Zero3_H618_用户手册_v1.6.pdf`
- `docs/vendor/orangepizero3/OrangePi-ZERO3_电路图.pdf`

These sources establish the local WAVE ROVER / Orange Pi / UART JSON /
firmware reference boundary only. They do not prove real WAVE ROVER UART
connectivity, HIL packet success, 2D LiDAR procurement, ToF procurement,
installation, wiring, power, calibration, Objective 5 external proof, or
delivery success.

## Output Contract

Artifact schema:

- `schema=trashbot.hardware_real_material_escalation_request.v1`
- `source=software_proof`
- `evidence_boundary=software_proof_docker_hardware_real_material_escalation_request_gate`
- `hardware_material_status=hardware_material_pending`
- `evidence_status=not_proven`
- `delivery_success=false`
- `primary_actions_enabled=false`

Summary schema:

- `schema=trashbot.hardware_real_material_escalation_request_summary.v1`
- `summary_only=true`
- `phone_safe=true`
- `delivery_success=false`
- `primary_actions_enabled=false`

The request must list both material families:

- WAVE ROVER/UART/HIL: powered bench evidence, Orange Pi UART confirmation,
  command/feedback capture, and HIL packet material.
- PR #5 2D LiDAR / ToF: SKU/source/receipt, mounting, wiring, power,
  calibration, channel/source, and HIL-entry material.

## Fail-Closed Rules

The gate fails closed when `docs/vendor/VENDOR_INDEX.md` is missing, the
production hardware boundary is missing, or output text contains raw
credentials, raw serial paths, raw JSON artifact copies, success claims,
`delivery_success=true`, or `primary_actions_enabled=true`.

`ready_for_hardware_real_material_escalation_request_not_proven` only means the
PC gate produced a safe escalation request. It is not HIL, not real WAVE
ROVER/UART proof, not real 2D LiDAR / ToF proof, and not Objective 5 external
proof.
