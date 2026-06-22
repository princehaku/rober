# Plain Wheel Record Status

sprint_type: micro

## 实际改动

- PC 普通首屏 `移动/导航` 卡片新增常驻“轮速记录”小面板，不再等 first-jog 成功后才临时出现保存按钮。
- 轮速记录状态压缩为普通话术：`待准备`、`待试动`、`可保存`、`待重试`、`保存中`、`已保存`。
- `保存轮速记录` 按钮始终可见但默认禁用；只有 first-jog 返回 during-motion L/R 非零证明后才允许保存。
- 保存动作仍复用既有 `savePlainWheelEvidence`，只写 operator report，不再次发送运动命令，不补 LiDAR、route 或 delivery。
- 更新 Vue 测试，覆盖默认禁用、first-jog 后可保存、保存后普通首屏显示已保存，并保持首屏禁词不泄露。

## 验证结果

- 通过：`npm test`，Vitest `2 passed (2)`，`113 passed (113)`。
- 通过：`npm run lint`，ESLint 无报错。
- 通过：`npm run build`，`tsc` 与 Vite production build 通过。
- 通过：`git diff --check`，无 whitespace error。

## 资料来源

- 本轮只改 PC UI 与测试，没有修改硬件协议。
- 轮速字段说明沿用 `docs/vendor/VENDOR_INDEX.md` 指向的 WAVE ROVER UART JSON 资料：`T=1001` 中 `L/R` 是底盘反馈字段。

## 剩余风险

- 本轮不触发真实 first-jog；真实 wheel raw L/R 非零仍需要现场安全确认后执行并由上位机返回 during-motion T1001 L/R 非零。
- 完整 Nav2 路线执行和 delivery success 仍未由本轮证明。
