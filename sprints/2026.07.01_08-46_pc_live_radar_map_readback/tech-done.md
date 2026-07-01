# 2026.07.01 08:46 PC 当前卡点雷达贴图只读收口

## sprint_type

micro

## 实际改动

- 在 PC 普通首屏当前卡点区新增 `plain-live-radar-map-readback`，当雷达贴图缺失、旧来源点被抑制或需要同轮刷新时直接显示雷达贴图收口说明。
- 新增 `plain-live-radar-map-readback-refresh` 按钮，复用既有 `refreshRadarProof({ focusAfterReady: false, mapPreviewAfter: true })`，只刷新雷达 scan proof、雷达状态和地图预览。
- 明确 DOM 合同：该入口不复测相机首帧、不读取相机 MJPEG 状态、不启动雷达 lifecycle、不启动建图 runtime、不执行 Nav2、不发送手控/键盘/自由移动、不提交 delivery、不 stop、不发送 motion。
- 更新 PC 工作站产品边界文档，记录相机卡在 USB full-speed 无首帧时，雷达贴图 WYSIWYG 仍可独立只读收口。

## 验证结果

- 通过：`cd pc-tools/workstation && npm test -- --run test/App.test.ts -t "renders Robot Control V1 by default with Robot API proxy and locked command boundary"`，结果 `1 passed | 230 skipped`。
- 通过：`cd pc-tools/workstation && npm run lint`。
- 通过：`cd pc-tools/workstation && npm run build`，生成 `dist/assets/index-mOmXfRZt.js` 与既有 CSS；仅保留 Vite 大 chunk 提示。
- 通过：`cd pc-tools/workstation && npm test`，结果 `3 passed`、`417 passed`。
- 通过：`git diff --check`。
- 通过：重启 PC API 后 `lsof -nP -iTCP:7001 -sTCP:LISTEN` 显示 `node` 监听 `*:7001`，PID `73751`。
- 通过：`curl -I http://127.0.0.1:7001/map` 返回 `HTTP/1.1 200 OK`。
- 通过：构建产物 `dist/assets/index-mOmXfRZt.js` 包含 `plain-live-radar-map-readback` 和 `只刷新雷达贴图`。
- 通过：真实 no-motion `POST /api/robot-control/radar/scan-proof/refresh` 返回 `proxy_status=refresh_forwarded`、`last_result_status=refreshed`、`robot_control_executed=false`。
- 通过：随后 `GET /api/robot-control/map/preview` 返回 `radar_overlay_status=loaded`、`radar_overlay_point_count=155`、`radar_overlay_refresh_required=false`。
- 通过：随后 `GET /api/robot-control/summary` 返回 `radar_map_points_visible=true`、`live_wysiwyg_radar_map_current_point_count=155`、`live_wysiwyg_radar_map_stale_source_points_suppressed=false`。

## 剩余风险

- 雷达贴图已通过本轮 no-motion 读回证明为当前地图可见；后续若雷达 runtime 再变 stale，当前卡点会再次显示 `plain-live-radar-map-readback-refresh`。
- 相机仍显示 USB full-speed 无首帧，需要现场换高速 USB 口/线或带供电 Hub 后再复测；本轮不改变相机采集链路。
- 完整 Nav2 闭环仍缺同窗口 wheel L/R 非零和 delivery success，需要现场安全确认后的运动窗口验证。
