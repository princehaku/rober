# Production Hardware Boundary

## Default Hardware Set

- WAVE ROVER mobile chassis.
- Orange Pi Zero 3 upper computer.
- Portable WiFi or local network access.
- Monocular 1080p camera (default semantic evidence sensor).
- Microphone.
- Speaker or buzzer.

## Default Exclusions

- Mechanical arm.
- Depth camera.
- Extra redundant lidar stacks beyond one baseline 2D LiDAR (unless acceptance evidence proves need).
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


## Navigation/Sensing Baseline (Mandatory for current MVP)

- Baseline combo: monocular camera + one 2D LiDAR + ToF safety ring (2 channels minimum, 4 channels recommended: front/back/left/right).
- Responsibility split:
  - 2D LiDAR: primary SLAM/Nav2 mapping + localization input.
  - Monocular camera: elevator door/target-floor semantic evidence, snapshots and operator diagnostics.
  - ToF: near-field collision safety and conservative enter/exit gating, not a primary SLAM source.
- Extensibility rule: sensor count, thresholds, frame IDs and safety policies must be configurable via launch/params, not hardcoded for a single hardware SKU.

## Code Quality Constraint (Implementation Gate)

- All technical comments in code/scripts must be Chinese.
- Meaningful Chinese technical comments must exceed 20% density (at least 1 comment line per 5 lines on average).
- Comments must explain **why** (tradeoff, risk, boundary), not only what the code does.
