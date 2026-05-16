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
