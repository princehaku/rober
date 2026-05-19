# Real Material Readiness Board

`real_material_readiness_board` is a PC/evidence software-proof gate for routing
real-material collection across Objective 5, Objective 1 / PR #5 hardware,
PR #4 route/elevator, and Objective 4 real phone readiness.

It is a routing surface, not a proof surface. Every artifact and summary must
remain:

- `source=software_proof`
- `status=not_proven`
- `delivery_success=false`
- `primary_actions_enabled=false`
- `safe_to_control=false`

## Vendor Source Boundary

Hardware-related fields must cite `docs/vendor/VENDOR_INDEX.md` as the entry
point and local vendor source boundary. The gate references:

- `docs/vendor/VENDOR_INDEX.md`
- `docs/vendor/waveshare_wave_rover/ugv_rpi/base_ctrl.py`
- `docs/vendor/waveshare_wave_rover/ugv_rpi/config.yaml`
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/json_cmd.h`
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/uart_ctrl.h`

These files establish the local WAVE ROVER / Orange Pi Zero 3 / ESP32 / UART /
firmware source boundary only. They do not prove real WAVE ROVER UART feedback,
HIL packet success, 2D LiDAR SKU/source/receipt, ToF SKU/source/receipt,
installation, wiring, power, calibration, or real field readiness.

## Output Contract

Artifact schema:

- `schema=trashbot.real_material_readiness_board.v1`
- `evidence_boundary=software_proof_docker_real_material_readiness_board_gate`
- `material_status=blocked_pending_real_materials`
- `review_threads.pr5_thread_id=PRRT_kwDOSWB9286CJ3tX`
- `review_threads.pr5_review_state=unresolved`
- `review_threads.pr5_material_state=blocked_pending_real_materials`
- `delivery_success=false`
- `primary_actions_enabled=false`
- `safe_to_control=false`

Summary schema:

- `schema=trashbot.real_material_readiness_board_summary.v1`
- `summary_only=true`
- `routing_surface_only=true`
- `safe_to_render_on_phone=true`
- `group_count=4`
- `delivery_success=false`
- `primary_actions_enabled=false`
- `safe_to_control=false`

## Material Groups

The board contains four required material groups:

| group_id | Objective / review ref | Owner | Boundary |
|---|---|---|---|
| `o5_external` | `Objective 5` | `product-okr-owner` | Missing real external HTTPS/TLS, 4G/SIM, OSS/CDN live traffic, production DB/queue, worker/migration/cutover proof. |
| `objective_1_pr5_hardware` | `Objective 1`, `PR #5`, `PRRT_kwDOSWB9286CJ3tX` | `hardware-engineer` | Missing real WAVE ROVER/UART/HIL packet and PR #5 2D LiDAR / ToF real materials. |
| `pr4_route_elevator` | `PR #4`, `Objective 2`, `Objective 3` | `autonomy-engineer` | `group_status=blocked_missing_pr4_route_elevator_real_materials`; missing `real_elevator_door_state`, `target_floor_confirmation`, `human_assistance_record`, `nav2_fixed_route_runtime_log`, `field_task_record`, `route_completion_signal`, `dropoff_completion_material`, `cancel_completion_material`, and `delivery_result`. |
| `objective_4_real_phone` | `Objective 4` | `full-stack-software-engineer` | Missing real phone browser/device/PWA/network/operator acceptance materials. |

## Fail-Closed Rules

The gate fails closed when `docs/vendor/VENDOR_INDEX.md` is missing or output
contains unsafe success/control claims such as `delivery_success=true`,
`primary_actions_enabled=true`, `safe_to_control=true`, HIL pass, field pass,
raw device paths, or credentials.

`ready_for_real_material_readiness_board_not_proven` only means the PC gate
created a safe readiness-routing artifact. It does not close PR #5, does not
resolve `PRRT_kwDOSWB9286CJ3tX`, does not prove Objective 5 external readiness,
does not prove PR #4 route/elevator real-material acceptance, and does not
prove Objective 4 real phone acceptance.
