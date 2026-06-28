# PC Nav2 轮速失败原因 WYSIWYG Micro Sprint

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`：Nav2/行程失败原因翻译新增 wheel raw L/R 相关识别；当回包原因包含 `wheel`、`base_feedback`、`lr_zero`、`L/R=0` 或 `nonzero` 时，普通首屏显示 `轮速未响应`，不再泛化为 `执行失败`。
- `pc-tools/workstation/test/App.test.ts`：新增可见图上路线执行失败用例，锁定 wheel feedback 未闭合时地图 marker、aria、行程执行标签和行程状态都显示 `轮速未响应`，并继续断言不触发 delivery、manual 或 `/cmd_vel`。
- `pc-tools/README.md`、`docs/product/pc_tools_workstation.md`：同步记录 Nav2 执行失败 wheel raw L/R 根因的普通首屏口径和只读边界。

## 验证结果

- 通过：`cd pc-tools/workstation && npm test -- --run test/App.test.ts -t "wheel feedback failures"`，结果 `1 passed (1)`，`1 passed | 203 skipped (204)`。
- 通过：`cd pc-tools/workstation && npm test`，结果 `2 passed (2)`，`352 passed (352)`。
- 通过：`cd pc-tools/workstation && npm run lint`。
- 通过：`cd pc-tools/workstation && npm run build`；Vite 仍提示既有 chunk size warning。
- 通过：`git diff --check`。

## 剩余风险

- 本轮只改 PC 普通首屏对 Nav2 失败回包的文案翻译，不触发真实 Nav2 execute、manual、delivery、free-roam、stop 或 `/cmd_vel`。
- 真实小车自动驾驶是否能完成移动，仍需要继续用上位机/实车验证 planner/controller、执行窗口 wheel raw L/R 非零和 delivery success。
