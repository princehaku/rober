# PC 当前所见只读刷新顺序补强

## sprint_type

micro

## 实际改动

- `pc-tools/workstation/src/server/robotControlSummary.ts`：把 `all_wysiwyg` 只读刷新链路调整为雷达扫描、雷达状态、地图画面、相机首帧、相机 MJPEG 状态、summary，确保雷达地图标记先拿同轮雷达状态再刷新地图，并最终回到总览。
- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`：同步普通首屏 live WYSIWYG fallback 链路，避免旧 summary/mock 场景退回旧顺序。
- `pc-tools/workstation/test/robotControlSummary.test.ts`、`pc-tools/workstation/test/App.test.ts`：同步 API、DOM 和只读 readback-all 断言。
- `docs/product/pc_tools_workstation.md`：同步 `all_wysiwyg` 固定只读顺序和 no-motion 边界。

## 验证结果

- 通过：`npm test -- --run robotControlSummary.test.ts App.test.ts catalog.test.ts`，428 tests passed。
- 通过：`npm run lint`。
- 通过：`npm run build`；仅保留既有 Vite chunk size warning。
- 通过：`git diff --check`。
- 通过：重启 PC Node 到 `0.0.0.0:7001`，`lsof` 显示 `TCP *:7001 (LISTEN)`；只读 summary smoke 读到 `field_acceptance_wysiwyg_refresh_sequence=[radar scan refresh, radar status, map preview, camera probe, camera mjpeg status, summary]`，且 `wysiwyg_refresh_sends_motion=false`、`wysiwyg_refresh_starts_radar_lifecycle=false`、`wysiwyg_refresh_starts_nav2=false`、`wysiwyg_refresh_starts_free_roam=false`。
- 通过：浏览器 DOM smoke 读到 `plain-field-acceptance-packet` 和 `plain-field-acceptance-wysiwyg-refresh` 均暴露同一条新 sequence，且 DOM 仍声明不发车、不启动雷达 lifecycle、不启动 Nav2。

## 剩余风险

- 本轮只调整只读 WYSIWYG 验收链路，不触发真实雷达启动、相机硬件更换、Nav2 重跑或自由移动；当前真实状态仍需现场处理相机 USB 12M、刷新雷达贴图，并在安全确认后重跑行程验证 wheel L/R 非零和送达确认。
