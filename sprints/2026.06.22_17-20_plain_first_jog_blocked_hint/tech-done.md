# Plain First-Jog Blocked Hint Micro Sprint

## sprint_type

micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 新增 `plainFirstJogBlockedHint`。
  - 普通 `移动/导航` 卡片在 `试动一下` 被禁用时显示普通原因，例如需要先连接小车、等待上一条请求、先恢复试动确认或先记录现场画面。
  - 文案不暴露 endpoint、HIL、proof 或 raw feedback 等工程细节。
- `pc-tools/workstation/test/App.test.ts`
  - 扩展送达草稿覆盖场景测试：恢复前显示“试动按钮已锁定：请先点恢复试动确认。”，恢复后提示消失且按钮解锁。
- `docs/product/pc_tools_workstation.md`
  - 同步记录普通禁用原因行为。

## 验证结果

- `npm test`
  - 通过：`Test Files 2 passed (2)`，`Tests 111 passed (111)`。
- `npm run lint`
  - 通过：`eslint .` 无报错。
- `npm run build`
  - 通过：`tsc -p tsconfig.app.json && vite build && tsc -p tsconfig.server.json`。

## 剩余风险

- 本轮没有执行真实 first-jog/manual。
- wheel raw L/R 非零仍需现场恢复试动确认后运行 during-motion 采集。
- delivery success 仍不能宣称完成。
