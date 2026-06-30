# PC 地图默认全图与细节放大

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 普通首屏地图和 `/map` 直达大屏默认从 `2400%` 改为 `100%` 整图铺满大画布。
  - 新增“细节放大”按钮，一键跳到 `2400%`，并继续让底图、图上路线、小车位置和雷达点共用同一个 WYSIWYG overlay frame。
  - 地图验收条和 ROS2 配套说明改为“默认看全图，细节最高 2400%”；RViz2/Foxglove 仍只作为旁路观察工具，不自动启动。
- `pc-tools/workstation/src/server/robotControlSummary.ts`
  - `live_closure_summary.map_display_default_zoom_percent` 改为 `100%`，最高缩放保持 `2400%`。
  - `map_display_companion_plain` 同步普通用户口径：`/map` 使用 PC 大地图，默认整图，细节放大最高 `2400%`。
- `pc-tools/workstation/src/shared/contracts.ts`
  - 同步 `map_display_default_zoom_percent` 类型合同为 `100%`。
- `pc-tools/workstation/test/App.test.ts`
  - 更新普通首屏地图、`/map` 直达页、旧 `?view=map` 兼容入口和 live closure DOM 断言。
  - 新增“细节放大”按钮断言，确认可从 `100%` 一键到 `2400%`，再用“适配”回到 `100%`。
- `pc-tools/workstation/test/robotControlSummary.test.ts`
  - 更新 summary API 地图显示合同断言。
- `docs/product/pc_tools_workstation.md`
  - 记录当前有效合同：默认 `100%` 整图，最高 `2400%` 细节放大，ROS2 配套仍为 RViz2 / Foxglove 旁路观察。

## 验证结果

- 通过：`cd pc-tools/workstation && npm test -- --run test/App.test.ts -t "map view|map display|direct map|plain map|Robot Control V1"`，1 file passed，7 tests passed。
- 通过：`cd pc-tools/workstation && npm test -- --run test/robotControlSummary.test.ts`，1 file passed，6 tests passed。
- 通过：`cd pc-tools/workstation && npm run build`，Vite chunk size warning 仍为既有提示，构建成功。
- 通过：`cd pc-tools/workstation && npm test -- --run`，3 files passed，413 tests passed。
- 通过：`cd pc-tools/workstation && npm run lint`，0 errors，0 warnings。
- 通过：`git diff --check`。
- 模板格式修正后复跑通过：`cd pc-tools/workstation && npm test -- --run test/App.test.ts -t "map view|map display|direct map|plain map|Robot Control V1"`，1 file passed，7 tests passed。
- 通过：7001 只读 smoke，listener PID `12954`，`GET http://127.0.0.1:7001/api/robot-control/summary` 返回 `live_status=needs_wheel_rerun`、`map_display_default_zoom_percent=100%`、`map_display_max_zoom_percent=2400%`、`primary_url=/map`、`overlays=image,route,robot,radar`、`starts_ros2=false`、`starts_rviz2=false`、`starts_nav2=false`、`sends_motion=false`。
- 通过：`HEAD http://127.0.0.1:7001/map` 返回 `200 OK`。

## 剩余风险

- 本轮只改变 PC 地图显示默认缩放和合同，不连接真实小车，不启动 RViz2/Foxglove，不执行 Nav2、manual、keyboard、free-roam、delivery、stop 或 `/cmd_vel`。
- 还需要后续现场用 7001 页面确认不同 PC 分辨率下真实地图是否足够清晰，并继续处理相机首帧、雷达贴图、轮速复验和完整 Nav2 执行闭环。
