# PC 大地图缩放滚动保护

sprint_type: micro

## 实际改动

- 修正 PC 普通首屏和 `/map` 直达大屏的地图缩放滚动层：`.plain-map-layer` 改为左上完整画布溢出，避免 `600%` 默认细节视图把画布压到负方向导致边缘不可达。
- `RobotControlConsolePanel.vue` 新增地图滚动层 ref 和缩放后自动居中逻辑；进入 `/map`、全屏、只看地图、刷新地图画面或调整缩放后，只居中当前视口，不改变地图、路线、小车位置或雷达点坐标。
- 前端 DOM 新增 `data-scroll-origin=top_left_full_canvas`、`data-auto-center-on-zoom=true`，并在 App 测试里固定该显示合同。
- 更新 `docs/product/pc_tools_workstation.md`，同步普通用户大地图、ROS2 配套观察和不发车边界。

## 验证结果

- 已运行：`npm test -- test/App.test.ts -t "direct map|plain PC console"`，结果 1 个文件通过，3 个相关用例通过。
- 已运行：`npm run lint`，通过。
- 已运行：`npm run build`，通过；Vite 保留现有 bundle size warning。
- 已运行：`npm test`，结果 3 个文件通过，418 个用例通过。
- 已运行：`git diff --check`，通过。
- 已用浏览器打开 `http://127.0.0.1:7001/map` 做只读 DOM 检查：`/map` 为直达地图模式，非地图卡片可见数为 0，地图面板约占 `1272x716`，地图层约占 `1260x696`，当前缩放为 `600%`。
- 已重启 PC Node：`HOST=0.0.0.0 PORT=7001 npm run api`，监听为 `*:7001`。
- 重启后只读复核：`POST /api/robot-control/radar/scan-proof/refresh` 返回 `robot_control_executed=false`、`latest_scan_proof_fresh=true`；随后 `GET /api/robot-control/map/preview` 返回 `radar_overlay_status=loaded`、当前地图雷达点 `139` 个；summary 显示 WYSIWYG 只剩 `camera`，建图启动缺口只剩 `camera_first_frame`。
- 重启后浏览器复验 `/map`：滚动层为 `data-scroll-origin=top_left_full_canvas`、`data-auto-center-on-zoom=true`，`600%` 画布 `scrollWidth=7548`、`maxScrollLeft=6290`、居中 `scrollLeft=3145`；页面雷达 DOM 稳定后显示 `radar_overlay_status=loaded`、地图雷达点 `72` 个且真实点层存在。

## 剩余风险

- 当前真实画面仍受上车摄像头首帧问题影响；该 sprint 只修地图大屏缩放滚动，不修摄像头硬件链路。
