# PC Nav2 Current Fact Raw L/R Micro Sprint

## sprint_type

micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`：普通首屏 `当前事实` 的 Nav2 行程成功/待复验文案改为复用
  `nav2BaseFeedbackPair()`，优先显示 raw L/R；wheel 已复验时显示 `轮速已复验 L/R=...`。
- `pc-tools/workstation/test/App.test.ts`：将 ROS 复验成功 fixture 的 raw L/R 设置为不同于旧 speed 的值，
  并断言 `当前事实` 显示 raw L/R，避免后续回退到旧 speed 字段。
- `pc-tools/README.md` 与 `docs/product/pc_tools_workstation.md`：同步记录 PC 只读 current fact raw L/R 口径。

## 验证结果

- 通过：`cd pc-tools/workstation && npm test -- --run test/App.test.ts -t "keeps the summary-requested ROS rerun visible for an old PWM route with zero wheel readback"`
  - 结果：1 passed，203 skipped。
- 通过：`cd pc-tools/workstation && npm test`
  - 结果：2 files passed，352 tests passed。
- 通过：`cd pc-tools/workstation && npm run lint`
  - 结果：`eslint .` 无错误。
- 通过：`cd pc-tools/workstation && npm run build`
  - 结果：TypeScript 与 Vite build 通过；Vite 仍提示单 chunk 超过 500 kB 的既有体积 warning。
- 通过：`git diff --check`
  - 结果：无 whitespace error。

## 剩余风险

- 本轮没有连接真实小车执行 Nav2，只用 PC/Vitest fixture 验证 summary/latest 显示口径。
- 若真实上位机 artifact 同时缺 raw 和 speed 字段，PC 仍会显示缺失/占位，不会伪造 wheel raw L/R。
