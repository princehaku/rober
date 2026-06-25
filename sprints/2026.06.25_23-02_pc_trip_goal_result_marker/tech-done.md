# PC 行程终点结果 marker

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 普通首屏地图上的行程终点 marker 从泛化 `终点/本轮目标` 改为直接显示执行证据：`已到达`、`到达缺反馈`、`旧到达` 或 `行程未通过`。
  - marker 仍只来自 Nav2 execution/latest readback 的目标坐标和状态，不生成新目标、不触发执行。
- `pc-tools/workstation/src/styles.css`
  - 为新的终点结果状态复用并扩展现有色彩层级：完整到达为蓝色，缺反馈/旧到达为黄色，未通过为虚线。
- `pc-tools/workstation/test/App.test.ts`
  - 更新完整到达用例断言，新增缺反馈目标坐标和 `到达缺反馈` marker 断言。
- `docs/product/pc_tools_workstation.md`
  - 同步记录地图终点 marker 的 WYSIWYG 口径和安全边界。

## 验证结果

- 通过：`npm test -- -t "route|Nav2 success without feedback|pending route goal"`，2 个测试文件、19 个相关用例通过。
- 通过：`npm run lint`。
- 通过：`npm test`，2 个测试文件、171 个用例全部通过。
- 通过：`npm run build`，TypeScript app/server 编译与 Vite production build 通过。
- 通过：`git diff --check`。
- 通过：`lsof -nP -iTCP:7001 -sTCP:LISTEN`，确认 `node` 监听 `TCP *:7001`。
- 已恢复全量 `npm test` 自动刷新的旧 smoke artifact `checked_at`，避免把历史验证时间戳混入本轮提交。

## 剩余风险

- 本轮是 PC/mock 层 WYSIWYG 展示增量，没有触发真实 Nav2 execute、manual、keyboard pulse、delivery complete、stop 或 `/cmd_vel`。
- 真实完整路线执行仍需要现场执行并读到本轮 `goal_succeeded` 与反馈样本。
