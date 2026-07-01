# PC 主只读复验按钮

sprint_type: micro

## 实际改动

- 普通首屏现场验收卡新增 `plain-field-acceptance-primary-no-motion-readback` 按钮。
- 按钮显示为“只读复验：刷新雷达贴图 / 刷新当前所见 / 复验全部读数”，直接对应 `field_acceptance_primary_no_motion_readback_action_*`。
- 点击分发：
  - `refresh_radar_map_overlay`：只刷新雷达 proof，并联动地图预览。
  - `refresh_current_wysiwyg`：复用当前所见最小只读刷新链路。
  - `readback_all`：只刷新总览读回。
- 按钮 DOM 暴露 primary action id、label、endpoint、method、`sends_motion=false`，以及不启动 Nav2/manual/keyboard/free-roam/map runtime/radar lifecycle、不提交 delivery、不 stop 的标志。
- `pc-tools/README.md` 同步记录普通用户入口和不发车边界。

## 验证结果

- 已通过：`npm test -- robotControlSummary.test.ts App.test.ts`
  - 结果：`Test Files 2 passed (2)`，`Tests 245 passed (245)`。
- 已通过：`npm run build`
  - 结果：TypeScript app/server 和 Vite production build 通过；仅保留既有 chunk size warning。
- 已通过：`git diff --check`
  - 结果：无 whitespace error。
- 已通过：后台重启 Node 工作站并读取真实 `GET /api/robot-control/summary`
  - 监听：`0.0.0.0:7001`，PID `68020`。
  - 小车地址：`http://192.168.1.11:8787`。
  - 重启后初始结果：`live_wysiwyg_missing_surface_ids=["camera","radar_map_points"]`，`radar_overlay_status=not_current`，primary 为 `refresh_radar_map_overlay` / `POST /api/robot-control/radar/scan-proof/refresh`，`primary_sends_motion=false`。
- 已执行一次真实 no-motion primary 复验：
  - `POST /api/robot-control/radar/scan-proof/refresh` 返回 `proxy_status=refresh_forwarded`，`proof_status=not_proven`。
  - 随后只读 `GET /api/robot-control/map/preview` 返回 `proxy_status=preview_forwarded`，`radar_overlay_status=loaded`，`path_preview_status=path_preview_observed`，`path_preview_point_count=18`。
  - 最终 summary：`live_wysiwyg_missing_surface_ids=["camera"]`，`radar_overlay_status=loaded`，`radar_points_visible=true`，primary 自动切到 `refresh_current_wysiwyg` / `/api/robot-control/camera/first-frame/probe`。

## 剩余风险

- 该按钮只做只读复验，不替代现场安全确认，也不会执行 Nav2、键盘、自由移动或建图。
- 当前真实小车仍需要现场处理相机 USB/full-speed 缺口，并在安全确认后完成 wheel L/R 非零、delivery success 等运动验收。
