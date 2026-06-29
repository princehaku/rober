# tech-done

sprint_type: micro

## 实际改动

- 将地图雷达 WYSIWYG 白话输出从“雷达 marker ...”统一改为“雷达点已贴到当前地图 / 雷达点未贴到当前地图 / 地图雷达点未加载”。
- 更新 `catalog.test.ts` 和 `App.test.ts` 中的只读 fixture 与期望，保留 `map_marker_*` 兼容字段名不变。
- 同步更新 `pc-tools/README.md` 与 `docs/product/pc_tools_workstation.md`，记录该变化只影响只读文案。

## 验证结果

- 通过：`npm --prefix pc-tools/workstation test -- catalog.test.ts -t "radar"`，13 passed / 151 skipped。
- 通过：`npm --prefix pc-tools/workstation test -- App.test.ts -t "renders Robot Control V1"`，1 passed / 214 skipped。
- 通过：`npm --prefix pc-tools/workstation test`，2 files passed，379 tests passed。
- 通过：`npm --prefix pc-tools/workstation run build`，Vite build 成功；仅保留既有 chunk size warning。
- 通过：重启 PC API 到 `0.0.0.0:7001`，PID `94604`；只读 live summary 回读 `loaded_count=15`、`failed_count=0`，`readback_summary.map.radar_overlay_wysiwyg_status_plain` 和 `readback_summary.radar.radar_overlay_wysiwyg_status_plain` 均显示“雷达点未贴到当前地图...”，聚合回读不包含 `marker`。

## 剩余风险

- 本轮不调用任何 unsafe endpoint，不启动雷达、不刷新地图、不执行 Nav2、manual、keyboard、free-roam、delivery、stop 或 `/cmd_vel`；真实雷达新扫描和地图贴点仍需现场启动雷达后验证。
