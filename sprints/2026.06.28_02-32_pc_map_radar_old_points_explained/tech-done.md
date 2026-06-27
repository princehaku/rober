# 2026-06-28 02:32 PC 地图旧雷达点未贴图说明

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 当 summary 明确地图雷达 overlay `not_current`，或雷达 lifecycle 已停且 runtime scan stale 时，继续禁止旧 scan preview 点回画到地图。
  - 地图 marker 从泛化“地图0点”提升为“旧点未贴图”，aria、雷达点口径和坐标口径同步说明“旧雷达点 N 个已判定为不当前，未贴到地图”。
  - 该改动只改变只读展示，不启动雷达、不刷新雷达、不发送 manual、Nav2、free-roam、delivery、stop 或 `/cmd_vel`。
- `pc-tools/workstation/test/App.test.ts`
  - 更新 not-current radar overlay 和 stale/stopped lidar 两条 WYSIWYG 测试，断言旧点不回到 SVG，同时 marker/caption 显示旧点数量和未贴图原因。
- `docs/product/pc_free_roam_mapping_design.md`
  - 同步记录地图旧雷达点解释口径。

## 验证结果

- `npm test -- -t "honors not-current map radar overlay summary instead of redrawing old proof points|treats stale stopped lidar as not-current even when map overlay summary is still partial"`：通过，2 passed / 330 skipped。
- `npm test -- --maxWorkers=1 --no-fileParallelism`：通过，2 files passed / 332 tests passed。
- `npm run lint`：通过。
- `npm run build`：通过；Vite 仍有既有 chunk size warning。
- `git diff --check`：通过。
- 重启 PC Node 到 `0.0.0.0:7001`：通过，`node` 监听 `*:7001`。
- 只读检查 `/api/robot-control/summary?baseUrl=http://192.168.1.11:8787`：通过，live summary 为 `radar_overlay_status=not_current`、`radar_overlay_scan_preview_point_count=0`、`radar_overlay_scan_preview_source_point_count=80`、`lidar.lifecycle_running=false`、`lidar.runtime_scan_status=stale`、`lidar.scan_preview_point_count=65`、`lidar.scan_preview_source_point_count=80`。这正是本轮“旧点未贴图但要解释旧点数量”的覆盖形态。

## 剩余风险

- 本轮不修复真实雷达未运行问题；live 仍需要启动/刷新雷达后才能获得当前 scan。
- 旧雷达点数量只用于解释未贴图原因，不是建图验收的 fresh radar 证据。
