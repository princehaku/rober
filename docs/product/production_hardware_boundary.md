# Production Hardware Boundary

## Default Hardware Set

- WAVE ROVER mobile chassis.
- Orange Pi Zero 3 upper computer.
- Portable WiFi or local network access.
- Monocular 1080p camera (default semantic evidence sensor).
- Microphone.
- Speaker or buzzer.

This default hardware set is the current product boundary, not a claim that all
future navigation or safety sensors have already been procured, installed,
wired, calibrated, or HIL-proven.

## Default Exclusions

- Mechanical arm.
- Depth camera.
- Any 2D LiDAR or ToF module that has not passed procurement validation,
  mounting/wiring review, calibration plan review, and HIL entry checks.
- Extra redundant lidar stacks beyond an explicitly validated baseline 2D
  LiDAR, unless acceptance evidence proves the need.
- Multi-board compute stack.
- Automatic trash sorting mechanism.

## Addition Rule

Any new hardware must document:

- Unit cost.
- Mounting and wiring impact.
- Power budget impact.
- Maintenance impact.
- Software benefit.
- Whether it reduces ordinary user friction or improves delivery success rate.

## MVP Product Boundary

The MVP is a low-speed fixed-route trash delivery robot for controlled indoor or neighborhood environments. It is not an open-road autonomous vehicle, a scattered-trash pickup robot, or a full classification and sorting system.


## Vendor/Source Attribution Boundary

Hardware facts must start from `docs/vendor/VENDOR_INDEX.md`. Current local
vendor coverage includes Orange Pi Zero 3 user manual/schematic references,
WAVE ROVER chassis/mechanical references, WAVE ROVER ESP32 firmware/source,
UART newline-delimited JSON command references, Waveshare Raspberry Pi
upper-computer examples, and vendor camera/tutorial material.

The current local vendor tree does not prove that a project 2D LiDAR or ToF
ring has been purchased, physically mounted, wired to the Orange Pi/WAVE ROVER,
calibrated, accepted into Nav2, or passed HIL. Any LiDAR/ToF language below is
therefore product target material with procurement validation pending, not
vendor-proven installed hardware and not O5 external proof.

Evidence state: `hardware_material_pending`, `not_proven`.

## Hardware Sensor Procurement Intake Gate

`hardware_sensor_procurement_intake` is the fail-closed PC gate for future 2D
LiDAR and ToF material intake. It converts the exact SKU, vendor/source
document, procurement status, mounting plan, wiring plan, power budget,
calibration plan, ToF channel count/source, and HIL entry material into a
machine-readable artifact and sanitized summary.

The gate starts from `docs/vendor/VENDOR_INDEX.md` only to record the current
source boundary: the local vendor index covers Orange Pi Zero 3, WAVE ROVER,
UART/JSON control, firmware/vendor app references, and camera-related vendor
material. It does **not** prove that a project 2D LiDAR or ToF SKU/source has
been selected, purchased, installed, wired, calibrated, accepted into Nav2, or
passed HIL.

Until real materials are provided and reviewed, the gate summary must remain
`hardware_material_pending`, `not_proven`, `delivery_success=false`, and
`primary_actions_enabled=false`. ToF channel count is still a product target
unless the intake links a concrete source document; when no source exists it
must be explicitly marked as product target pending validation rather than
vendor-proven hardware.

## Hardware Sensor Procurement Review Decision Gate

`hardware_sensor_procurement_review_decision` is the follow-up fail-closed PC
gate for the previous `hardware_sensor_procurement_intake` artifact or summary.
It converts intake gaps into a review decision, blockers,
`next_required_evidence`, `owner_handoff`, and `rerun_commands` so hardware,
Robot diagnostics, mobile/web, and Product closeout can act on the same
material state without weakening the evidence boundary.

The review decision gate still starts from `docs/vendor/VENDOR_INDEX.md` only
as the current vendor/source boundary. That index covers Orange Pi Zero 3,
WAVE ROVER, UART/JSON control, firmware/vendor app references, and
camera-related vendor material; it does not prove a project `2D LiDAR` or
`ToF` SKU/source, purchase order, mounting bracket, wiring path, power budget,
calibration artifact, HIL entry, Nav2/SLAM field pass, near-field safety pass,
or delivery result.

Supported decisions are
`blocked_missing_hardware_sensor_procurement_intake`,
`blocked_unsupported_hardware_sensor_procurement_intake`,
`blocked_missing_procurement_materials`,
`blocked_missing_mounting_wiring_calibration`, and
`ready_for_procurement_review_not_proven`. Every decision must keep
`software_proof`, `hardware_material_pending`, `not_proven`,
`delivery_success=false`, and `primary_actions_enabled=false`.

## Hardware Sensor Procurement Execution Pack Gate

`hardware_sensor_procurement_execution_pack` is the metadata-only PC gate after
`hardware_sensor_procurement_review_decision`. It converts the supported review
decision artifact or summary into procurement execution material templates,
`owner_handoff`, `rerun_commands`, `blocked_reason`, and
`next_required_evidence` for the same 2D LiDAR / ToF material chain.

The execution pack remains a software-proof planning artifact. It does not call
any procurement system, read sensor drivers, access ROS, open serial devices,
install hardware, calibrate hardware, run HIL, prove route/elevator behavior,
or prove delivery success. Its evidence boundary is
`software_proof_docker_hardware_sensor_procurement_execution_pack_gate`.

Supported output states include
`blocked_missing_hardware_sensor_procurement_review_decision`,
`blocked_unsupported_hardware_sensor_procurement_review_decision`,
`blocked_hardware_sensor_procurement_review_not_ready`,
`blocked_unsafe_hardware_sensor_procurement_execution_pack_copy`,
`blocked_weak_hardware_sensor_procurement_review_contract`, and
`ready_for_hardware_sensor_procurement_execution_pack_not_proven`. Every state
must keep `software_proof`, `hardware_material_pending`, `not_proven`,
`delivery_success=false`, and `primary_actions_enabled=false`.

The source boundary is still `docs/vendor/VENDOR_INDEX.md` and its local
Orange Pi / WAVE ROVER / UART / firmware / vendor-app references. Those local
vendor references are useful for preventing hardware guesses, but they still do
not prove a project 2D LiDAR or ToF SKU, purchase order, mounting/wiring plan,
power budget, calibration result, HIL entry, Nav2/SLAM field pass, near-field
safety pass, route/elevator pass, or delivery result.

## Hardware Sensor Procurement Receipt Intake Gate

`hardware_sensor_procurement_receipt_intake` is the fail-closed PC gate after
`hardware_sensor_procurement_execution_pack`. It accepts only sanitized
summaries or references for future receipt, source, vendor, SKU, cost,
install, wiring, power, calibration, and HIL-entry materials, then emits
`accepted_materials`, `missing_materials`, `rejected_materials`,
`next_required_evidence`, and `owner_handoff` for the same 2D LiDAR / ToF
material chain.

The receipt intake remains software proof only. It does not call a procurement
system, inspect warehouse/shipping state, read sensor drivers, access ROS,
open serial/UART devices, install hardware, validate wiring or power, calibrate
hardware, run HIL, prove route/elevator behavior, prove Objective 5 external
cloud proof, or prove delivery success. Its evidence boundary is
`software_proof_docker_hardware_sensor_procurement_receipt_intake_gate`.

Supported output states include
`blocked_missing_hardware_sensor_procurement_execution_pack`,
`blocked_unsupported_hardware_sensor_procurement_execution_pack`,
`blocked_hardware_sensor_procurement_execution_pack_not_ready`,
`blocked_missing_hardware_sensor_procurement_receipt_materials`,
`blocked_unsafe_hardware_sensor_procurement_receipt_intake_copy`,
`blocked_weak_hardware_sensor_procurement_execution_pack_contract`, and
`ready_for_hardware_sensor_procurement_receipt_intake_not_proven`. Every state
must keep `software_proof`, `hardware_material_pending`, `not_proven`,
`delivery_success=false`, and `primary_actions_enabled=false`.

The required entry materials for the intake gate are receipt, source, vendor,
and SKU summaries or references. Cost, install, wiring, power, calibration, and
HIL-entry materials may be missing and must remain listed in
`missing_materials` until real reviewed evidence exists. The gate must reject
raw credentials, token/OSS AK/SK material, DB/queue URLs, raw serial/UART
paths, complete local filesystem paths, checksums, raw JSON, complete artifact
copies, procurement-success wording, HIL-success wording, delivery success, or
Objective 5 external proof claims.

The source boundary remains `docs/vendor/VENDOR_INDEX.md` plus the local Orange
Pi / WAVE ROVER / UART / firmware / vendor-app references listed there. Those
local vendor files still do not prove a project 2D LiDAR or ToF SKU, receipt,
vendor/source acceptance, purchase order, mounting/wiring plan, power budget,
calibration result, HIL entry, Nav2/SLAM field pass, near-field safety pass,
route/elevator pass, Objective 5 external proof, or delivery result.

## Navigation/Sensing Baseline (Product Target, Procurement Validation Pending)

- Target baseline combo: monocular camera + one 2D LiDAR + ToF safety ring.
  The monocular camera is the current default semantic evidence sensor; the 2D
  LiDAR and ToF ring are target hardware pending procurement/source
  attribution, mounting, wiring, calibration, and HIL evidence.
- ToF product target: 2 channels minimum, 4 channels recommended
  (front/back/left/right). These channel counts are product acceptance targets,
  not local vendor or HIL-proven facts.
- Responsibility split:
  - 2D LiDAR: target primary SLAM/Nav2 mapping + localization input after
    procurement validation and calibration evidence.
  - Monocular camera: elevator door/target-floor semantic evidence, snapshots and operator diagnostics.
  - ToF: target near-field collision safety and conservative enter/exit
    gating after wiring and HIL checks; it is not a primary SLAM source.
- Extensibility rule: sensor count, thresholds, frame IDs and safety policies must be configurable via launch/params, not hardcoded for a single hardware SKU.
- Acceptance rule: do not treat 2D LiDAR or ToF as part of the Default Hardware
  Set until the exact SKU, vendor/source document, procurement status,
  mechanical mount, wiring path, calibration method, and HIL result are linked
  from the relevant hardware runbook or sprint evidence.

## Code Quality Constraint (Implementation Gate)

- All technical comments in code/scripts must be Chinese.
- Meaningful Chinese technical comments must exceed 20% density (at least 1 comment line per 5 lines on average).
- Comments must explain **why** (tradeoff, risk, boundary), not only what the code does.
