# PC 移动首屏最小预检文案

sprint_type: micro

## 实际改动

- 修改 `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`：
  - 普通首屏 `移动/导航` 总状态不再提示“先记录现场画面，再试动一下”。
  - 未勾安全确认时显示：勾安全确认后可底盘试动、键盘手控或执行已准备行程；画面记录不是发车前置。
  - 已勾安全确认时显示：可底盘试动或启用键盘；相机和雷达只影响建图验收。
  - 历史 `试动一下` 被 first-jog 材料挡住时，提示改用 `底盘试动`，避免继续误导成复杂预检。
- 修改 `pc-tools/workstation/test/App.test.ts`：
  - 更新普通首屏、共享安全确认、first-jog 恢复、底盘试动相关断言，锁定“勾安全确认即可进入普通移动入口”的口径。
- 更新 `docs/product/pc_tools_workstation.md`：
  - 同步记录 2026-06-27 后的最小预检 UX 边界。

## 验证结果

- 通过：`cd pc-tools/workstation && npm test -- App.test.ts --testNamePattern "plain|底盘试动|安全确认|first-jog|移动/导航|keyboard|键盘"`（59 tests）
- 通过：`cd pc-tools/workstation && npm test`（313 tests）
- 通过：`cd pc-tools/workstation && npm run lint`
- 通过：`cd pc-tools/workstation && npm run build`
- 通过：`git diff --check`

## 剩余风险

- 本轮没有发送真实底盘试动、键盘手控、Nav2 或自由移动命令。
- live 仍显示 Nav2 action 成功但 wheel raw L/R=0/0；真实底盘运动需要现场安全确认后复验。
