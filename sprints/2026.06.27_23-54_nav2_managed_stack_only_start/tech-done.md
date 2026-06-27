# Nav2 受管 stack-only 启动入口

## sprint_type

micro

## 实际改动

- `onboard/src/ros2_trashbot_bringup/launch/autonomous.launch.py`
  - 新增 `nav2_stack_only` 参数，默认 `false`。
  - `nav2_stack_only=true` 时只保留 ESP32 bridge 与 Nav2 bringup；跳过 `waypoint_manager`、`nav_to_goal`、`task_orchestrator`、`fixed_route_autonomy`、operator gateway 和 remote bridge，避免 Nav2 runtime 恢复动作顺手启动巡逻/任务节点。
- `onboard/scripts/o11_nav2_lifecycle.sh`
  - 新增受管 Nav2 lifecycle 脚本，支持 `start|stop|status`。
  - `start` 固定使用 `autonomous.launch.py nav2_stack_only:=true`，默认地图 `/root/rober/onboard/runtime/maps/trashbot_map.yaml`，默认现场 WAVE ROVER UART `/dev/ttyS5@115200`，默认 `command_mode=ros`。
  - 脚本状态明确写入 vendor 来源：`docs/vendor/VENDOR_INDEX.md`、`docs/vendor/waveshare_wave_rover/ugv_rpi/base_ctrl.py`、`docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/json_cmd.h`。
- `onboard/scripts/upper_robot_api.py`
  - `/api/nav2/start|stop` 默认不再是 dry-run stub，改为默认受管 `o11_nav2_lifecycle.sh`。
  - 新增 Nav2 lifecycle 命令白名单校验，拒绝 shell 拼接、直接 `/cmd_vel`、直接 `NavigateToPose`、底盘 JSON token 和非预期底盘串口。
- `onboard/tests/test_upper_robot_api.py`
  - 覆盖默认 Nav2 start/stop 配置、默认 start 调用、危险命令拒绝和 unmanaged `ros2 launch` 字符串拒绝。
- `onboard/src/ros2_trashbot_bringup/test/test_launch_contract_static.py`
  - 覆盖 `nav2_stack_only` 参数和业务导航节点必须受 condition 保护。
- `docs/navigation/field_route_evidence_preflight.md`
  - 记录真实上位机只读根因：`ROBER_NAV2_START_COMMAND` 未配置、planner/controller inactive。
- `docs/product/pc_tools_workstation.md`
  - 记录 PC 普通首屏 Nav2 恢复动作的新边界。

## 验证结果

- SSH 只读复核 `root@192.168.1.11:37878`
  - 当前 `pgrep` 只看到 free-roam 节点和 `upper_robot_api`，未看到完整 autonomous/Nav2 launch。
  - `/api/nav2/status` 显示 `commands.start.configured=false`、`planner_server_active=false`、`controller_server_active=false`。
  - `/api/robot-control/summary` 显示 Nav2 blockers 包含 `planner_server_inactive`、`controller_server_inactive`。
- 上车部署复核
  - 已 scp `upper_robot_api.py`、`o11_nav2_lifecycle.sh` 与 `autonomous.launch.py` 到 `/root/rober/onboard`。
  - 已按原参数重启 `upper_robot_api`，新 PID 为 `275495`。
  - 部署后 `/api/nav2/status` 显示 `commands.start.configured=true`，argv 为受管
    `bash /root/rober/onboard/scripts/o11_nav2_lifecycle.sh start --map-file /root/rober/onboard/runtime/maps/trashbot_map.yaml --base-port /dev/ttyS5 --base-baudrate 115200 --command-mode ros`。
  - `o11_nav2_lifecycle.sh status` 显示 `state=stopped`、`motion_requires_explicit_goal_execute=true`、
    `sends_base_motion_commands=false`、`safe_to_control=false`。
- `bash -n onboard/scripts/o11_nav2_lifecycle.sh`
  - 通过。
- `python3 -m py_compile onboard/scripts/upper_robot_api.py`
  - 通过。
- `python3 -m unittest onboard.tests.test_upper_robot_api -k nav2`
  - 通过：9 tests。
- `python3 -m unittest onboard.src.ros2_trashbot_bringup.test.test_launch_contract_static.LaunchContractStaticTest`
  - 通过：19 tests。
- `python3 -m unittest onboard.tests.test_upper_robot_api`
  - 通过：69 tests。
- `npm test -- --maxWorkers=1 --no-fileParallelism`
  - 通过：2 test files，318 tests。
- `npm run lint`
  - 通过。
- `npm run build`
  - 通过；Vite 仍提示主 chunk 超过 500 kB，这是既有体积提示。
- `bash onboard/scripts/docker_humble_build.sh`
  - 通过：`Summary: 6 packages finished [43.5s]`。

## 剩余风险

- 本轮没有执行 `/api/nav2/start`，没有启动上车 Nav2 runtime，也没有发送 `NavigateToPose`、`/cmd_vel`、manual、keyboard、free-roam 或 delivery 命令。
- 真实自动驾驶仍需要现场显式执行顺序：部署新脚本/API、重启 upper API、点击或调用固定 `/api/nav2/start`、刷新 Nav2 proof，确认 planner/controller active、AMCL pose、path points，再在安全确认后执行路线。
- 当前 live summary 仍显示相机无首帧、雷达 runtime stale、地图位姿缺失；这些不会阻止受管 Nav2 start，但会继续影响建图验收和完整路线证明。
