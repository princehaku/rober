# 2026.06.29 10:10 PC map preview radar overlay alias WYSIWYG

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/shared/contracts.ts`：为 `/api/robot-control/map/preview.radar_overlay` 增加 `status/count/source_count/frame_id/points` 短字段，保留原有 `overlay_status/scan_preview_*` 字段。
- `pc-tools/workstation/src/server/robotControlSummary.ts`：地图预览 overlay 构造时同步填充短字段；`count/points` 始终代表地图上实际会画的当前雷达 marker，旧雷达点只进入 `source_count` 诊断。
- `pc-tools/workstation/test/catalog.test.ts`：补充 loaded 与 not_current 两种 overlay 形态的短字段断言，防止调试脚本再把 `radar_overlay.status/count` 读成空。
- `docs/product/pc_tools_workstation.md`：同步记录短字段语义与只读安全边界。

## 验证结果

- 通过：`npm --prefix pc-tools/workstation test -- --run test/catalog.test.ts -t "map preview"`，结果 `1 passed`、`2 passed | 152 skipped`。
- 通过：`npm --prefix pc-tools/workstation test`，结果 `2 passed`、`366 passed`。
- 通过：`npm --prefix pc-tools/workstation run build`，结果 `tsc` 和 `vite build` 成功；Vite 仅保留既有大 chunk warning。
- 通过：`git diff --check -- pc-tools/workstation/src/shared/contracts.ts pc-tools/workstation/src/server/robotControlSummary.ts pc-tools/workstation/test/catalog.test.ts pc-tools/workstation/test/App.test.ts docs/product/pc_tools_workstation.md sprints/2026.06.29_10-10_pc_map_preview_radar_overlay_alias_wysiwyg/tech-done.md`，无 whitespace 问题。
- 通过：重启 PC Node 到 `0.0.0.0:7001` 后只读请求 `GET /api/robot-control/map/preview`；返回 `proxy_status=preview_forwarded`、`path_preview_point_count=18`、`path_preview_frame_id=map`、`radar_overlay.overlay_status=not_current`、`radar_overlay.status=not_current`、`radar_overlay.count=0`、`radar_overlay.source_count=81`、`radar_overlay.frame_id=laser_frame`、`robot_control_executed=false`。

## 剩余风险

- 本轮只修 PC 地图预览 JSON 的所见即所得读法，不启动雷达，也不证明现场 radar lifecycle 已恢复。
- 未获得本轮现场安全确认，因此不执行 Nav2 goal、manual、keyboard、free-roam、delivery、stop 或 `/cmd_vel`。
