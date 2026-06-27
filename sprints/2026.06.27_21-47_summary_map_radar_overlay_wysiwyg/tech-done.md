# Summary Map Radar Overlay WYSIWYG

sprint_type: micro

## 实际改动

- 扩展 PC `readback_summary.map`，新增 `radar_overlay_status`、`radar_overlay_blocked_reasons`、`radar_overlay_scan_preview_*` 和 `radar_overlay_robot_pose_status`。
- summary 现在能表达地图雷达 overlay 的 `loaded/partial/not_loaded`：有雷达局部点但缺机器人 map pose 时显示 `partial`，并给出 `robot_pose_missing_for_map_radar_overlay`。
- 新增 catalog 回归测试，覆盖有 pose 的完整 overlay 和当前 live 形态的 partial overlay，避免只读 summary 把局部雷达点误说成已贴地图。
- 同步更新 `docs/product/pc_free_roam_mapping_design.md`。

## 验证结果

- 通过：`cd pc-tools/workstation && npm test -- catalog.test.ts --testNamePattern "partial map radar overlay|aggregates robot API"`，1 个文件通过，1 个命中测试通过。
- 通过：`cd pc-tools/workstation && npm test`，2 个文件通过，315 个测试通过。
- 通过：`cd pc-tools/workstation && npm run lint`。
- 通过：`cd pc-tools/workstation && npm run build`；Vite 仍提示单 chunk 超过 500 kB 的既有体积提醒。
- 通过：`git diff --check`。

## 剩余风险

- 本轮只提升 summary 的只读 WYSIWYG 证据，不刷新雷达、不重启定位、不执行 Nav2、不发 manual/free-roam/stop 或 `/cmd_vel`。
