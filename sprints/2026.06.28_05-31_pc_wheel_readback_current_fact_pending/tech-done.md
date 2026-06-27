# PC Wheel Readback Current Fact Pending

## sprint_type

micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 普通首屏 `当前事实` 新增轮速只读刷新 pending 行。
  - 当 `刷新当前轮速（只读）` 请求未返回时，明确显示正在刷新当前 `wheel raw L/R`，不会发车，且返回前不把旧 L/R 当作当前轮速结论。
- `pc-tools/workstation/test/App.test.ts`
  - 新增 delayed base feedback samples 测试，锁定 pending 文案、按钮 `刷新中` 状态和不触发 manual/Nav2/delivery/`cmd_vel`。
- `docs/product/pc_tools_workstation.md`
  - 同步普通首屏轮速 pending 展示边界和只读代理安全边界。

## 验证结果

- 通过：`npm test -- --run test/App.test.ts -t "shows wheel readback pending in current facts"`
  - `1 passed | 194 skipped`
- 通过：`npm test`
  - `2 passed`，`342 passed`
- 通过：`npm run lint`
- 通过：`npm run build`
  - Vite 输出 chunk size warning，构建成功。
- 通过：`git diff --check`

## 剩余风险

- 本轮只验证 PC 前端 pending 展示和只读调用边界；不等价于真实小车轮速非零、Nav2 完整路线执行或键盘连续手控 HIL 成功。
