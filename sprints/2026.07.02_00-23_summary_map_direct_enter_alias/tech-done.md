# Summary 地图大屏进入读回 Alias

sprint_type: micro

## 实际改动

- 在 `RobotControlLiveClosureSummary` 和 summary 顶层增加 `/map` 直达进入读回 alias：
  `map_display_direct_map_refreshes_radar_scan_proof_on_enter`、`map_display_direct_map_refreshes_map_preview_on_enter`、
  `map_display_direct_map_refreshes_radar_status_on_enter` 和 `map_display_direct_map_starts_radar_lifecycle_on_enter`。
- server summary 固定返回：进入 `/map` 会刷新 no-motion 雷达 scan proof、地图预览和雷达状态，同时不启动雷达 lifecycle。
- 同步 PC App fixture、summary 单测、README 和产品文档，保证 DOM 合同和 summary 合同一致。

## 验证结果

- 已通过：`git diff --check`
- 已通过：`cd pc-tools/workstation && npm test -- robotControlSummary.test.ts App.test.ts`，2 个测试文件、245 个用例通过。
- 已通过：`cd pc-tools/workstation && npm run lint`
- 已通过：`cd pc-tools/workstation && npm run build`；Vite 仍提示既有大 chunk warning。
- 已通过：重启 `0.0.0.0:7001` 后读取 summary，顶层和 `live_closure_summary` 都返回
  `map_display_direct_map_refreshes_radar_scan_proof_on_enter=true`、
  `map_display_direct_map_refreshes_map_preview_on_enter=true`、
  `map_display_direct_map_refreshes_radar_status_on_enter=true`、
  `map_display_direct_map_starts_radar_lifecycle_on_enter=false`；同时 `map_display_sends_motion_when_clicked=false`、`map_display_starts_nav2=false`、`map_display_starts_map_runtime=false`。

## 剩余风险

- 本轮只补 summary 合同，不新增真实发车、不启动雷达 lifecycle、不证明硬件雷达点一定可见；真实 WYSIWYG 仍依赖上车 no-motion radar proof 和 map preview 的返回。
