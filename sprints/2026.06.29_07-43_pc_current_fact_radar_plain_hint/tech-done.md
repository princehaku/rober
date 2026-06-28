# PC 当前事实使用普通雷达摘要

## sprint_type

micro

## 实际改动

- `pc-tools/workstation/src/server/robotControlSummary.ts`：`current_fact_plain` 的雷达段优先消费 `readback_summary.radar.plain_hint`，让顶层当前事实显示普通用户口径的“地图雷达点 / 旧来源点只作诊断 / 下一步”，不再直接暴露高级诊断里的 marker/overlay 文案。
- `pc-tools/workstation/test/catalog.test.ts`：补充 summary 契约断言，锁定顶层当前事实不包含 `marker` / `overlay`，并验证 stopped/stale 雷达只在当前事实里出现一次“旧来源点只作诊断”。
- `docs/product/pc_tools_workstation.md`：同步记录该 summary 合成口径和只读边界。

## 验证结果

- 通过：`npm --prefix pc-tools/workstation test -- catalog.test.ts -t "Robot Control summary"`，结果 `1 passed`、`38 passed | 122 skipped`。
- 通过：`npm --prefix pc-tools/workstation run build`，结果 `tsc` 与 `vite build` 成功；Vite 仍提示既有 chunk 超过 500 kB。
- 通过：`npm --prefix pc-tools/workstation test`，结果 `2 passed`、`375 passed`。
- 通过：重启 PC API 到 `0.0.0.0:7001` 后只读请求 `GET /api/robot-control/summary`，live 返回 `current_fact_plain` 包含“雷达未运行或扫描已停；地图雷达点当前显示 0 个，旧来源点 81 个只作诊断。下一步：先启动雷达并等待新扫描，再刷新地图画面确认雷达点”，且 `marker_in_current=false`、`overlay_in_current=false`。

## 剩余风险

- 当前改动只调整 PC summary 的只读文案合成；真实雷达启动、地图刷新和 Nav2 路线复验仍需要现场用户显式操作。
