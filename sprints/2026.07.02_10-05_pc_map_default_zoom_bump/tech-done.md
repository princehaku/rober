# PC Map Default Zoom Bump

## sprint_type

micro

## 实际改动

- 将 PC 普通地图和 `/map` 直达地图大屏的默认缩放从 `2400%` 提升到 `3200%`，细节放大上限从 `4800%` 提升到 `6400%`。
- 扩展地图缩放档位到 `64x`，保持 `适配` 回到 `100%` 全图；地图底图、路线、小车位置和雷达点仍共用同一张 WYSIWYG overlay frame。
- 同步 `GET /api/robot-control/summary` 地图易用性 alias、TypeScript contract、普通首屏 DOM 测试、catalog 测试和 `docs/product/pc_tools_workstation.md`。
- ROS2 配套口径保持不变：RViz2 用于本地工程调试，Foxglove bridge + Foxglove Web 用于远程观察；普通用户仍优先使用 PC `/map` 大地图。该入口不启动 ROS2/RViz2/Foxglove/Nav2/建图 runtime，不发送 manual、keyboard、free-roam、delivery、stop 或 `/cmd_vel`。

## 验证结果

- `npm test -- --run App.test.ts robotControlSummary.test.ts catalog.test.ts`：3 个测试文件、429 个用例通过。
- `npm run build`：通过，Vite 仅保留既有大 chunk warning。
- `npm run lint`：通过。
- `git diff --check`：通过。
- PC Node 已重启到 `0.0.0.0:7001`，监听 PID `65436`。
- `GET http://127.0.0.1:7001/api/robot-control/summary` 读回：
  - `map_display_default_zoom_percent=3200%`
  - `map_display_max_zoom_percent=6400%`
  - `map_display_primary_url=/map`
  - `map_display_ros2_companion_tools=["rviz2","foxglove"]`
  - `map_display_ros2_companion_required=false`
  - `map_display_starts_ros2=false`
  - `map_display_starts_nav2=false`
  - `map_display_starts_map_runtime=false`
  - `live_wysiwyg_missing_surface_ids=["camera"]`
  - `radar_map_points_visible=true`
  - `radar_overlay_status=loaded`
  - `radar_overlay_current_point_count=153`
- `GET http://127.0.0.1:7001/map` 返回 HTTP 200。

## 剩余风险

- 本轮没有执行任何 motion/control POST，没有复验 Nav2 wheel raw L/R 非零、delivery success、PC 键盘连续手控或自由移动真实运动；这些仍需现场安全确认后验收。
- 本轮没有浏览器截图像素级验证；验证边界是 Vitest DOM、build/lint、HTTP 读回和 summary live smoke。
- 当前 WYSIWYG / 建图仍剩相机首帧缺口；live summary 显示地图和雷达点已可见，缺口集中在 camera。
