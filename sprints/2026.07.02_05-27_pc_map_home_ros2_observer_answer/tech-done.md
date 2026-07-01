# PC 地图首页放大与 ROS2 观察回答

sprint_type: micro

## 实际改动

- 调整 PC 普通首页地图布局：页面宽度放宽到 `min(2800px, 100%)`，普通大地图默认高度和 large 模式高度上调，避免地图继续像小卡片。
- 地图标题新增短回答：`普通看 /map；工程看 RViz2 / Foxglove`，并同步 summary 文案，明确 PC 首页和 `/map` 都是普通用户主地图视图。
- 保持 ROS2 配套分层：RViz2 用于本地工程调试，Foxglove bridge + Foxglove Web 用于远程浏览器观察；这些入口只观察 `/map`、`/scan`、TF、路径、定位和 costmap，不启动 ROS2/RViz2/Foxglove/Nav2/建图 runtime，也不发送任何运动指令。
- 同步更新 `docs/product/pc_tools_workstation.md` 和前端/summary 测试断言。

## 验证结果

- `npm test -- --run App.test.ts robotControlSummary.test.ts catalog.test.ts`：通过，3 files / 428 tests passed。
- `npm run lint`：通过。
- `npm run build`：通过；Vite 仅保留既有 chunk size warning。
- `git diff --check`：通过。
- 已重启 PC Node，监听 `0.0.0.0:7001`。
- no-motion summary smoke：`map_display_primary_url=/map`，`map_display_too_small_next_action_plain` 已说明 PC 首页和 `/map` 都是主地图视图；`map_display_starts_ros2=false`、`map_display_starts_rviz2=false`、`map_display_starts_foxglove=false`、`map_display_starts_nav2=false`、`map_display_starts_map_runtime=false`、`map_display_sends_motion_when_clicked=false`。
- Chrome DOM smoke：PC 首页地图层 `1680px`，标题为 `PC 大地图 1600% · /map 满屏 · 普通看 /map；工程看 RViz2 / Foxglove`；`/map` 直达页地图层 `812px`，非地图卡片已隐藏，`刷新地图画面` 与 `ROS2观察` 均标记不发车、不启动 ROS2/RViz2/Foxglove。

## 剩余风险

- 本轮只做 PC 地图显示和 ROS2 观察入口说明，不执行运动，不验证 wheel raw L/R、Nav2 route execution、delivery success、键盘连续手控真实运动。
- 真实 smoke 中当前地图状态仍可能显示 `地图未读取`，这表示当前上位机地图读回事实，不影响本轮布局和 ROS2 观察入口验证。
