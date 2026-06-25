# PC 键盘连续手控 L/R 实时状态

## sprint_type

micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 新增 `keyboardLastWheelFeedbackValues`，在键盘 manual pulse 返回 `remote_motion_key_values` 时记录最近一次轮速读回。
  - 普通键盘 live status 在按住方向键时显示 `轮速 L/R=...` 和非零状态，帮助现场确认连续手控有没有读到 wheel feedback。
  - 扫地式建图 `扫图状态` 同步显示同一 L/R 摘要，让“正在扫图”和“轮速是否非零”同屏可见。
  - 不改变键盘 armed/gate、速度、duration、stop 兜底、后端 endpoint 或 `/cmd_vel` 边界。
- `pc-tools/workstation/test/App.test.ts`
  - 更新 free-roam keyboard 测试 fixture，模拟键盘 manual pulse 返回 `wheel_feedback_latest_raw_left/right` 和 `wheel_feedback_lr_nonzero_proven=true`。
  - 断言普通键盘状态和扫图状态都显示 `轮速 L/R=0.07/0.08，非零已读到`，同时保持原有 Nav2 execute / delivery complete 不被触发的断言。
- `docs/product/pc_tools_workstation.md`
  - 记录普通首屏按住键盘时的 L/R 可见规则和安全边界。

## 验证结果

- `npm test -- --testNamePattern "keeps free-roam keyboard locked until map recording starts"`：通过，1 passed / 168 skipped。
- `npm run lint`：通过。
- `npm test`：通过，2 files / 169 tests passed。
- `npm run build`：通过，`tsc -p tsconfig.app.json && vite build && tsc -p tsconfig.server.json` 成功。
- `lsof -nP -iTCP:7001 -sTCP:LISTEN`：`node` 监听 `TCP *:7001`。

## 剩余风险

- 本轮没有触发真实 Nav2 execute、delivery complete、map start、radar start 或 `/cmd_vel`；测试中的 stop/manual 都是 mocked PC API。
- wheel raw L/R 非零仍以真实上位机返回的 motion window evidence 为准；本轮只把已返回的 L/R 摘要显示到普通首屏。
