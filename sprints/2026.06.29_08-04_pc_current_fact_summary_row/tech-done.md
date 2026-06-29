# PC 当前事实展示后端总览

## sprint_type

micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`：普通首屏 `当前事实` 增加 `总览` 行，展示 `summary.current_fact_plain`，并将“路线”清洗为“行程”、`wheel raw L/R` 清洗为“轮速 L/R”；本地 pending/停止/读取中的实时事实行继续保留。
- `pc-tools/workstation/test/App.test.ts`：补充 Robot Control V1 首屏断言，锁定总览行出现并不包含 `雷达 marker` / `overlay`。
- `docs/product/pc_tools_workstation.md`：同步记录该只读展示边界。

## 验证结果

- 通过：`npm --prefix pc-tools/workstation test -- App.test.ts -t "Robot Control V1"`，结果 `1 passed | 214 skipped`。
- 通过：`npm --prefix pc-tools/workstation run build`，结果 `tsc` 与 `vite build` 成功；Vite 仍提示既有 chunk 超过 500 kB。
- 通过：`npm --prefix pc-tools/workstation test`，结果 `2 passed`、`375 passed`。
- 通过：PC API 已在 `0.0.0.0:7001` 监听；只读请求 `GET /api/robot-control/summary` 返回 `current_fact_plain`，且 `marker_in_current=false`、`overlay_in_current=false`。前端总览行的“路线 -> 行程”和 `wheel raw L/R -> 轮速 L/R` 清洗由 App 测试锁定。

## 剩余风险

- 当前改动只调整普通首屏只读展示；真实 Nav2 路线复验、键盘连续控制、雷达启动、地图刷新和建图验收仍需要现场用户显式操作。
