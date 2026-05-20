# PR #5 Mandatory Sensor Source Alignment

`pc-tools/evidence/pr5_mandatory_sensor_source_alignment.py` is the canonical
PC-only gate for PR #5 unresolved review thread `PRRT_kwDOSWB9286CJ3tX`.

- Artifact schema: `trashbot.pr5_mandatory_sensor_source_alignment.v1`
- Summary schema: `trashbot.pr5_mandatory_sensor_source_alignment_summary.v1`
- Evidence boundary:
  `software_proof_docker_pr5_mandatory_sensor_source_alignment_gate`
- Required source entrypoint: `docs/vendor/VENDOR_INDEX.md`
- Required state: `source=software_proof`, `hardware_material_pending`,
  `not_proven`, `safe_to_control=false`, `delivery_success=false`, and
  `primary_actions_enabled=false`

The gate answers the mandatory sensor assumption review request without
claiming hardware fulfillment. It checks that the current default hardware set
is separate from the target sensing baseline, and that `2D LiDAR` / `ToF`
remain pending real SKU/source/receipt, procurement, mounting, wiring, power,
calibration, HIL-entry, and reviewer-resolution material.

The gate reads local source-boundary references only:

- `docs/vendor/VENDOR_INDEX.md`
- `docs/vendor/orangepizero3/OrangePi_Zero3_H618_用户手册_v1.6.pdf`
- `docs/vendor/orangepizero3/OrangePi-ZERO3_电路图.pdf`
- `docs/vendor/waveshare_wave_rover/ugv_rpi/README.md`
- `docs/vendor/waveshare_wave_rover/ugv_rpi/base_ctrl.py`
- `docs/vendor/waveshare_wave_rover/ugv_rpi/config.yaml`
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/json_cmd.h`
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/uart_ctrl.h`
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/movtion_module.h`

Those files establish local source context for Orange Pi Zero 3, WAVE ROVER,
UART newline-delimited JSON, WAVE ROVER firmware, the vendor upper-computer
application, and vendor camera/video/CV examples. They do not prove a project
`2D LiDAR` or `ToF` SKU/source/receipt, purchase order, mounting, wiring,
power budget, calibration, HIL entry, Nav2/SLAM field pass, near-field safety
pass, `PRRT_kwDOSWB9286CJ3tX` resolution, Objective 5 external proof, or
delivery success.

Consumers should read the summary first. It exposes only sanitized fields:
`thread_id`, `alignment_status`, `vendor_source_boundary`,
`mandatory_sensor_assumptions`, `missing_materials`,
`next_required_evidence`, `owner_handoff`, `safe_copy`,
`safe_to_control=false`, `delivery_success=false`, and
`primary_actions_enabled=false`.

Fail-closed states:

- `blocked_missing_pr5_mandatory_sensor_source_alignment_source`
- `blocked_missing_pr5_mandatory_sensor_source_alignment_boundary`
- `blocked_unsafe_pr5_mandatory_sensor_source_alignment_claim`

Missing source files, missing product boundary semantics, raw local paths, raw
serial paths, credentials, HIL/field pass wording, PR thread resolved wording,
`delivery_success=true`, `safe_to_control=true`, or
`primary_actions_enabled=true` must fail closed.
