# O3 No-Motion Nav2 Runtime Repair Tech Done

## sprint_type

sprint_type: epic

## 实际改动

- `onboard/scripts/o11_nav2_lifecycle.sh`
  - 修复 `start -> __run` 参数透传缺口，补传 `base_enabled`、`lidar_enabled`、LiDAR 串口/波特率和 `static_laser_tf_enabled`，避免 manager 子进程退回 launch 默认值。
- `onboard/scripts/upper_robot_api.py`
  - 修复 `/api/nav2/proof/refresh` 的 managed runtime readback 漂移；当 artifact 已记录 `managed_runtime_started=true` 时，响应同步回填 `starts_nav2=true`，同时保持 no-motion 安全字段全部为 false。
- `onboard/tests/test_upper_robot_api.py`
  - 新增默认 Nav2 start 命令关键 flag 回归测试。
  - 更新 managed no-motion refresh 回归，要求 `starts_nav2=true` 与 artifact 对齐。
- `docs/navigation/field_route_evidence_preflight.md`
  - 补充 `managed_runtime_started=true -> starts_nav2=true` 的 no-motion 边界说明。
- `docs/navigation/fixed_route_workflow.md`
  - 补充 `o11_nav2_lifecycle.sh` 子进程必须保留 runtime flags 的 runbook 约束。

## 验证结果

- `bash -n onboard/scripts/o11_nav2_lifecycle.sh`
  - 通过。
- `python3 -m py_compile onboard/scripts/upper_robot_api.py onboard/scripts/field_route_evidence_preflight.py`
  - 通过。
- `python3 -m unittest onboard.tests.test_upper_robot_api onboard.tests.test_field_route_evidence_preflight`
  - `Ran 123 tests in 0.276s`, `OK (skipped=1)`。
- `python3 -m unittest discover -s onboard/src/ros2_trashbot_bringup/test`
  - `Ran 23 tests in 0.045s`, `OK`。
- `python3 onboard/scripts/field_route_evidence_preflight.py --mode local --dry-run --output sprints/2026.07.11_07-38_o3_no_motion_nav2_runtime_repair/artifacts/local_preflight.raw.json`
  - 输出 `status=dry_run_template_only_not_proven`。
- `git diff --check -- onboard/scripts/o11_nav2_lifecycle.sh onboard/scripts/upper_robot_api.py onboard/tests/test_upper_robot_api.py onboard/src/ros2_trashbot_bringup/launch/autonomous.launch.py onboard/src/ros2_trashbot_bringup/test/test_launch_contract_static.py onboard/scripts/field_route_evidence_preflight.py onboard/tests/test_field_route_evidence_preflight.py docs/navigation/field_route_evidence_preflight.md docs/navigation/fixed_route_workflow.md sprints/2026.07.11_07-38_o3_no_motion_nav2_runtime_repair`
  - 通过。

## 真实板 artifact 摘要

- 已执行 no-motion `stop -> status -> start -> status -> refresh -> stop`，artifact 位于 `artifacts/`。
- 同步前：
  - `live_nav2_start.raw.json`
    - `command_result.ok=true`，`stdout_preview` 已显示 `base_enabled=auto`、`lidar_enabled=auto`、`lidar_serial_port=/dev/ttyACM0`、`static_laser_tf_enabled=true`，说明 `o11_nav2_lifecycle.sh` 的关键 runtime flag 已进入现场 start 回包。
  - `live_nav2_refresh.raw.json`
    - 顶层仍是旧板上进程逻辑产物：`status=blocked_with_root_cause`、`starts_ros2=true`、`starts_nav2=false`。
    - 但 `latest_result.proof.managed_runtime_started=true`、`managed_runtime_requested=true`，证明 helper 实际已经在 no-motion 边界内拉起过 managed runtime；这正是本轮修复的 readback 漂移。
- 已把本轮修改过的 `o11_nav2_lifecycle.sh` 与 `upper_robot_api.py` 同步到真实板，并重启 `trashbot-upper-robot-api.service`。
  - `live_nav2_start_after_sync.raw.json` 与 `live_nav2_status_after_sync_start.raw.json` 证明新命令配置已生效：`/api/nav2/status.commands.start.argv` 明确带 `--base-enabled auto --lidar-enabled auto --lidar-serial-port /dev/ttyACM0 --lidar-serial-baudrate 230400 --static-laser-tf-enabled true`。
  - `live_nav2_refresh_after_sync.raw.json` 已证明本地 readback 修复在板上生效：顶层 `starts_ros2=true`、`starts_nav2=true`、`managed_runtime_opt_in=true`，且 `latest_result.proof.managed_runtime_started=true`。
  - 同步后仍 fail-closed：`status=blocked_with_root_cause`、`path_generated=false`、`path_generation_succeeded=false`、`path_point_count=0`。
  - 同轮 root cause 保持在 AMCL/TF 层：
    - `AMCL localization: /amcl_pose_once_not_observed`
    - `Localization TF: map_to_odom_not_observed`
    - `Localization TF: map_to_base_link_blocked_by_missing_map_to_odom`
    - `helper_process_timeout_after_partial_artifact`
  - 安全字段仍固定 `safe_to_control=false`、`robot_control_executed=false`、`delivery_success=false`、`hil_pass=false`。
- `live_nav2_runtime_repair_after_sync.raw.json` 仍显示 SSH 预检层 `status=blocked_refresh_readback_failed`，`/map` 与 `/amcl_pose` topic metadata 仍不可用，`map->odom` / `map->base_link` 仍因 `map` frame 未建立而 blocked。这说明 API refresh 已能表达 `starts_nav2=true`，但 ROS graph / SSH smoke 仍未拿到 AMCL/TF 成功证据。

## OKR 结论

- 当前只做 O3 no-motion Nav2/map/AMCL runtime repair。
- 本轮新增真实板 repair evidence：`starts_nav2=true` readback 已在同步后 refresh 里成立，但 `path_generated=false`。
- 因此不调整 O1/O3/O5/O6/O7 百分比，不归档 KR。

## 剩余风险

- 本轮已经修掉两处软件漂移：
  - `o11_nav2_lifecycle.sh` 子进程不再丢失 runtime flags。
  - `upper_robot_api.py` 本地代码已把 `managed_runtime_started=true` 对齐到 `starts_nav2=true`。
- 同步后的真实板 refresh 已证明顶层 `starts_nav2=true` 生效，但仍没有 same-run path/material success。
- 板上当前真实 blocker 已从“runtime flag / readback 漂移”前移到 AMCL/TF：
  - `/amcl_pose` 未稳定观测；
  - `map->odom` 未建立；
  - `map->base_link` 被 `map->odom` 缺失级联阻塞。
- 本轮所有结论都必须保持 no-motion 边界：不发送 `/cmd_vel`、不调用 `/api/base/manual`、不执行 NavigateToPose goal。
