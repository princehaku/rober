# Direct Map Pending WYSIWYG Guard

## sprint_type

micro

## 实际改动

- 修正 PC `/map` 直达大屏入场刷新中的中间态：`mapWysiwygRefreshPending` 现在包含 `radarRefreshPending`。
- `plainMapVisualSummary.state` 统一使用 `mapWysiwygRefreshPending`，因此入场雷达 scan proof 或地图预览仍 pending 时，`plain-map-panel` 与 `plain-map-wysiwyg-view` 显示 `地图处理中`，不会把旧 summary 点数、局部雷达点或上一轮地图状态当作最终 WYSIWYG 结果。
- 新增 App 回归测试：挂起 `/api/robot-control/radar/scan-proof/refresh` 时，`/map` 必须显示处理中、按钮显示“等待地图刷新”，且不触发 radar lifecycle、相机流、Nav2 goal、manual 或 `/cmd_vel`。
- 同步更新 `pc-tools/README.md` 和 `docs/product/pc_tools_workstation.md`。

## 验证结果

- 已验证：`npm test -- --run App.test.ts`，237 个用例通过。
- `git diff --check`：通过。
- `npm test -- --run catalog.test.ts App.test.ts robotControlSummary.test.ts`：3 个测试文件、428 个用例通过。
- `npm run lint`：通过。
- `npm run build`：通过，Vite 仅保留既有大 chunk warning。
- PC Node 已重启到 `0.0.0.0:7001`，监听 PID `8901`。
- 真实 summary smoke：
  - `status=needs_wheel_rerun`
  - `live_wysiwyg_missing_surface_ids=["camera"]`
  - `radar_overlay_wysiwyg_complete=true`
  - `radar_map_points_visible=true`
  - `map_display_direct_map_refreshes_radar_scan_proof_on_enter=true`
  - `map_display_direct_map_refreshes_map_preview_on_enter=true`
  - `map_display_direct_map_refreshes_radar_status_on_enter=true`
  - `map_display_direct_map_starts_radar_lifecycle_on_enter=false`
  - `trip_execution_ready=true`、`keyboard_ready=true`、`free_move_start_ready=true`
  - `mapping_start_ready=false`，仍缺 `camera_first_frame`
- 真实浏览器 `/map` smoke：
  - URL `http://127.0.0.1:7001/map`
  - 面板 `plain-map-panel` 尺寸 `1280x720`，地图 viewport `1272x626`
  - `data-direct-map-view-requested=true`
  - `data-direct-map-view-visible-controls=zoom,map_refresh,radar_refresh,ros2_observe_toggle`
  - `data-direct-map-view-hides-map-lifecycle-actions=true`
  - `data-direct-map-view-hides-non-map-cards=true`
  - `data-direct-map-starts-radar-lifecycle-on-enter=false`
  - `data-direct-map-loads-camera-preview=false`
  - `data-direct-map-starts-camera-webrtc=false`
  - 真实地图图片加载完成，natural size `261x113`
  - `data-map-zoom-percent=1600%`
  - `data-radar-map-points-visible=true`
  - `data-radar-map-point-count=72`
  - `data-radar-map-source-point-count=190`
  - `data-radar-map-overlay-status=loaded`
  - `plain-map-radar-scan-points` 内有 72 个 circle，source `map_preview`，frame `laser_frame`
  - 非地图卡片可见数为 0
  - `plain-map-direct-refresh` 声明 `data-sends-motion-when-clicked=false`、`data-starts-map-runtime=false`、`data-starts-nav2=false`
  - `plain-map-radar-wysiwyg-proof` 声明 `data-sends-motion-when-clicked=false`、`data-starts-radar=false`、`data-starts-map-runtime=false`、`data-starts-nav2=false`、`data-starts-manual=false`

## 剩余风险

- 本轮只修 `/map` 入场 no-motion 刷新中间态，不执行任何 motion/control POST。
- 完整 Nav2 路线的同窗口 wheel L/R 非零、送达确认、PC 键盘连续手控和自由移动仍需要现场安全确认后验收。
- 相机 WYSIWYG 仍受 USB 12M full-speed / 首帧不可见影响；需要现场换高速 USB/线/供电 Hub 后复测。
