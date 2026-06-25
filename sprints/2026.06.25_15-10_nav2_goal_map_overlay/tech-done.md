# Nav2 Goal Map Overlay

sprint_type: micro

## 实际改动

- PC `GET /api/robot-control/nav2/goal/execution/latest` 的短摘要新增 `goal_frame_id`、`goal_x`、`goal_y`、`goal_yaw`、`result_timeout_s`，来源是上位机 latest artifact 的 `latest_result.goal_request`。
- 普通首屏地图视口新增最近 Nav2 目标点 overlay：只在真实地图预览已加载、goal frame 为 `map`、地图 metadata 完整时显示。
- 目标点按 YAML/PGM metadata 换算：`origin + resolution + width/height`，并把 ROS map y 轴翻转为浏览器图像坐标。
- UI 状态区分 `终点`、`历史目标`、`目标待复验`，避免把旧行程或不完整行程冒充本轮完整路线。
- 补充前端和 server 代理测试；同步更新 PC 产品文档和 fixed-route 工作流文档。

## 验证结果

- 已通过 targeted 测试：`npm test -- -t "Nav2 latest execution proxy|latest Nav2 goal|renders Robot Control V1"`。
- 已通过完整 `npm test`：2 个测试文件、154 个测试全部通过。
- 已通过 `npm run lint`。
- 已通过 `npm run build`。
- 已通过 `git diff --check`。
- 已重启 PC workstation 到 `0.0.0.0:7001` 并做真实只读 API 验证：latest Nav2 goal 返回 `goal_succeeded`、`goal_frame_id=map`、`goal_x=0.8`、`goal_y=0`、`feedback_sample_count=8`，同时 `safe_to_control=false`、`delivery_success=false`、`robot_control_executed=false`。
- 已做真实浏览器 DOM 验证：普通首屏地图 PNG 已加载，`plain-map-route-goal-marker` 存在，文本为 `历史目标`，aria 为 `历史目标，地图坐标 x=0.80, y=0.00`，样式位置约 `left: 54.09%; top: 92.84%`；因为真实 latest 是旧记录，UI 没把它标成本轮目标。

## 剩余风险

- 当前只画最近 goal target，不画完整 path/trajectory；完整路径线需要上位机 latest artifact 暴露路径点或轨迹点。
- 本轮没有触发 Nav2 execute、delivery complete、manual、keyboard、stop、radar start、map start 或 `/cmd_vel`。
