# 2026-06-23 00:25 送达确认按钮下一步文案

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`：新增 `plainDeliveryConfirmBlockedLabel`，已有送达草稿但最终 checklist 未齐时，`确认送达` 按钮按当前第一组缺口显示更具体的下一步。
- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`：按钮文案从抽象的 `先确认 N 项` 细化为 `先勾选安全`、`先确认到达`、`先核对材料`、`先确认投放` 等普通动作。
- `pc-tools/workstation/test/App.test.ts`：更新送达草稿 readback 和只剩投放确认两条回归，确认按钮文案更贴近现场操作。
- `docs/product/pc_tools_workstation.md`：同步说明该文案只引导本地 checklist，不提交 operator report、不调用 delivery complete、不发送 Nav2、manual 或 `/cmd_vel`。

## 验证结果

- `npm test`：通过，`2 passed (2)`，`125 passed (125)`。
- `npm run lint`：通过，无 ESLint 报错。
- `npm run build`：通过，`tsc -p tsconfig.app.json && vite build && tsc -p tsconfig.server.json` 完成。
- `git diff --check`：通过，无 whitespace error。

## 剩余风险

- 本轮只改善 PC 普通首屏 delivery success 收口的下一步可读性；真实 delivery success 仍必须由现场 operator 完成 checklist、提交送达材料并通过上位机 delivery gate。
- 本轮没有发送任何真实运动控制、Nav2 执行或送达确认请求。
