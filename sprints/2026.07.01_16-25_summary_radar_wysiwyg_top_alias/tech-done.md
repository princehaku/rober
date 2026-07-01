# Summary Radar WYSIWYG Top Alias

## Sprint 类型

sprint_type: micro

## 实际改动

- `GET /api/robot-control/summary` 顶层新增雷达贴图恢复 alias，直接透出 `live_closure_summary` 内已有的雷达 WYSIWYG 诊断。
- 新增字段覆盖旧来源点抑制原因、当前点数与来源点数白话说明、刷新下一步、是否阻塞 WYSIWYG、是否阻塞自由移动、固定恢复 endpoint、以及刷新动作不会发车/不会启动雷达 lifecycle 的 proof flags。
- 更新 summary 合同、服务端返回、定向测试、catalog live-summary 合同测试和 PC 工作站产品文档。

## 验证结果

- 通过：`git diff --check`
- 通过：`npm test -- --run test/robotControlSummary.test.ts`，结果 `1 passed / 9 passed`。
- 通过：`npm test -- --run test/catalog.test.ts -t "live-summary"`，结果 `1 passed / 1 passed / 180 skipped`。
- 通过：`npm test`，结果 `3 passed / 421 passed`。
- 通过：`npm run lint`。
- 通过：`npm run build`；仅保留 Vite 既有 chunk size warning。
- 通过：重启 `0.0.0.0:7001` 后，用只读 `GET /api/robot-control/summary?baseUrl=http%3A%2F%2F192.168.1.11%3A8787` 确认顶层雷达贴图恢复 alias 非空：`radar_overlay_primary_blocked_reason=runtime_scan_stale_for_map_radar_overlay`、`radar_overlay_needs_refresh=true`、`radar_overlay_blocks_wysiwyg=true`、`radar_overlay_blocks_free_move=false`、`radar_overlay_recovery_sequence=[/api/robot-control/radar/scan-proof/refresh,/api/robot-control/map/preview]`、`radar_overlay_refresh_sends_motion=false`、`radar_overlay_refresh_starts_radar_lifecycle=false`。

## 剩余风险

- 本轮只增加只读 summary alias，不调用雷达刷新 POST，不启动雷达 lifecycle，不执行 Nav2、manual、keyboard、free-roam、建图、delivery、stop 或 `/cmd_vel`。
- 真实雷达贴图是否恢复仍依赖现场手动执行固定 no-motion 刷新链路：先刷新雷达扫描读数，再刷新地图画面。
