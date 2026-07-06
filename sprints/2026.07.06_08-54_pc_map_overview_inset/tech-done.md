# PC 地图完整态势小窗

## sprint_type

micro

## 实际改动

- PC 简易控制台和 `/map` 保持普通用户优先，不把 RViz2/Foxglove 作为主界面；主地图默认继续使用 `800%`，解决现场反馈“地图太小”。
- 在地图画布右上角新增固定 `100%` 完整态势小窗，复用同一份真实地图、Nav2 路线、小车位置、雷达点和目标点 WYSIWYG 图层。
- 小窗明确为只读展示层：不发送 manual、keyboard、free-roam、delivery、stop 或 `/cmd_vel`，不启动 ROS2/RViz2/Foxglove/Nav2/建图 runtime。
- `summary` 和 `live-summary` 新增并透出 `map_display_overview_inset_visible`、`map_display_overview_inset_zoom_percent`、`map_display_overview_inset_overlays`、`map_display_overview_inset_sends_motion`，方便 PC 页面和验收脚本直接判断。
- 同步更新 PC 工具 README 与产品文档，记录普通用户 PC 大地图优先、ROS2 配套工具只用于工程观察的边界。

## 验证结果

- `npm test -- test/robotControlSummary.test.ts --run` 通过：1 个文件、18 个测试通过。
- `npm test -- test/App.test.ts --run` 通过：1 个文件、242 个测试通过；覆盖 `/map` 下小窗存在、主图 `800%`、小窗 `100%`、五层 overlay 和只读/不启动工程 runtime 属性。
- `npm test -- test/catalog.test.ts --run` 通过：1 个文件、195 个测试通过。
- `npm run build` 通过；仅保留已有 Vite 大 chunk 警告。
- `curl http://127.0.0.1:7001/api/robot-control/live-summary?baseUrl=http://192.168.1.11:8787` 返回：`status=ready_for_motion`、`map_current_visible=true`、`path_current_visible=true`、`radar_map_points_visible=true`、`route_target_current_visible=true`、`map_display_default_zoom_percent=800%`、`map_display_overview_inset_visible=true`、`map_display_overview_inset_zoom_percent=100%`、`map_display_overview_inset_overlays=image/route/robot/radar/target`、`map_display_overview_inset_sends_motion=false`、`delivery_success=true`。
- PC 服务确认监听 `*:7001`：`node` 进程占用 TCP 7001，未改 Clash，也未改到 7071。
- 本轮只读尝试使用内置浏览器打开 `/map` 时，浏览器插件连续返回 webview attach timeout；因此视觉截图未作为本轮证据，改由 Vitest DOM 属性和 live-summary 运行证据覆盖。

## 剩余风险

- 实时视频仍未闭环：live-summary 仍为 `camera_current_visible=false`，本轮没有把相机预览包装成完成。
- WAVE ROVER vendor T1001 的 `wheel_lr_nonzero_proven=false` 仍是独立反馈风险；PC 手控链路已有 command raw L/R 与 IMU 运动信号证据，但 vendor 反馈闭环未完成。
- 浏览器插件本轮无法 attach 到 in-app tab，缺少人工可见截图证据；用户可直接打开 `http://192.168.1.55:7001/` 或 `http://192.168.1.55:7001/map` 复核视觉效果。
