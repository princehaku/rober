# 2026.07.02 25:05 键盘连续手控焦点合同

sprint_type: micro

## 实际改动

- 在 PC 普通首屏键盘连续手控面板补充焦点/输入区安全合同：
  - 启用键盘后面板自动聚焦。
  - 只有本页非输入区的 W/A/S/D 或方向键会进入连续手控。
  - 输入框内按键只输入文字，不触发运动。
- DOM 新增 `data-keyboard-event-scope`、`data-keyboard-auto-focus-after-arm`、`data-keyboard-editable-fields-block-motion`、`data-keyboard-global-listener-owner-required` 和 `data-keyboard-input-fields-safe`，方便现场 smoke 和脚本直接读回。
- 同步更新 PC 工作站产品文档。

## 验证结果

- 通过：`cd pc-tools/workstation && npm test -- --run App.test.ts`（1 file / 237 tests passed）
- 通过：`git diff --check`
- 通过：`cd pc-tools/workstation && npm run build`（Vite 仅提示 chunk size warning）
- 通过：`cd pc-tools/workstation && npm run lint`

## 剩余风险

- 本轮只验证 PC 前端焦点和 DOM 合同，没有对真实小车执行键盘手控 HIL；真实 wheel L/R 非零和 stop 收口仍需现场验证。
