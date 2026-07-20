# Shared-file baseline before latency work

Captured before latency edits on `2026-07-21`.

## Existing dirty files

- `onboard/scripts/upper_robot_api.py`: SHA-256 `7f7de12fe5aa1e0cd4c6b75983bb14c8a26e4914a34088edc99868113da0e31c`; existing diff `+298/-45`.
- `onboard/tests/test_upper_robot_api.py`: SHA-256 `bbdd648b2985b160926418449985aa90ec419a1ffc1d0e24317dd491987cb675`; existing diff `+399/-8`.
- `docs/interfaces/ros_runtime_contracts.md`: SHA-256 `952ecc2ce4e06ff132a40523b15e58cd84424b484894665230fc7d557fcafdc7`; existing diff `+64/-0`.

## Existing hunk audit

- `upper_robot_api.py` had Nav2 hunks near lines `154`, `1959-2037`, `2607-2660`, `3366-3573`, and `10048-11448`.
- `test_upper_robot_api.py` had Nav2/shared regressions near lines `2861-3571` and `5267-5456`.
- `ros_runtime_contracts.md` had one additive Nav2 contract hunk at file start.

The exact pre-edit patch is recoverable from the Git index plus the hashes above; latency changes must remain additive and must not remove any of these hunk families. No checkout, reset, stash, rebase, or whole-file formatting is authorized.

## Post-implementation audit

- `onboard/scripts/upper_robot_api.py`: final SHA-256 `417c81ce4aa2a1c24376c1c74e34e4eae4977dba65a807d5107c45b153a5fb64` at audit time.
- `onboard/tests/test_upper_robot_api.py`: final SHA-256 `bfbeb992d204031b8f34b32eeeb42a91504f2960f04de6f14e3f28d0345b58c4` at audit time.
- `docs/interfaces/ros_runtime_contracts.md`: final SHA-256 `caff7a5011d8b80bbc99b8e4cf4e1832f16b932e79011a004920d24d768d7099` at audit time.
- Existing Nav2 hunk families around helper argv/lifecycle parsing/API methods and their test blocks remain present. Latency hunks are additive around trace normalization, cmd_vel context/publish, manual hold, server startup/handler, tests, and the contract tail.
- The concurrent Nav2 owner completed additional changes during this implementation window; after the subscriber-race repair the combined shared suite passed `328` tests with `1` intentional skip. No Nav2 hunk was reverted or reformatted by this sprint.
