# PC 轮速刷新 pending 使用普通文案

## sprint_type

micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`：普通首屏 `当前事实` 的轮速只读刷新 pending 文案从 `wheel raw L/R` 改为“轮速 L/R”。
- `pc-tools/workstation/test/App.test.ts`：更新 pending 状态断言，并锁定该状态不展示 `wheel raw L/R（只读）`；原有断言继续确认不会调用 manual、Nav2 execute、delivery complete 或 `/cmd_vel`。
- `docs/product/pc_tools_workstation.md`：同步记录普通首屏文案和只读边界。

## 验证结果

- 跳过并修正：`npm --prefix pc-tools/workstation test -- App.test.ts -t "base feedback refresh pending"` 未匹配测试名，结果 `215 skipped`；随后改用真实用例名重跑。
- 通过：`npm --prefix pc-tools/workstation test -- App.test.ts -t "shows wheel readback pending in current facts"`，结果 `1 passed | 214 skipped`。
- 通过：`npm --prefix pc-tools/workstation run build`，结果 `tsc` 与 `vite build` 成功；Vite 仍提示既有 chunk 超过 500 kB。
- 通过：`npm --prefix pc-tools/workstation test`，结果 `2 passed`、`375 passed`。
- 通过：PC API 仍在 `0.0.0.0:7001` 监听；只读请求 `GET /api/robot-control/summary` 返回 `current_fact_plain`，且 `marker_in_current=false`、`overlay_in_current=false`。

## 剩余风险

- 当前改动只调整普通首屏只读 pending 文案；真实轮速非零、Nav2 路线复验、键盘连续控制和建图验收仍需要现场用户显式操作。
