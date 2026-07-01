# PC map and focused WYSIWYG refresh

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 现场验收 WYSIWYG 刷新新增 `data-wysiwyg-refresh-mode`，按当前缺口选择最小只读刷新链路。
  - 只缺相机时只复测相机首帧、读取 MJPEG 状态和 summary；只缺雷达贴图或地图时分别走对应只读刷新。
  - 该按钮继续不启动 Nav2、键盘、自由移动、建图 runtime、雷达 lifecycle、delivery complete 或 stop。
- `pc-tools/workstation/test/App.test.ts`
  - 补充 `all_wysiwyg` 模式断言。
  - 新增 camera-only 回归测试，确认单缺口刷新不调用雷达、地图或任何运动接口。
- `docs/product/pc_tools_workstation.md`
  - 修正 PC 大地图缩放上限为 3200%。
  - 记录普通用户地图优先 `/map` 大屏；ROS2 配套工具为 RViz2 本地工程调试、Foxglove 远程浏览器观察。
  - 记录 WYSIWYG 聚焦刷新四种模式。

## 验证结果

- `npm --prefix pc-tools/workstation test -- --run test/App.test.ts`：通过，232 passed。
- `npm --prefix pc-tools/workstation run lint`：通过。
- `npm --prefix pc-tools/workstation run build`：通过；Vite 输出 `index-J7rqPjFc.js`、`index-COyplIBP.css`，仅保留既有 chunk size warning。
- `npm --prefix pc-tools/workstation test -- --run`：通过，3 files / 422 passed。
- PC Node 已重启到 `0.0.0.0:7001`，监听 PID 61699。
- 只读 smoke：
  - `GET http://127.0.0.1:7001/`：200。
  - `GET http://127.0.0.1:7001/map`：200。
  - `GET /api/robot-control/summary?baseUrl=http://192.168.1.11:8787`：`robot_api_connection=readable`、`status=needs_wheel_rerun`、`map_display_primary_url=/map`、`map_display_default_zoom_percent=600%`、`map_display_max_zoom_percent=3200%`、`radar_overlay_status=loaded`、`radar_overlay_point_count=149`。
  - live bundle 包含 `data-wysiwyg-refresh-mode`、`camera_only`、`all_wysiwyg`、`PC 大地图`、`Foxglove Web`、大地图 CSS 和工程观察样式。

## 剩余风险

- 真实相机仍需要换线、换 USB 口或 known-good UVC 后复测首帧；本轮只修 PC 侧聚焦刷新和地图入口呈现。
- 未收到新的现场安全确认，本轮不触发 Nav2 execute、manual、free-roam start、map start、delivery complete 或 stop。
