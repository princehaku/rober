# PC 雷达压缩点数 WYSIWYG 兜底

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - `effectiveLidarReadback` 合并口径补齐 `scan_preview_point_count`、`scan_preview_source_point_count`、`scan_preview_frame_id`。
  - `plainRadarPointHint` 在 `o3_proof_summary.scan_preview_points` 为空、`scan_preview_point_count` 为 0 时，继续读取普通 `readback_summary.lidar.scan_preview_point_count`。
  - 保持地图行为 fail-closed：只有点数没有点数组时，只在雷达卡显示已有点数，不在地图上伪造点坐标。
- `pc-tools/workstation/test/App.test.ts`
  - 新增“只有 lidar summary 点数、没有 scan point 数组”用例，验证雷达卡显示 `已有雷达点 72 个`，地图不画假点，不触发 radar start 或 `/cmd_vel`。
- `docs/product/pc_tools_workstation.md`
  - 补充普通首屏雷达压缩点数兜底与地图坐标边界。

## 验证结果

- `cd pc-tools/workstation && npm test -- App.test.ts`
  - 通过：`Test Files 1 passed`，`Tests 141 passed`。
- `cd pc-tools/workstation && npm run build`
  - 通过：`tsc -p tsconfig.app.json && vite build && tsc -p tsconfig.server.json` 成功；Vite 仅保留既有 chunk size warning。
- `git diff --check`
  - 通过，无空白错误。

## 剩余风险

- 这轮是 PC 前端显示口径修正，没有发送任何真实运动、雷达启动、Nav2 执行或 `/cmd_vel`。
- 只有压缩点数时仍不能在地图上画具体点位；这符合 WYSIWYG 边界，后续要贴地图必须读到 `scan_preview_points` 和 map-frame 位姿。
- 真实自由移动和底盘非零 `T=1001 L/R` 仍需现场安全确认后的低速运动验证。
