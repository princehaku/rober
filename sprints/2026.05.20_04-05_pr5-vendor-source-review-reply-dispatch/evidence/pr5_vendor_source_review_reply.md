## PR #5 vendor/source reply for `PRRT_kwDOSWB9286CJ3tX`

Status: `reply-ready`, `software_proof`, `not_proven`, `hardware_material_pending`, `delivery_success=false`, `primary_actions_enabled=false`.

I checked the local vendor/source boundary for this thread. The repo-local source entrypoint remains `docs/vendor/VENDOR_INDEX.md`; it points to Orange Pi Zero 3 references plus WAVE ROVER firmware/vendor-app UART JSON references. Those files support source attribution only. They do **not** prove project 2D LiDAR / ToF SKU, purchase, install, wiring, power, calibration, HIL entry, Nav2/SLAM field pass, or delivery success.

Source refs used:
- `docs/vendor/VENDOR_INDEX.md`
- `docs/vendor/waveshare_wave_rover/ugv_rpi/base_ctrl.py`
- `docs/vendor/waveshare_wave_rover/ugv_rpi/config.yaml`
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/json_cmd.h`

Still missing real hardware materials:
- `real_2d_lidar_sku_source_receipt`
- `real_tof_sku_source_receipt`
- `real_mounting_wiring_power_plan`
- `real_calibration_material`
- `real_sensor_hil_entry`
- `real_nav2_slam_field_pass`

Next required evidence before this can become hardware proof:
- Provide reviewed 2D LiDAR SKU/source/receipt or purchase-order material.
- Provide reviewed ToF SKU/source/channel-count material.
- Link mounting, wiring, power-budget, and calibration plans.
- Run a separate HIL-entry review after real materials exist.
- Only then request reviewer resolution for hardware-material obligations.

This reply is safe to publish manually as a review-thread response, but it is not an automatic GitHub write, not a request to resolve the thread, and not a real hardware-material or HIL pass.

Dispatch gate: `software_proof_docker_pr5_vendor_source_review_reply_dispatch_gate`; reply status: `ready_for_manual_github_review_reply_not_proven`.
