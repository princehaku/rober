# Free Roam Autonomy

## 目标

`ros2_trashbot_nav.free_roam_autonomy` 是“像扫地机一样自由跑动建图”的上车端策略内核。`ros2_trashbot_nav.free_roam_autonomy_node` 负责把 ROS2 `/scan`、`/map` 和停止兜底接到该策略，并写出 runtime artifact。

## 输入

- `operator_confirmed`：现场人员已确认人在旁边、周围安全、停止手段就绪。
- `mapping_active`：扫地式建图记录已经启动。
- `stop_available`：停止按钮或上车停止服务可用。
- `lidar_min_distance_m`、`lidar_age_s`：实时雷达最近障碍距离和数据新鲜度。
- `map_free_cells`、`map_unknown_ratio`：地图覆盖增长和未知区域比例。
- `elapsed_s`：本轮自动扫图运行时间。
- `external_stop_requested`：现场或上层请求停止。

## 输出

策略输出 `trashbot.free_roam_autonomy.decision.v1`：

- `state=locked`：任一必需安全门禁缺失，线速度和角速度都为 0。
- `state=running`：所有必需门禁通过，输出受限低速直行。
- `state=avoiding`：雷达看到近距离障碍，线速度为 0，只允许原地换向。
- `state=turning_for_coverage`：地图 free cell 长时间没有增长，线速度为 0，原地扫描找新方向。
- `state=completed`：达到最长运行时间或 unknown 占比低于目标，输出停止。
- `stop_required=true`：上层必须执行停止兜底，不能继续沿用旧速度。

## ROS2 节点

`free_roam_autonomy_node` 当前已完成以下接线：

- 订阅 `/scan`，只接受有限正数距离，计算最近障碍距离和数据年龄。
- 订阅 `/map`，统计 free、unknown、occupied 和 unknown ratio。
- 每个 tick 生成 `FreeRoamSnapshot`，调用策略内核并写出 `trashbot.free_roam_autonomy.runtime.v1` artifact。
- 当 `decision.stop_required=true` 且停止服务可用时，调用 `/trashbot/stop` 兜底。
- 默认 `enable_cmd_vel_publish=false` 且 `motion_hil_unlocked=false`，不会发布 `/cmd_vel`。
- 上位机 `GET /api/free-roam/autonomy/latest` 只读该 artifact，`GET /api/status` 同步提供 `free_roam_autonomy` 摘要。
- PC `GET /api/robot-control/summary` 会消费该摘要并把 `decision.gates` 显示到“自动扫图准备”门禁，同时把
  `decision.state/reason/stop_required` 压缩为 `safe_command_boundary.free_roam_autonomy_runtime`，让首屏显示
  上车端状态机当前是锁定、直行判断、避障换向、补覆盖、停止中还是完成。
- 2026-06-30 20:36 CST 起，`GET /api/free-roam/autonomy/latest` 必须保持 artifact-only：只读取
  `free_roam_autonomy_latest.json`、已落盘 LiDAR scan proof 和 runtime snapshot，不再同步调用相机
  `/health` 或完整 `radar_status()`。相机 readiness 在该入口中保守标为
  `deferred_to_camera_health_endpoint`，因此不会误放开建图；PC summary 需要完整建图 ready 时，应继续
  合并独立相机、雷达和地图 preview 只读端点。这个边界避免 8787 latest 在相机 HTTP、雷达 lifecycle
  或并发 summary 慢读时卡住，同时不改变自由移动的安全确认门禁。
- 同一轮起，8787 的常用只读同步 handler（radar/base/map/Nav2/free-roam latest/status、delivery latest 等）
  必须通过线程隔离执行，避免 PC summary 并发读取多个端点时某个慢文件或状态读取阻塞 aiohttp 事件循环。
  这只改变 HTTP 并发稳定性，不启动 ROS2 runtime、不打开底盘串口、不发送 `/cmd_vel`。

## 当前边界

`free_roam_autonomy` 离线 console script 默认空输入会输出 `locked`。`free_roam_autonomy_node` 默认 artifact-only，不发布 `/cmd_vel`；即使策略输出 `running`，也必须同时设置 `enable_cmd_vel_publish=true` 和 `motion_hil_unlocked=true` 才会发布受限 Twist。该双参数门禁用于防止单个误配参数让真车运动。

下一步接线顺序：

1. 在真实小车低速 HIL 中验证 stop fallback 响应时间、雷达避障换向和地图覆盖增长。
2. HIL 通过后，才允许用双参数显式解锁 `/cmd_vel` 发布。
3. 把每个 tick 的 decision、传感器摘要和 stop 响应写入验收 artifact。

## 2026-06-26 PC 启动门禁口径

PC `GET /api/robot-control/summary` 中的 `free_roam_autonomy_start_ready` 只表示“基础自助移动入口可以引导 operator 开始”，不等同于完整自动扫图 ready。该字段现在只要求上车 free-roam runtime 已加载且 `stop_available` gate 为 ready；`lidar_fresh`、`obstacle_clear` 和 `motion_hil_unlock` 继续显示在门禁列表中，但不再阻塞基础启动提示。

完整自动扫图仍必须满足上车端双参数 `enable_cmd_vel_publish=true` 与 `motion_hil_unlocked=true`，并且雷达避障、地图覆盖、停止兜底和真车 HIL 证据齐全后，`free_roam_autonomy` 才能从 `locked` 提升为 `ready`。当前真实上位机读回仍是 `artifact_only=true`、`cmd_vel_publish_enabled=false`，所以这次调整不会让 PC summary 直接发车或发布 `/cmd_vel`。

## 2026-06-26 PC 建图入口传感器口径

PC 普通首屏把“基础自助移动可引导”和“开始扫地式建图记录”分开处理。`free_roam_autonomy_start_ready`
可以在雷达 proof 不 fresh 时继续引导 operator 处理基础自移动准备；但 `扫地式建图` 的 `开始扫地式建图`
按钮必须同时看到相机源首帧 ready 和雷达卡片 `雷达已运行`。相机失败时只引导 `检查画面`，雷达 stale/incomplete
时只引导 `刷新雷达`，都不会调用 map start、manual、keyboard pulse、Nav2、delivery、stop 或 `/cmd_vel`。

这个口径保持“车能不能低速手控”不依赖雷达；低速键盘手控仍使用自己的安全确认和 stop 兜底。建图记录之所以要求相机和雷达
ready，是为了保证 operator 开始记录时能看到实时画面和实时雷达点，不把 stale artifact 当成可用于建图的现场状态。

2026-06-27 14:50 起，PC 普通首屏进一步把建图操作卡的标题和状态文案也按这个口径拆开：当相机或雷达未 ready、
且地图记录未启动时，卡片显示 `自由移动 / 建图` 与 `自由移动状态`，说明低速自移动不依赖雷达新鲜度；
只有传感器与地图记录满足建图验收链路时，才使用扫地式建图文案。该调整不改变上车 runtime 参数，也不自动发布 `/cmd_vel`。

2026-06-29 17:50 起，PC summary 会把 `external_stop_requested=true` 单独显示为 `external_stop_request`
运行诊断门禁，下一步写明勾选现场安全确认后点击开始自由移动会先清除停止请求。这个状态不是雷达 blocker；
`lidar_fresh` 仍只属于建图验收材料，雷达过期时也只能说明不能按完整建图验收，不能反向写成“小车不能低速自由移动”。
策略内核的 `mapping_active` gate 文案也同步说明：地图记录未启动只影响建图记录，不影响现场监看的低速自由移动。
