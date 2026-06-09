# Nav2 lifecycle activation probe

## sprint_type

micro

## 实际改动

- 新增本轮远端证据目录：
  `sprints/2026.06.10_08-15_nav2_lifecycle_activation_probe/artifacts/remote_capture/`。
- 新增远端执行脚本 artifact：
  `artifacts/remote_capture/run_nav2_lifecycle_activation_probe.sh`。
- 拉回最终远端 runtime 包：
  `artifacts/remote_capture/20260610_0815_nav2_lifecycle_activation_probe.tgz`。
- 拉回最终解包目录：
  `artifacts/remote_capture/rober_20260610_0815_nav2_lifecycle_activation_probe/`。
- 同步更新：
  - `docs/hardware/board_sensor_stack_smoke.md`
  - `docs/navigation/fixed_route_workflow.md`

本轮未改产品代码、launch、硬件参数或 firmware。

## 远端环境与包证据

远端 `root@192.168.1.11:37878` 可达：

- `hostname=op-z3-b6.home`
- 远端时间：`Wed Jun 10 05:39:03 AM CST 2026`
- kernel：`Linux op-z3-b6.home 6.1.31-sun50iw9 ... aarch64`

`ros2 pkg prefix` 安装后结果：

```text
nav2_lifecycle_manager /opt/ros/humble
nav2_navfn_planner /opt/ros/humble
nav2_regulated_pure_pursuit_controller /opt/ros/humble
nav2_amcl /opt/ros/humble
nav2_planner /opt/ros/humble
nav2_controller /opt/ros/humble
nav2_map_server /opt/ros/humble
```

窄包 dry-run：

```text
The following NEW packages will be installed:
  ros-humble-diagnostic-updater ros-humble-nav2-lifecycle-manager
  ros-humble-nav2-navfn-planner
  ros-humble-nav2-regulated-pure-pursuit-controller
0 upgraded, 4 newly installed, 0 to remove and 322 not upgraded.
```

实际安装：

```text
Setting up ros-humble-nav2-regulated-pure-pursuit-controller ...
Setting up ros-humble-diagnostic-updater ...
Setting up ros-humble-nav2-navfn-planner ...
Setting up ros-humble-nav2-lifecycle-manager ...
```

安装符合本轮边界：只新增 4 个包，未升级、未卸载系统包。

## lifecycle activation 结果

手动 no-motion runtime 使用：

- LiDAR `/dev/ttyACM0 @ 150000`
- static TF `base_link -> laser_frame`
- static TF `odom -> base_link`
- direct `map_server`、`amcl`、`planner_server`、`controller_server`
- `nav2_lifecycle_manager` autostart

手动状态快照：

```text
/map_server active [3]
/amcl active [3]
/controller_server inactive [2]
/global_costmap/global_costmap activating [13]
/local_costmap/local_costmap inactive [2]
```

关键日志：

- `map_server` 成功读取 `/root/rober/onboard/runtime/maps/trashbot_map.yaml`
  和 `trashbot_map.pgm`，并进入 `Activating`。
- `amcl` 进入 active，但持续输出：
  `AMCL cannot publish a pose or update the transform. Please set the initial pose...`
- `planner_server` 卡在 global costmap activation，日志持续输出：
  `Timed out waiting for transform from base_link to map ... frame_id "map" ... does not exist`
- `controller_server` 已加载
  `nav2_regulated_pure_pursuit_controller::RegulatedPurePursuitController`，
  但未 active。

结论：新增窄包消除了插件/manager 缺失层，但 no-motion 手动激活仍未达到完整
Nav2 ready。当前新 blocker 是：本轮安全边界禁止 `/initialpose`，所以 AMCL 不发布
`map -> odom`；planner global costmap 因缺 `map -> base_link` transform 卡在
activation。

## topic 与 /cmd_vel 证据

手动 runtime 窗口：

- `/scan`：`scan_rc=0`，`manual_scan_once_after_hang.log` 有 LaserScan 样本。
- `/map`：`map_rc=124`，8 秒未收到一次样本。
- `/amcl_pose`：`amcl_rc=124`，8 秒未收到一次样本。
- `/cmd_vel`：topic 出现，publisher 是 `controller_server`，但
  `manual_cmd_vel_echo_after_hang.log` 8 秒超时无消息，`cmd_echo_rc=124`。

`/cmd_vel` 结论：本轮没有发布任何 `/cmd_vel` 消息；controller server 只创建了
publisher。未调用 `ros2 action send_goal`、compute path service、`/initialpose`、
`/api/base/*`、`/api/map/start`、`/api/nav2/start` 或 `/api/nav2/stop`。

## formal API collector 结果

正式调用：

```bash
curl --max-time 150 -sS -X POST http://127.0.0.1:8787/api/nav2/proof/refresh \
  -H 'Content-Type: application/json' \
  -d '{"timeout_s":20}'
curl --max-time 30 -sS http://127.0.0.1:8787/api/nav2/proof/latest
curl --max-time 30 -sS http://127.0.0.1:8787/api/nav2/status
```

`POST /api/nav2/proof/refresh` 返回：

- `status=blocked_with_root_cause`
- `failure_reason=configured_command_failed`
- helper `returncode=2`
- `map_server_active=false`
- `amcl_active=false`
- `planner_active=false`
- `controller_active=false`
- `scan_once_observed=false`
- `map_once_observed=false`
- `amcl_pose_observed=false`
- `path_generation_ready=false`
- `publishes_cmd_vel=false`
- `calls_base_manual=false`
- `uses_base_uart=false`
- `delivery_success=false`

`GET /api/nav2/proof/latest` 和 `GET /api/nav2/status` 均返回 HTTP 200，并读取同一
canonical artifact：
`/root/rober/onboard/runtime/nav2_lifecycle_latest.json`。

注意：formal collector 是 read-only existing ROS graph collector，不负责启动本轮
手动 stack。清场后调用它时没有 `/scan` 或 Nav2 lifecycle nodes，所以 canonical
artifact 仍记录 `*_active=false` 与 `/scan_once_not_observed`。手动 stack 证据与
formal API canonical readback 必须分开解释。

## 清理结果

本轮强制清理两个本轮 PGID：

- `129122`：手动 stack PGID。
- `129080`：runner 主 PGID，曾卡在 `ros2 lifecycle get /planner_server`。

最终清场：

```text
### final process check after forced cleanup
2026-06-10T05:51:02+08:00
### final lsof
### final fuser
```

`/dev/ttyS5` 与 `/dev/ttyACM0` final `lsof/fuser` 均无输出。本轮没有打开
WAVE ROVER/base UART `/dev/ttyS5`；`/dev/ttyACM0` 只在手动 LiDAR runtime 窗口
被 `lidar_driver` 占用，结束后释放。

## 验证结果

- 远端环境、ROS graph、serial occupancy 已记录。
- 窄包 dry-run 与实际安装已记录，未升级/卸载。
- no-motion manual lifecycle runtime 已启动并定位 root cause。
- `/scan` 在手动 runtime 中观测成功。
- `/map`、`/amcl_pose` 未观测。
- `/cmd_vel` 无消息；未调用任何 motion/action/path/initialpose 禁止项。
- formal API collector 已调用，canonical 状态仍 blocked。
- 本轮 PGID 与串口占用已清理。
- 本地 `git diff --check` 已通过。

## 剩余风险

- `map_server_active=true` 与 `amcl_active=true` 只在手动 runtime 窗口成立；
  canonical `/api/nav2/proof/latest` 仍是 blocked。
- `planner_server` activation 被 global costmap 等待 `map -> base_link` 卡住；
  根因是 AMCL 未获得 initial pose，不能发布 localization transform。
- 本轮按安全边界禁止 `/initialpose`，因此 `/amcl_pose` 未观测是预期 blocker，
  不能声明 localization 或 Nav2 ready。
- 现场 ROS graph 仍有多组历史 `map_recorder`、`task_orchestrator`、
  `waypoint_manager` 重名节点；本轮未清理非本轮进程。
- 未证明 path generation、fixed-route execution、controller output、
  physical motion、safe_to_control 或 delivery_success。
