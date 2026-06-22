# Restore Button In Wheel Panel

sprint_type: micro

## 实际改动

- 将普通首屏 `恢复试动确认` 按钮从移动/导航顶部动作行移动到“轮速记录”小面板。
- “轮速记录”现在同时包含当前状态、恢复试动确认、保存轮速记录，和当前真实 blocker 的提示处于同一上下文。
- 按钮行为不变：仍调用既有 `restorePlainFirstJogMaterial`，只提交 first-jog 前置 basic safety report，不发送运动命令。
- 更新 Vue 测试，确保送达草稿覆盖 latest operator report 时，“轮速记录”面板内可见 `恢复试动确认`。

## 验证结果

- 通过：`npm test`，Vitest `2 passed (2)`，`114 passed (114)`。
- 通过：`npm run lint`，ESLint 无报错。
- 通过：`npm run build`，`tsc` 与 Vite production build 通过。
- 通过：`git diff --check`，无 whitespace error。

## 剩余风险

- 本轮只是移动按钮位置，不触发真实 first-jog。
- wheel raw L/R 非零、完整 Nav2 路线执行、delivery success 仍需要现场安全确认和真实执行证据。
