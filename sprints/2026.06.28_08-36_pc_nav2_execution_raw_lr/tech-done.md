# PC Nav2 Execution Raw L/R Micro Sprint

## sprint_type

micro

## 实际改动

- `pc-tools/workstation/src/server/index.ts`：Nav2 goal execution/latest 的 key-values 新增
  `base_feedback_latest_raw_left` 和 `base_feedback_latest_raw_right`，并兼容 `raw_left/raw_right`、
  `left_raw/right_raw`、`L/R` 和旧 `left_speed/right_speed` 字段。
- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`：普通首屏行程执行 L/R 显示优先使用 raw L/R，
  旧响应缺 raw 字段时再退回 speed 别名，避免用户验收口径被旧字段名遮住。
- `pc-tools/workstation/test/App.test.ts` 与 `pc-tools/workstation/test/catalog.test.ts`：补充 raw L/R
  透传和前端优先显示 raw 的回归覆盖。
- `pc-tools/README.md` 与 `docs/product/pc_tools_workstation.md`：同步记录 PC 侧 raw L/R 只读口径。

## 验证结果

- 通过：`cd pc-tools/workstation && npm test -- --run test/App.test.ts -t "keeps Nav2 success with IMU motion signal out of complete route evidence until wheel raw L/R is nonzero"`
  - 结果：1 passed，203 skipped。
- 通过：`cd pc-tools/workstation && npm test -- --run test/catalog.test.ts -t "Nav2 latest execution proxy reads fixed GET artifact without replaying navigation"`
  - 结果：1 passed，147 skipped。
- 通过：`cd pc-tools/workstation && npm test`
  - 结果：2 files passed，352 tests passed。
- 通过：`cd pc-tools/workstation && npm run lint`
  - 结果：`eslint .` 无错误。
- 通过：`cd pc-tools/workstation && npm run build`
  - 结果：TypeScript 与 Vite build 通过；Vite 仍提示单 chunk 超过 500 kB 的既有体积 warning。
- 通过：`git diff --check`
  - 结果：无 whitespace error。

## 剩余风险

- 本轮是 PC 只读显示和代理 key-values 修正，没有连接真实小车执行 Nav2、manual、keyboard 或 `/cmd_vel`。
- 如果真实上位机 artifact 完全不输出 raw/speed 任一字段，PC 仍会显示 `not_observed`，不会伪造 wheel raw L/R 非零。
