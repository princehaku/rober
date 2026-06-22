# 2026-06-23 00:34 轮速保存禁用态下一步文案

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`：普通首屏 `保存轮速记录` 按钮在禁用态显示当前下一步，而不是统一显示 `等非零 L/R`。
- 新文案包括：缺现场画面时 `保存轮速记录（先记录画面）`，送达草稿覆盖试动材料时 `保存轮速记录（先恢复确认）`，材料已齐但还没试动时 `保存轮速记录（先试动）`，试动后仍未拿到非零 L/R 时 `保存轮速记录（等非零 L/R）`。
- `pc-tools/workstation/test/App.test.ts`：补充默认待试动、summary L/R=0/0、缺现场画面、恢复试动确认和试动后 0/0 五种按钮文案断言。
- `docs/product/pc_tools_workstation.md`：同步记录按钮启用条件不变，仍只允许保存本轮 first-jog during-motion 同帧非零 L/R 材料。

## 验证结果

- `npm test`：通过，`2 passed (2)`，`125 passed (125)`。
- `npm run lint`：通过，无 ESLint 报错。
- `npm run build`：通过，`tsc -p tsconfig.app.json && vite build && tsc -p tsconfig.server.json` 完成。
- `git diff --check`：通过，无 whitespace error。

## 剩余风险

- 本轮只改善 wheel raw L/R 非零证据保存前的禁用态提示；真实非零 L/R 仍需要现场 operator 安全试动，并由上位机 during-motion T1001 同帧 L/R 非零证明。
- 本轮没有发送任何真实运动控制、Nav2 执行或送达确认请求。
