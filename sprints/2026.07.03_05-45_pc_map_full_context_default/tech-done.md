# PC 地图完整态势默认视角

sprint_type: micro

## 实际改动

- 将 PC 普通首页和 `/map` 直达页的地图默认缩放从 `400%` 局部细节改为 `45%` 完整态势视角，优先完整显示地图、Nav2 路线、小车位置、雷达点和目标点。
- 保留 `细节放大` 到 `1200%` 和逐级缩放；`适配` 现在回到 45% 完整态势档位。
- 同步更新 Robot Control summary、类型契约、Vue DOM 验收字段、测试期望、`pc-tools/README.md` 和 `docs/product/pc_tools_workstation.md` 的 ROS2 配套口径。
- ROS2 配套结论保持不变：普通用户默认用 PC 简易页面；RViz2 用于本地工程调试，Foxglove bridge 用于远程浏览器观察，二者只观察不发车。

## 验证结果

- `npm test -- --run test/App.test.ts test/robotControlSummary.test.ts test/catalog.test.ts` 通过：3 个 test files，433 个 tests passed。
- `npm run build` 通过：`tsc -p tsconfig.app.json && vite build && tsc -p tsconfig.server.json` 通过；Vite 仍提示现有大 chunk 警告。
- PC Node 已按 `HOST=0.0.0.0 PORT=7001 WORKSTATION_NODE_PORT=7001 npm run api` 重启，`lsof` 读到 `TCP *:7001 (LISTEN)`。
- `GET /api/robot-control/summary?baseUrl=http://192.168.1.11:8787` 读回 `map_display_default_zoom_percent=45%`、`map_current_visible=true`、`path_current_visible=true`、`radar_map_points_visible=true`、`keyboard_ready=true`。
- 浏览器 1280x720 首页 smoke 通过：地图面板、实时画面、移动/键盘面板均在首屏；地图 frame 856x371，`scrollWidth=clientWidth=856`，默认无横向滚动；机器人、起点、目标、路线 SVG、雷达 marker 和 72 个雷达点均可见。
- 浏览器 1280x720 `/map` 直达页 smoke 通过：非地图卡片 0 个，地图 frame 1270x550，`scrollWidth=clientWidth=1270`；机器人、起点、目标、路线 SVG、雷达 marker 和雷达点均可见。

## 剩余风险

- 摄像头仍未出首帧，页面显示 `mjpeg_auto_retry_cooldown_after_first_frame_failure`；这轮只修地图默认视角和 ROS2 配套口径，不改变上车 USB/UVC 物理风险。
- 本轮未执行真实底盘运动；键盘和行程入口仅验证 UI/API ready 状态。
