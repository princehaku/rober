# tech-done

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/server/robotControlSummary.ts`：`field_acceptance_packet` 和 summary 顶层新增主缺口证据复验口径：readback method、是否必须先运动、是否需先安全确认、是否阻塞现场验收。
- `pc-tools/workstation/src/shared/contracts.ts`：补齐新增字段类型。
- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`：普通首屏 field acceptance 总包、剩余动作区和缺失证据区同步暴露 `data-primary-missing-evidence-*` 复验口径。
- `pc-tools/workstation/test/robotControlSummary.test.ts`、`pc-tools/workstation/test/App.test.ts`：覆盖 API 和 DOM 字段。
- `pc-tools/README.md`、`docs/product/pc_tools_workstation.md`：同步说明这些字段只区分只读复验/执行后复验，不触发任何运动。

## 验证结果

- `git diff --check`：通过。
- `npm test -- robotControlSummary.test.ts App.test.ts`：2 files / 246 tests passed。
- `npm run lint`：通过。
- `npm run build`：通过；仅保留 Vite chunk size warning。

## 剩余风险

- 本切片只改验收可读性，不执行实车 Nav2、键盘、自由移动、建图或 stop；主缺口仍需现场安全确认后执行对应动作再复验。
