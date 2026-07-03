# PC 大地图 1600% 与 ROS2 配套入口 micro sprint

sprint_type: micro

## 实际改动

- 将 PC 普通首页和 `/map` 直达页的默认地图缩放从 `800%` 提升到 `1600%`，`细节放大` 上限从 `3200%` 提升到 `4800%`；`完整态势` 保持 `100%` 全局视角。
- 同步 `RobotControlConsolePanel`、`robotControlSummary`、共享 TypeScript contract 和 Vitest 断言，让 DOM、summary、live-summary 的地图缩放合同一致。
- 将地图工具行按钮从“工程观察”改为“工程观察：RViz2 / Foxglove”，明确 ROS2 配套：普通用户用 PC 大地图，本地工程看 RViz2/Nav2 RViz 配置，远程浏览器看 Foxglove bridge + Foxglove Web。
- 更新 `pc-tools/README.md`、`docs/product/pc_tools_workstation.md`、`docs/product/pc_free_roam_mapping_design.md` 和 `docs/process/okr_progress_log.md` 的当前有效口径。

## 验证结果

- 通过：`npm run lint`。
- 通过：`npm test -- test/App.test.ts test/robotControlSummary.test.ts test/catalog.test.ts --run`，结果 `Test Files 3 passed`、`Tests 452 passed`。
- 通过：`npm run build`，TypeScript/Vite 构建完成；保留既有 Vite chunk size warning。
- 通过：`git diff --check`。
- 通过：PC Node 已重启并监听 `0.0.0.0:7001`；`GET /api/robot-control/summary` 与
  `GET /api/robot-control/live-summary` 均读回 `status=ready_for_motion`、
  `map_display_default_zoom_percent=1600%`、`map_display_direct_map_default_zoom_percent=1600%`、
  `map_display_max_zoom_percent=4800%`、`map_display_engineering_tools_action_label=工程观察：RViz2 / Foxglove`。
- 通过但有缺口：`GET /api/robot-control/map/preview` 读回地图 PNG 存在、Nav2 路线 18 点、
  `route_target_visible=true`、`robot_pose_status=map_pose_observed`；同轮雷达 overlay 为
  `not_current/0`，不能宣称当前雷达点已贴图。
- 未完成：Codex 内置浏览器两次创建本地 tab 时卡在 webview attach，未能补截图；本轮以 Vitest DOM 合同、
  build 和 7001 运行态 API 作为可复现证据。

## 剩余风险

- 这轮只改变 PC 地图显示和 ROS2 工程观察入口文案，不启动 RViz2/Foxglove，不改变 ROS2 graph、Nav2、底盘控制或相机链路。
- 实时图传仍依赖 DV20 真实首帧；本轮不处理相机 0 帧问题。
- 雷达当前贴图读回为 `not_current/0`，需要后续恢复 `/scan` 当前 proof 后再宣称地图雷达点 WYSIWYG。
