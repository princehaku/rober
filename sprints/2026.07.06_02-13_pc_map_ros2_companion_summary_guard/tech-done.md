# 2026.07.06 02:13｜pc_map_ros2_companion_summary_guard｜PC 地图可读缩放与相机诊断守卫

## sprint_type

micro

## 本轮目标

响应现场反馈“PC 上地图太小，ROS2 有没有配套可以用”，把普通用户 PC 地图从极端局部放大调整为默认可读大图，同时保留 ROS2 工程观察分层口径：

- 普通用户：继续使用 PC 首页地图和 `/map` 简易大图，不要求会 ROS2。
- 本地工程调试：RViz2 / Nav2 RViz 配置观察 `/map`、`/scan`、TF、路径、定位和 costmap。
- 远程浏览器观察：部署 `foxglove_bridge` 后用 Foxglove Web 观察 ROS2 topic。

同轮修正相机摘要诊断优先级：UVC vendor extension 控制查询短包不能覆盖最新首帧/探测无帧事实，避免页面把“无画面”误导成单纯传输层问题。

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 首页和 `/map` 默认缩放从极端局部大图调整为 `200%` 可读大图。
  - 缩放档位调整为 `100% / 150% / 200% / 300% / 400% / 600% / 800% / 1200%`，`完整态势` 仍回到 `100%`，`细节放大` 到 `1200%`。
- `pc-tools/workstation/src/shared/contracts.ts`
  - 同步 `map_display_default_zoom_percent=200%`、`map_display_direct_map_default_zoom_percent=200%`、`map_display_max_zoom_percent=1200%` 合同字面量。
- `pc-tools/workstation/src/server/robotControlSummary.ts`
  - summary/live-summary 输出同步为 `200% / 1200%`。
  - 相机诊断聚合新增“transport 必须自带首帧失败证据才可盖过 no-frame”的守卫。
- `pc-tools/workstation/src/server/index.ts`
  - `camera/first-frame/probe` 和 summary overlay 共用相机 transport 证据守卫。
  - XU 控制查询短包 + 最近 probe 无帧时，顶层诊断保持 `uvc_no_frame_not_exclusive` 与“检查摄像头输入/供电后复测”。
- `pc-tools/workstation/test/App.test.ts`
- `pc-tools/workstation/test/robotControlSummary.test.ts`
- `pc-tools/workstation/test/catalog.test.ts`
  - 更新地图缩放和相机诊断回归断言。
- `pc-tools/README.md`
- `docs/product/pc_tools_workstation.md`
- `docs/product/pc_free_roam_mapping_design.md`
- `OKR.md`
  - 同步当前 PC 地图口径、ROS2 配套边界和相机诊断守卫状态。

## 验证结果

已通过的定向验证：

```bash
cd pc-tools/workstation
npm run test -- catalog.test.ts -t "workstation camera MJPEG status keeps recent first-frame"
npm run test -- App.test.ts -t "map"
npm run test -- robotControlSummary.test.ts
```

结果：

- 相机诊断回归通过：XU 控制查询短包不会覆盖最近首帧/探测无帧事实。
- 地图 DOM/API 定向断言通过：默认 `200%`，细节上限 `1200%`。
- `robotControlSummary` 单测通过。

完整验证：

```bash
cd pc-tools/workstation
npm run lint
npm run test
npm run build
cd /Users/m1/apps/rober
git diff --check
```

结果：

- `npm run lint` 通过。
- `npm run test` 通过：3 个 test file，453 个测试用例通过。
- `npm run build` 通过；Vite 仅输出已有的大 bundle 警告。
- `git diff --check` 通过。

现场只读验证：

```bash
HOST=0.0.0.0 PORT=7001 npm run api
curl -I http://127.0.0.1:7001/map
curl http://127.0.0.1:7001/api/robot-control/live-summary?baseUrl=http://192.168.1.11:8787
```

结果：

- Node 已监听 `*:7001`，`/map` 返回 HTTP 200。
- `live-summary` 返回 `map_current_visible=true`、`path_current_visible=true`、`radar_map_points_visible=true`。
- `live-summary` 返回 `map_display_default_zoom_percent=200%`、`map_display_direct_map_default_zoom_percent=200%`、`map_display_max_zoom_percent=1200%`。
- `live-summary` 返回 ROS2 配套口径：本地工程调试用 RViz2，远程浏览器观察用 Foxglove bridge + Foxglove Web，普通用户仍使用 PC 大地图和 `/map`。
- `POST /api/robot-control/camera/first-frame/probe` 返回 `source_diagnosis_status=uvc_no_frame_not_exclusive`、`camera_hardware_action_label=检查摄像头输入/供电后复测`、`camera_blocks_free_move=false`。
- 复测后 `live-summary` 同步返回 `camera_source_diagnosis_status=uvc_no_frame_not_exclusive`、`live_wysiwyg_camera_source_diagnosis_status=uvc_no_frame_not_exclusive`。
- `keyboard_ready=true`、`delivery_success=true`。

## 剩余风险

- 真实相机仍然没有首帧，当前仅修正 PC 端诊断聚合和普通用户可理解提示；仍需继续检查 DV20 上游视频输入、线材、接口、供电、采集卡/摄像头或换 known-good UVC。
- 真实轮速 `T=1001` raw L/R 非零仍是现场遗留验收项；本轮 live-summary 仍为 `wheel_lr_nonzero_proven=false`，当前改动不发送运动命令。
- RViz2/Foxglove 是 ROS2 配套观察工具，本轮只同步口径和 PC 简易地图体验，不自动启动 RViz2、Foxglove、ROS2 runtime 或 Nav2。
