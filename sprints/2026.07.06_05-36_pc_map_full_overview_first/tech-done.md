# 2026.07.06 05:36｜pc_map_full_overview_first｜PC 地图完整态势优先

## sprint_type

micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - PC 首页和 `/map` 默认地图缩放从历史 `1600%` 收敛回 `100%` 完整态势。
  - 保留最高 `4800%` 细节放大，局部排障时再手动放大。
  - 更新普通用户文案：先完整显示地图、Nav2 路线、小车位置、雷达点和目标点，再用细节放大。
- `pc-tools/workstation/src/styles.css`
  - 首页 `visual-first` 布局里地图卡 `order=-20`，图传 `order=10`，WASD `order=11`，连接/雷达/建图详情 `order=20`。
  - 真实地图 overlay 默认按画布宽度铺满并保留比例，不再按高度乘默认大倍率导致只看到局部空白。
- `pc-tools/workstation/src/server/robotControlSummary.ts`
- `pc-tools/workstation/src/shared/contracts.ts`
  - summary/live-summary 与共享类型合同同步为 `map_display_default_zoom_percent=100%`、
    `map_display_direct_map_default_zoom_percent=100%`、`map_display_max_zoom_percent=4800%`。
- `pc-tools/workstation/test/App.test.ts`
- `pc-tools/workstation/test/catalog.test.ts`
- `pc-tools/workstation/test/robotControlSummary.test.ts`
  - 回归测试同步当前地图合同：默认缩放 scale 为 `1`，第一次放大到 `150%`，细节放大到 `4800%`。
  - CSS/DOM 断言改为 `width-first-preserve-aspect-full-overview`，并验证默认完整态势下缩小/重置按钮禁用。
- `pc-tools/README.md`
- `docs/product/pc_tools_workstation.md`
- `docs/product/pc_free_roam_mapping_design.md`
  - 同步当前有效口径：普通用户先用 PC 首页完整态势和 `/map`，RViz2/Foxglove 只作工程观察。

## 验证结果

- `npm run test` 通过：`Test Files 3 passed (3)`，`Tests 455 passed (455)`。
- `npm run build` 通过：`tsc -p tsconfig.app.json && vite build && tsc -p tsconfig.server.json`，Vite 构建成功。
- Chrome 1920x1080 headless 实测首页：
  - `mapPanel.top=89`，`cameraPanel.top=1275`，`motionPanel.top=1275`，地图已排在图传和 WASD 之前。
  - `mapZoomPercent=100%`，地图图像渲染尺寸 `1866x808`，自然尺寸 `261x113`。
  - `robot/routeGoal/routePath/radarScanPoints` 四类 marker 均存在且 `inViewport=true`。
- Chrome 1920x1080 headless 实测 `/map`：
  - `mapPanel=1920x1080`，`mapLayer=1920x1039`。
  - `mapZoomPercent=100%`，机器人、目标、路线和雷达点均在 viewport 内。
- 7001 运行态复验：
  - `GET /api/robot-control/live-summary?baseUrl=http://192.168.1.11:8787` 返回
    `map_display_default_zoom_percent=100%`、`map_display_direct_map_default_zoom_percent=100%`、
    `map_display_max_zoom_percent=4800%`。
  - 同次读回 `map_current_visible=true`、`path_current_visible=true`、`radar_map_points_visible=true`、
    `keyboard_ready=true`、`camera_current_visible=false`。

## 剩余风险

- 实时图传仍是 DV20 UVC 无首帧问题，本轮只修地图布局，不宣称相机恢复。
- WAVE ROVER `T=1001` wheel raw L/R 仍可能保持 `0/0`，本轮未改底盘反馈闭环。
