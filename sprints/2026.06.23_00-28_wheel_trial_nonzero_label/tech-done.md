# 2026-06-23 00:28 轮速试动按钮非零目标文案

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`：普通首屏 `轮速记录` 的试动按钮在只读 L/R 已明确为 `0/0` 时显示 `低速试动读非零 L/R`。
- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`：first-jog 已失败但未拿到非零轮速时，按钮显示 `重试低速试动读非零 L/R`；恢复试动确认后显示 `开始低速试动读非零 L/R`。
- `pc-tools/workstation/test/App.test.ts`：补充当前 summary L/R=0/0、恢复试动确认后、试动失败重试三种文案断言。
- `docs/product/pc_tools_workstation.md`：同步说明该改动只改按钮文案，不改变 first-jog gate、固定低速短时参数或 operator material 前置条件。

## 验证结果

- `npm test`：通过，`2 passed (2)`，`125 passed (125)`。
- `npm run lint`：通过，无 ESLint 报错。
- `npm run build`：通过，`tsc -p tsconfig.app.json && vite build && tsc -p tsconfig.server.json` 完成。
- `git diff --check`：通过，无 whitespace error。

## 剩余风险

- 本轮只降低 wheel raw L/R 非零采集的操作歧义；真实非零 L/R 仍需要现场 operator 在安全确认后运行 first-jog，并由上位机 during-motion T1001 同帧 L/R 非零证明。
- 本轮没有发送任何真实运动控制、Nav2 执行或送达确认请求。
