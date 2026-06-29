# PC 雷达贴图 done 项下一步口径修正

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/server/robotControlSummary.ts`：当地图雷达点已经 `current_on_map` 时，动作卡和目标清单优先使用 `radar_overlay_wysiwyg_*` 事实，普通下一步显示“继续观察地图雷达层”。
- `pc-tools/workstation/test/catalog.test.ts`：补回归断言，覆盖雷达点已贴到当前地图时，`radar_map_points` action card 和 `radar_map_points_wysiwyg` checklist 均显示 done 口径，不再提示修复扫描 proof。
- `docs/product/pc_tools_workstation.md`、`docs/process/okr_progress_log.md`：同步记录普通用户口径和高级诊断口径的分层。

## 验证结果

- `cd pc-tools/workstation && npm test -- test/catalog.test.ts`：通过，168 tests OK。
- `cd pc-tools/workstation && npm test -- test/App.test.ts`：通过，218 tests OK。
- `cd pc-tools/workstation && npm run build`：通过。

## 剩余风险

- 本轮只修正只读 summary 文案，不启动雷达、不刷新地图、不执行 Nav2、不发送 keyboard/manual/free-roam/delivery/stop 或 `/cmd_vel`。
- 雷达贴图 WYSIWYG 已按 live summary 完成；工程诊断里 `scan_once/scan_hz/raw_packet_once` proof 缺口仍存在，但不再阻塞普通目标项。
- 相机首帧和建图启动仍未完成；完整 Nav2 路线执行仍需要现场安全确认后重跑并证明 wheel raw L/R 非零。
