# Keyboard Fixed Endpoint Aliases

## sprint_type

micro

## 目标

- 修复 `GET /api/robot-control/summary` 顶层 `fixed_keyboard_manual_endpoint` 和 `fixed_keyboard_stop_endpoint` 为 `null` 的问题。
- 让现场脚本只读 summary 顶层即可确认键盘连续控制的固定 manual/stop 端点和按住后复验链路。

## 实际改动

- `pc-tools/workstation/src/server/robotControlSummary.ts`
  - 顶层透出 `fixed_keyboard_manual_endpoint` 和 `fixed_keyboard_stop_endpoint`。
- `pc-tools/workstation/src/shared/contracts.ts`
  - 补齐 summary 顶层键盘 fixed endpoint alias 类型。
- `pc-tools/workstation/test/robotControlSummary.test.ts`
  - 增加顶层 fixed manual/stop endpoint 断言。
- `docs/product/pc_tools_workstation.md`
  - 同步记录 summary 顶层键盘固定端点 alias 合同。

## 验证结果

- `npm test -- --run robotControlSummary.test.ts App.test.ts catalog.test.ts`
  - 通过：`Test Files 3 passed (3)`、`Tests 428 passed (428)`。
- `npm run lint`
  - 通过。
- `git diff --check`
  - 通过。
- `npm run build`
  - 通过；Vite 仍提示既有 bundle 大小 warning。
- 重启 PC Node：
  - 通过；`node` 监听 `*:7001`。
- 只读 smoke：
  - `fixed_keyboard_manual_endpoint=/api/robot-control/base/manual`。
  - `fixed_keyboard_stop_endpoint=/api/robot-control/base/stop`。
  - `manual_nested_same=true`、`stop_nested_same=true`、`feedback_nested_same=true`、`summary_nested_same=true`。

## 剩余风险

- 本轮只补 summary 顶层只读 alias，不执行或证明真实键盘连续运动；真实完成仍需现场勾安全确认后按住 W/A/S/D 或方向键，并读取同窗口 wheel L/R 非零与松开后 stop 证据。
