# 2026-06-23 00:40 送达确认全禁用态动作文案

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`：普通首屏 `确认送达` 按钮在所有禁用态都显示具体下一步动作，不再只在已有送达草稿时这样做。
- 新文案覆盖：缺材料时 `确认送达（先准备材料）`，材料已预填但未完成人工确认时 `确认送达（先勾选安全）`，后续继续沿用 `先确认到达`、`先核对材料`、`先确认投放`。
- `pc-tools/workstation/test/App.test.ts`：更新缺材料和预填材料未保存草稿两种期望，确认按钮仍 disabled。
- `docs/product/pc_tools_workstation.md`：同步记录该文案只引导本地 checklist，不提交 operator report、不调用 delivery complete、不发送 Nav2、manual 或 `/cmd_vel`。

## 验证结果

- `npm test`：通过，`2 passed (2)`，`126 passed (126)`。
- `npm run lint`：通过，无 ESLint 报错。
- `npm run build`：通过，`tsc -p tsconfig.app.json && vite build && tsc -p tsconfig.server.json` 完成。
- `git diff --check`：通过，无 whitespace error。

## 剩余风险

- 本轮只改善 delivery success 收口前的按钮可读性；真实 delivery success 仍必须由现场 operator 完成 checklist、提交送达材料并通过上位机 delivery gate。
- 本轮没有发送任何真实运动控制、Nav2 执行或送达确认请求。
