# PR #5 Vendor Source Review Packet

`pc-tools/evidence/pr5_vendor_source_review_packet.py` generates the
thread-specific PC-only packet for PR #5 unresolved review thread
`PRRT_kwDOSWB9286CJ3tX`.

- Artifact schema: `trashbot.pr5_vendor_source_review_packet.v1`
- Summary schema: `trashbot.pr5_vendor_source_review_packet_summary.v1`
- Evidence boundary:
  `software_proof_docker_pr5_vendor_source_review_packet_gate`
- Required source entrypoint: `docs/vendor/VENDOR_INDEX.md`
- Required local vendor refs:
  `docs/vendor/waveshare_wave_rover/ugv_rpi/base_ctrl.py`,
  `docs/vendor/waveshare_wave_rover/ugv_rpi/config.yaml`, and
  `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/json_cmd.h`

The packet exists to answer the review request for `2D LiDAR` / `ToF` source
attribution without weakening the hardware boundary. It records that local
vendor files cover Orange Pi Zero 3, WAVE ROVER, UART newline-delimited JSON,
WAVE ROVER firmware/vendor app references, and an optional vendor app lidar
parser reference. Those files are source-boundary material only.

The packet must keep `source=software_proof`,
`overall_status=not_proven`, `hardware_material_pending`,
`delivery_success=false`, and `primary_actions_enabled=false`.
`ready_for_pr5_vendor_source_review_packet_not_proven` means only that the
thread now has a machine-readable packet with source refs, missing materials,
safe copy, and next required evidence. It is not proof of real 2D LiDAR / ToF
SKU, receipt, installation, wiring, power validation, calibration, HIL entry,
Nav2/SLAM field pass, near-field safety pass, Objective 5 external proof, or
delivery success.

Fail-closed states:

- `blocked_missing_pr5_vendor_source_review_packet_source`
- `blocked_missing_pr5_vendor_source_review_context`
- `blocked_unsafe_pr5_vendor_source_review_packet_claim`

Missing source files, missing product boundary context, unsafe copy, raw local
paths, raw serial/UART paths, raw credentials, procurement/HIL/field success
claims, `delivery_success=true`, or `primary_actions_enabled=true` must fail
closed.
