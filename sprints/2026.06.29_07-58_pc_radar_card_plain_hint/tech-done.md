# PC 雷达卡片优先展示普通 plain_hint

## sprint_type

micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`：普通首屏雷达卡片的 `地图雷达事实` 行优先消费 `readback_summary.radar.plain_hint`，避免把高级 `雷达 marker` / `overlay` 文案展示给普通用户；旧响应没有 `plain_hint` 时仍回退原拆分字段。
- `pc-tools/workstation/test/App.test.ts`：更新 Robot Control V1 首屏断言，锁定雷达卡片显示普通地图雷达口径且不包含 `雷达 marker` / `overlay`。
- `docs/product/pc_tools_workstation.md`：同步记录首屏字段的数据源和只读边界。

## 验证结果

- 通过：`npm --prefix pc-tools/workstation test -- App.test.ts -t "Robot Control V1"`，结果 `1 passed | 214 skipped`。
- 通过：`npm --prefix pc-tools/workstation run build`，结果 `tsc` 与 `vite build` 成功；Vite 仍提示既有 chunk 超过 500 kB。
- 通过：`npm --prefix pc-tools/workstation test`，结果 `2 passed`、`375 passed`。
- 通过：重启 PC API 到 `0.0.0.0:7001` 后只读请求 `GET /api/robot-control/summary`，live 返回 `readback_summary.radar.plain_hint` 为“雷达未运行或扫描已停；地图雷达点当前显示 0 个，旧来源点 81 个只作诊断。下一步：先启动雷达并等待新扫描，再刷新地图画面确认雷达点。”，且 `marker_in_radar_plain=false`、`overlay_in_radar_plain=false`；首屏雷达卡片消费该字段由 App 测试锁定。

## 剩余风险

- 当前改动只调整普通首屏雷达卡片只读展示；真实雷达启动、地图刷新、Nav2 路线复验和建图验收仍需要现场用户显式操作。
