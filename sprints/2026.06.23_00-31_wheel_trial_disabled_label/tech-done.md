# 2026-06-23 00:31 轮速试动禁用态下一步文案

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`：普通首屏 `轮速记录` 的试动按钮在禁用态直接显示下一步动作。
- 禁用态文案包括：未连接时 `连接后试动读轮速`、请求处理中 `等待上一条请求`、送达草稿覆盖试动材料时 `先恢复确认再试动`、缺现场画面时 `先记录画面再试动`。
- `pc-tools/workstation/test/App.test.ts`：补充缺现场画面和需要恢复试动确认两种禁用态按钮文案断言，确认按钮仍保持 disabled。
- `docs/product/pc_tools_workstation.md`：同步记录该改动只改变文案，不改变 first-jog gate 或 preflight。

## 验证结果

- `npm test`：通过，`2 passed (2)`，`125 passed (125)`。
- `npm run lint`：通过，无 ESLint 报错。
- `npm run build`：通过，`tsc -p tsconfig.app.json && vite build && tsc -p tsconfig.server.json` 完成。
- `git diff --check`：通过，无 whitespace error。

## 剩余风险

- 本轮只改善 wheel raw L/R 非零采集前的禁用态提示；真实非零 L/R 仍需要现场 operator 在安全确认后运行 first-jog，并由上位机 during-motion T1001 同帧 L/R 非零证明。
- 本轮没有发送任何真实运动控制、Nav2 执行或送达确认请求。
