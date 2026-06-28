# PC 轮速试动底盘兜底 Micro Sprint

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`：轮速卡 `试动读轮速` 入口优先走 first-jog；当 first-jog 缺画面材料但现场安全确认已勾时，退到底盘试动 `sendManualMotion("forward")`，不再提示普通用户先记录现场画面。
- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`：轮速进度、下一步、保存按钮禁用文案统一改成 `底盘试动读取轮速 / 非零 L/R`，明确画面只影响旧 first-jog 材料和建图验收。
- `pc-tools/workstation/test/App.test.ts`：更新轮速进度断言，并覆盖画面材料缺失时 `plain-wheel-trial` 可直接调用固定 `/api/robot-control/base/manual`，且不调用 `/api/robot-control/base/first-jog`。
- `pc-tools/README.md`、`docs/product/pc_tools_workstation.md`：同步记录轮速卡底盘兜底的用户口径和安全边界。

## 验证结果

- 通过：`cd pc-tools/workstation && npm test -- --run test/App.test.ts -t "non-stop motion disabled|current wheel L/R|static zero wheel"`，结果 `1 passed (1)`，`3 passed | 201 skipped (204)`。
- 初次全量 `cd pc-tools/workstation && npm test` 失败于 `shows wheel readback pending in current facts` 的旧断言；根因是测试假设页面全程没有 manual 调用，本轮新路径允许其它入口用 manual，但该用例真正要守的是“只读轮速刷新不新增 manual”。已改为比较刷新前后 manual 调用数。
- 通过：`cd pc-tools/workstation && npm test -- --run test/App.test.ts -t "wheel readback pending"`，结果 `1 passed (1)`，`1 passed | 203 skipped (204)`。
- 通过：`cd pc-tools/workstation && npm test`，结果 `2 passed (2)`，`352 passed (352)`。
- 通过：`cd pc-tools/workstation && npm run lint`。
- 通过：`cd pc-tools/workstation && npm run build`；Vite 仍提示既有 chunk size warning。
- 通过：`git diff --check`。

## 剩余风险

- 本轮只改 PC 普通首屏轮速卡入口和 mock 测试，不触发真实底盘试动、真实 first-jog、真实键盘手控或 `/cmd_vel`。
- 真实 wheel raw L/R 非零仍需要在上位机/实车上用底盘试动或键盘连续手控产生 during-motion T1001 证据后闭环。
