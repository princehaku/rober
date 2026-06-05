# Nav2 Map Quality Metrics

## 目标和边界

本页记录 O3 Nav2/map quality 的 ROS-free 离线评估入口。它只读取 map
YAML、PGM 和 waypoint JSON，用于在真实 Nav2/AMCL/SLAM runtime 前筛掉明显
不可用的地图候选；它不连接 ROS graph，不启动 Nav2，不证明真实 `/map`、
`/amcl_pose`、TF、`/scan` 消费、固定路线实跑或 waypoint 真实可达。

实现入口：

```bash
PYTHONPATH=onboard/src/ros2_trashbot_nav \
python3 -m ros2_trashbot_nav.map_quality_metrics \
  <map.yaml> \
  --waypoints <waypoints.json>
```

真实 map artifact 切换时，只需要把 `<map.yaml>` 换成 SLAM/map_server 保存的
真实 YAML，把 `<waypoints.json>` 换成同一 `map` frame 下的候选路线点。工具会
从 YAML 的 `image` 字段解析相对或绝对 PGM 路径，并检查 resolution、origin、
YAML/image 一致性、coverage、unknown ratio 和 waypoint cell 状态。

## 输出字段

`map_quality_metrics.py` 输出 `trashbot.nav2_map_quality.v1`：

- `metrics`: `coverage_area_m2`、`explored_area_m2`、`free_ratio`、
  `occupied_ratio`、`unknown_ratio`。
- `save_load_consistency`: YAML、image、resolution、origin 和尺寸是否可离线加载。
- `waypoint_reachability`: 每个 waypoint 落在 `free`、`occupied`、`unknown`、
  `out_of_bounds` 或 `frame_mismatch`。
- `quality_gates.software_guard_pass`: coverage、unknown ratio 和 reachable waypoint
  ratio 的离线门槛。
- `failure_samples`: 可以直接给 operator/debug 页展示的失败原因。
- `not_proven`: 固定保留真实 SLAM、AMCL、Nav2 消费、路线实跑和真实 waypoint
  可达未证明项。

## O10 AMCL/Nav2 readiness 输入护栏

`GET /api/nav2/status` 现在会从 canonical map lifecycle latest 只读折算
`amcl_nav2_readiness`：

- latest JSON 固定读取 `/root/rober/onboard/runtime/map_lifecycle_latest.json`。
- map artifact 目录固定按 `/root/rober/onboard/runtime/maps` 校验。
- 只有 latest 载入成功、`proof.status=map_once_artifact_metadata_observed`、
  `map_once_observed=true`、map metadata 存在，并且 proof 中同时列出 YAML 和 PGM
  时，状态才会变为 `map_inputs_ready_for_no_motion_nav2_collector`。
- 失败时状态为 `blocked_with_root_cause`，root cause 会落到 latest 缺失、proof
  不干净、canonical map 目录漂移、YAML 缺失、PGM 缺失或 metadata 缺失等输入层。
- 该字段的 `evidence_type=software_guard`，可以保留上游
  `source_evidence_type=robot_runtime_material`，但不把地图 artifact 外推成 AMCL、
  Nav2、路径生成或 fixed-route 已证明。

该护栏只做 readback 和输入归一化：不启动 ROS2，不发布 `/cmd_vel`，不调用
`/api/base/manual`，不打开底盘 UART。输入齐备后，下一步仍需单独采集 map
quality、AMCL `/initialpose`/`/amcl_pose`、map server、planner/controller
lifecycle 和 `/scan` + map 消费材料。

## Fixture 复跑

当前可复跑 fixture：

```bash
PYTHONPATH=onboard/src/ros2_trashbot_nav \
python3 -m ros2_trashbot_nav.map_quality_metrics \
  pc-tools/evidence/fixtures/nav2_map_quality_offline_eval/map.yaml \
  --waypoints pc-tools/evidence/fixtures/nav2_map_quality_offline_eval/waypoints.json
```

该 fixture 的预期退出码是 `1`。这不是命令崩溃，而是刻意让 waypoint
reachability gate fail-closed：4 个 waypoint 中只有 1 个落在 free cell，另外 3
个分别覆盖 occupied、unknown 和 out_of_bounds。复跑时应核对：

- `schema=trashbot.nav2_map_quality.v1`。
- `quality_gates.software_guard_pass=false`。
- `waypoint_reachability.summary.reachable_ratio=0.25`。
- `failure_samples` 包含 occupied、unknown 和 out_of_bounds。
- `proof_status=not_proven`，不把 fixture 解释成真实 Nav2 runtime。

fixture summary 文件
`pc-tools/evidence/fixtures/nav2_map_quality_offline_eval/software_guard_summary.json`
已显式记录 `expected_exit_code=1`，方便 evidence runner 区分 fail-closed 证据和
脚本异常。

## 进入真实地图评估的最低要求

真实 map artifact 进入 operator workflow 或 O2 电梯现场前，至少需要：

- map YAML 和 image 可加载，resolution 为正，origin 可解析。
- unknown/ambiguous ratio 低于当前阈值，且覆盖面积满足当前路线候选。
- waypoint 均使用 `frame_id=map`，不能混用 odom/base_link/camera frame。
- 关键 waypoint 的 reachable ratio 达标；occupied、unknown、out_of_bounds 必须
  输出失败原因并阻止进入实跑候选。
- 仍需另行采集 ROS2 runtime 证据：SLAM `/map`、map file、AMCL pose、TF
  freshness、Nav2 lifecycle 和 `/scan` + map 消费。

## 2026-06-05 O9 map lifecycle runtime root cause

Robot Software Engineer 通过上位机
`ssh root@192.168.1.11 -p 37878` 只读复核 SLAM/map lifecycle。指定验收命令
中远端默认 shell 是 `zsh`，直接 `source /opt/ros/humble/setup.bash` 会出现
`BASH_SOURCE[0]: parameter not set`、`AMENT_TRACE_SETUP_FILES: parameter not set`，
并导致后续 `ros2` 不进 PATH；复核命令必须用 `bash -lc` 且不要启用
`set -u` 后再 source ROS2。

修正 shell 后，现场 root cause 已收敛：

- `ros2 topic list` 只有 `/parameter_events` 和 `/rosout`，没有 `/map`、`/scan`、
  `/lidar/raw_packet`、`/tf_static`、AMCL 或 Nav2 runtime topic。
- `GET /api/map/proof/latest` 返回 HTTP 404 但带结构化 JSON，artifact 状态为
  `missing`；canonical latest JSON 路径锁定为
  `/root/rober/onboard/runtime/map_lifecycle_latest.json`，旧
  `/root/rober/runtime/map_lifecycle_latest.json` 只能作为 legacy path 审计，不再作为
  latest readback 的事实来源。
- `/root/rober/onboard/runtime` 和 `/root/rober/onboard/runtime/maps` 均不存在，
  `/api/map/list` 因此返回 `failure_reason=map_artifact_dir_missing`。
- 进程列表只看到 `upper_robot_api.py`，没有 `slam_toolbox`、`map_server`、
  `nav2` 或常驻 `lidar` 进程。

本轮结论：当前只证明 API-managed 短窗口 fresh LiDAR proof，不证明 SLAM
`/map`、map artifact、AMCL、Nav2 或 continuous radar。下一步最小命令应先启动
no-motion learning/SLAM runtime，并在同一窗口采集 `/map` once 与地图 artifact；
在获得现场安全授权前不得运行 `/cmd_vel`、`/api/base/manual` 或任何底盘控制。

### Map lifecycle proof refresh route

`POST /api/map/proof/refresh` 是本轮新增的 no-motion map lifecycle proof 入口。
它调用 `onboard/scripts/o3_map_lifecycle_proof.py`，目标是在同一窗口内启动
`learn.launch.py lidar_enabled:=true`，观察 `/scan` once、`/map` once，调用
`/trashbot/save_map`，并把 `runtime/maps` 下的 YAML/PGM 和最小 map metadata 写入
`/root/rober/onboard/runtime/map_lifecycle_latest.json`。`GET /api/map/proof/latest`
只读回放该 canonical JSON，不会启动 ROS2、SLAM 或任何硬件；如果现场仍残留
`/root/rober/runtime/map_lifecycle_latest.json`，只能说明旧契约曾经写入过 legacy
位置，不能覆盖 canonical latest。

失败时 helper 必须写入 `blocked_with_root_cause`，并在 `proof.root_causes` 中区分
`ROS install/source`、`LiDAR/launch/topic remap`、`SLAM/TF/topic remap`、
`map saver`、`file path/permissions` 等层。2026-06-05 09:33 CST 远端收口后，
`slam_toolbox` 已安装，helper 已在 no-motion 窗口观察到 `/scan` once、`/map`
once 和 map metadata，并且 `/trashbot/save_map` 返回
`success=True, message='Map saved to runtime/maps/trashbot_map.pgm'`。命令末尾
`find /root/rober/onboard/runtime` 已确认 `trashbot_map.pgm` 与
`trashbot_map.yaml` 存在。

本轮同步修正 helper 对 `runtime/maps` 的相对路径枚举：文件检查按 onboard workdir
解析，避免 systemd/current-working-directory 不同导致已保存地图被误判为
`map_save_reported_success_but_no_artifact_files_found`。该修正只改 artifact
列举边界，不改变 no-motion 安全口径。

该 route/helper 的证据边界固定为 no-motion：不发布 `/cmd_vel`，不调用
`/api/base/manual`，不写 WAVE ROVER 底盘 UART，且所有 payload 必须保持
`safe_to_control=false`、`sends_base_motion_commands=false`、
`robot_control_executed=false`。即使后续出现 `/map` once 和 map artifact，也仍需
另行验证 map quality、AMCL、Nav2 lifecycle、路径生成和现场安全净空，不能把本
route 的结果写成地图可导航或 fixed-route 可跑。

## 剩余风险

该 helper 只能过滤明显坏地图，不能评估回环漂移、动态障碍、局部规划可行性、
控制器跟踪误差或现场安全净空。低质量地图不得进入 O7 operator workflow 或 O2
电梯实景；通过 software guard 也只能作为真实 runtime 前的候选，不得作为 OKR
涨分证据。
