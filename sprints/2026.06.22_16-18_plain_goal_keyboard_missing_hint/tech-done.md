# Plain Goal Keyboard Missing Hint

sprint_type: micro

## 实际改动

- 普通首屏“本轮进度”的 `键盘手控` 项复用键盘 gate 缺项清单。
- 未满足时显示具体还差项，例如移动前检查、轮速记录、雷达移动记录，而不是泛化提示。
- 补 Vue 测试确认进度区和键盘面板都展示普通缺项提示。
- 更新 `docs/product/pc_tools_workstation.md`。

## 验证结果

- 通过：`npm test`，2 个 test files、121 个 tests 全部通过。
- 通过：`npm run lint`，ESLint 无报错。
- 通过：`npm run build`，完成 `tsc -p tsconfig.app.json && vite build && tsc -p tsconfig.server.json`。
- 通过：`git diff --check`。

## 剩余风险

- 本轮只改善 PC 普通首屏提示，不放开 keyboard/manual gate。
- PC 键盘连续手控仍依赖 wheel raw L/R 非零、LiDAR delta 和 operator report gate 满足。
