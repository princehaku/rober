# PC 键盘停止失败后锁定方向键

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 键盘 release stop 返回失败后，退出 keyboard armed、释放全局键盘 owner，并清空本次连续验证计数。
  - 键盘面板状态显示 `停止失败`，提示 operator 先现场确认小车已停，再重新启用键盘。
  - stop 失败后方向键和屏幕方向按钮保持禁用，避免继续发送新的 manual pulse。
- `pc-tools/workstation/src/styles.css`
  - 新增 `plain-keyboard-control[data-state="停止失败"]` 异常视觉态。
- `pc-tools/workstation/test/App.test.ts`
  - 扩展 release stop rejected 用例，锁定 stop 失败后的禁用方向键、全局按键不再发 manual、重新启用后才恢复按键入口。
- `docs/product/pc_tools_workstation.md`
  - 记录键盘 stop 失败后锁定方向键和清验证计数的产品契约。

## 验证结果

- `npm test -- -t "does not verify keyboard control when release stop is rejected"`：通过，1 passed。
- `npm test -- -t "keeps free-roam map fail-closed when keyboard release stop fails|does not verify keyboard control when release stop is rejected"`：通过，2 passed。
- `npm run lint`：通过。
- `npm run build`：通过；Vite 输出 chunk size warning，但构建成功。
- `npm test`：通过，2 test files passed，201 tests passed。
- 完整测试会刷新两个历史 DOM smoke artifact 的 `checked_at`，本轮已恢复为原始时间戳，避免无关 diff。

## 剩余风险

- 当前仅完成 PC 前端 mock 验证，不触发真实键盘手控、真实 stop 或 WAVE ROVER HIL。
