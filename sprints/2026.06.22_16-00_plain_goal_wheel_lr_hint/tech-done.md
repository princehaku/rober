# Plain Goal Wheel L/R Hint

sprint_type: micro

## 实际改动

- 普通首屏“本轮进度”的 `轮速记录` 项现在显示当前 L/R 和已读帧数。
- hint 同时支持 PC summary 的 base readback 和本页刚执行的只读底盘反馈采样结果。
- 补 Vue 测试覆盖 summary 直接给出 `L/R=0/0、12 帧` 时的普通进度提示，以及采样后 `L/R=0/0、3 帧` 的更新提示。
- 更新 `docs/product/pc_tools_workstation.md`。

## 验证结果

- 通过：`npm test`，2 个 test files、121 个 tests 全部通过。
- 通过：`npm run lint`，ESLint 无报错。
- 通过：`npm run build`，完成 `tsc -p tsconfig.app.json && vite build && tsc -p tsconfig.server.json`。
- 通过：`git diff --check`。

## 剩余风险

- 本轮只改善 PC 普通首屏诊断，不执行真实 first-jog/manual。
- 当前真实 wheel raw L/R 仍为 `0/0`，非零证明尚未完成。
