# PC 键盘轮速验收口径前置

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/shared/contracts.ts`
  - `RobotControlKeyboardReadbackSummary` 新增 `wheel_feedback_acceptance_plain`。
- `pc-tools/workstation/src/server/robotControlSummary.ts`
  - `readback_summary.keyboard`、`keyboard_control`、`keyboard_teleop` 同步输出键盘轮速验收口径。
- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 普通首屏键盘事实行展示“同一次按住窗口 / manual pulse 回包 / wheel L/R 非零”的验收口径。
- `pc-tools/workstation/test/catalog.test.ts`、`pc-tools/workstation/test/App.test.ts`
  - 增加 API 和 DOM 断言，锁定该字段不丢失。
- `docs/product/pc_tools_workstation.md`、`docs/process/okr_progress_log.md`
  - 同步记录只读合同、安全边界和 Objective 3/5 进展。

## 验证结果

- 通过：`npm --prefix pc-tools/workstation test -- catalog.test.ts -t "Robot Control summary proxies"`，1 passed / 167 skipped。
- 通过：`npm --prefix pc-tools/workstation test -- App.test.ts -t "safety confirmation"`，4 passed / 214 skipped。
- 通过：`npm --prefix pc-tools/workstation test -- App.test.ts -t "does not verify keyboard control when release stop is rejected"`，1 passed / 217 skipped。
- 通过：`npm --prefix pc-tools/workstation test`，2 个测试文件、386 个用例通过。
- 通过：`npm --prefix pc-tools/workstation run build`，TypeScript app/server 编译和 Vite build 通过；仅保留既有 chunk size warning。
- 通过：`git diff --check`。
- 通过：重启 PC API 到 `0.0.0.0:7001`，`lsof -nP -iTCP:7001 -sTCP:LISTEN` 显示 `node *:7001 (LISTEN)`。
- 通过：只读请求 `http://127.0.0.1:7001/api/robot-control/summary`，`readback_summary.keyboard.wheel_feedback_acceptance_plain` 返回“同一次按住窗口 / manual pulse 回包 / wheel L/R 非零”的验收口径。

## 剩余风险

- 本轮只补 PC summary/UI 文案和测试合同，不启用键盘、不发送 manual、stop、Nav2、free-roam、delivery 或 `/cmd_vel`。
- 真实键盘连续控制仍需现场勾选安全确认后按住方向键复验，并在同一次按住窗口的 manual pulse 回包里读到 wheel L/R 非零。
