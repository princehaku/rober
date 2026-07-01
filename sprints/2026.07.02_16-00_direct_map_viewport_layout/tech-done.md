# Direct Map Viewport Layout

## sprint_type

micro

## 实际改动

- 将 `/map` 直达地图页从“普通地图卡片放大”收敛为整屏 flex 地图布局：
  - `plain-map-panel` 在直达页使用 `width: 100vw`、`height: 100vh`、`overflow: hidden` 和纵向 flex。
  - 地图 viewport `flex: 1`，地图层 `height: 100%`，吃满标题/状态条之外的剩余高度。
  - 直达页不再套固定浮窗阴影，避免第一眼仍像普通面板。
- `/map` 直达页隐藏普通地图卡底部动作和说明：地图列表、重新建图、保存地图、普通说明、非地图卡片不再挤占地图画布。
- `/map` 直达页新增专用 `plain-map-direct-refresh` 只读按钮，固定调用 `/api/robot-control/map/preview` 并刷新雷达状态；按钮声明不启动 map runtime、Nav2、manual、keyboard、free-roam 或 `/cmd_vel`。
- 普通首页仍保留 `进入地图大屏` 入口；进入 `/map` 后不再重复显示这个入口，只保留缩放、只读刷新、雷达贴图刷新和 `ROS2观察`。
- summary 和 PC 文档同步更新“地图太小”的当前口径：普通用户优先 `/map`，ROS2 配套仍只是 RViz2 / Foxglove 工程观察，不替代 PC 简易界面。

## 验证结果

- `git diff --check`：通过。
- `npm test -- --run App.test.ts robotControlSummary.test.ts`：2 个测试文件、246 个用例通过。
- `npm test -- --run catalog.test.ts App.test.ts robotControlSummary.test.ts`：3 个测试文件、427 个用例通过。
- `npm run lint`：通过。
- `npm run build`：通过，Vite 仅保留既有大 chunk warning。
- PC Node 已重启到 `0.0.0.0:7001`，监听 PID `75192`。
- 真实 summary smoke：
  - `map_display_primary_url=/map`
  - `map_display_default_zoom_percent=1600%`
  - `map_display_max_zoom_percent=4800%`
  - `map_display_too_small_next_action_plain` 已说明 `/map` 只保留缩放、只读刷新和工程观察入口，并收起建图、保存和其它卡片。
  - `map_display_starts_ros2=false`
  - `map_display_starts_nav2=false`
  - `map_display_starts_map_runtime=false`
  - `live_wysiwyg_missing_surface_ids=["camera"]`
  - `radar_overlay_wysiwyg_complete=true`
  - `radar_map_points_visible=true`
- `GET http://127.0.0.1:7001/map` 返回 HTTP 200。
- 生产 CSS smoke 确认 dist 中包含直达页整屏规则：
  - `.shell[data-direct-map-view-requested=true] .plain-map-panel{display:flex; ... height:100vh ... overflow:hidden}`
  - `.plain-map-direct-refresh-action`
  - 直达页隐藏 `.panel-action-row` 和非工程观察说明。

## 剩余风险

- 本轮没有浏览器截图级自动化依赖，未输出像素截图；验证边界是 Vitest DOM、真实 7001 HTTP/API smoke 和生产 CSS 检查。
- 本轮没有安全确认，未执行任何 motion/control POST；Nav2 wheel raw L/R 非零、delivery success、PC 键盘连续手控和自由移动真实运动仍待现场安全确认后验收。
- 当前 WYSIWYG / 建图仍剩相机首帧缺口；需要现场处理 USB 12M full-speed、供电、线缆或 known-good UVC 后复测。
