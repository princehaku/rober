# O6/O7 Route Bag Pose Progress Replay PRD

## 用户问题

运营人员已经能看到 route bag 的 topic、payload hash 和白名单 ROS 语义摘要，但还无法从同一任务材料里判断“这段 DB3 是否包含可用于路线回放的位姿进度”。当前下一步判断仍停留在泛化的 `live_nav2_pose_progress` 缺口，缺少可读的 pose progress software proof。

## 用户价值

本轮让 PC/O7 和 O6 consumer detail 在同一 `task_id` 下显示：

- pose source：来自 `/tf`、`/tf_static` 或未来 `/odom` 的白名单位姿摘要。
- sample count、timestamp span、frame pair。
- 起点、终点、位移距离和是否观察到非零位移。
- 为什么仍不能判定 live Nav2 run 或 delivery success。

这让下一轮能更明确地选择：补真实 live Nav2 log、补 odom/TF 采样、补 delivery result，还是修 route bag 采集质量。

## 范围

本轮做：

- 新增 `route_bag_pose_progress_replay` 软件证据合同。
- 接入 Algorithm manifest / O6 archive / O7 consumer display。
- 补测试、文档和 sprint 留档。

本轮不做：

- 不启动 ROS2/Nav2 runtime。
- 不发 `/cmd_vel`，不做底盘控制。
- 不接真实 production cloud、4G、TLS、OSS/CDN。
- 不宣称 delivery success 或 route execution success。

## OKR 对齐

- O6 KR2 / KR6：任务和感知/路线证据存档、consumer read API 增强。
- O7 KR3 / KR4：历史路线回放和标注工作台获得位姿进度上下文。

本轮仍不归档 KR，除非出现超出预期的真实生产或真实现场材料证据。

## 成功标准

- 三个 owner 的验证命令全部通过。
- `OKR.md` 和 `docs/process/okr_progress_log.md` 更新证据边界。
- `tech-done.md`、`side2side_check.md`、`final.md` 记录实际改动、验证结果、剩余风险。
