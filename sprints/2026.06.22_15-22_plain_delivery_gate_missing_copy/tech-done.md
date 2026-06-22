# Plain Delivery Gate Missing Copy

- sprint_type: micro
- owner: User Touchpoint Full-Stack Engineer
- date: 2026-06-22

## 实际改动

- 普通首屏 `任务收口` 新增 `上位机还差：...` 提示，把 delivery gate blocked reasons 映射成普通用户能理解的确认项。
- 映射覆盖当前真实上位机缺口：现场确认报告、已观察到到达/移动、已观察到停止、确认已投放/送达、最后点击确认送达。
- 补测试确认首屏显示普通缺口文案，同时不暴露后端字段名、不自动提交 operator report、不调用 delivery complete。
- 更新 `docs/product/pc_tools_workstation.md`。

## 验证结果

- 通过：`npm test`，2 个 test files、118 个 tests 全部通过。
- 通过：`npm run lint`。
- 通过：`npm run build`，完成 `tsc -p tsconfig.app.json && vite build && tsc -p tsconfig.server.json`。
- 通过：`git diff --check`。

## 剩余风险

- 本轮只改善 PC 首屏可理解性，不完成真实 delivery success。
- 真实上位机当前仍缺 wheel raw L/R 非零、LiDAR motion delta、operator observed motion/stop 和最终送达确认。
