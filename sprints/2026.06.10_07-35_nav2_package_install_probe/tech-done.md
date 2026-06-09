# Nav2 package install probe

Keyword: `nav2 package install`.

## Sprint Type

- `sprint_type: micro`
- Owner: `robot-software-engineer`
- Scope: true upper-computer Nav2 package remediation on `root@192.168.1.11:37878`, followed by read-only no-motion Nav2 proof refresh.
- Remote capture time: `2026-06-10 05:19:15 CST` to `2026-06-10 05:22:50 CST`.

## Safety Boundary

Required source review was completed before remote action:

- `AGENTS.md`
- `OKR.md`
- `docs/vendor/VENDOR_INDEX.md`
- `docs/hardware/board_sensor_stack_smoke.md`
- `docs/navigation/fixed_route_workflow.md`
- `onboard/scripts/upper_robot_api.py`
- `onboard/scripts/o10_amcl_nav2_runtime_proof.py`
- `sprints/2026.06.10_07-20_nav2_refresh_stable_rerun/tech-done.md`

Vendor and project facts used only as safety exclusions: WAVE ROVER/base UART is `/dev/ttyS5` on the current board evidence chain, LiDAR is `/dev/ttyACM0`, and this sprint was not allowed to open base UART except read-only `lsof`/`fuser` checks. This sprint did not publish `/cmd_vel`, did not call `/api/base/*`, `/api/map/start`, `/api/nav2/start`, `/api/nav2/stop`, and did not start autonomous launch or send goals.

## Remote Identity And Apt Sources

Artifacts:

- `artifacts/remote_capture/env_identity.txt`
- `artifacts/remote_capture/apt_sources.txt`

Key output:

```text
op-z3-b6.home
Wed Jun 10 05:19:15 AM CST 2026
PRETTY_NAME="Ubuntu 22.04.5 LTS"
ROS_DISTRO=
ROS_DISTRO_AFTER_SOURCE=humble
/opt/ros/humble/bin/ros2
```

APT sources in use:

- Ubuntu ports: `https://mirrors.tuna.tsinghua.edu.cn/ubuntu-ports jammy`
- ROS 2: `http://packages.ros.org/ros2/ubuntu jammy main`
- Docker: `https://repo.huaweicloud.com/docker-ce/linux/ubuntu jammy stable`

## Pre-Install Package State

Artifacts:

- `artifacts/remote_capture/dpkg_nav2_status_pre.txt`
- `artifacts/remote_capture/ros2_pkg_prefix_pre.txt`
- `artifacts/remote_capture/apt_cache_policy_nav2.txt`
- `artifacts/remote_capture/pre_api_nav2_proof_latest_response.json`
- `artifacts/remote_capture/pre_api_nav2_status_response.json`

`apt-cache policy` showed:

- `ros-humble-nav2-map-server` installed: `1.1.20-1jammy.20260423.180326`
- `ros-humble-nav2-amcl` candidate: `1.1.20-1jammy.20260423.175841`
- `ros-humble-nav2-planner` candidate: `1.1.20-1jammy.20260426.044006`
- `ros-humble-nav2-controller` candidate: `1.1.20-1jammy.20260426.043720`

The exact requested multi-package command was captured:

```bash
source /opt/ros/humble/setup.bash && ros2 pkg prefix nav2_amcl nav2_planner nav2_controller nav2_map_server
```

On this ROS2 CLI it returned:

```text
ros2: error: unrecognized arguments: nav2_planner nav2_controller nav2_map_server
EXIT_CODE:2
```

The pre-refresh artifact still had the expected package blockers:

- `nav2_amcl_missing`
- `nav2_planner_missing`
- `nav2_controller_missing`
- `nav2_map_server` was already present at `/opt/ros/humble`

## Dry-Run And Install

Artifact:

- `artifacts/remote_capture/apt_get_sim_install_nav2.txt`
- `artifacts/remote_capture/apt_get_install_nav2.txt`
- `artifacts/remote_capture/dpkg_nav2_status_post.txt`
- `artifacts/remote_capture/ros2_pkg_prefix_post_exact.txt`
- `artifacts/remote_capture/ros2_pkg_prefix_post_individual.txt`

Dry-run result:

```text
The following NEW packages will be installed:
  ros-humble-angles ros-humble-nav-2d-msgs ros-humble-nav-2d-utils
  ros-humble-nav2-amcl ros-humble-nav2-controller ros-humble-nav2-core
  ros-humble-nav2-costmap-2d ros-humble-nav2-planner
  ros-humble-nav2-voxel-grid
0 upgraded, 9 newly installed, 0 to remove and 322 not upgraded.
```

Because dry-run had no removals and no upgrades, the actual command was run:

```bash
DEBIAN_FRONTEND=noninteractive apt-get install -y --no-upgrade \
  ros-humble-nav2-amcl \
  ros-humble-nav2-planner \
  ros-humble-nav2-controller \
  ros-humble-nav2-map-server
```

Install summary:

```text
Skipping ros-humble-nav2-map-server, it is already installed and upgrade is not set.
0 upgraded, 9 newly installed, 0 to remove and 322 not upgraded.
Need to get 1,792 kB of archives.
After this operation, 10.3 MB of additional disk space will be used.
Setting up ros-humble-nav2-amcl (1.1.20-1jammy.20260423.175841) ...
Setting up ros-humble-nav2-planner (1.1.20-1jammy.20260426.044006) ...
Setting up ros-humble-nav2-controller (1.1.20-1jammy.20260426.043720) ...
EXIT_CODE:0
```

Post-install individual package prefix check:

```text
nav2_amcl /opt/ros/humble
nav2_planner /opt/ros/humble
nav2_controller /opt/ros/humble
nav2_map_server /opt/ros/humble
EXIT_CODE:0
```

## Serial Occupancy Checks

Artifacts:

- `artifacts/remote_capture/pre_lsof_ttyS5_ttyACM0.txt`
- `artifacts/remote_capture/pre_fuser_ttyS5_ttyACM0.txt`
- `artifacts/remote_capture/install_lsof_ttyS5_ttyACM0.txt`
- `artifacts/remote_capture/install_fuser_ttyS5_ttyACM0.txt`
- `artifacts/remote_capture/post_lsof_ttyS5_ttyACM0.txt`
- `artifacts/remote_capture/post_fuser_ttyS5_ttyACM0.txt`
- `artifacts/remote_capture/final_lsof_ttyS5_ttyACM0.txt`
- `artifacts/remote_capture/final_fuser_ttyS5_ttyACM0.txt`

All `lsof /dev/ttyS5 /dev/ttyACM0 || true` and `fuser -v /dev/ttyS5 /dev/ttyACM0 || true` captures produced no process rows. The only interaction with `/dev/ttyS5` and `/dev/ttyACM0` in this sprint was these read-only occupancy checks.

## No-Motion Nav2 Proof Refresh

Artifacts:

- `artifacts/remote_capture/api_nav2_proof_refresh_response.json`
- `artifacts/remote_capture/api_nav2_proof_latest_response.json`
- `artifacts/remote_capture/api_nav2_status_response.json`
- `artifacts/remote_capture/onboard_runtime_nav2_lifecycle_latest.json`
- `artifacts/remote_capture/onboard_runtime_map_lifecycle_latest.json`

Command executed:

```bash
curl -sS -X POST http://127.0.0.1:8787/api/nav2/proof/refresh \
  -H 'Content-Type: application/json' \
  -d '{"timeout_s":20}'
curl -sS http://127.0.0.1:8787/api/nav2/proof/latest
curl -sS http://127.0.0.1:8787/api/nav2/status
```

Refresh result:

- HTTP: `200`
- top-level `status=blocked_with_root_cause`
- `proof_state=blocked_with_root_cause`
- `evidence_type=blocked_with_root_cause`
- helper `ok=false`
- helper `returncode=2`
- helper `elapsed_ms=93060`
- evidence ref: `o10-amcl-nav2-runtime-1781040077853`

Package blocker change:

- Before install: `nav2_amcl_missing`, `nav2_planner_missing`, and `nav2_controller_missing` were present.
- After install: package checks for `nav2_amcl`, `nav2_planner`, `nav2_controller`, and `nav2_map_server` all returned `ok=true` with `/opt/ros/humble`; the package-missing blockers disappeared.

Remaining blockers after install:

- `map_server_lifecycle_not_active`
- `amcl_lifecycle_not_active`
- `planner_lifecycle_not_active`
- `controller_lifecycle_not_active`
- `/scan_once_not_observed`
- `/map_once_not_observed`
- `/amcl_pose_once_not_observed`

Key flags after refresh:

- `map_server_active=false`
- `amcl_active=false`
- `planner_active=false`
- `controller_active=false`
- `scan_once_observed=false`
- `map_once_observed=false`
- `amcl_pose_observed=false`
- `path_generation_ready=false`
- `path_generated=false`
- `publishes_cmd_vel=false`
- `calls_base_manual=false`
- `uses_base_uart=false`
- `safe_to_control=false`
- `delivery_success=false`

`GET /api/nav2/status` returned:

- `status=not_proven`
- `amcl_nav2_readiness.status=map_inputs_ready_for_no_motion_nav2_collector`
- `proof_latest.latest_proof_status=blocked_with_root_cause`
- `latest_map_server_active=false`
- `latest_amcl_active=false`
- `latest_planner_active=false`
- `latest_controller_active=false`
- `latest_scan_consumed=false`
- `latest_map_consumed=false`
- `latest_path_generated=false`

## Actual Changed Files

- `docs/hardware/board_sensor_stack_smoke.md`
- `sprints/2026.06.10_07-35_nav2_package_install_probe/tech-done.md`
- `sprints/2026.06.10_07-35_nav2_package_install_probe/artifacts/remote_capture/*`

No product code, tests, launch files, firmware, or hardware configuration were changed.

## Validation Results

Remote validation artifacts cover:

- `hostname; date; cat /etc/os-release | head; echo ROS_DISTRO=$ROS_DISTRO`
- `source /opt/ros/humble/setup.bash && ros2 pkg prefix nav2_amcl nav2_planner nav2_controller nav2_map_server`
- `apt-cache policy ros-humble-nav2-amcl ros-humble-nav2-planner ros-humble-nav2-controller ros-humble-nav2-map-server`
- `apt-get -s install ros-humble-nav2-amcl ros-humble-nav2-planner ros-humble-nav2-controller ros-humble-nav2-map-server`
- actual install output summary and post individual `ros2 pkg prefix`
- pre/install/post/final `lsof` and `fuser` for `/dev/ttyS5` and `/dev/ttyACM0`
- no-motion `POST /api/nav2/proof/refresh`
- no-motion `GET /api/nav2/proof/latest`
- no-motion `GET /api/nav2/status`

Local validation commands:

```bash
git diff --check
rg -n "nav2 package install|ros-humble-nav2-amcl|ros-humble-nav2-planner|ros-humble-nav2-controller|/api/nav2/proof/refresh|nav2_amcl_missing|map_server_lifecycle_not_active|publishes_cmd_vel|calls_base_manual|uses_base_uart|delivery_success|/dev/ttyS5" docs/hardware/board_sensor_stack_smoke.md docs/navigation/fixed_route_workflow.md sprints/2026.06.10_07-35_nav2_package_install_probe/tech-done.md
```

Local validation results:

- `git diff --check`: passed with no output.
- Required `rg`: passed; matches were found in `docs/hardware/board_sensor_stack_smoke.md`, `docs/navigation/fixed_route_workflow.md`, and this `tech-done.md`.

## Remaining Risks

- This sprint only removed the remote Nav2 package-missing blocker. It did not start Nav2 lifecycle nodes and did not prove AMCL/Nav2 runtime readiness.
- The remaining blocker has moved to lifecycle and topic observation: map server, AMCL, planner, and controller are not active; `/scan`, `/map`, and `/amcl_pose` were not observed in the collector graph.
- `map_inputs_ready_for_no_motion_nav2_collector` remains a precondition status only; it does not prove map quality, localization, path generation, fixed-route execution, HIL, safe-to-control, or delivery success.
- The exact multi-package `ros2 pkg prefix ...` command is not accepted by this ROS2 CLI; individual `ros2 pkg prefix <pkg>` checks were used to confirm package availability after recording the exact command failure.
