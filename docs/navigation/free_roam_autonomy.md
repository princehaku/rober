# Free Roam Autonomy

## 目标

`ros2_trashbot_nav.free_roam_autonomy` 是“像扫地机一样自由跑动建图”的上车端策略内核。它先定义安全状态机和 artifact 合同，再接 ROS2 发布链，避免 PC 按钮直接变成无限运动。

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

## 当前边界

当前实现是纯 Python 策略内核和 `free_roam_autonomy` 离线 console script，默认空输入会输出 `locked`。它不订阅 `/scan`、不订阅 `/map`、不发布 `/cmd_vel`，因此不会触发真实小车运动。

下一步接线顺序：

1. ROS2 节点订阅 `/scan` 和 `/map`，把实时雷达距离、free cell 增量和 unknown 占比写入 snapshot。
2. 接入停止服务或 `/trashbot/stop`，确保 `stop_required=true` 时真实发 stop。
3. 只在 HIL 低速验证通过后，才把 `FreeRoamDecision` 中的受限速度发布到 `/cmd_vel`。
4. 把每个 tick 的 decision 写入 artifact，并由上位机 summary 转成 PC 的 `free_roam_autonomy_gates`。
