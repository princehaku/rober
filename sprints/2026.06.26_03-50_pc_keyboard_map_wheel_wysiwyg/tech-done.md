# 2026-06-26 03:50 PC 键盘扫图地图轮速提示

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 普通首屏扫图方向 marker 在按住键盘/屏幕方向键后同步显示轮速结论：`轮速非零` 或 `轮速待非零`。
  - marker 的可访问说明同步包含本次连续脉冲进度和 L/R 读数，让地图、键盘状态行和扫图状态三处口径一致。
  - 扫图流程 marker 的 `扫图移动中` 说明也补充连续脉冲进度和 L/R 读数。
- `pc-tools/workstation/test/App.test.ts`
  - 扩展 free-roam keyboard 流程组件测试，覆盖地图方向 marker 和流程 marker 的轮速/连续脉冲 WYSIWYG 文案。
- `docs/product/pc_tools_workstation.md`
  - 记录键盘连续手控轮速结论同步到地图 marker。

## 验证结果

- 通过：`npm test -- -t "keeps free-roam keyboard locked until map recording starts"`
  - `Test Files 1 passed | 1 skipped (2)`
  - `Tests 1 passed | 177 skipped (178)`
- 通过：`npm run lint`
- 通过：`npm run build`
  - `vite v7.3.3 building client environment for production`
  - `dist/assets/index-CF929f3l.js 473.92 kB`
- 通过：`npm test`
  - `Test Files 2 passed (2)`
  - `Tests 178 passed (178)`
- 通过：`git diff --check`
- 通过：`lsof -nP -iTCP:7001 -sTCP:LISTEN`
  - `node 90259 ... TCP *:7001 (LISTEN)`

## 剩余风险

- 本轮只覆盖 PC 前端状态和 mock 组件测试，不触发真实上位机建图、manual、keyboard pulse、Nav2、delivery、stop 或 `/cmd_vel`。
- 真实现场仍需 operator 在 `0.0.0.0:7001` 上按住方向键扫图，复核地图 marker 与实际底盘反馈是否一致。
