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

## 剩余风险

该 helper 只能过滤明显坏地图，不能评估回环漂移、动态障碍、局部规划可行性、
控制器跟踪误差或现场安全净空。低质量地图不得进入 O7 operator workflow 或 O2
电梯实景；通过 software guard 也只能作为真实 runtime 前的候选，不得作为 OKR
涨分证据。
