sprint_type: micro

# PC 键盘安全确认提示

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue` 在普通首屏键盘区新增 `plain-keyboard-safety-summary`。
- 未勾安全确认时显示“键盘手控：勾选安全确认后即可启用；按住方向键才会动。”
- 勾上同一安全确认后显示“键盘手控：安全确认已完成；现在可启用键盘，按住方向键才会动。”
- `pc-tools/workstation/test/App.test.ts` 扩展共享安全确认测试，断言勾选只改变 UI gate，不自动调用 manual、stop 或 Nav2 execute。
- `docs/product/pc_tools_workstation.md` 同步记录该提示和不自动发车边界。

## 验证结果

- `npm test -- test/App.test.ts -t "reuses one plain safety confirmation"`：通过，1 passed / 121 skipped。
- `npm test -- test/App.test.ts`：通过，122 passed。
- `npm test`：通过，2 files / 219 passed。
- `npm run build`：通过；Vite 仍有既有 chunk size warning。
- `npm run lint`：通过。
- `git diff --check`：通过。

## 剩余风险

- 该改动只让键盘入口的普通用户路径更清楚；完整 PC 键盘连续手控仍需要 operator 点击“启用键盘”并按住方向键，且 stop 收口成功后才算验证完成。
