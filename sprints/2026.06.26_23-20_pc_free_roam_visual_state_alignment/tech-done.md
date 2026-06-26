# PC Free Roam Visual State Alignment

sprint_type: micro

## 实际改动

- 修改 `pc-tools/workstation/src/styles.css`：为 `扫地式建图` 新状态 `可移动` 与 `可建图` 补齐卡片外层视觉态。
- 同步状态 chip 样式：`可移动` 使用提示色，`可建图` 使用完成色，避免普通首屏文案和视觉反馈脱节。
- 修改 `pc-tools/workstation/test/App.test.ts`：新增 CSS 选择器断言，锁定 `.plain-free-roam-map[data-state="可移动/可建图"]` 与 `.status-chip[data-state="可移动/可建图"]`。
- 更新 `docs/product/pc_tools_workstation.md`：记录 2026-06-26 23:20 起 `可移动/可建图` 的 WYSIWYG 视觉合同。

## 验证结果

- `cd pc-tools/workstation && npm test -- App.test.ts`：通过，`141 passed`。
- `cd pc-tools/workstation && npm run build`：通过，仅保留既有 Vite chunk size warning。
- `git diff --check`：通过。

## 剩余风险

- 本轮是 PC 前端视觉态修正，没有真实上车 HIL。
- `可移动` 仍只代表 PC 允许进入低速移动流程，不证明底盘轮速 L/R 已非零；真实运动证据仍需现场验证。
