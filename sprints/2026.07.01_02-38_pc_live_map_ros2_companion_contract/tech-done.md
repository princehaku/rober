# PC live 地图 ROS2 配套合同

sprint_type: micro

## 实际改动

- `live_closure_summary` 新增普通用户地图显示合同：主工具 `/map` PC 大地图、默认/最高 `2400%`、WYSIWYG overlay 范围，以及 RViz2/Foxglove 配套命令。
- PC 首屏 `plain-live-closure-summary` 新增 `plain-live-map-companion-summary`，让现场脚本和普通用户不用读长文案也能确认“普通用户看 PC 大地图，ROS2 工具只做工程观察”。
- 窄窗口媒体查询不再把地图压成最高 520px，小屏/窄 PC 下仍保持地图主视图高度。
- 同步更新 `docs/product/pc_tools_workstation.md`。

## 验证结果

- 通过：`npm test -- test/robotControlSummary.test.ts --run`，1 个文件、6 条测试通过。
- 通过：`npm test -- test/App.test.ts -t "live closure|map defaults to a PC big-screen" --run`，命中 1 条 DOM/地图首屏测试通过。
- 通过：`npm run build`，TypeScript app/server 与 Vite build 通过；仅保留既有 chunk size warning。
- 通过：`npm test -- --run`，3 个文件、413 条测试通过。
- 通过：`npm run lint`，0 error，4 个既有 Vue 多行 HTML warning。
- 通过：`git diff --check`。
- 通过：重启 PC Node 到 `0.0.0.0:7001` 后只读 `GET /api/robot-control/summary`，返回 `status=needs_wheel_rerun`，并确认 `map_display_primary_tool=pc_big_map`、`map_display_primary_url=/map`、`map_display_default_zoom_percent=2400%`、`map_display_ros2_companion_tools=rviz2,foxglove`、`map_display_starts_ros2=false`、`map_display_starts_nav2=false`、`map_display_sends_motion_when_clicked=false`。

## 剩余风险

- 本轮不触发 Nav2、manual、keyboard、free-roam、map start、delivery、stop 或 `/cmd_vel`；真实地图大屏视觉效果仍需要浏览器现场查看确认。
- 当前目标仍未整体完成：真实自动驾驶重跑同窗口轮速非零、相机画面恢复、雷达 fresh 贴图和真实建图启动仍需现场安全确认后继续验证。
